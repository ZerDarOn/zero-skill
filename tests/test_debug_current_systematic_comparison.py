"""Frozen-design checks for the current debug skill versus systematic-debugging."""

import hashlib
import json
from pathlib import Path
import runpy
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
COMPARISON = ROOT / "evaluations/comparisons/debug-current-systematic-three-arm-25"
UPSTREAM_COMMIT = "b36e0829c6d0140e93cfef2ca599b1b07d4a7797"
UPSTREAM_PACKAGE = (
    ROOT / "evaluations/fixtures/upstreams/superpowers-systematic-debugging" / UPSTREAM_COMMIT
)
UPSTREAM_SOURCE = ROOT / "evaluations/fixtures/upstreams/superpowers" / UPSTREAM_COMMIT
EXPECTED_PROTOCOL_SHA256 = (
    "71d0d8c472e081d7691368ceb8c19aa3270fef29d90ca293caa93e9c2180d20d"
)
EXPECTED_CASES_SHA256 = (
    "9ab66e760df491dd34b2826aea5a3ec0e1cd320eeb11e254d9fb04fb7b5e7d18"
)
EXPECTED_PREPARED_CONFIG_SHA256 = (
    "709aab6bed1937447377994734afdd0449f12f68ddb83b9a449c7daa3a21d8a3"
)
EXPECTED_PREPARED_TESTS_SHA256 = (
    "573cd8f3a58b56863f9ea0b4cfd3a36dfa0942bb2a414e206e7865de4379b0cb"
)
EXPECTED_OURS_PACKAGE_SHA256 = (
    "5c880634b3b728ec83a26efdc7f186c33f1196a1e6c6cfce6ea29cf4d2862e72"
)
EXPECTED_UPSTREAM_PACKAGE_SHA256 = (
    "17c82641ac6528efd6c1728206442de6ca345314a176a8448c351191b35ca731"
)
FREEZE_COMMIT = "8de3dbde770439ac682b38168847bfd641938d69"
PRE_FREEZE_ACTIVE_IDS = {
    "correlation-is-not-root-cause",
    "trace-request-boundary",
    "recovery-is-not-verification",
    "decisive-reproduction",
    "local-pass-is-not-deployed-fix",
    "two-ordered-checks",
    "regression-clock-skew-trace-over-wall-time",
    "regression-ordered-runtime-and-key-checks",
    "regression-control-plane-complete-workload-old",
    "regression-quiet-dashboard-without-partition-reconnect",
    "regression-timeout-idempotency-key-not-enforcement",
    "regression-get-endpoint-has-read-repair-write",
    "regression-decisive-substring-role-reproduction",
}
VALIDATOR = runpy.run_path(str(ROOT / "scripts/validate_collection.py"))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class DebugCurrentSystematicComparisonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.protocol = json.loads(
            (COMPARISON / "promptfoo.json").read_text(encoding="utf-8")
        )
        cls.cases = json.loads(
            (COMPARISON / "cases.json").read_text(encoding="utf-8")
        )

    def test_protocol_freezes_balanced_current_three_arm_design(self):
        protocol = self.protocol
        self.assertEqual(
            sha256_file(COMPARISON / "promptfoo.json"), EXPECTED_PROTOCOL_SHA256
        )
        self.assertEqual(
            sha256_file(COMPARISON / "cases.json"), EXPECTED_CASES_SHA256
        )
        self.assertEqual(protocol["id"], "debug-current-systematic-three-arm-25")
        self.assertEqual(protocol["comparison_kind"], "quality")
        self.assertEqual(protocol["model"], "gpt-5.6-sol")
        self.assertEqual(protocol["reasoning_effort"], "medium")
        self.assertEqual(protocol["repetitions"], 3)
        self.assertEqual(protocol["sandbox_mode"], "read-only")
        self.assertEqual(len(self.cases) * len(protocol["arms"]) * 3, 54)
        self.assertEqual(
            protocol["decision_gate"],
            {
                "scope": "ours-versus-baseline",
                "core_failure_definition": "A repetition has a core failure when any zero-based criterion index listed in that case's core_criteria is false in the completed blind review.",
                "minimum_cases_in_same_mechanism": 2,
                "ours_min_core_failures_per_case": 2,
                "baseline_max_core_failures_per_case": 1,
                "required_valid_outputs": 54,
                "upstream_role": "context-only",
                "effect": "open-minimal-candidate-design-only",
            },
        )
        self.assertEqual(
            protocol["arms"],
            [
                {"id": "baseline", "skill": None},
                {
                    "id": "ours",
                    "skill": {
                        "id": "debug-evidence-triage",
                        "source": "../../../skills/engineering/debug-evidence-triage",
                        "install_mode": "project",
                        "invocation": "explicit",
                    },
                },
                {
                    "id": "upstream",
                    "skill": {
                        "id": "systematic-debugging",
                        "source": "../../fixtures/upstreams/superpowers-systematic-debugging/b36e0829c6d0140e93cfef2ca599b1b07d4a7797",
                        "install_mode": "project",
                        "invocation": "explicit",
                    },
                },
            ],
        )

    def test_cases_cover_three_new_mechanisms_without_reusing_prefreeze_ids(self):
        counts = {}
        identifiers = set()
        for case in self.cases:
            self.assertNotIn(case["id"], identifiers)
            identifiers.add(case["id"])
            counts[case["mechanism"]] = counts.get(case["mechanism"], 0) + 1
            self.assertEqual(len(case["hard_criteria"]), 4)
            self.assertTrue(case["core_criteria"])
            self.assertEqual(len(case["core_criteria"]), len(set(case["core_criteria"])))
            self.assertTrue(all(0 <= index < 4 for index in case["core_criteria"]))
        self.assertEqual(
            counts,
            {
                "observation-coverage": 2,
                "causal-discrimination": 2,
                "execution-identity-continuity": 2,
            },
        )
        self.assertTrue(identifiers.isdisjoint(PRE_FREEZE_ACTIVE_IDS))
        if (ROOT / ".git").exists():
            frozen_active = json.loads(
                subprocess.run(
                    [
                        "git",
                        "show",
                        f"{FREEZE_COMMIT}:evaluations/cases/debug-evidence-triage.json",
                    ],
                    cwd=ROOT,
                    check=True,
                    capture_output=True,
                ).stdout.decode("utf-8")
            )
            self.assertEqual(
                {case["id"] for case in frozen_active["cases"]},
                PRE_FREEZE_ACTIVE_IDS,
            )

    def test_task_material_supports_hidden_requirements_and_new_surfaces(self):
        cases = {case["id"]: case for case in self.cases}
        required_fragments = {
            "zero-five-hundreds-misses-empty-success": (
                "Android v12",
                "HTTP 200",
                "orders=[]",
                "只统计网页请求和 status>=500",
                "没有Android v12请求",
            ),
            "finished-only-query-hides-stalled-jobs": (
                "25个导出任务",
                "8个在租约过期后仍停在queued",
                "WHERE finished_at IS NOT NULL",
                "17个completed任务",
            ),
            "bundled-timeout-and-index-recovery": (
                "服务端p99为2.8秒",
                "新增数据库索引",
                "客户端超时改为5秒",
                "没有单变量对照",
            ),
            "flag-cohort-confounded-by-payload-size": (
                "开启组20次请求失败8次",
                "关闭组20次失败0次",
                "全部大于5MB",
                "全部小于200KB",
                "四种可能结果",
            ),
            "same-job-id-different-retry-attempts": (
                "job=j7、attempt=1",
                "job=j7、attempt=2",
                "该次worker记录缺失",
                "该次publisher与queue接收记录缺失",
            ),
            "session-id-reused-across-process-boot": (
                "boot_id=B1",
                "boot_id=B2",
                "进程内内存",
                "产品是否要求session跨重启恢复尚未确定",
            ),
        }
        for case_id, fragments in required_fragments.items():
            for fragment in fragments:
                self.assertIn(fragment, cases[case_id]["prompt"])

        active_prompts = json.loads(
            (ROOT / "evaluations/cases/debug-evidence-triage.json").read_text(
                encoding="utf-8"
            )
        )["cases"]
        active_text = "\n".join(case["prompt"] for case in active_prompts)
        for new_marker in ("orders=[]", "finished_at IS NOT NULL", "boot_id=B2"):
            self.assertNotIn(new_marker, active_text)

    def test_upstream_fixture_matches_fixed_provenance(self):
        provenance = json.loads(
            (UPSTREAM_PACKAGE / "provenance.json").read_text(encoding="utf-8")
        )
        self.assertEqual(provenance["repository"], "https://github.com/obra/superpowers")
        self.assertEqual(provenance["commit"], UPSTREAM_COMMIT)
        self.assertEqual(provenance["license"], "MIT")
        self.assertTrue(provenance["modifications"].startswith("Source bytes are unchanged."))
        self.assertEqual(
            set(provenance["files"]),
            {
                "LICENSE",
                "SKILL.md",
                "root-cause-tracing.md",
                "defense-in-depth.md",
                "condition-based-waiting.md",
                "condition-based-waiting-example.ts",
                "find-polluter.sh",
            },
        )
        for name, record in provenance["files"].items():
            self.assertEqual(sha256_file(UPSTREAM_PACKAGE / name), record["sha256"])
            self.assertEqual(
                (UPSTREAM_PACKAGE / name).read_bytes(),
                (UPSTREAM_SOURCE / record["source_path"]).read_bytes(),
            )
        skill_text = (UPSTREAM_PACKAGE / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST", skill_text)
        self.assertIn("root-cause-tracing.md", skill_text)
        self.assertTrue((UPSTREAM_PACKAGE / "LICENSE").is_file())
        self.assertIn("sibling test-driven-development", provenance["modifications"])
        self.assertIn("verification-before-completion", provenance["modifications"])

        same_directory_references = {
            "SKILL.md": {
                "root-cause-tracing.md",
                "defense-in-depth.md",
                "condition-based-waiting.md",
            },
            "root-cause-tracing.md": {"find-polluter.sh"},
            "condition-based-waiting.md": {"condition-based-waiting-example.ts"},
        }
        for source_name, references in same_directory_references.items():
            source_text = (UPSTREAM_PACKAGE / source_name).read_text(encoding="utf-8")
            for reference in references:
                self.assertIn(reference, source_text)
                self.assertTrue((UPSTREAM_PACKAGE / reference).is_file())

    def test_preparation_hides_rubric_and_copies_complete_packages(self):
        prepare = runpy.run_path(
            str(ROOT / "evaluations/promptfoo/prepare_skill_comparison.py")
        )
        case_by_id = {case["id"]: case for case in self.cases}
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "prepared-run"
            prepare["prepare_comparison"](
                repo_root=ROOT,
                spec_path=COMPARISON / "promptfoo.json",
                output_dir=output,
            )
            tests = json.loads(
                (output / "prepared/tests.json").read_text(encoding="utf-8")
            )
            config_path = output / "prepared/promptfooconfig.json"
            config = json.loads(config_path.read_text(encoding="utf-8"))
            self.assertEqual(
                sha256_file(config_path), EXPECTED_PREPARED_CONFIG_SHA256
            )
            self.assertEqual(
                sha256_file(output / "prepared/tests.json"),
                EXPECTED_PREPARED_TESTS_SHA256,
            )
            frozen = json.loads((output / "frozen.json").read_text(encoding="utf-8"))
            packages = {
                "ours": (
                    ROOT / "skills/engineering/debug-evidence-triage",
                    output / "prepared/skills/ours/debug-evidence-triage",
                    output / "prepared/fixtures/ours/.agents/skills/debug-evidence-triage",
                    EXPECTED_OURS_PACKAGE_SHA256,
                ),
                "upstream": (
                    UPSTREAM_PACKAGE,
                    output / "prepared/skills/upstream/systematic-debugging",
                    output / "prepared/fixtures/upstream/.agents/skills/systematic-debugging",
                    EXPECTED_UPSTREAM_PACKAGE_SHA256,
                ),
            }
            frozen_arms = {arm["id"]: arm for arm in frozen["arms"]}
            for arm_id, (source, prepared, fixture, expected_hash) in packages.items():
                source_files = {
                    path.relative_to(source).as_posix(): path.read_bytes()
                    for path in source.rglob("*")
                    if path.is_file()
                }
                for copied in (prepared, fixture):
                    copied_files = {
                        path.relative_to(copied).as_posix(): path.read_bytes()
                        for path in copied.rglob("*")
                        if path.is_file()
                    }
                    self.assertEqual(copied_files, source_files)
                    self.assertEqual(
                        VALIDATOR["package_fingerprint"](copied), expected_hash
                    )
                self.assertEqual(
                    VALIDATOR["package_fingerprint"](source), expected_hash
                )
                self.assertEqual(
                    frozen_arms[arm_id]["skill_package_sha256"], expected_hash
                )

        self.assertEqual(len(tests), 18)
        self.assertEqual(
            frozen["selected_case_ids"], [case["id"] for case in self.cases]
        )
        self.assertEqual(frozen["spec_sha256"], EXPECTED_PROTOCOL_SHA256)
        self.assertEqual(frozen["cases_sha256"], EXPECTED_CASES_SHA256)
        self.assertEqual(
            frozen["prepared_config_sha256"], EXPECTED_PREPARED_CONFIG_SHA256
        )
        self.assertEqual(
            frozen["prepared_tests_sha256"], EXPECTED_PREPARED_TESTS_SHA256
        )
        self.assertEqual(
            {key: value for key, value in config.items() if key != "providers"},
            {
                "$schema": "https://promptfoo.dev/config-schema.json",
                "description": "Native Codex skill comparison: debug-current-systematic-three-arm-25",
                "tags": {
                    "comparison": "debug-current-systematic-three-arm-25",
                    "runtime": "codex-sdk",
                },
                "prompts": ["{{prompt}}"],
                "tests": "file://tests.json",
                "sharing": False,
            },
        )
        self.assertEqual(
            [provider["label"] for provider in config["providers"]],
            ["baseline", "ours", "upstream"],
        )
        for provider in config["providers"]:
            label = provider["label"]
            self.assertEqual(provider["id"], "openai:codex-sdk")
            self.assertEqual(
                provider["config"],
                {
                    "model": "gpt-5.6-sol",
                    "model_reasoning_effort": "medium",
                    "working_dir": f"./fixtures/{label}",
                    "skip_git_repo_check": False,
                    "sandbox_mode": "read-only",
                    "approval_policy": "never",
                    "network_access_enabled": False,
                    "web_search_enabled": False,
                    "web_search_mode": "disabled",
                    "inherit_process_env": False,
                    "enable_streaming": True,
                    "cli_config": {
                        "features": {
                            "apps": False,
                            "plugins": False,
                            "multi_agent": False,
                        },
                        "apps": {"_default": {"enabled": False}},
                    },
                    "cli_env": {
                        "CODEX_HOME": f"{{{{ env.EVAL_HOME_BASE }}}}/{label}/.codex",
                        "HOME": f"{{{{ env.EVAL_HOME_BASE }}}}/{label}",
                        "USERPROFILE": f"{{{{ env.EVAL_HOME_BASE }}}}/{label}",
                    },
                },
            )
        for test in tests:
            source = case_by_id[test["metadata"]["case_id"]]
            arm_id = test["metadata"]["arm_id"]
            invocation = "none" if arm_id == "baseline" else "explicit"
            self.assertEqual(
                test["metadata"],
                {
                    "case_id": source["id"],
                    "arm_id": arm_id,
                    "invocation": invocation,
                    "purpose": source["purpose"],
                    "hard_criteria": source["hard_criteria"],
                },
            )
            prefix = ""
            if arm_id != "baseline":
                skill_id = {"ours": "debug-evidence-triage", "upstream": "systematic-debugging"}[
                    arm_id
                ]
                prefix = (
                    f"请显式运行 ${skill_id} 后完成下方任务。"
                    "只返回任务要求的结果，不说明 Skill 加载过程。\n\n"
                )
            prompt = test["vars"]["prompt"]
            self.assertEqual(
                prompt,
                f"{prefix}{self.protocol['common_prompt']}\n\n{source['prompt']}",
            )
            self.assertNotIn("core_criteria", test["metadata"])
            self.assertNotIn("core_criteria", prompt)
            self.assertFalse(
                any(criterion in prompt for criterion in source["hard_criteria"])
            )


if __name__ == "__main__":
    unittest.main()
