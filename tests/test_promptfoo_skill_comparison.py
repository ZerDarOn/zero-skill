import json
from pathlib import Path
import runpy
import subprocess
import tempfile
import unittest
from unittest import mock


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "evaluations"
    / "promptfoo"
    / "prepare_skill_comparison.py"
)
RUN_MODULE_PATH = MODULE_PATH.with_name("run_skill_comparison.py")


class PromptfooSkillComparisonTests(unittest.TestCase):
    def setUp(self):
        self.module = runpy.run_path(str(MODULE_PATH))
        self.run_module = runpy.run_path(str(RUN_MODULE_PATH))
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        (self.root / "skills" / "ours").mkdir(parents=True)
        (self.root / "skills" / "ours" / "SKILL.md").write_text(
            "---\nname: ours\ndescription: test\n---\n\nUse evidence.\n",
            encoding="utf-8",
        )
        (self.root / "skills" / "ours" / "references").mkdir()
        (self.root / "skills" / "ours" / "references" / "example.md").write_text(
            "example\n", encoding="utf-8"
        )
        (self.root / "upstream").mkdir()
        (self.root / "upstream" / "SKILL.md").write_text(
            "---\nname: upstream\ndescription: test\n---\n\nBe concise.\n",
            encoding="utf-8",
        )
        (self.root / "cases.json").write_text(
            json.dumps(
                [
                    {
                        "id": "C01",
                        "purpose": "preserve evidence",
                        "prompt": "Rewrite this synthetic note.",
                        "hard_criteria": ["Keep the date", "Do not invent facts"],
                        "expected_output": "SYNTHETIC",
                    }
                ]
            ),
            encoding="utf-8",
        )
        self.spec_path = self.root / "promptfoo.json"
        self.spec_path.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "id": "sample-three-arm",
                    "cases": "cases.json",
                    "model": "gpt-5.6-sol",
                    "reasoning_effort": "medium",
                    "repetitions": 3,
                    "common_prompt": "Complete the synthetic task.",
                    "arms": [
                        {"id": "baseline", "skill": None},
                        {
                            "id": "ours",
                            "skill": {
                                "id": "ours",
                                "source": "skills/ours",
                                "invocation": "explicit",
                            },
                        },
                        {
                            "id": "upstream",
                            "skill": {
                                "id": "upstream",
                                "source": "upstream",
                                "install_mode": "home",
                                "invocation": "explicit",
                            },
                        },
                    ],
                }
            ),
            encoding="utf-8",
        )

    def tearDown(self):
        self.tempdir.cleanup()

    def test_prepares_isolated_native_skill_fixtures_and_frozen_manifest(self):
        output = self.root / "run"
        result = self.module["prepare_comparison"](
            repo_root=self.root,
            spec_path=self.spec_path,
            output_dir=output,
        )

        config = json.loads(
            (output / "prepared" / "promptfooconfig.json").read_text(encoding="utf-8")
        )
        tests = json.loads(
            (output / "prepared" / "tests.json").read_text(encoding="utf-8")
        )
        frozen = json.loads((output / "frozen.json").read_text(encoding="utf-8"))

        self.assertEqual(result, output.resolve())
        self.assertEqual(
            [provider["label"] for provider in config["providers"]],
            ["baseline", "ours", "upstream"],
        )
        self.assertEqual(config["prompts"], ["{{prompt}}"])
        self.assertFalse(config["sharing"])
        self.assertEqual(len(tests), 3)
        self.assertEqual(tests[0]["providers"], ["baseline"])
        self.assertEqual(tests[1]["providers"], ["ours"])
        self.assertEqual(tests[2]["providers"], ["upstream"])
        self.assertEqual(
            tests[0]["assert"], [{"type": "equals", "value": "SYNTHETIC"}]
        )
        self.assertEqual(
            tests[0]["vars"]["prompt"],
            "Complete the synthetic task.\n\nRewrite this synthetic note.",
        )
        self.assertIn("$ours", tests[1]["vars"]["prompt"])
        self.assertIn("$upstream", tests[2]["vars"]["prompt"])
        self.assertEqual(tests[1]["metadata"]["invocation"], "explicit")
        self.assertNotIn("hard_criteria", tests[0]["vars"])
        self.assertEqual(
            tests[0]["metadata"]["hard_criteria"],
            ["Keep the date", "Do not invent facts"],
        )
        self.assertFalse(
            (output / "prepared" / "fixtures" / "baseline" / ".agents").exists()
        )
        copied = (
            output
            / "prepared"
            / "fixtures"
            / "ours"
            / ".agents"
            / "skills"
            / "ours"
        )
        self.assertEqual(
            (copied / "SKILL.md").read_text(encoding="utf-8"),
            (self.root / "skills" / "ours" / "SKILL.md").read_text(encoding="utf-8"),
        )
        self.assertTrue((copied / "references" / "example.md").is_file())
        upstream_fixture = output / "prepared" / "fixtures" / "upstream"
        self.assertFalse((upstream_fixture / ".agents").exists())
        upstream_snapshot = (
            output / "prepared" / "skills" / "upstream" / "upstream"
        )
        self.assertTrue((upstream_snapshot / "SKILL.md").is_file())
        self.assertEqual(frozen["arms"][2]["install_mode"], "home")
        self.assertEqual(frozen["arms"][1]["invocation"], "explicit")
        provider_config = config["providers"][2]["config"]
        self.assertEqual(provider_config["sandbox_mode"], "read-only")
        self.assertEqual(frozen["constraints"]["sandbox_mode"], "read-only")
        self.assertIn(
            "/upstream/.codex",
            provider_config["cli_env"]["CODEX_HOME"],
        )
        self.assertIn("/upstream", provider_config["cli_env"]["HOME"])
        self.assertIn("/upstream", provider_config["cli_env"]["USERPROFILE"])
        self.assertFalse(provider_config["skip_git_repo_check"])
        self.assertFalse(provider_config["web_search_enabled"])
        self.assertEqual(
            provider_config["cli_config"]["features"],
            {"apps": False, "plugins": False, "multi_agent": False},
        )
        self.assertFalse(
            provider_config["cli_config"]["apps"]["_default"]["enabled"]
        )
        self.assertEqual(
            frozen["spec_sha256"], self.module["sha256_file"](self.spec_path)
        )
        self.assertEqual(
            frozen["cases_sha256"],
            self.module["sha256_file"](self.root / "cases.json"),
        )
        self.assertEqual(
            frozen["arms"][1]["skill_package_sha256"],
            self.module["package_sha256"](self.root / "skills" / "ours"),
        )
        self.assertNotIn("auth", json.dumps(frozen).lower())

    def test_implicit_invocation_keeps_natural_prompt_identical_across_arms(self):
        spec = json.loads(self.spec_path.read_text(encoding="utf-8"))
        spec["arms"] = spec["arms"][:2]
        spec["arms"][1]["skill"]["invocation"] = "implicit"
        spec["sandbox_mode"] = "workspace-write"
        self.spec_path.write_text(json.dumps(spec), encoding="utf-8")

        output = self.root / "implicit-run"
        self.module["prepare_comparison"](
            repo_root=self.root,
            spec_path=self.spec_path,
            output_dir=output,
        )
        tests = json.loads(
            (output / "prepared" / "tests.json").read_text(encoding="utf-8")
        )
        config = json.loads(
            (output / "prepared" / "promptfooconfig.json").read_text(encoding="utf-8")
        )
        frozen = json.loads((output / "frozen.json").read_text(encoding="utf-8"))

        self.assertEqual(tests[0]["vars"]["prompt"], tests[1]["vars"]["prompt"])
        self.assertNotIn("$ours", tests[1]["vars"]["prompt"])
        self.assertEqual(tests[1]["metadata"]["invocation"], "implicit")
        self.assertTrue(
            all(
                provider["config"]["sandbox_mode"] == "workspace-write"
                for provider in config["providers"]
            )
        )
        self.assertEqual(frozen["constraints"]["sandbox_mode"], "workspace-write")
        self.assertEqual(
            tests[0]["assert"],
            [
                {"type": "equals", "value": "SYNTHETIC"},
                {"type": "not-skill-used", "value": "ours"},
            ],
        )
        self.assertEqual(
            tests[1]["assert"],
            [
                {"type": "equals", "value": "SYNTHETIC"},
                {"type": "skill-used", "value": "ours"},
            ],
        )
        self.assertTrue(frozen["constraints"]["implicit_skill_trace_assertions"])

    def test_rejects_invalid_sandbox_mode(self):
        spec = json.loads(self.spec_path.read_text(encoding="utf-8"))
        spec["sandbox_mode"] = "danger-full-access"
        self.spec_path.write_text(json.dumps(spec), encoding="utf-8")

        with self.assertRaisesRegex(ValueError, "sandbox_mode"):
            self.module["prepare_comparison"](
                repo_root=self.root,
                spec_path=self.spec_path,
                output_dir=self.root / "run-invalid-sandbox",
            )

    def test_rejects_source_outside_repository(self):
        outside = self.root.parent / "outside-skill"
        outside.mkdir(exist_ok=True)
        try:
            (outside / "SKILL.md").write_text("outside", encoding="utf-8")
            spec = json.loads(self.spec_path.read_text(encoding="utf-8"))
            spec["arms"][1]["skill"]["source"] = str(outside)
            self.spec_path.write_text(json.dumps(spec), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "inside the repository"):
                self.module["prepare_comparison"](
                    repo_root=self.root,
                    spec_path=self.spec_path,
                    output_dir=self.root / "run-outside",
                )
        finally:
            for child in outside.iterdir():
                child.unlink()
            outside.rmdir()

    def test_rejects_duplicate_arms_and_missing_skill_entrypoint(self):
        spec = json.loads(self.spec_path.read_text(encoding="utf-8"))
        spec["arms"][2]["id"] = "ours"
        self.spec_path.write_text(json.dumps(spec), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "unique"):
            self.module["prepare_comparison"](
                repo_root=self.root,
                spec_path=self.spec_path,
                output_dir=self.root / "run-duplicate",
            )

        spec["arms"][2]["id"] = "upstream"
        spec["arms"][1]["skill"]["source"] = "missing"
        self.spec_path.write_text(json.dumps(spec), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "SKILL.md"):
            self.module["prepare_comparison"](
                repo_root=self.root,
                spec_path=self.spec_path,
                output_dir=self.root / "run-missing",
            )

    def test_runner_uses_temporary_auth_home_and_preserves_results_without_credentials(self):
        output = self.root / "run-live"
        self.module["prepare_comparison"](self.root, self.spec_path, output)
        auth = self.root / "auth.json"
        auth.write_text('{"token":"synthetic-secret"}', encoding="utf-8")
        execution_roots = []
        initialized_fixtures = []

        def fake_run(command, **kwargs):
            cwd = Path(kwargs["cwd"])
            if "init" in command:
                initialized_fixtures.append(cwd)
                return subprocess.CompletedProcess(command, 0, "", "")
            execution_roots.append(cwd)
            evaluation_homes = Path(kwargs["env"]["EVAL_HOME_BASE"])
            self.assertTrue(evaluation_homes.is_relative_to(cwd))
            for arm_id in ("baseline", "ours", "upstream"):
                self.assertEqual(
                    (
                        evaluation_homes / arm_id / ".codex" / "auth.json"
                    ).read_text(encoding="utf-8"),
                    auth.read_text(encoding="utf-8"),
                )
            self.assertFalse(
                (evaluation_homes / "baseline" / ".agents" / "skills").exists()
            )
            self.assertFalse(
                (evaluation_homes / "ours" / ".agents" / "skills").exists()
            )
            self.assertTrue(
                (
                    evaluation_homes
                    / "upstream"
                    / ".agents"
                    / "skills"
                    / "upstream"
                    / "SKILL.md"
                ).is_file()
            )
            if "eval" in command:
                (cwd / "results.json").write_text(
                    '{"version":3,"results":{"results":[{"success":true},{"success":true},{"success":true}]}}',
                    encoding="utf-8",
                )
                (cwd / "results.html").write_text(
                    "<html></html>", encoding="utf-8"
                )
            return subprocess.CompletedProcess(command, 0, "ok", "")

        with mock.patch.object(
            self.run_module["subprocess"], "run", side_effect=fake_run
        ):
            result = self.run_module["run_comparison"](
                run_dir=output,
                auth_json=auth,
                npx_path="npx-test",
                repeat=1,
                git_path="git-test",
            )

        self.assertEqual(result["exit_code"], 0)
        self.assertEqual(len(initialized_fixtures), 3)
        self.assertEqual(
            {path.name for path in initialized_fixtures},
            {"baseline", "ours", "upstream"},
        )
        self.assertEqual(len(execution_roots), 2)
        self.assertEqual(execution_roots[0], execution_roots[1])
        self.assertFalse(execution_roots[0].exists())
        self.assertTrue((output / "results.json").is_file())
        self.assertTrue((output / "results.html").is_file())
        self.assertFalse(any(path.name == "auth.json" for path in output.rglob("*")))
        meta_text = (output / "run-meta.json").read_text(encoding="utf-8")
        self.assertNotIn("synthetic-secret", meta_text)
        metadata = json.loads(meta_text)
        self.assertEqual(metadata["repeat"], 1)
        self.assertEqual(
            metadata["frozen_sha256"],
            self.run_module["sha256_file"](output / "frozen.json"),
        )

    def test_runner_preserves_completed_eval_when_assertions_fail(self):
        output = self.root / "run-failed-assertion"
        self.module["prepare_comparison"](self.root, self.spec_path, output)
        auth = self.root / "auth.json"
        auth.write_text("{}", encoding="utf-8")

        def fake_run(command, **kwargs):
            cwd = Path(kwargs["cwd"])
            if "eval" in command:
                (cwd / "results.json").write_text(
                    '{"version":3,"results":{"results":[{"success":false},{"success":false},{"success":false}]}}',
                    encoding="utf-8",
                )
                (cwd / "results.html").write_text(
                    "<html></html>", encoding="utf-8"
                )
                return subprocess.CompletedProcess(command, 1, "assertion failed", "")
            return subprocess.CompletedProcess(command, 0, "valid", "")

        with mock.patch.object(
            self.run_module["subprocess"], "run", side_effect=fake_run
        ):
            result = self.run_module["run_comparison"](
                run_dir=output,
                auth_json=auth,
                npx_path="npx-test",
                repeat=1,
                git_path="git-test",
            )

        self.assertEqual(result["exit_code"], 1)
        self.assertEqual(result["status"], "completed-with-failures")
        self.assertTrue((output / "results.json").is_file())

    def test_runner_refuses_mutated_prepared_input(self):
        output = self.root / "run-mutated"
        self.module["prepare_comparison"](self.root, self.spec_path, output)
        auth = self.root / "auth.json"
        auth.write_text("{}", encoding="utf-8")
        config = output / "prepared" / "promptfooconfig.json"
        config.write_text(
            config.read_text(encoding="utf-8") + " ", encoding="utf-8"
        )

        with self.assertRaisesRegex(ValueError, "prepared config hash"):
            self.run_module["run_comparison"](
                run_dir=output,
                auth_json=auth,
                npx_path="npx-test",
                repeat=1,
            )

    def test_runner_records_git_initialization_failure(self):
        output = self.root / "run-git-failure"
        self.module["prepare_comparison"](self.root, self.spec_path, output)
        auth = self.root / "auth.json"
        auth.write_text("{}", encoding="utf-8")

        with mock.patch.object(
            self.run_module["subprocess"],
            "run",
            return_value=subprocess.CompletedProcess(
                ["git-test", "init"], 1, "", "synthetic git failure"
            ),
        ):
            with self.assertRaisesRegex(RuntimeError, "git init failed"):
                self.run_module["run_comparison"](
                    run_dir=output,
                    auth_json=auth,
                    npx_path="npx-test",
                    repeat=1,
                    git_path="git-test",
                )

        metadata = json.loads((output / "run-meta.json").read_text(encoding="utf-8"))
        self.assertEqual(metadata["status"], "runtime-error")
        self.assertIn("git init failed", metadata["setup_error"])


if __name__ == "__main__":
    unittest.main()