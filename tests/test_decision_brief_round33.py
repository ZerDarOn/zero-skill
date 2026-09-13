"""Integrity checks for the Round 33 decision brief comparison."""

import copy
import hashlib
import json
from pathlib import Path
import runpy
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]
COMPARISON = ROOT / "evaluations/comparisons/decision-brief-complex-boundaries-two-arm-26"
REPORT_PATH = ROOT / "evaluations/reports/decision-brief-complex-round-33-diagnostic.json"
RUN = ROOT / "evaluations/runs/decision-brief-complex-boundaries-two-arm-26-formal-20260914-v1"
PREFLIGHT = ROOT / "evaluations/runs/decision-brief-complex-boundaries-two-arm-26-preflight-20260914-v1"
ACTIVE = ROOT / "evaluations/cases/decision-brief-draft.json"
SKILL = ROOT / "skills/creation/decision-brief-draft"
PREPARER = ROOT / "evaluations/promptfoo/prepare_skill_comparison.py"
FREEZE_COMMIT = "e9eca467b68a6e7fc29a6a6a0e6e8d672b49901c"
EXPECTED_PROJECTION = "7e9c258da9e6a2e7112e2bbee418cbcc6efe674b648a91041fcefd3459920f03"
ORDER = ("baseline", "ours")
VALIDATOR = runpy.run_path(str(ROOT / "scripts/validate_collection.py"))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def object_sha(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode()
    ).hexdigest()


