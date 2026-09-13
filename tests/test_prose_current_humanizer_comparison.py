"""Frozen-design checks for the current prose-polish versus Humanizer comparison."""

import hashlib
import json
from pathlib import Path
import runpy
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
COMPARISON = ROOT / "evaluations/comparisons/prose-polish-current-humanizer-24"
UPSTREAM_COMMIT = "9862685f575c65a8247f90369951df1b3416e3d6"
UPSTREAM_PACKAGE = (
    ROOT / "evaluations/fixtures/upstreams/humanizer" / UPSTREAM_COMMIT
)
EXPECTED_PROTOCOL_SHA256 = (
    "b1109cc9fc2d69e440fdb2c4d523778d889499ab7224e1009d79b03117a92eb3"
)
EXPECTED_CASES_SHA256 = (
    "2fdd0ce433b9c581165800c128f9461a41f8fcbf72360fae66b21d4282f95898"
)
EXPECTED_PREPARED_CONFIG_SHA256 = (
    "a4f0110813322a8c5916a827de4f165d1ad401ac807f7915d84f4a84524ddba1"
)
EXPECTED_PREPARED_TESTS_SHA256 = (
    "e0826494ef2a4acf5015f3d89d492606de872140db166f73fd99e2d8755040c4"
)
EXPECTED_OURS_PACKAGE_SHA256 = (
    "85460012946903fe6401f8df5f6b284497103606fbeaed86eda963d92a103047"
)
EXPECTED_UPSTREAM_PACKAGE_SHA256 = (
    "1f7cf25aac13904bfa2a9e1f54f83ba8f620c50bd059b2f7b634e62d7010adde"
)
FREEZE_COMMIT = "5fb4a1ca09a7a17059b41a372daf1c06e0927fa0"
PRE_FREEZE_ACTIVE_IDS = {
    "preserve-qualified-claims",
    "match-author-voice",
    "edit-prose-only",
    "leave-clear-text-alone",
    "authorized-corrections-in-protected-content",
    "quiet-voice-without-new-events",
    "local-revision-and-rollback",
    "preserve-reschedule-relation-under-limit",
    "preserve-conjunctive-audience-condition",
}
VALIDATOR = runpy.run_path(str(ROOT / "scripts/validate_collection.py"))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ProseCurrentHumanizerComparisonTests(unittest.TestCase):
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
        self.assertEqual(protocol["id"], "prose-polish-current-humanizer-24")
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
                        "id": "prose-polish",
                        "source": "../../../skills/creation/prose-polish",
                        "install_mode": "project",
                        "invocation": "explicit",
                    },
                },
                {
                    "id": "upstream",
                    "skill": {
                        "id": "humanizer",
                        "source": "../../fixtures/upstreams/humanizer/9862685f575c65a8247f90369951df1b3416e3d6",
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
                "bounded-condition-preservation": 2,
                "revision-history-control": 2,
                "author-voice-restraint": 2,
            },
        )
        self.assertTrue(identifiers.isdisjoint(PRE_FREEZE_ACTIVE_IDS))
        if (ROOT / ".git").exists():
            frozen_active = json.loads(
                subprocess.run(
                    [
                        "git",
                        "show",
                        f"{FREEZE_COMMIT}:evaluations/cases/prose-polish.json",
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

    def test_character_limits_are_feasible_without_dropping_relations(self):
        examples = {
            "scoped-migration-plan-under-limit": "2026年Q4迁移计划仅含东区、北区试点；南区须在10月3日前通过传感器兼容性验证才纳入，西区不在本轮。名单未定，以上是计划范围，并非上线承诺。",
            "triple-eligibility-with-exceptions": "预约页9月22日开放。仅持有效校园卡、首次到访且需无障碍路线者须于9月24日17:00前填写；线上、非首次或无需无障碍路线者不用填，无有效卡者不能预约。",
            "audit-invalidates-metric-keeps-quote": "试点实际覆盖27家。因计时起点不一致，原18%已作废，现无法判断等待时间变化方向或幅度。一位客户主观反馈：“确实少等了一会儿”。",
        }
        limits = {
            "scoped-migration-plan-under-limit": 85,
            "triple-eligibility-with-exceptions": 90,
            "audit-invalidates-metric-keeps-quote": 110,
        }
        for case_id, example in examples.items():
            with self.subTest(case_id=case_id):
                self.assertLessEqual(len(example.strip()), limits[case_id])

    def test_revision_and_voice_material_support_hidden_requirements(self):
        cases = {case["id"]: case for case in self.cases}
        scoped = cases["scoped-migration-plan-under-limit"]["prompt"]
        for fact in (
            "2026年第四季度",
            "只包含东区和北区",
            "10月3日前通过传感器兼容性验证才纳入",
            "西区不在本轮",
            "参与名单尚未确定",
            "不是已经上线或承诺上线",
        ):
            self.assertIn(fact, scoped)
        for reused_structure in ("原定", "改到", "会议号", "已经确认", "回复邮件"):
            self.assertNotIn(reused_structure, scoped)

        audit = cases["audit-invalidates-metric-keeps-quote"]["prompt"]
        for fact in (
            "实际覆盖27家",
            "计时起点不一致",
            "18%已作废",
            "无法判断等待时间变化的方向或幅度",
            "确实少等了一会儿",
        ):
            self.assertIn(fact, audit)

        rollback = cases["partial-rollback-keeps-schedule-revision"]["prompt"]
        for fact in (
            "恢复14名",
            "v2的公开试用安排继续有效",
            "原定9月20日",
            "9月18日前通过",
            "9月22日开始",
        ):
            self.assertIn(fact, rollback)

        voice = cases["restrained-voice-with-fixed-closing"]["prompt"]
        self.assertIn("7位居民一起修好了11把伞", voice)
        self.assertIn("末句必须逐字保留", voice)
        self.assertIn("不要移植样文里的事实或意象", voice)
        control = cases["intentional-fragments-no-change-control"]["prompt"]
        self.assertIn("短句与重复是刻意的", control)
        self.assertIn("请原样返回", control)

    def test_upstream_fixture_matches_fixed_provenance(self):
        provenance = json.loads(
            (UPSTREAM_PACKAGE / "provenance.json").read_text(encoding="utf-8")
        )
        self.assertEqual(provenance["repository"], "https://github.com/blader/humanizer")
        self.assertEqual(provenance["commit"], UPSTREAM_COMMIT)
        self.assertEqual(provenance["license"], "MIT")
        self.assertEqual(provenance["modifications"].split(";")[0], "None")
        self.assertEqual(
            set(provenance["files"]), {"LICENSE", "SKILL.md", "agents/openai.yaml"}
        )
        for name, record in provenance["files"].items():
            self.assertEqual(sha256_file(UPSTREAM_PACKAGE / name), record["sha256"])
        skill_text = (UPSTREAM_PACKAGE / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn('version: "3.0.0"', skill_text)
        self.assertIn("license: MIT", skill_text)

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
                    ROOT / "skills/creation/prose-polish",
                    output / "prepared/skills/ours/prose-polish",
                    output / "prepared/fixtures/ours/.agents/skills/prose-polish",
                    EXPECTED_OURS_PACKAGE_SHA256,
                ),
                "upstream": (
                    UPSTREAM_PACKAGE,
                    output / "prepared/skills/upstream/humanizer",
                    output / "prepared/fixtures/upstream/.agents/skills/humanizer",
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
                "description": "Native Codex skill comparison: prose-polish-current-humanizer-24",
                "tags": {
                    "comparison": "prose-polish-current-humanizer-24",
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
                skill_id = {"ours": "prose-polish", "upstream": "humanizer"}[
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
