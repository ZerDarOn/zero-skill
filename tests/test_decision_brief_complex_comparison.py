"""Frozen-design checks for the Round 33 decision brief comparison."""

import hashlib
import json
from pathlib import Path
import runpy
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
COMPARISON = ROOT / "evaluations/comparisons/decision-brief-complex-boundaries-two-arm-26"
SKILL = ROOT / "skills/creation/decision-brief-draft"
ACTIVE = ROOT / "evaluations/cases/decision-brief-draft.json"
BASE_COMMIT = "7c65a3c16377f3e31398e96c9d558076c953e2d7"
EXPECTED_PROTOCOL_SHA256 = "a0c4124b17bb731a46f1436008dbf976b0206614f415c9967c898878bf1b2951"
EXPECTED_CASES_SHA256 = "21670547b8ee96b09a0b145d06433ec34f71cad8821137ac139afd9c9b63c426"
EXPECTED_PREPARED_CONFIG_SHA256 = "d13d1e09ba6f7d80af6992657bfe9dc1adabf2c905a63dd89eea683bd9780bbc"
EXPECTED_PREPARED_TESTS_SHA256 = "e3d7fd741ff8a17652a62d8f0cd8e1550f5e8b3203ee32913fde68de3e2819ef"
EXPECTED_SKILL_PACKAGE_SHA256 = "d66fc65cda321f4a9718c5517ff17e87f704646c9de07d9afb9cb4b4b1495c17"
EXPECTED_ACTIVE_CASES_SHA256 = "7cfe377e96097d77fd0ab5d409d542b1d7c05740c05ac24fc05523961450ee72"
EXPECTED_PREPARER_SHA256 = "4eca5a4c2caeffbeca6663ecf49ce8f9e293f86372593abfb3d794ea1d1b788b"
PRE_FREEZE_ACTIVE_IDS = {
    "recommendation-is-not-approval",
    "tradeoff-under-hard-constraint",
    "bounded-decision-revision",
    "reader-context-without-invention",
    "preserve-approved-decision-history",
    "ask-only-decision-changing-question",
}
VALIDATOR = runpy.run_path(str(ROOT / "scripts/validate_collection.py"))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class DecisionBriefComplexComparisonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.protocol = json.loads(
            (COMPARISON / "promptfoo.json").read_text(encoding="utf-8")
        )
        cls.cases = json.loads(
            (COMPARISON / "cases.json").read_text(encoding="utf-8")
        )

    def test_protocol_freezes_balanced_two_arm_design_and_gate(self):
        protocol = self.protocol
        self.assertEqual(sha(COMPARISON / "promptfoo.json"), EXPECTED_PROTOCOL_SHA256)
        self.assertEqual(sha(COMPARISON / "cases.json"), EXPECTED_CASES_SHA256)
        self.assertEqual(
            (
                protocol["id"],
                protocol["comparison_kind"],
                protocol["model"],
                protocol["reasoning_effort"],
                protocol["repetitions"],
                protocol["sandbox_mode"],
            ),
            (
                "decision-brief-complex-boundaries-two-arm-26",
                "quality",
                "gpt-5.6-sol",
                "medium",
                3,
                "read-only",
            ),
        )
        self.assertEqual(len(self.cases) * len(protocol["arms"]) * 3, 36)
        self.assertEqual(
            protocol["review_policy"],
            {
                "blind_arm_mapping": True,
                "hard_criteria_judgment": "Accept any semantically equivalent answer supported by the frozen case prompt; do not require exact wording and do not add post-hoc requirements.",
                "preference_separate_from_criteria": True,
            },
        )
        self.assertEqual(
            protocol["decision_gate"],
            {
                "scope": "ours-versus-baseline",
                "core_failure_definition": "A repetition has a core failure when any zero-based criterion index listed in that case's core_criteria is false in the completed blind review.",
                "minimum_cases_in_same_mechanism": 2,
                "ours_min_core_failures_per_case": 2,
                "baseline_max_core_failures_per_case": 1,
                "required_valid_outputs": 36,
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
                        "id": "decision-brief-draft",
                        "source": "../../../skills/creation/decision-brief-draft",
                        "install_mode": "project",
                        "invocation": "explicit",
                    },
                },
            ],
        )

    def test_cases_are_new_balanced_and_have_fixed_core_criteria(self):
        self.assertEqual(sha(ACTIVE), EXPECTED_ACTIVE_CASES_SHA256)
        counts = {}
        identifiers = set()
        for case in self.cases:
            self.assertNotIn(case["id"], identifiers)
            identifiers.add(case["id"])
            counts[case["mechanism"]] = counts.get(case["mechanism"], 0) + 1
            self.assertEqual(len(case["hard_criteria"]), 4)
            self.assertEqual(case["core_criteria"], [0, 1, 2])
            self.assertTrue(case["purpose"].strip())
        self.assertEqual(
            counts,
            {
                "decision-history": 2,
                "constraint-and-denominator": 2,
                "role-and-evidence": 2,
            },
        )
        self.assertTrue(identifiers.isdisjoint(PRE_FREEZE_ACTIVE_IDS))
        active = json.loads(ACTIVE.read_text(encoding="utf-8"))
        self.assertEqual(
            {case["id"] for case in active["cases"]}, PRE_FREEZE_ACTIVE_IDS
        )
        if (ROOT / ".git").exists():
            frozen_active = json.loads(
                subprocess.run(
                    [
                        "git",
                        "show",
                        f"{BASE_COMMIT}:evaluations/cases/decision-brief-draft.json",
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

    def test_prompts_make_each_hidden_requirement_observable(self):
        cases = {case["id"]: case for case in self.cases}
        required = {
            "approved-choice-new-qualification-evidence": (
                "D14",
                "批准继续用 Atlas",
                "Beacon 现也取得 AA",
                "无批准权",
                "没有同口径退出成本",
                "是否重开选型",
            ),
            "cost-correction-does-not-revoke-approval": (
                "D22 已批准 North",
                "欧盟驻留和审计导出",
                "South 只有欧盟驻留",
                "North 首年估计应为105万元",
                "D22 批准状态不变",
            ),
            "normalize-three-year-cost-basis": (
                "一次性实施20万元",
                "年费30万元",
                "无实施费",
                "年费36万元",
                "三年内年费不变",
                "未含税估计",
            ),
            "no-feasible-option-with-one-unknown": (
                "至少7年",
                "4小时内",
                "从未做过恢复演练",
                "只保留5年",
                "签约或暂缓",
            ),
            "executive-preference-without-approval-authority": (
                "采购委员会才有批准权",
                "CTO 个人偏好 Beta",
                "项目工作组也建议 Beta",
                "尚未表决",
                "供应链风险结果",
            ),
            "small-usability-check-does-not-prove-rollout": (
                "12名内部测试者",
                "9名首次完成",
                "没有与现流程对照",
                "全公司有1200人",
                "P95响应低于2秒",
                "委员会尚未批准",
            ),
        }
        for case_id, fragments in required.items():
            for fragment in fragments:
                self.assertIn(fragment, cases[case_id]["prompt"])

    def test_length_bound_tasks_have_feasible_complete_answers(self):
        exemplars = {
            "approved-choice-new-qualification-evidence": "D14上月已批准继续用Atlas，依据是当时仅Atlas确认达到AA。S9显示Beacon现也达到AA；财务总监偏好不构成批准，委员会未重表决。明天只决定是否待两者同口径退出成本补齐后重开选型。",
            "small-usability-check-does-not-prove-rollout": "12名内部测试者中9名首次完成新流程，无现流程对照，不能证明1200人全员效果；推广底线是月末峰值P95低于2秒，测试未测。运营副总建议全员启用，委员会未批准，建议补测峰值后再决定。",
        }
        limits = {
            "approved-choice-new-qualification-evidence": 120,
            "small-usability-check-does-not-prove-rollout": 130,
        }
        for case_id, answer in exemplars.items():
            self.assertLessEqual(len(answer), limits[case_id])
            prompt = next(case["prompt"] for case in self.cases if case["id"] == case_id)
            self.assertIn(f"不超过{limits[case_id]}字", prompt)

    def test_preparation_hides_rubric_and_copies_exact_skill(self):
        self.assertEqual(
            sha(ROOT / "evaluations/promptfoo/prepare_skill_comparison.py"),
            EXPECTED_PREPARER_SHA256,
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "prepared-run"
            subprocess.run(
                [
                    "python",
                    str(ROOT / "evaluations/promptfoo/prepare_skill_comparison.py"),
                    "--spec",
                    str(COMPARISON / "promptfoo.json"),
                    "--output",
                    str(output),
                ],
                cwd=ROOT,
                check=True,
            )
            prepared = output / "prepared"
            self.assertEqual(sha(prepared / "promptfooconfig.json"), EXPECTED_PREPARED_CONFIG_SHA256)
            self.assertEqual(sha(prepared / "tests.json"), EXPECTED_PREPARED_TESTS_SHA256)
            frozen = json.loads((output / "frozen.json").read_text(encoding="utf-8"))
            self.assertEqual(frozen["prepared_config_sha256"], EXPECTED_PREPARED_CONFIG_SHA256)
            self.assertEqual(frozen["prepared_tests_sha256"], EXPECTED_PREPARED_TESTS_SHA256)
            ours = next(arm for arm in frozen["arms"] if arm["id"] == "ours")
            self.assertEqual(ours["skill_package_sha256"], EXPECTED_SKILL_PACKAGE_SHA256)
            self.assertEqual(
                ours["skill_package_sha256"], VALIDATOR["package_fingerprint"](SKILL)
            )
            copied = prepared / "skills" / "ours" / "decision-brief-draft"
            source_files = {
                path.relative_to(SKILL).as_posix(): path.read_bytes()
                for path in SKILL.rglob("*")
                if path.is_file()
            }
            copied_files = {
                path.relative_to(copied).as_posix(): path.read_bytes()
                for path in copied.rglob("*")
                if path.is_file()
            }
            self.assertEqual(copied_files, source_files)

            config = json.loads(
                (prepared / "promptfooconfig.json").read_text(encoding="utf-8")
            )
            baseline_provider, ours_provider = config["providers"]
            self.assertEqual(baseline_provider["id"], ours_provider["id"])
            baseline_config = baseline_provider["config"]
            ours_config = ours_provider["config"]
            self.assertEqual(
                {k: v for k, v in baseline_config.items() if k not in {"working_dir", "cli_env"}},
                {k: v for k, v in ours_config.items() if k not in {"working_dir", "cli_env"}},
            )
            self.assertEqual(baseline_config["working_dir"], "./fixtures/baseline")
            self.assertEqual(ours_config["working_dir"], "./fixtures/ours")
            for env_name in ("CODEX_HOME", "HOME", "USERPROFILE"):
                self.assertEqual(
                    baseline_config["cli_env"][env_name].replace("/baseline", "/ARM"),
                    ours_config["cli_env"][env_name].replace("/ours", "/ARM"),
                )

            generated = json.loads((prepared / "tests.json").read_text(encoding="utf-8"))
            self.assertEqual(len(generated), len(self.cases) * 2)
            for item in generated:
                self.assertEqual(set(item["vars"]), {"prompt"})
            public_prompts = "\n".join(item["vars"]["prompt"] for item in generated)
            invocation_prefix = (
                "请显式运行 $decision-brief-draft 后完成下方任务。"
                "只返回任务要求的结果，不说明 Skill 加载过程。"
            )
            for case in self.cases:
                expected_baseline = f'{self.protocol["common_prompt"]}\n\n{case["prompt"]}'
                by_arm = {
                    item["metadata"]["arm_id"]: item
                    for item in generated
                    if item["metadata"]["case_id"] == case["id"]
                }
                self.assertEqual(set(by_arm), {"baseline", "ours"})
                self.assertEqual(by_arm["baseline"]["vars"]["prompt"], expected_baseline)
                self.assertEqual(
                    by_arm["ours"]["vars"]["prompt"],
                    f"{invocation_prefix}\n\n{expected_baseline}",
                )
                for criterion in case["hard_criteria"]:
                    self.assertNotIn(criterion, public_prompts)


if __name__ == "__main__":
    unittest.main()
