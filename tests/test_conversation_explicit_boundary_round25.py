"""Protect the frozen Round 25 explicit-boundary confirmation protocol."""

import hashlib
import json
from pathlib import Path
import runpy
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
COMPARISON = (
    ROOT
    / "evaluations"
    / "comparisons"
    / "conversation-explicit-boundary-two-arm-18"
)
PREPARE = runpy.run_path(
    str(ROOT / "evaluations" / "promptfoo" / "prepare_skill_comparison.py")
)
RUNNER = runpy.run_path(
    str(ROOT / "evaluations" / "native_resume" / "run_native_resume.py")
)
VALIDATOR = runpy.run_path(str(ROOT / "scripts" / "validate_collection.py"))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ConversationExplicitBoundaryRound25Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec = json.loads(
            (COMPARISON / "promptfoo.json").read_text(encoding="utf-8")
        )
        cls.cases = json.loads(
            (COMPARISON / "cases.json").read_text(encoding="utf-8")
        )

    def test_frozen_design_has_two_paired_mechanisms(self):
        self.assertEqual(
            self.spec["id"], "conversation-explicit-boundary-two-arm-18"
        )
        self.assertEqual(self.spec["model"], "gpt-5.6-sol")
        self.assertEqual(self.spec["reasoning_effort"], "medium")
        self.assertEqual(self.spec["repetitions"], 3)
        self.assertEqual([arm["id"] for arm in self.spec["arms"]], ["baseline", "ours"])

        case_ids = [case["id"] for case in self.cases]
        self.assertEqual(len(case_ids), len(set(case_ids)))
        mechanisms = {}
        for case in self.cases:
            mechanisms.setdefault(case["mechanism"], []).append(case["id"])
            self.assertEqual(case["prompt"], case["turns"][0])
            self.assertEqual(len(case["turns"]), 1)
            self.assertEqual(len(case["hard_criteria"]), 4)
            for criterion in case["hard_criteria"]:
                self.assertNotIn(criterion, case["prompt"])
        self.assertEqual(
            {name: len(ids) for name, ids in mechanisms.items()},
            {"explicit-boundary-clarity": 2, "generalized-fiction-control": 2},
        )
        self.assertEqual(len(self.cases) * len(self.spec["arms"]) * 3, 24)
        self.assertEqual(
            sum(len(case["turns"]) for case in self.cases)
            * len(self.spec["arms"])
            * 3,
            24,
        )
        self.assertEqual(
            sum(len(case["hard_criteria"]) for case in self.cases)
            * len(self.spec["arms"])
            * 3,
            96,
        )

    def test_candidate_gate_is_mechanism_paired_and_failure_specific(self):
        self.assertEqual(
            self.spec["candidate_gate"],
            {
                "group_field": "mechanism",
                "cases_per_group": 2,
                "criterion_index": 0,
                "ours_arm": "ours",
                "baseline_arm": "baseline",
                "ours_min_failures_per_case": 2,
                "baseline_max_failures_per_case": 1,
                "require_all_cases_in_group": True,
                "opens_candidate_design_only": True,
            },
        )

    def test_prepare_binds_sources_fixtures_and_prompt_isolation(self):
        runs_root = ROOT / "evaluations" / "runs"
        runs_root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=runs_root) as temporary:
            run_dir = Path(temporary) / "run"
            PREPARE["prepare_comparison"](
                ROOT,
                COMPARISON / "promptfoo.json",
                run_dir,
            )
            frozen = json.loads(
                (run_dir / "frozen.json").read_text(encoding="utf-8")
            )
            tests = json.loads(
                (run_dir / "prepared" / "tests.json").read_text(encoding="utf-8")
            )
            self.assertEqual(
                frozen["spec_sha256"], sha256_file(COMPARISON / "promptfoo.json")
            )
            self.assertEqual(
                frozen["cases_sha256"], sha256_file(COMPARISON / "cases.json")
            )
            self.assertEqual(
                frozen["arms"][1]["skill_package_sha256"],
                VALIDATOR["package_fingerprint"](
                    ROOT / "skills" / "relationships" / "conversation-rehearsal"
                ),
            )
            manifests = RUNNER["verify_execution_fixtures"](run_dir, frozen)
            self.assertEqual(manifests["baseline"], {})
            self.assertEqual(
                list(manifests["ours"]),
                [
                    ".agents/skills/conversation-rehearsal/SKILL.md",
                    ".agents/skills/conversation-rehearsal/references/example.md",
                ],
            )

            self.assertEqual(len(tests), 8)
            prompts = RUNNER["load_prepared_prompts"](run_dir, frozen)
            all_criteria = [
                criterion
                for case in self.cases
                for criterion in case["hard_criteria"]
            ]
            for test in tests:
                self.assertEqual(set(test["vars"]), {"prompt"})
                self.assertTrue(
                    all(criterion not in test["vars"]["prompt"] for criterion in all_criteria)
                )
            for case in self.cases:
                baseline = prompts[(case["id"], "baseline")]
                ours = prompts[(case["id"], "ours")]
                self.assertNotIn("$conversation-rehearsal", baseline)
                self.assertIn("$conversation-rehearsal", ours)
                self.assertTrue(baseline.endswith(case["turns"][0]))
                self.assertTrue(ours.endswith(case["turns"][0]))


if __name__ == "__main__":
    unittest.main()
