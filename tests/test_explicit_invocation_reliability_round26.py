"""Protect the frozen Round 26 explicit invocation reliability protocol."""

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
    / "explicit-invocation-reliability-19"
)
PREPARE = runpy.run_path(
    str(ROOT / "evaluations" / "promptfoo" / "prepare_skill_comparison.py")
)
ANALYZER = runpy.run_path(
    str(
        ROOT
        / "evaluations"
        / "native_resume"
        / "analyze_invocation_reliability.py"
    )
)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ExplicitInvocationReliabilityRound26Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.protocol = json.loads(
            (COMPARISON / "protocol.json").read_text(encoding="utf-8")
        )
        cls.cohorts = ANALYZER["validate_protocol"](cls.protocol)

    def test_protocol_binds_specs_and_operational_infrastructure(self):
        self.assertEqual(self.protocol["id"], "explicit-invocation-reliability-19")
        self.assertEqual(self.protocol["model"], "gpt-5.6-sol")
        self.assertEqual(self.protocol["reasoning_effort"], "medium")
        self.assertEqual(self.protocol["repetitions"], 10)
        self.assertEqual(self.protocol["job_order_seed"], 260913)
        for cohort in self.cohorts:
            self.assertEqual(
                sha256_file(ROOT / cohort["spec"]), cohort["spec_sha256"]
            )
            spec_path = ROOT / cohort["spec"]
            spec = json.loads(spec_path.read_text(encoding="utf-8"))
            skill = next(arm["skill"] for arm in spec["arms"] if arm["skill"])
            source = (spec_path.parent / skill["source"]).resolve()
            self.assertEqual(
                PREPARE["package_sha256"](source), cohort["skill_package_sha256"]
            )
        for item in self.protocol["infrastructure"].values():
            self.assertEqual(sha256_file(ROOT / item["path"]), item["sha256"])

    def test_two_cohorts_freeze_eighty_single_turn_trajectories(self):
        total = 0
        for cohort in self.cohorts:
            spec_path = ROOT / cohort["spec"]
            spec = json.loads(spec_path.read_text(encoding="utf-8"))
            cases = json.loads((spec_path.parent / spec["cases"]).read_text(encoding="utf-8"))
            self.assertEqual(spec["comparison_kind"], "operational")
            self.assertEqual(spec["repetitions"], 10)
            self.assertEqual(spec["native_resume"]["job_order_seed"], 260913)
            self.assertEqual(len(cases), 2)
            self.assertEqual(len(spec["arms"]), 2)
            for case in cases:
                self.assertEqual(case["turns"], [case["prompt"]])
                self.assertEqual(len(case["hard_criteria"]), 4)
                for criterion in case["hard_criteria"]:
                    self.assertNotIn(criterion, case["prompt"])
            total += len(cases) * len(spec["arms"]) * spec["repetitions"]
        self.assertEqual(total, 80)

    def test_business_cases_preserve_the_round25_task_shapes(self):
        previous = json.loads(
            (
                ROOT
                / "evaluations"
                / "comparisons"
                / "conversation-explicit-boundary-two-arm-18"
                / "cases.json"
            ).read_text(encoding="utf-8")
        )
        previous_by_id = {case["id"]: case for case in previous}
        current = json.loads(
            (COMPARISON / "business" / "cases.json").read_text(encoding="utf-8")
        )
        expected = {
            "business-explicit-boundary": "explicit-boundary-work-style-imitation",
            "business-fictional-counterpart": "generic-counterpart-no-boundary-detour",
        }
        for case in current:
            self.assertEqual(case["prompt"], previous_by_id[expected[case["id"]]]["prompt"])

    def test_preparation_isolates_prompts_fixtures_and_hidden_tokens(self):
        with tempfile.TemporaryDirectory(
            dir=ROOT / "evaluations" / "runs"
        ) as temporary:
            base = Path(temporary)
            for cohort in self.cohorts:
                spec_path = ROOT / cohort["spec"]
                run_dir = base / cohort["id"]
                PREPARE["prepare_comparison"](ROOT, spec_path, run_dir)
                frozen = json.loads(
                    (run_dir / "frozen.json").read_text(encoding="utf-8")
                )
                tests = json.loads(
                    (run_dir / "prepared" / "tests.json").read_text(encoding="utf-8")
                )
                self.assertEqual(frozen["comparison_kind"], "operational")
                self.assertEqual(frozen["spec_sha256"], cohort["spec_sha256"])
                prompts = {
                    (item["metadata"]["case_id"], item["metadata"]["arm_id"]):
                    item["vars"]["prompt"]
                    for item in tests
                }
                for case_id in frozen["selected_case_ids"]:
                    baseline = prompts[(case_id, cohort["baseline_arm"])]
                    skill = prompts[(case_id, cohort["skill_arm"])]
                    self.assertNotIn("请显式运行 $", baseline)
                    self.assertIn("请显式运行 $", skill)
                baseline_fixture = (
                    run_dir
                    / "prepared"
                    / "fixtures"
                    / cohort["baseline_arm"]
                )
                self.assertEqual(list(baseline_fixture.rglob("*")), [])

                if cohort["role"] == "canary":
                    for token in cohort["expected_output_by_case"].values():
                        self.assertTrue(all(token not in prompt for prompt in prompts.values()))
                    probe = (
                        run_dir
                        / "prepared"
                        / "fixtures"
                        / cohort["skill_arm"]
                        / ".agents"
                        / "skills"
                        / "explicit-invocation-probe"
                        / "SKILL.md"
                    )
                    self.assertTrue(probe.is_file())


if __name__ == "__main__":
    unittest.main()
