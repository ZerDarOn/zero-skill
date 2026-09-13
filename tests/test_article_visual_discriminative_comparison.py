"""Frozen-design checks for the discriminative article visual comparison."""

import hashlib
import json
from pathlib import Path
import runpy
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
COMPARISON = (
    ROOT / "evaluations" / "comparisons" / "article-visual-plan-discriminative-23"
)
UPSTREAM_COMMIT = "6b7a2e417500561a5ecdd0b168332f4142584617"
UPSTREAM_PACKAGE = (
    ROOT
    / "evaluations"
    / "fixtures"
    / "upstreams"
    / "baoyu-skills"
    / UPSTREAM_COMMIT
    / "skills"
    / "baoyu-article-illustrator"
)
EXPECTED_PROTOCOL_SHA256 = (
    "85a3b9acb6a1b039ae59973042b961362a265b5cbbe5bbeecb47ed99cb691faf"
)
EXPECTED_CASES_SHA256 = (
    "08073406fd3fa237a051e6d4a1e59cff05b331e99cbc44007524e39df5b8915a"
)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ArticleVisualDiscriminativeComparisonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.protocol = json.loads(
            (COMPARISON / "promptfoo.json").read_text(encoding="utf-8")
        )
        cls.cases = json.loads(
            (COMPARISON / "cases.json").read_text(encoding="utf-8")
        )

    def test_protocol_freezes_balanced_three_arm_design_and_gate(self):
        protocol = self.protocol
        self.assertEqual(
            sha256_file(COMPARISON / "promptfoo.json"), EXPECTED_PROTOCOL_SHA256
        )
        self.assertEqual(sha256_file(COMPARISON / "cases.json"), EXPECTED_CASES_SHA256)
        self.assertEqual(protocol["id"], "article-visual-plan-discriminative-23")
        self.assertEqual(protocol["model"], "gpt-5.6-sol")
        self.assertEqual(protocol["reasoning_effort"], "medium")
        self.assertEqual(protocol["repetitions"], 3)
        self.assertEqual(protocol["sandbox_mode"], "read-only")
        self.assertEqual(
            [arm["id"] for arm in protocol["arms"]],
            ["baseline", "ours", "upstream"],
        )
        self.assertIsNone(protocol["arms"][0]["skill"])
        self.assertEqual(protocol["arms"][1]["skill"]["id"], "article-visual-plan")
        self.assertEqual(
            protocol["arms"][2]["skill"]["id"], "baoyu-article-illustrator"
        )
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
            protocol["common_prompt"],
            "请完成下方合成文章配图规划任务。这是一次性文本规划：跳过偏好配置、EXTEND.md 检查、首次设置、确认、生图、写盘和文章回填。只使用题目给出的材料，不调用工具，不读取或写入文件，不生成图片，不问澄清问题，直接给出最终回答。遵守用户指定的图片数量、位置、比例和输出格式；不要声称已经创建、保存、渲染或插入任何素材。",
        )
        self.assertEqual(
            protocol["arms"],
            [
                {"id": "baseline", "skill": None},
                {
                    "id": "ours",
                    "skill": {
                        "id": "article-visual-plan",
                        "source": "../../../skills/creation/article-visual-plan",
                        "install_mode": "project",
                        "invocation": "explicit",
                    },
                },
                {
                    "id": "upstream",
                    "skill": {
                        "id": "baoyu-article-illustrator",
                        "source": "../../fixtures/upstreams/baoyu-skills/6b7a2e417500561a5ecdd0b168332f4142584617/skills/baoyu-article-illustrator",
                        "install_mode": "project",
                        "invocation": "explicit",
                    },
                },
            ],
        )

    def test_cases_cover_three_new_mechanisms_without_reusing_active_ids(self):
        counts = {}
        for case in self.cases:
            counts[case["mechanism"]] = counts.get(case["mechanism"], 0) + 1
            self.assertEqual(len(case["hard_criteria"]), 4)
            self.assertTrue(case["core_criteria"])
            self.assertEqual(len(case["core_criteria"]), len(set(case["core_criteria"])))
            self.assertTrue(all(0 <= index < 4 for index in case["core_criteria"]))
        self.assertEqual(
            counts,
            {
                "source-revision-control": 2,
                "evidence-compatible-encoding": 2,
                "compound-plan-state": 2,
            },
        )
        active = json.loads(
            (
                ROOT / "evaluations" / "cases" / "article-visual-plan.json"
            ).read_text(encoding="utf-8")
        )
        self.assertTrue(
            {case["id"] for case in self.cases}.isdisjoint(
                {case["id"] for case in active["cases"]}
            )
        )

    def test_task_material_supports_each_hidden_core_requirement(self):
        cases = {case["id"]: case for case in self.cases}
        retracted = cases["retracted-metric-evidence-summary"]["prompt"]
        self.assertIn("43% 已撤回", retracted)
        self.assertIn("无法判断升级工单变化的方向或幅度", retracted)
        self.assertIn("5 名受访者中有 3 人", retracted)

        corrected = cases["owner-corrected-human-review-flow"]["prompt"]
        self.assertIn("系统从未自动批准", corrected)
        self.assertIn("每个请求都由人工复核", corrected)
        self.assertIn("未通过则退回申请人修改", corrected)

        unequal = cases["unequal-cohort-observed-rates"]["prompt"]
        for fact in ("20 名", "12 人完成", "18 名", "14 人完成", "入选条件也改过"):
            self.assertIn(fact, unequal)

        qualitative = cases["qualitative-themes-without-intensity"]["prompt"]
        self.assertIn("没有对应的确切人数", qualitative)
        self.assertIn("没有统一标签频次", qualitative)

    def test_compound_plan_cases_make_exact_state_transition_scoreable(self):
        cases = {case["id"]: case for case in self.cases}
        style = cases["global-style-with-local-content-correction"]["prompt"]
        self.assertEqual(style.count("共同风格：蓝灰扁平线稿"), 4)
        for identifier in ("V2", "V5", "V8", "V13"):
            self.assertIn(identifier, style)
        self.assertIn("暖灰报刊拼贴", style)
        self.assertIn("评分→调整队列优先级→人工复核→通过后发布", style)

        edit = cases["delete-and-insert-with-stable-ids"]["prompt"]
        for identifier in ("V1", "V4", "V7", "V9", "V10"):
            self.assertIn(identifier, edit)
        self.assertIn("删除 V4", edit)
        self.assertIn("在 V7 后、V10 前新增 V9", edit)

    def test_preparation_keeps_rubric_hidden_and_upstream_license_attached(self):
        prepare = runpy.run_path(
            str(ROOT / "evaluations" / "promptfoo" / "prepare_skill_comparison.py")
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
                (output / "prepared" / "tests.json").read_text(encoding="utf-8")
            )
            frozen = json.loads(
                (output / "frozen.json").read_text(encoding="utf-8")
            )
            license_path = (
                output
                / "prepared"
                / "fixtures"
                / "upstream"
                / ".agents"
                / "skills"
                / "baoyu-article-illustrator"
                / "LICENSE"
            )
            self.assertEqual(
                license_path.read_bytes(), (UPSTREAM_PACKAGE / "LICENSE").read_bytes()
            )

        self.assertEqual(len(tests), 18)
        self.assertEqual(
            frozen["selected_case_ids"], [case["id"] for case in self.cases]
        )
        for test in tests:
            source = case_by_id[test["metadata"]["case_id"]]
            prompt = test["vars"]["prompt"]
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
                skill_id = {
                    "ours": "article-visual-plan",
                    "upstream": "baoyu-article-illustrator",
                }[arm_id]
                prefix = (
                    f"请显式运行 ${skill_id} 后完成下方任务。"
                    "只返回任务要求的结果，不说明 Skill 加载过程。\n\n"
                )
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
