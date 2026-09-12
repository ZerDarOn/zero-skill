"""Protect the frozen Round 27 implicit discovery design."""

import hashlib
import json
from pathlib import Path
import runpy
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
COMPARISON = (
    ROOT / "evaluations" / "comparisons" / "implicit-discovery-host-boundary-20"
)
PROTOCOL_PATH = COMPARISON / "protocol.json"
PREPARE = runpy.run_path(
    str(ROOT / "evaluations" / "promptfoo" / "prepare_skill_comparison.py")
)
RUNNER = runpy.run_path(
    str(ROOT / "evaluations" / "native_resume" / "run_native_resume.py")
)
VALIDATOR = runpy.run_path(str(ROOT / "scripts" / "validate_collection.py"))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ImplicitDiscoveryRound27Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.protocol = json.loads(PROTOCOL_PATH.read_text(encoding="utf-8"))
        cls.spec = json.loads((COMPARISON / "promptfoo.json").read_text(encoding="utf-8"))
        cls.cases = json.loads((COMPARISON / "cases.json").read_text(encoding="utf-8"))

    def test_protocol_binds_current_design_and_infrastructure(self):
        protocol = self.protocol
        self.assertEqual(protocol["id"], "implicit-discovery-host-boundary-20")
        self.assertEqual(protocol["model"], "gpt-5.6-sol")
        self.assertEqual(protocol["reasoning_effort"], "medium")
        self.assertEqual(protocol["repetitions"], 3)
        self.assertEqual(protocol["job_order_seed"], 270913)
        for binding in protocol["infrastructure"].values():
            self.assertEqual(sha256_file(ROOT / binding["path"]), binding["sha256"])
        cohort = protocol["cohort"]
        self.assertEqual(sha256_file(ROOT / cohort["spec"]), cohort["spec_sha256"])
        self.assertEqual(sha256_file(ROOT / cohort["cases"]), cohort["cases_sha256"])
        self.assertEqual(
            VALIDATOR["package_fingerprint"](
                COMPARISON / "fixtures" / "implicit-discovery-probe"
            ),
            cohort["skill_package_sha256"],
        )
        self.assertFalse(protocol["gate"]["quality_scoring"])
        self.assertFalse(protocol["gate"]["skill_change_authorized"])
        self.assertTrue(protocol["gate"]["business_comparison_requires_pass"])
        self.assertFalse(
            protocol["decision_boundary"]["skill_or_catalog_change_authorized"]
        )

    def test_two_natural_surfaces_freeze_twelve_trajectories(self):
        self.assertEqual(self.spec["comparison_kind"], "discovery")
        self.assertEqual([arm["id"] for arm in self.spec["arms"]], ["baseline", "probe"])
        self.assertEqual(self.spec["arms"][1]["skill"]["invocation"], "implicit")
        self.assertEqual(len(self.cases), 2)
        self.assertEqual(len(self.cases) * len(self.spec["arms"]) * 3, 12)
        tokens = set(self.protocol["cohort"]["expected_output_by_case"].values())
        skill_id = self.protocol["cohort"]["probe_skill"]
        for case in self.cases:
            self.assertEqual(case["turns"], [case["prompt"]])
            self.assertEqual(len(case["hard_criteria"]), 4)
            self.assertEqual(
                case["expected_output"],
                self.protocol["cohort"]["expected_output_by_case"][case["id"]],
            )
            self.assertNotIn(skill_id, case["prompt"])
            self.assertTrue(all(token not in case["prompt"] for token in tokens))
        self.assertNotIn(skill_id, self.spec["common_prompt"])
        self.assertTrue(
            all(token not in self.spec["common_prompt"] for token in tokens)
        )

    def test_preparation_keeps_prompts_equal_and_fixtures_isolated(self):
        runs_root = ROOT / "evaluations" / "runs"
        runs_root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=runs_root) as temporary:
            run_dir = Path(temporary) / "run"
            PREPARE["prepare_comparison"](
                ROOT, COMPARISON / "promptfoo.json", run_dir
            )
            frozen = json.loads((run_dir / "frozen.json").read_text(encoding="utf-8"))
            prompts = RUNNER["load_prepared_prompts"](run_dir, frozen)
            manifests = RUNNER["verify_execution_fixtures"](run_dir, frozen)
            self.assertEqual(manifests["baseline"], {})
            self.assertEqual(
                list(manifests["probe"]),
                [".agents/skills/implicit-discovery-probe/SKILL.md"],
            )
            for case in self.cases:
                self.assertEqual(
                    prompts[(case["id"], "baseline")],
                    prompts[(case["id"], "probe")],
                )
                self.assertNotIn(
                    self.protocol["cohort"]["probe_skill"],
                    prompts[(case["id"], "probe")],
                )
            self.assertTrue(frozen["constraints"]["implicit_skill_trace_assertions"])
            self.assertEqual(frozen["constraints"]["sandbox_mode"], "read-only")


if __name__ == "__main__":
    unittest.main()
