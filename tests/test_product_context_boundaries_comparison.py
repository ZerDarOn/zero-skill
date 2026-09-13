"""Frozen-design checks for the Round 34 product-context comparison."""

import hashlib
import json
from pathlib import Path
import runpy
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
COMPARISON = ROOT / "evaluations/comparisons/product-context-boundaries-three-arm-27"
SKILL = ROOT / "skills/productivity/product-context-brief"
ACTIVE = ROOT / "evaluations/cases/product-context-brief.json"
UPSTREAM_REVISION = "5b2c0007766c6a1cf1d53fd8fc73e979e0821022"
UPSTREAM_ROOT = (
    ROOT / "evaluations/fixtures/upstreams/marketingskills" / UPSTREAM_REVISION
)
UPSTREAM_SKILL = UPSTREAM_ROOT / "skills/product-marketing"
FREEZE_COMMIT = "977af538a891126ad560e7286dd3cd9b778ef2ef"
EXPECTED_PROTOCOL_SHA256 = "82731f1012a1421d3e88c7c591c836bf40bd2c3afc80a805de8477f025cfe768"
EXPECTED_CASES_SHA256 = "109c493b3a13d178d67128dd0d181d47209ffbfbfa26c6f9cdb212aac897b7de"
EXPECTED_PREPARED_CONFIG_SHA256 = "7bf0aaee00b0b4a95a48e6ea4b64638ce9880403b8a6a6c25e6a5835ae1e0957"
EXPECTED_PREPARED_TESTS_SHA256 = "54592764c1f7b8c4169ba74a9c9a913f3b95c5dfce2649181c993350dce230ac"
EXPECTED_OURS_PACKAGE_SHA256 = "f821cb134112decd46c07b8b50d5fef7e03c4bbae91d6af68344e45552dbc4c5"
EXPECTED_UPSTREAM_PACKAGE_SHA256 = "802ecb5ec6a435db0ea22a1b95a67450bd0e4c5d3c8f3d8f8ef5525ef77c49de"
EXPECTED_ACTIVE_CASES_SHA256 = "15ff60f439b044d5714fcb54d67f3fb42ce8b37d96cc01f88be4f605e6fe91ec"
EXPECTED_PREPARER_SHA256 = "4eca5a4c2caeffbeca6663ecf49ce8f9e293f86372593abfb3d794ea1d1b788b"
EXPECTED_PROVENANCE_SHA256 = "49bab9352c7b3c6185418d9443c7f5cdc2d895d5406d7fb7b2ea415aa13d8f91"
VALIDATOR = runpy.run_path(str(ROOT / "scripts/validate_collection.py"))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ProductContextBoundariesComparisonTests(unittest.TestCase):
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
                "product-context-boundaries-three-arm-27",
                "quality",
                "gpt-5.6-sol",
                "medium",
                3,
                "read-only",
            ),
        )
        self.assertEqual(len(self.cases) * len(protocol["arms"]) * 3, 54)
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
                        "id": "product-context-brief",
                        "source": "../../../skills/productivity/product-context-brief",
                        "install_mode": "project",
                        "invocation": "explicit",
                    },
                },
                {
                    "id": "upstream",
                    "skill": {
                        "id": "product-marketing",
                        "source": "../../fixtures/upstreams/marketingskills/5b2c0007766c6a1cf1d53fd8fc73e979e0821022/skills/product-marketing",
                        "install_mode": "project",
                        "invocation": "explicit",
                    },
                },
            ],
        )

    def test_cases_are_new_balanced_and_make_requirements_observable(self):
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
                "publication-scope": 2,
                "stakeholder-authority": 2,
                "bounded-evidence-update": 2,
            },
        )
        if FREEZE_COMMIT != "PENDING" and (ROOT / ".git").exists():
            frozen_bytes = subprocess.run(
                ["git", "show", f"{FREEZE_COMMIT}:evaluations/cases/product-context-brief.json"],
                cwd=ROOT,
                check=True,
                capture_output=True,
            ).stdout
            self.assertEqual(hashlib.sha256(frozen_bytes).hexdigest(), EXPECTED_ACTIVE_CASES_SHA256)
            active = json.loads(frozen_bytes.decode("utf-8"))
        else:
            active = json.loads(ACTIVE.read_text(encoding="utf-8"))
        self.assertTrue(identifiers.isdisjoint({case["id"] for case in active["cases"]}))

        prompts = {case["id"]: case["prompt"] for case in self.cases}
        fragments = {
            "scoped-incident-does-not-revoke-availability": (
                "Business 和 Enterprise",
                "欧盟分片的4个 Enterprise 租户",
                "尚无恢复时间",
                "没有报告其他租户受影响",
            ),
            "retirement-banner-does-not-collapse-cohorts": (
                "新账户不再提供 Ledger Sync",
                "120个已有合同账户仍可用到12月31日",
                "横幅对所有管理员可见",
                "没有账户范围或迁移日期",
            ),
            "approval-threshold-excludes-current-quote": (
                "不超过100万元",
                "128万元",
                "只在有权批准后签署合同",
                "付款预算归谁都未确认",
            ),
            "privacy-veto-is-not-purchase-approval": (
                "可以否决隐私不合格方案",
                "没有预算或采购批准权",
                "采购委员会决定是否采购",
                "获批后执行付款",
            ),
            "incompatible-studies-cannot-be-pooled": (
                "18家诊所",
                "10名前台协调员",
                "没有现流程对照",
                "28个参与者中20个改善了运营结果",
            ),
            "approved-document-bounded-revision": (
                "只更新 Target Audience 与 Goals",
                "禁止改 Document version、Last updated 或 Changelog",
                "实际日常用户是现场协调员",
                "尚未经变更委员会批准",
            ),
        }
        for case_id, required in fragments.items():
            for fragment in required:
                self.assertIn(fragment, prompts[case_id])

    def test_length_and_format_constraints_have_feasible_answers(self):
        exemplars = {
            "retirement-banner-does-not-collapse-cohorts": "S1确认新账户已停售Ledger Sync，120个已有合同账户仍可用至12月31日。S2退役横幅缺账户范围和迁移日期，不能推翻该窗口；12月31日后安排及迁移日期待确认。",
            "incompatible-studies-cannot-be-pooled": "U1为4周、18家诊所中12家称遗漏回电变少，无统一计数；U2为2周、10名协调员中8人首次完成操作，无现流程对照。两者单位与结果不同，不能合为28中20或证明普遍有效。",
        }
        limits = {
            "retirement-banner-does-not-collapse-cohorts": 120,
            "incompatible-studies-cannot-be-pooled": 150,
        }
        for case_id, answer in exemplars.items():
            self.assertLessEqual(len(answer), limits[case_id])
            prompt = next(case["prompt"] for case in self.cases if case["id"] == case_id)
            self.assertIn(f"{limits[case_id]}字以内" if case_id == "incompatible-studies-cannot-be-pooled" else f"不超过{limits[case_id]}字", prompt)

    def test_exact_line_and_protected_document_formats_are_feasible(self):
        three_bullets = (
            "- 当前：审计导出已向Business和Enterprise正式开放。\n"
            "- 事件：欧盟分片4个Enterprise租户导出失败，仍在调查，恢复时间未知；未报告其他租户受影响。\n"
            "- 口径：销售笔记的全面不可用只是解释；总体开放与局部故障并存。"
        )
        self.assertEqual(len(three_bullets.splitlines()), 3)
        self.assertTrue(all(line.startswith("- ") for line in three_bullets.splitlines()))

        four_roles = (
            "财务分析师：日常用户。\n"
            "RevOps负责人：收集需求并推荐Nova，是推动者。\n"
            "财务副总：仅支持继续评估；128万元超过其100万元审批上限，未最终批准。\n"
            "采购专员及未知角色：专员仅在获批后签约；最终批准人和付款预算归属未知。"
        )
        self.assertEqual(len(four_roles.splitlines()), 4)
        self.assertTrue(all("：" in line for line in four_roles.splitlines()))

        five_data_rows = (
            "| 角色 | 当前证据 |\n"
            "| --- | --- |\n"
            "| 门诊护士 | 每天录入随访，是用户 |\n"
            "| 护理部主任 | 建议采用CareArc，是推动者 |\n"
            "| 数据保护官 | 可否决隐私不合格方案，无采购批准权；复核未完成 |\n"
            "| 医院采购委员会 | 决定是否采购 |\n"
            "| 财务共享中心 | 仅在获批后执行付款 |"
        )
        self.assertEqual(len(five_data_rows.splitlines()), 7)
        self.assertEqual(len(five_data_rows.splitlines()[2:]), 5)

        bounded_document = """# Product Context
Document version: v7
Last updated: 2026-08-30

## Product Overview
Mira 把现场巡检记录汇总为待办。

## Target Audience
主要用户：现场协调员；区域经理只查看汇总。

## Proof Points
P3：6个站点试用3周，其中4个称交接更清楚；未统一计时。

## Goals
10月全面推广是运营团队提议，尚未经变更委员会批准。

## Brand Voice
直接、谨慎。

## Changelog
- v7 (2026-08-30) — 初稿待审批。"""
        protected = (
            "Document version: v7",
            "Last updated: 2026-08-30",
            "Mira 把现场巡检记录汇总为待办。",
            "P3：6个站点试用3周，其中4个称交接更清楚；未统一计时。",
            "直接、谨慎。",
            "- v7 (2026-08-30) — 初稿待审批。",
        )
        for fragment in protected:
            self.assertIn(fragment, bounded_document)
        self.assertIn("主要用户：现场协调员；区域经理只查看汇总。", bounded_document)
        self.assertIn("尚未经变更委员会批准", bounded_document)

    def test_upstream_provenance_and_package_are_exact(self):
        self.assertEqual(sha(UPSTREAM_ROOT / "provenance.json"), EXPECTED_PROVENANCE_SHA256)
        provenance = json.loads(
            (UPSTREAM_ROOT / "provenance.json").read_text(encoding="utf-8")
        )
        self.assertEqual(provenance["repository"], "https://github.com/coreyhaines31/marketingskills")
        self.assertEqual(provenance["commit"], UPSTREAM_REVISION)
        self.assertEqual(provenance["license"], "MIT")
        self.assertEqual(
            set(provenance["files"]),
            {
                "LICENSE",
                "skills/product-marketing/SKILL.md",
                "skills/product-marketing/LICENSE",
            },
        )
        for relative, metadata in provenance["files"].items():
            self.assertEqual(sha(UPSTREAM_ROOT / relative), metadata["sha256"])
            self.assertIn(UPSTREAM_REVISION, metadata["url"])
        self.assertEqual(
            (UPSTREAM_SKILL / "LICENSE").read_bytes(),
            (UPSTREAM_ROOT / "LICENSE").read_bytes(),
        )
        self.assertEqual(
            VALIDATOR["package_fingerprint"](UPSTREAM_SKILL),
            EXPECTED_UPSTREAM_PACKAGE_SHA256,
        )
        self.assertEqual(
            {
                path.relative_to(UPSTREAM_SKILL).as_posix()
                for path in UPSTREAM_SKILL.rglob("*")
                if path.is_file()
            },
            {"SKILL.md", "LICENSE"},
        )
        self.assertEqual(
            {
                path.relative_to(UPSTREAM_ROOT).as_posix()
                for path in UPSTREAM_ROOT.rglob("*")
                if path.is_file()
            },
            {
                "LICENSE",
                "provenance.json",
                "skills/product-marketing/SKILL.md",
                "skills/product-marketing/LICENSE",
            },
        )

    def test_preparation_hides_rubric_and_copies_exact_packages(self):
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
            packages = {
                "ours": (SKILL, "product-context-brief", EXPECTED_OURS_PACKAGE_SHA256),
                "upstream": (UPSTREAM_SKILL, "product-marketing", EXPECTED_UPSTREAM_PACKAGE_SHA256),
            }
            for arm_id, (source, skill_id, expected_hash) in packages.items():
                arm = next(item for item in frozen["arms"] if item["id"] == arm_id)
                self.assertEqual(arm["skill_package_sha256"], expected_hash)
                self.assertEqual(expected_hash, VALIDATOR["package_fingerprint"](source))
                copied = prepared / "skills" / arm_id / skill_id
                self.assertEqual(
                    {
                        path.relative_to(copied).as_posix(): path.read_bytes()
                        for path in copied.rglob("*")
                        if path.is_file()
                    },
                    {
                        path.relative_to(source).as_posix(): path.read_bytes()
                        for path in source.rglob("*")
                        if path.is_file()
                    },
                )

            config = json.loads((prepared / "promptfooconfig.json").read_text(encoding="utf-8"))
            self.assertEqual(
                [provider["label"] for provider in config["providers"]],
                ["baseline", "ours", "upstream"],
            )
            self.assertEqual(
                {provider["id"] for provider in config["providers"]},
                {"openai:codex-sdk"},
            )
            provider_configs = [provider["config"] for provider in config["providers"]]
            for candidate in provider_configs[1:]:
                self.assertEqual(
                    {k: v for k, v in provider_configs[0].items() if k not in {"working_dir", "cli_env"}},
                    {k: v for k, v in candidate.items() if k not in {"working_dir", "cli_env"}},
                )
            for arm_id, provider_config in zip(
                ("baseline", "ours", "upstream"), provider_configs, strict=True
            ):
                self.assertEqual(provider_config["working_dir"], f"./fixtures/{arm_id}")
                for env_name in ("CODEX_HOME", "HOME", "USERPROFILE"):
                    self.assertEqual(
                        provider_config["cli_env"][env_name].replace(f"/{arm_id}", "/ARM"),
                        provider_configs[0]["cli_env"][env_name].replace("/baseline", "/ARM"),
                    )

            generated = json.loads((prepared / "tests.json").read_text(encoding="utf-8"))
            self.assertEqual(len(generated), len(self.cases) * 3)
            public_prompts = "\n".join(item["vars"]["prompt"] for item in generated)
            for item in generated:
                self.assertEqual(set(item["vars"]), {"prompt"})
            for case in self.cases:
                by_arm = {
                    item["metadata"]["arm_id"]: item
                    for item in generated
                    if item["metadata"]["case_id"] == case["id"]
                }
                self.assertEqual(set(by_arm), {"baseline", "ours", "upstream"})
                common = f'{self.protocol["common_prompt"]}\n\n{case["prompt"]}'
                self.assertEqual(by_arm["baseline"]["vars"]["prompt"], common)
                for arm_id, skill_id in (
                    ("ours", "product-context-brief"),
                    ("upstream", "product-marketing"),
                ):
                    prefix = (
                        f"请显式运行 ${skill_id} 后完成下方任务。"
                        "只返回任务要求的结果，不说明 Skill 加载过程。"
                    )
                    self.assertEqual(by_arm[arm_id]["vars"]["prompt"], f"{prefix}\n\n{common}")
                for criterion in case["hard_criteria"]:
                    self.assertNotIn(criterion, public_prompts)


if __name__ == "__main__":
    unittest.main()