class DecisionBriefRound33Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
        cls.cases = json.loads(
            (COMPARISON / "cases.json").read_text(encoding="utf-8")
        )
        cls.protocol = json.loads(
            (COMPARISON / "promptfoo.json").read_text(encoding="utf-8")
        )

    def _recompute_failures(self, report, criterion_field):
        case_by = {case["id"]: case for case in self.cases}
        failures = {
            case_id: {arm: 0 for arm in ORDER} for case_id in case_by
        }
        prefix = "raw" if criterion_field == "raw_criteria_pass" else "calibrated"
        for item in report["experiment"]["items"]:
            case = case_by[item["case_id"]]
            for candidate in item["candidates"]:
                criteria = candidate[criterion_field]
                core = any(not criteria[index] for index in case["core_criteria"])
                self.assertEqual(candidate[f"{prefix}_core_failure"], core)
                failures[case["id"]][candidate["arm_id"]] += int(core)
        return failures

    def _expected_mechanisms(self, failures):
        gate = self.protocol["decision_gate"]
        grouped = {}
        for case in self.cases:
            grouped.setdefault(case["mechanism"], []).append(case["id"])
        result = []
        for mechanism, case_ids in grouped.items():
            self.assertEqual(
                len(case_ids), gate["minimum_cases_in_same_mechanism"]
            )
            ours_met = all(
                failures[case_id]["ours"]
                >= gate["ours_min_core_failures_per_case"]
                for case_id in case_ids
            )
            baseline_met = all(
                failures[case_id]["baseline"]
                <= gate["baseline_max_core_failures_per_case"]
                for case_id in case_ids
            )
            result.append(
                {
                    "mechanism": mechanism,
                    "case_ids": case_ids,
                    "core_failures": {
                        case_id: failures[case_id] for case_id in case_ids
                    },
                    "ours_threshold_met": ours_met,
                    "baseline_threshold_met": baseline_met,
                    "triggered": ours_met and baseline_met,
                }
            )
        return result

    def test_sources_projection_and_freeze_are_bound(self):
        report = self.report
        self.assertEqual(
            report["report_id"], "decision-brief-complex-round-33-diagnostic"
        )
        experiment = report["experiment"]
        self.assertEqual(experiment["freeze_commit"], FREEZE_COMMIT)
        sources = {
            "promptfoo.json": COMPARISON / "promptfoo.json",
            "cases.json": COMPARISON / "cases.json",
            "active-cases.json": ACTIVE,
            "SKILL.md": SKILL / "SKILL.md",
            "prepare_skill_comparison.py": PREPARER,
        }
        for name, path in sources.items():
            self.assertEqual(experiment["source_hashes"][name], sha(path))
        for name, expected in experiment["review_hashes"].items():
            self.assertEqual(expected, sha(COMPARISON / name))
        projection = {
            key: report[key]
            for key in ("scope", "experiment", "analysis", "decision", "limitations")
        }
        self.assertEqual(object_sha(projection), report["evidence_projection_sha256"])
        self.assertEqual(report["evidence_projection_sha256"], EXPECTED_PROJECTION)
        self.assertEqual(
            experiment["arms"][1]["skill_package_sha256"],
            VALIDATOR["package_fingerprint"](SKILL),
        )
        self.assertNotIn("D:\\\\", REPORT_PATH.read_text(encoding="utf-8"))
        if (ROOT / ".git").exists():
            subprocess.run(
                ["git", "merge-base", "--is-ancestor", FREEZE_COMMIT, "HEAD"],
                cwd=ROOT,
                check=True,
            )
            for name, path in sources.items():
                if name == "active-cases.json":
                    continue
                frozen = subprocess.run(
                    [
                        "git",
                        "show",
                        f"{FREEZE_COMMIT}:{path.relative_to(ROOT).as_posix()}",
                    ],
                    cwd=ROOT,
                    check=True,
                    capture_output=True,
                ).stdout
                self.assertEqual(
                    hashlib.sha256(frozen).hexdigest(),
                    experiment["source_hashes"][name],
                )

    def test_scores_calibration_failures_gates_and_efficiency_recompute(self):
        report = self.report
        raw_aggregate = {arm: [0, 0, 0, 0] for arm in ORDER}
        calibrated_aggregate = {arm: [0, 0, 0, 0] for arm in ORDER}
        corrections = []
        for item in report["experiment"]["items"]:
            self.assertEqual(len(item["candidates"]), 2)
            for candidate in item["candidates"]:
                arm = candidate["arm_id"]
                raw = candidate["raw_criteria_pass"]
                calibrated = candidate["calibrated_criteria_pass"]
                self.assertEqual(len(raw), 4)
                self.assertEqual(len(calibrated), 4)
                self.assertEqual(
                    candidate["output_sha256"],
                    hashlib.sha256(candidate["output"].encode()).hexdigest(),
                )
                self.assertEqual(candidate["raw_passed"], sum(raw))
                self.assertEqual(candidate["calibrated_passed"], sum(calibrated))
                for index, (before, after) in enumerate(zip(raw, calibrated)):
                    if before != after:
                        self.assertEqual((before, after), (False, True))
                        entry = next(
                            value
                            for value in candidate["calibrations"]
                            if value["criterion_index"] == index
                        )
                        corrections.append((item["review_id"], arm, index, entry["reason"]))
                raw_aggregate[arm][0] += 1
                raw_aggregate[arm][1] += int(all(raw))
                raw_aggregate[arm][2] += sum(raw)
                raw_aggregate[arm][3] += int(candidate["preferred"])
                calibrated_aggregate[arm][0] += 1
                calibrated_aggregate[arm][1] += int(all(calibrated))
                calibrated_aggregate[arm][2] += sum(calibrated)
                calibrated_aggregate[arm][3] += int(candidate["preferred"])
        self.assertEqual(
            raw_aggregate,
            {"baseline": [18, 10, 63, 0], "ours": [18, 14, 68, 5]},
        )
        self.assertEqual(
            calibrated_aggregate,
            {"baseline": [18, 10, 64, 0], "ours": [18, 14, 68, 5]},
        )
        calibration = report["experiment"]["semantic_calibration"]
        self.assertEqual(
            (
                calibration["original_false_count"],
                calibration["correction_count"],
                calibration["retained_false_count"],
            ),
            (13, 1, 12),
        )
        self.assertEqual(len(corrections), 1)
        self.assertEqual(corrections[0][:3], (
            "approved-choice-new-qualification-evidence-r3",
            "baseline",
            2,
        ))
        self.assertEqual(report["analysis"]["preference_ties"], 13)
        raw_failures = self._recompute_failures(report, "raw_criteria_pass")
        calibrated_failures = self._recompute_failures(
            report, "calibrated_criteria_pass"
        )
        expected = {
            "approved-choice-new-qualification-evidence": {"baseline": 2, "ours": 1},
            "cost-correction-does-not-revoke-approval": {"baseline": 0, "ours": 0},
            "normalize-three-year-cost-basis": {"baseline": 0, "ours": 0},
            "no-feasible-option-with-one-unknown": {"baseline": 3, "ours": 3},
            "executive-preference-without-approval-authority": {"baseline": 0, "ours": 0},
            "small-usability-check-does-not-prove-rollout": {"baseline": 0, "ours": 0},
        }
        self.assertEqual(raw_failures, expected)
        self.assertEqual(calibrated_failures, expected)
        self.assertEqual(report["analysis"]["raw_case_core_failures"], expected)
        self.assertEqual(report["analysis"]["calibrated_case_core_failures"], expected)
        self.assertEqual(
            report["analysis"]["raw_mechanisms"],
            self._expected_mechanisms(raw_failures),
        )
        self.assertEqual(
            report["analysis"]["calibrated_mechanisms"],
            self._expected_mechanisms(calibrated_failures),
        )
        self.assertFalse(any(item["triggered"] for item in report["analysis"]["raw_mechanisms"]))
        self.assertFalse(any(item["triggered"] for item in report["analysis"]["calibrated_mechanisms"]))
        runtime = {
            arm["arm_id"]: arm["runtime"] for arm in report["experiment"]["arms"]
        }
        expected_efficiency = {}
        for field in ("tokens_total", "cost_total", "latency_ms_median"):
            left = runtime["ours"][field]["total"] if field == "tokens_total" else runtime["ours"][field]
            right = runtime["baseline"][field]["total"] if field == "tokens_total" else runtime["baseline"][field]
            expected_efficiency[field] = round((left / right - 1) * 100, 1)
        self.assertEqual(
            report["analysis"]["efficiency"]["ours_vs_baseline_percent"],
            expected_efficiency,
        )

    def test_active_cases_and_skill_state_match_decision(self):
        active = json.loads(ACTIVE.read_text(encoding="utf-8"))
        by_id = {case["id"]: case for case in active["cases"]}
        self.assertEqual(len(by_id), 12)
        for case in self.cases:
            current = by_id[case["id"]]
            self.assertEqual(current["prompt"], case["prompt"])
            self.assertEqual(current["expected_route"], "decision-brief-draft")
            self.assertEqual(
                current["input"],
                {"kind": "synthetic", "comparison_case_id": case["id"]},
            )
            self.assertEqual(len(current["must_include"]), 3)
            self.assertEqual(len(current["must_avoid"]), 3)
        catalog = json.loads(
            (ROOT / "catalog/collection.json").read_text(encoding="utf-8")
        )
        entry = next(
            item for item in catalog["skills"] if item["id"] == "decision-brief-draft"
        )
        self.assertEqual(
            (entry["version"], entry["status"], entry["evidence"]),
            ("0.1.1", "experimental", None),
        )
        total = sum(
            len(
                json.loads(
                    (ROOT / item["evaluation"]).read_text(encoding="utf-8")
                )["cases"]
            )
            for item in catalog["skills"]
        )
        self.assertEqual(self.report["scope"]["collection_active_case_count"], 178)
        self.assertGreaterEqual(total, 178)
        decision = self.report["decision"]
        self.assertEqual(decision["active_cases_sha256"], sha(ACTIVE))
        self.assertEqual(
            decision["skill_package_sha256"], VALIDATOR["package_fingerprint"](SKILL)
        )
        self.assertEqual(
            decision["active_cases_added"], [case["id"] for case in self.cases]
        )
        self.assertFalse(
            any(
                decision[field]
                for field in (
                    "candidate_design_open",
                    "skill_changed",
                    "version_changed",
                    "verification_status_changed",
                )
            )
        )

    def test_ignored_runs_reproject_when_present(self):
        if not RUN.is_dir():
            self.skipTest("ignored Round 33 run is unavailable")
        self.assertTrue(PREFLIGHT.is_dir())
        experiment = self.report["experiment"]
        for name, expected in experiment["artifact_hashes"].items():
            self.assertEqual(sha(RUN / name), expected)
        self.assertEqual(
            sha(PREFLIGHT / "summary.json"),
            experiment["preflight"]["summary_sha256"],
        )
        frozen = json.loads((RUN / "frozen.json").read_text(encoding="utf-8"))
        summary = json.loads((RUN / "summary.json").read_text(encoding="utf-8"))
        self.assertEqual(frozen["spec_sha256"], experiment["source_hashes"]["promptfoo.json"])
        self.assertEqual(frozen["cases_sha256"], experiment["source_hashes"]["cases.json"])
        self.assertEqual(frozen["prepared_config_sha256"], experiment["prepared_hashes"]["config"])
        self.assertEqual(frozen["prepared_tests_sha256"], experiment["prepared_hashes"]["tests"])
        self.assertTrue(summary["infrastructure_valid"])
        self.assertEqual(sum(arm["rows"] for arm in summary["arms"]), 36)
        self.assertEqual(sum(arm["provider_errors"] for arm in summary["arms"]), 0)
        self.assertEqual(sum(arm["forbidden_tool_rows"] for arm in summary["arms"]), 0)
        self.assertEqual(
            {arm["id"]: arm for arm in summary["arms"]},
            {
                arm["arm_id"]: arm["runtime"]
                for arm in experiment["arms"]
            },
        )
        packet = json.loads((RUN / "blind-review.json").read_text(encoding="utf-8"))
        key = json.loads((RUN / "blind-review-key.json").read_text(encoding="utf-8"))
        completed = json.loads(
            (RUN / "blind-review-completed-independent.json").read_text(encoding="utf-8")
        )
        packet_by = {item["review_id"]: item for item in packet["items"]}
        key_by = {item["review_id"]: item for item in key["items"]}
        completed_by = {item["review_id"]: item for item in completed["reviews"]}
        public_by = {item["review_id"]: item for item in experiment["items"]}
        self.assertEqual(set(public_by), set(packet_by))
        for review_id, public in public_by.items():
            outputs = {
                item["candidate_id"]: item["output"]
                for item in packet_by[review_id]["candidates"]
            }
            identities = {
                item["candidate_id"]: item["arm_id"]
                for item in key_by[review_id]["candidates"]
            }
            raw = completed_by[review_id]["criteria_pass"]
            for candidate in public["candidates"]:
                candidate_id = candidate["candidate_id"]
                self.assertEqual(candidate["output"], outputs[candidate_id])
                self.assertEqual(candidate["arm_id"], identities[candidate_id])
                self.assertEqual(candidate["raw_criteria_pass"], raw[candidate_id])

    def test_coordinated_mutations_fail_fixed_or_semantic_checks(self):
        mutated = copy.deepcopy(self.report)
        candidate = mutated["experiment"]["items"][0]["candidates"][0]
        candidate["output"] += "篡改"
        candidate["output_sha256"] = hashlib.sha256(candidate["output"].encode()).hexdigest()
        projection = {
            key: mutated[key]
            for key in ("scope", "experiment", "analysis", "decision", "limitations")
        }
        mutated["evidence_projection_sha256"] = object_sha(projection)
        self.assertNotEqual(mutated["evidence_projection_sha256"], EXPECTED_PROJECTION)

        gate_mutation = copy.deepcopy(self.report)
        gate_mutation["analysis"]["raw_mechanisms"][0]["triggered"] = True
        failures = self._recompute_failures(gate_mutation, "raw_criteria_pass")
        self.assertNotEqual(
            gate_mutation["analysis"]["raw_mechanisms"],
            self._expected_mechanisms(failures),
        )


if __name__ == "__main__":
    unittest.main()
