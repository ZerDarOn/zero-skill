"""Frozen-design checks for article visual planning three-arm comparison."""

import hashlib
import json
from pathlib import Path
import re
import runpy
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
COMPARISON = (
    ROOT
    / "evaluations"
    / "comparisons"
    / "article-visual-plan-three-arm-22"
)
COMMIT = "6b7a2e417500561a5ecdd0b168332f4142584617"
FIXTURE = (
    ROOT
    / "evaluations"
    / "fixtures"
    / "upstreams"
    / "baoyu-skills"
    / COMMIT
)


class ArticleVisualComparisonTests(unittest.TestCase):
    def test_protocol_has_balanced_three_arm_repeated_design_and_frozen_gate(self):
        protocol = json.loads((COMPARISON / "promptfoo.json").read_text(encoding="utf-8"))
        cases = json.loads((COMPARISON / "cases.json").read_text(encoding="utf-8"))
        self.assertEqual(protocol["model"], "gpt-5.6-sol")
        self.assertEqual(protocol["reasoning_effort"], "medium")
        self.assertEqual(protocol["repetitions"], 3)
        self.assertEqual(protocol["sandbox_mode"], "read-only")
        self.assertIn("跳过偏好配置、EXTEND.md 检查、首次设置、确认、生图、写盘和文章回填", protocol["common_prompt"])
        self.assertEqual([arm["id"] for arm in protocol["arms"]], ["baseline", "ours", "upstream"])
        self.assertIsNone(protocol["arms"][0]["skill"])
        self.assertEqual(protocol["arms"][1]["skill"]["id"], "article-visual-plan")
        self.assertEqual(protocol["arms"][2]["skill"]["id"], "baoyu-article-illustrator")
        self.assertEqual(len(cases) * len(protocol["arms"]) * protocol["repetitions"], 54)
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

    def test_cases_cover_two_tasks_per_mechanism_with_valid_core_indexes(self):
        cases = json.loads((COMPARISON / "cases.json").read_text(encoding="utf-8"))
        counts = {}
        for case in cases:
            counts[case["mechanism"]] = counts.get(case["mechanism"], 0) + 1
            self.assertEqual(len(case["hard_criteria"]), 4)
            self.assertEqual(len(set(case["core_criteria"])), len(case["core_criteria"]))
            self.assertTrue(case["core_criteria"])
            self.assertTrue(all(0 <= index < 4 for index in case["core_criteria"]))
        self.assertEqual(
            counts,
            {
                "value-based-selection": 2,
                "evidence-strength": 2,
                "plan-state-preservation": 2,
            },
        )

    def test_upstream_fixture_matches_fixed_commit_provenance(self):
        provenance = json.loads((FIXTURE / "provenance.json").read_text(encoding="utf-8"))
        self.assertEqual(provenance["repository"], "https://github.com/JimLiu/baoyu-skills")
        self.assertEqual(provenance["commit"], COMMIT)
        self.assertEqual(provenance["license"], "MIT")
        self.assertIn("No upstream source bytes changed", provenance["modifications"])
        self.assertIn("no upstream code is installed or executed", provenance["modifications"])
        self.assertEqual(len(provenance["known_source_issues"]), 1)
        self.assertIn("references/references/style-presets.md", provenance["known_source_issues"][0])
        recorded = set(provenance["files"])
        actual = {
            path.relative_to(FIXTURE).as_posix()
            for path in FIXTURE.rglob("*")
            if path.is_file() and path.name != "provenance.json"
        }
        self.assertEqual(recorded, actual)
        self.assertIn("skills/baoyu-article-illustrator/SKILL.md", recorded)
        self.assertIn("skills/baoyu-article-illustrator/references/workflow.md", recorded)
        for name, evidence in provenance["files"].items():
            self.assertEqual(hashlib.sha256((FIXTURE / name).read_bytes()).hexdigest(), evidence["sha256"])
        self.assertEqual(
            (FIXTURE / "LICENSE").read_bytes(),
            (FIXTURE / "skills" / "baoyu-article-illustrator" / "LICENSE").read_bytes(),
        )
        self.assertIn("MIT License", (FIXTURE / "LICENSE").read_text(encoding="utf-8"))

    def test_upstream_source_bytes_stay_lf_and_only_known_markdown_link_is_broken(self):
        package = FIXTURE / "skills" / "baoyu-article-illustrator"
        source_files = [FIXTURE / "LICENSE", *sorted(package.rglob("*.md"))]
        for path in source_files:
            self.assertNotIn(b"\r\n", path.read_bytes(), path.relative_to(FIXTURE).as_posix())

        link_pattern = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
        missing = []
        for path in sorted(package.rglob("*.md")):
            for raw_target in link_pattern.findall(path.read_text(encoding="utf-8")):
                target = raw_target.strip().strip("<>").split("#", 1)[0]
                if not target.endswith(".md") or "://" in target:
                    continue
                resolved = path.parent / target
                if not resolved.exists():
                    missing.append((path.relative_to(package).as_posix(), raw_target))
        self.assertEqual(
            missing,
            [("references/usage.md", "references/style-presets.md")],
        )

    def test_prepared_prompts_exclude_hidden_rubric_and_package_carries_license(self):
        prepare = runpy.run_path(
            str(ROOT / "evaluations" / "promptfoo" / "prepare_skill_comparison.py")
        )
        cases = json.loads((COMPARISON / "cases.json").read_text(encoding="utf-8"))
        case_by_id = {case["id"]: case for case in cases}
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "prepared-run"
            prepare["prepare_comparison"](
                repo_root=ROOT,
                spec_path=COMPARISON / "promptfoo.json",
                output_dir=output,
            )
            tests = json.loads((output / "prepared" / "tests.json").read_text(encoding="utf-8"))
            frozen = json.loads((output / "frozen.json").read_text(encoding="utf-8"))
            prepared_license = (
                output
                / "prepared"
                / "fixtures"
                / "upstream"
                / ".agents"
                / "skills"
                / "baoyu-article-illustrator"
                / "LICENSE"
            )
            self.assertEqual(prepared_license.read_bytes(), (FIXTURE / "LICENSE").read_bytes())
        self.assertEqual(len(tests), 18)
        self.assertEqual(frozen["selected_case_ids"], [case["id"] for case in cases])
        upstream = next(arm for arm in frozen["arms"] if arm["id"] == "upstream")
        self.assertIn("LICENSE", {item["path"] for item in upstream["files"]})
        for test in tests:
            source = case_by_id[test["metadata"]["case_id"]]
            prompt = test["vars"]["prompt"]
            self.assertNotIn("core_criteria", test["metadata"])
            self.assertNotIn("core_criteria", prompt)
            self.assertFalse(any(criterion in prompt for criterion in source["hard_criteria"]))


if __name__ == "__main__":
    unittest.main()
