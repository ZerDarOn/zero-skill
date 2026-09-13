"""Integrity checks for the Round 34 product-context comparison."""

import copy
import hashlib
import json
from pathlib import Path
import runpy
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]
COMPARISON = ROOT / "evaluations/comparisons/product-context-boundaries-three-arm-27"
REPORT_PATH = ROOT / "evaluations/reports/product-context-boundaries-round-34-diagnostic.json"
RUN = ROOT / "evaluations/runs/product-context-boundaries-three-arm-27-formal-20260914-v1"
PREFLIGHT = ROOT / "evaluations/runs/product-context-boundaries-three-arm-27-preflight-20260914-v1"
ACTIVE = ROOT / "evaluations/cases/product-context-brief.json"
SKILL = ROOT / "skills/productivity/product-context-brief"
UPSTREAM = ROOT / "evaluations/fixtures/upstreams/marketingskills/5b2c0007766c6a1cf1d53fd8fc73e979e0821022"
PREPARER = ROOT / "evaluations/promptfoo/prepare_skill_comparison.py"
FREEZE_COMMIT = "977af538a891126ad560e7286dd3cd9b778ef2ef"
EXPECTED_PROJECTION = "522d357dad423b0a2a2a76fda1eabaf59fa14d812256f300b5bab8d540584034"
ORDER = ("baseline", "ours", "upstream")
VALIDATOR = runpy.run_path(str(ROOT / "scripts/validate_collection.py"))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def object_sha(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


class ProductContextRound34Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
        cls.cases = json.loads((COMPARISON / "cases.json").read_text(encoding="utf-8"))
        cls.protocol = json.loads((COMPARISON / "promptfoo.json").read_text(encoding="utf-8"))

    def _recompute_failures(self, field):
        result = {case["id"]: {arm: 0 for arm in ORDER} for case in self.cases}
        case_by = {case["id"]: case for case in self.cases}
        prefix = "raw" if field == "raw_criteria_pass" else "calibrated"
        for item in self.report["experiment"]["items"]:
            case = case_by[item["case_id"]]
            for candidate in item["candidates"]:
                values = candidate[field]
                core = any(not values[index] for index in case["core_criteria"])
                self.assertEqual(candidate[f"{prefix}_core_failure"], core)
                result[item["case_id"]][candidate["arm_id"]] += int(core)
        return result

    def _expected_mechanisms(self, failures):
        grouped = {}
        for case in self.cases:
            grouped.setdefault(case["mechanism"], []).append(case["id"])
        gate = self.protocol["decision_gate"]
        result = []
        for mechanism, case_ids in grouped.items():
            self.assertEqual(len(case_ids), gate["minimum_cases_in_same_mechanism"])
            ours_met = all(
                failures[case_id]["ours"] >= gate["ours_min_core_failures_per_case"]
                for case_id in case_ids
            )
            baseline_met = all(
                failures[case_id]["baseline"] <= gate["baseline_max_core_failures_per_case"]
                for case_id in case_ids
            )
            result.append(
                {
                    "mechanism": mechanism,
                    "case_ids": case_ids,
                    "core_failures": {case_id: failures[case_id] for case_id in case_ids},
                    "ours_threshold_met": ours_met,
                    "baseline_threshold_met": baseline_met,
                    "triggered": ours_met and baseline_met,
                }
            )
        return result

    def _assert_raw_run_semantics(self, frozen, run_meta, summary, preflight_summary):
        experiment = self.report["experiment"]
        self.assertEqual(frozen["comparison_id"], self.protocol["id"])
        self.assertEqual(frozen["spec_sha256"], experiment["source_hashes"]["promptfoo.json"])
        self.assertEqual(frozen["cases_sha256"], experiment["source_hashes"]["cases.json"])
        self.assertEqual(frozen["prepared_config_sha256"], experiment["prepared_hashes"]["config"])
        self.assertEqual(frozen["prepared_tests_sha256"], experiment["prepared_hashes"]["tests"])
        self.assertEqual({arm["id"] for arm in frozen["arms"]}, set(ORDER))

        self.assertEqual(run_meta["comparison_id"], self.protocol["id"])
        self.assertEqual(run_meta["frozen_sha256"], sha(RUN / "frozen.json"))
        self.assertEqual(run_meta["repeat"], 3)
        self.assertEqual(len(run_meta["commands"]), 2)
        validate_command, eval_command = run_meta["commands"]
        self.assertEqual(validate_command[:3], eval_command[:3])
        self.assertEqual(validate_command[3:], ["validate", "config", "-c", "promptfooconfig.json"])
        self.assertEqual(
            eval_command[3:],
            ["eval", "-c", "promptfooconfig.json", "--repeat", "3", "--no-cache", "-o", "results.json", "-o", "results.html"],
        )
        self.assertEqual(sum(command.count("eval") for command in run_meta["commands"]), 1)
        self.assertEqual((run_meta["validation_exit_code"], run_meta["exit_code"], run_meta["status"]), (0, 0, "completed"))
        self.assertEqual(
            (run_meta["expected_rows"], run_meta["result_rows"], run_meta["passed_rows"], run_meta["failed_rows"]),
            (54, 54, 54, 0),
        )
        self.assertEqual(run_meta["results_sha256"], experiment["artifact_hashes"]["results.json"])

        self.assertEqual(summary["comparison_id"], self.protocol["id"])
        self.assertEqual(summary["comparison_kind"], "quality")
        self.assertTrue(summary["infrastructure_valid"])
        self.assertEqual((summary["planned_repetitions"], summary["executed_repetitions"]), (3, 3))
        self.assertEqual(summary["results_sha256"], run_meta["results_sha256"])
        self.assertEqual({arm["id"] for arm in summary["arms"]}, set(ORDER))
        self.assertEqual(sum(arm["rows"] for arm in summary["arms"]), 54)
        for arm in summary["arms"]:
            self.assertEqual((arm["rows"], arm["promptfoo_passed_rows"], arm["provider_errors"], arm["forbidden_tool_rows"]), (18, 18, 0, 0))
        self.assertEqual(
            {arm["arm_id"]: arm["runtime"] for arm in experiment["arms"]},
            {arm["id"]: arm for arm in summary["arms"]},
        )

        self.assertEqual(preflight_summary["comparison_id"], self.protocol["id"])
        self.assertEqual(preflight_summary["comparison_kind"], "quality")
        self.assertTrue(preflight_summary["infrastructure_valid"])
        self.assertEqual(preflight_summary["executed_repetitions"], 1)
        self.assertEqual({arm["id"] for arm in preflight_summary["arms"]}, set(ORDER))
        self.assertEqual(sum(arm["rows"] for arm in preflight_summary["arms"]), 3)
        for arm in preflight_summary["arms"]:
            self.assertEqual((arm["rows"], arm["promptfoo_passed_rows"], arm["provider_errors"], arm["forbidden_tool_rows"]), (1, 1, 0, 0))

    def test_sources_projection_and_freeze_are_bound(self):
        report = self.report
        self.assertEqual(report["report_id"], "product-context-boundaries-round-34-diagnostic")
        experiment = report["experiment"]
        self.assertEqual(experiment["freeze_commit"], FREEZE_COMMIT)
        sources = {
            "promptfoo.json": COMPARISON / "promptfoo.json",
            "cases.json": COMPARISON / "cases.json",
            "active-cases.json": ACTIVE,
            "ours/SKILL.md": SKILL / "SKILL.md",
            "upstream/SKILL.md": UPSTREAM / "skills/product-marketing/SKILL.md",
            "upstream/LICENSE": UPSTREAM / "skills/product-marketing/LICENSE",
            "upstream/provenance.json": UPSTREAM / "provenance.json",
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
        self.assertNotIn("D:\\\\", REPORT_PATH.read_text(encoding="utf-8"))
        self.assertEqual(
            experiment["arms"][1]["skill_package_sha256"],
            VALIDATOR["package_fingerprint"](SKILL),
        )
        self.assertEqual(
            experiment["arms"][2]["skill_package_sha256"],
            VALIDATOR["package_fingerprint"](UPSTREAM / "skills/product-marketing"),
        )
        if (ROOT / ".git").exists():
            subprocess.run(["git", "merge-base", "--is-ancestor", FREEZE_COMMIT, "HEAD"], cwd=ROOT, check=True)
            for name, path in sources.items():
                if name == "active-cases.json":
                    continue
                frozen = subprocess.run(
                    ["git", "show", f"{FREEZE_COMMIT}:{path.relative_to(ROOT).as_posix()}"],
                    cwd=ROOT,
                    check=True,
                    capture_output=True,
                ).stdout
                self.assertEqual(hashlib.sha256(frozen).hexdigest(), experiment["source_hashes"][name])

    def test_scores_calibration_failures_gates_and_efficiency_recompute(self):
        raw = {arm: [0, 0, 0, 0] for arm in ORDER}
        calibrated = {arm: [0, 0, 0, 0] for arm in ORDER}
        false_entries = []
        for item in self.report["experiment"]["items"]:
            self.assertEqual(len(item["candidates"]), 3)
            for candidate in item["candidates"]:
                arm = candidate["arm_id"]
                before = candidate["raw_criteria_pass"]
                after = candidate["calibrated_criteria_pass"]
                self.assertEqual(before, after)
                self.assertEqual(candidate["calibrations"], [])
                self.assertEqual(candidate["output_sha256"], hashlib.sha256(candidate["output"].encode()).hexdigest())
                self.assertEqual(candidate["raw_passed"], sum(before))
                self.assertEqual(candidate["calibrated_passed"], sum(after))
                false_entries.extend(
                    (item["review_id"], candidate["candidate_id"], arm, index)
                    for index, value in enumerate(before)
                    if not value
                )
                for aggregate, values in ((raw, before), (calibrated, after)):
                    aggregate[arm][0] += 1
                    aggregate[arm][1] += int(all(values))
                    aggregate[arm][2] += sum(values)
                    aggregate[arm][3] += int(candidate["preferred"])
        expected = {
            "baseline": [18, 17, 71, 0],
            "ours": [18, 18, 72, 1],
            "upstream": [18, 18, 72, 0],
        }
        self.assertEqual(raw, expected)
        self.assertEqual(calibrated, expected)
        self.assertEqual(false_entries, [("retirement-banner-does-not-collapse-cohorts-r2", "C", "baseline", 1)])
        semantic = self.report["experiment"]["semantic_calibration"]
        self.assertEqual(
            (semantic["original_false_count"], semantic["correction_count"], semantic["retained_false_count"]),
            (1, 0, 1),
        )
        self.assertEqual(semantic["corrections"], [])
        self.assertEqual(self.report["analysis"]["preference_ties"], 17)
        raw_failures = self._recompute_failures("raw_criteria_pass")
        calibrated_failures = self._recompute_failures("calibrated_criteria_pass")
        expected_failures = {
            case["id"]: {
                "baseline": 1 if case["id"] == "retirement-banner-does-not-collapse-cohorts" else 0,
                "ours": 0,
                "upstream": 0,
            }
            for case in self.cases
        }
        self.assertEqual(raw_failures, expected_failures)
        self.assertEqual(calibrated_failures, expected_failures)
        self.assertEqual(self.report["analysis"]["raw_case_core_failures"], expected_failures)
        self.assertEqual(self.report["analysis"]["raw_mechanisms"], self._expected_mechanisms(raw_failures))
        self.assertEqual(self.report["analysis"]["calibrated_mechanisms"], self._expected_mechanisms(calibrated_failures))
        self.assertFalse(any(item["triggered"] for item in self.report["analysis"]["raw_mechanisms"]))

        runtime = {arm["arm_id"]: arm["runtime"] for arm in self.report["experiment"]["arms"]}
        for comparison, left, right in (
            ("ours_vs_baseline_percent", "ours", "baseline"),
            ("upstream_vs_baseline_percent", "upstream", "baseline"),
            ("ours_vs_upstream_percent", "ours", "upstream"),
        ):
            expected_delta = {}
            for field in ("tokens_total", "cost_total", "latency_ms_median"):
                lval = runtime[left][field]["total"] if field == "tokens_total" else runtime[left][field]
                rval = runtime[right][field]["total"] if field == "tokens_total" else runtime[right][field]
                expected_delta[field] = round((lval / rval - 1) * 100, 1)
            self.assertEqual(self.report["analysis"]["efficiency"][comparison], expected_delta)

    def test_active_cases_and_skill_state_match_decision(self):
        active = json.loads(ACTIVE.read_text(encoding="utf-8"))
        by_id = {case["id"]: case for case in active["cases"]}
        self.assertEqual(len(by_id), 13)
        for case in self.cases:
            current = by_id[case["id"]]
            self.assertEqual(current["prompt"], case["prompt"])
            self.assertEqual(current["expected_route"], "product-context-brief")
            self.assertEqual(current["input"], {"kind": "synthetic", "comparison_case_id": case["id"]})
            self.assertEqual(len(current["must_include"]), 3)
            self.assertEqual(len(current["must_avoid"]), 3)
        catalog = json.loads((ROOT / "catalog/collection.json").read_text(encoding="utf-8"))
        entry = next(item for item in catalog["skills"] if item["id"] == "product-context-brief")
        self.assertEqual((entry["version"], entry["status"], entry["evidence"]), ("0.1.0", "experimental", None))
        total = sum(
            len(json.loads((ROOT / item["evaluation"]).read_text(encoding="utf-8"))["cases"])
            for item in catalog["skills"]
        )
        self.assertEqual(total, 184)
        decision = self.report["decision"]
        self.assertEqual(decision["active_cases_sha256"], sha(ACTIVE))
        self.assertEqual(decision["skill_package_sha256"], VALIDATOR["package_fingerprint"](SKILL))
        self.assertEqual(decision["active_cases_added"], [case["id"] for case in self.cases])
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
            self.skipTest("ignored Round 34 run is unavailable")
        experiment = self.report["experiment"]
        for name, expected in experiment["artifact_hashes"].items():
            self.assertEqual(sha(RUN / name), expected)
        self.assertEqual(sha(PREFLIGHT / "summary.json"), experiment["preflight"]["summary_sha256"])
        frozen = json.loads((RUN / "frozen.json").read_text(encoding="utf-8"))
        run_meta = json.loads((RUN / "run-meta.json").read_text(encoding="utf-8"))
        summary = json.loads((RUN / "summary.json").read_text(encoding="utf-8"))
        preflight_summary = json.loads((PREFLIGHT / "summary.json").read_text(encoding="utf-8"))
        self._assert_raw_run_semantics(frozen, run_meta, summary, preflight_summary)

        prepared = RUN / "prepared"
        self.assertEqual(sha(prepared / "promptfooconfig.json"), frozen["prepared_config_sha256"])
        self.assertEqual(sha(prepared / "tests.json"), frozen["prepared_tests_sha256"])
        frozen_arms = {arm["id"]: arm for arm in frozen["arms"]}
        for arm, skill_id in (("ours", "product-context-brief"), ("upstream", "product-marketing")):
            expected = frozen_arms[arm]
            for package in (
                prepared / "skills" / arm / skill_id,
                prepared / "fixtures" / arm / ".agents" / "skills" / skill_id,
            ):
                files = [path.relative_to(package).as_posix() for path in package.rglob("*") if path.is_file()]
                self.assertEqual(sorted(files), [item["path"] for item in expected["files"]])
                self.assertEqual(VALIDATOR["package_fingerprint"](package), expected["skill_package_sha256"])

        results = json.loads((RUN / "results.json").read_text(encoding="utf-8"))["results"]["results"]
        self.assertEqual(len(results), 54)
        for row in results:
            self.assertTrue(row["success"])
            self.assertTrue(row["gradingResult"]["pass"])
            self.assertTrue(row["response"]["output"].strip())
            raw_response = json.loads(row["response"]["raw"])
            self.assertEqual(raw_response["finalResponse"], row["response"]["output"])
            self.assertEqual([item["type"] for item in raw_response["items"]], ["agent_message"])

        packet = json.loads((RUN / "blind-review.json").read_text(encoding="utf-8"))
        key = json.loads((RUN / "blind-review-key.json").read_text(encoding="utf-8"))
        completed = json.loads((RUN / "blind-review-completed-independent.json").read_text(encoding="utf-8"))
        calibration = json.loads((RUN / "review-calibration-independent.json").read_text(encoding="utf-8"))
        self.assertEqual(experiment["semantic_calibration"], calibration)
        packet_by = {item["review_id"]: item for item in packet["items"]}
        key_by = {item["review_id"]: item for item in key["items"]}
        completed_by = {item["review_id"]: item for item in completed["reviews"]}
        public_by = {item["review_id"]: item for item in experiment["items"]}
        self.assertEqual(set(public_by), set(packet_by))
        for review_id, public in public_by.items():
            outputs = {item["candidate_id"]: item["output"] for item in packet_by[review_id]["candidates"]}
            identities = {item["candidate_id"]: item["arm_id"] for item in key_by[review_id]["candidates"]}
            scores = completed_by[review_id]["criteria_pass"]
            for candidate in public["candidates"]:
                candidate_id = candidate["candidate_id"]
                self.assertEqual(candidate["output"], outputs[candidate_id])
                self.assertEqual(candidate["arm_id"], identities[candidate_id])
                self.assertEqual(candidate["raw_criteria_pass"], scores[candidate_id])

    def test_coordinated_raw_validity_changes_fail_semantic_checks(self):
        if not RUN.is_dir() or not PREFLIGHT.is_dir():
            self.skipTest("ignored Round 34 runs are unavailable")
        frozen = json.loads((RUN / "frozen.json").read_text(encoding="utf-8"))
        run_meta = json.loads((RUN / "run-meta.json").read_text(encoding="utf-8"))
        summary = json.loads((RUN / "summary.json").read_text(encoding="utf-8"))
        preflight_summary = json.loads((PREFLIGHT / "summary.json").read_text(encoding="utf-8"))

        invalid_meta = copy.deepcopy(run_meta)
        invalid_meta["result_rows"] = 53
        invalid_meta["failed_rows"] = 1
        with self.assertRaises(AssertionError):
            self._assert_raw_run_semantics(frozen, invalid_meta, summary, preflight_summary)

        repeated_eval = copy.deepcopy(run_meta)
        repeated_eval["commands"][0] = copy.deepcopy(repeated_eval["commands"][1])
        with self.assertRaises(AssertionError):
            self._assert_raw_run_semantics(frozen, repeated_eval, summary, preflight_summary)

        invalid_summary = copy.deepcopy(summary)
        invalid_summary["infrastructure_valid"] = False
        with self.assertRaises(AssertionError):
            self._assert_raw_run_semantics(frozen, run_meta, invalid_summary, preflight_summary)

        invalid_preflight = copy.deepcopy(preflight_summary)
        invalid_preflight["arms"][0]["rows"] = 0
        with self.assertRaises(AssertionError):
            self._assert_raw_run_semantics(frozen, run_meta, summary, invalid_preflight)

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
        failures = self._recompute_failures("raw_criteria_pass")
        self.assertNotEqual(
            gate_mutation["analysis"]["raw_mechanisms"],
            self._expected_mechanisms(failures),
        )


if __name__ == "__main__":
    unittest.main()
