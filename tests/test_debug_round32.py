"""Integrity checks for the Round 32 debug comparison and calibration."""

import copy
import hashlib
import json
from pathlib import Path, PureWindowsPath
import runpy
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]
COMPARISON = ROOT / "evaluations/comparisons/debug-current-systematic-three-arm-25"
REPORT_PATH = ROOT / "evaluations/reports/debug-current-systematic-round-32-diagnostic.json"
RUN = ROOT / "evaluations/runs/debug-current-systematic-three-arm-25-formal-20260914-v1"
PREFLIGHT_RUN = ROOT / "evaluations/runs/debug-current-systematic-three-arm-25-preflight-20260914-v1"
ACTIVE = ROOT / "evaluations/cases/debug-evidence-triage.json"
SKILL = ROOT / "skills/engineering/debug-evidence-triage"
COMMIT = "b36e0829c6d0140e93cfef2ca599b1b07d4a7797"
UPSTREAM = ROOT / "evaluations/fixtures/upstreams/superpowers-systematic-debugging" / COMMIT
UPSTREAM_SOURCE = ROOT / "evaluations/fixtures/upstreams/superpowers" / COMMIT
FREEZE_COMMIT = "674321cbe70acf6bbafd1cdafb23fda3e34d53da"
EXPECTED_PROJECTION = "0341f2ac66ad9c0d17ee85c306a367061883a4c9e6f185f30f8ae94a912c2321"
VALIDATOR = runpy.run_path(str(ROOT / "scripts/validate_collection.py"))
ORDER = {"baseline": 0, "ours": 1, "upstream": 2}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def object_sha(value: object) -> str:
    payload = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode()
    return hashlib.sha256(payload).hexdigest()


class DebugRound32Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
        cls.cases = json.loads((COMPARISON / "cases.json").read_text(encoding="utf-8"))
        cls.protocol = json.loads(
            (COMPARISON / "promptfoo.json").read_text(encoding="utf-8")
        )

    def _recompute_failures(self, report, criterion_field):
        case_by = {case["id"]: case for case in self.cases}
        failures = {
            case_id: {arm: 0 for arm in ORDER} for case_id in case_by
        }
        suffix = "raw" if criterion_field == "raw_criteria_pass" else "calibrated"
        for item in report["experiment"]["items"]:
            case = case_by[item["case_id"]]
            for candidate in item["candidates"]:
                criteria = candidate[criterion_field]
                core = any(not criteria[index] for index in case["core_criteria"])
                self.assertEqual(candidate[f"{suffix}_core_failure"], core)
                failures[case["id"]][candidate["arm_id"]] += core
        return failures

    def _expected_mechanisms(self, failures):
        gate = self.protocol["decision_gate"]
        grouped = {}
        for case in self.cases:
            grouped.setdefault(case["mechanism"], []).append(case["id"])
        mechanisms = []
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
            mechanisms.append(
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
        return mechanisms

    def _assert_frozen_package(self, frozen_arm, package, report_arm):
        self.assertEqual(frozen_arm["skill"], report_arm["skill"])
        self.assertEqual(
            frozen_arm["skill_source"], report_arm["package_evidence_path"]
        )
        files = []
        for path in sorted(
            (item for item in package.rglob("*") if item.is_file()),
            key=lambda item: item.relative_to(package).as_posix(),
        ):
            files.append(
                {
                    "path": path.relative_to(package).as_posix(),
                    "bytes": path.stat().st_size,
                    "sha256": sha(path),
                }
            )
        self.assertEqual(frozen_arm["files"], files)
        self.assertEqual(
            frozen_arm["skill_package_sha256"],
            VALIDATOR["package_fingerprint"](package),
        )
        self.assertEqual(
            frozen_arm["skill_package_sha256"],
            report_arm["skill_package_sha256"],
        )

    def test_sources_projection_freeze_and_upstream_are_bound(self):
        report = self.report
        self.assertEqual(
            report["report_id"], "debug-current-systematic-round-32-diagnostic"
        )
        experiment = report["experiment"]
        self.assertEqual(experiment["freeze_commit"], FREEZE_COMMIT)
        sources = {
            "promptfoo.json": COMPARISON / "promptfoo.json",
            "cases.json": COMPARISON / "cases.json",
            "active-cases.json": ACTIVE,
            "SKILL.md": SKILL / "SKILL.md",
            "upstream-provenance.json": UPSTREAM / "provenance.json",
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

        provenance = json.loads(
            (UPSTREAM / "provenance.json").read_text(encoding="utf-8")
        )
        upstream_report = experiment["upstream_provenance"]
        self.assertEqual(upstream_report["repository"], provenance["repository"])
        self.assertEqual(upstream_report["commit"], COMMIT)
        self.assertEqual(upstream_report["license"], "MIT")
        self.assertEqual(
            upstream_report["package_sha256"],
            VALIDATOR["package_fingerprint"](UPSTREAM),
        )
        self.assertTrue(upstream_report["same_directory_references_closed"])
        self.assertEqual(
            upstream_report["excluded_sibling_skills"],
            ["test-driven-development", "verification-before-completion"],
        )
        self.assertFalse(upstream_report["scripts_executed"])
        for name, record in provenance["files"].items():
            self.assertEqual((UPSTREAM / name).read_bytes(), (UPSTREAM_SOURCE / record["source_path"]).read_bytes())

        if (ROOT / ".git").exists():
            subprocess.run(
                ["git", "merge-base", "--is-ancestor", FREEZE_COMMIT, "HEAD"],
                cwd=ROOT,
                check=True,
            )
            for name, path in sources.items():
                if name == "active-cases.json":
                    continue
                content = subprocess.run(
                    [
                        "git",
                        "show",
                        f"{FREEZE_COMMIT}:{path.relative_to(ROOT).as_posix()}",
                    ],
                    cwd=ROOT,
                    check=True,
                    capture_output=True,
                ).stdout
                self.assertEqual(hashlib.sha256(content).hexdigest(), experiment["source_hashes"][name])

    def test_raw_and_calibrated_scores_failures_gates_and_efficiency_recompute(self):
        report = self.report
        raw_aggregate = {arm: [0, 0, 0, 0] for arm in ORDER}
        calibrated_aggregate = {arm: [0, 0, 0, 0] for arm in ORDER}
        public_corrections = []
        for item in report["experiment"]["items"]:
            for candidate in item["candidates"]:
                arm = candidate["arm_id"]
                raw = candidate["raw_criteria_pass"]
                calibrated = candidate["calibrated_criteria_pass"]
                self.assertEqual(len(raw), 4)
                self.assertEqual(len(calibrated), 4)
                self.assertEqual(candidate["output_sha256"], hashlib.sha256(candidate["output"].encode()).hexdigest())
                self.assertEqual(candidate["raw_passed"], sum(raw))
                self.assertEqual(candidate["calibrated_passed"], sum(calibrated))
                for index, (before, after) in enumerate(zip(raw, calibrated)):
                    if before != after:
                        self.assertEqual((before, after), (False, True))
                        calibration = next(
                            entry
                            for entry in candidate["calibrations"]
                            if entry["criterion_index"] == index
                        )
                        public_corrections.append(
                            (item["review_id"], arm, index, calibration["reason"])
                        )
                raw_aggregate[arm][0] += 1
                raw_aggregate[arm][1] += candidate["raw_passed"] == 4
                raw_aggregate[arm][2] += candidate["raw_passed"]
                raw_aggregate[arm][3] += candidate["preferred"]
                calibrated_aggregate[arm][0] += 1
                calibrated_aggregate[arm][1] += candidate["calibrated_passed"] == 4
                calibrated_aggregate[arm][2] += candidate["calibrated_passed"]
                calibrated_aggregate[arm][3] += candidate["preferred"]
        self.assertEqual(
            raw_aggregate,
            {
                "baseline": [18, 4, 51, 5],
                "ours": [18, 1, 45, 1],
                "upstream": [18, 1, 44, 0],
            },
        )
        self.assertEqual(
            calibrated_aggregate,
            {
                "baseline": [18, 6, 53, 5],
                "ours": [18, 3, 50, 1],
                "upstream": [18, 4, 47, 0],
            },
        )
        calibration = report["experiment"]["semantic_calibration"]
        self.assertEqual(calibration["original_false_count"], 76)
        self.assertEqual(calibration["correction_count"], 10)
        self.assertEqual(calibration["retained_false_count"], 66)
        self.assertEqual(len(public_corrections), 10)
        self.assertFalse(calibration["raw_artifacts_modified"])
        self.assertFalse(calibration["preferences_recomputed"])
        self.assertEqual(report["analysis"]["preference_ties"], 12)

        raw_failures = self._recompute_failures(report, "raw_criteria_pass")
        calibrated_failures = self._recompute_failures(
            report, "calibrated_criteria_pass"
        )
        expected_raw = {
            "zero-five-hundreds-misses-empty-success": {"baseline": 3, "ours": 3, "upstream": 3},
            "finished-only-query-hides-stalled-jobs": {"baseline": 1, "ours": 2, "upstream": 2},
            "bundled-timeout-and-index-recovery": {"baseline": 3, "ours": 3, "upstream": 3},
            "flag-cohort-confounded-by-payload-size": {"baseline": 3, "ours": 3, "upstream": 3},
            "same-job-id-different-retry-attempts": {"baseline": 1, "ours": 3, "upstream": 3},
            "session-id-reused-across-process-boot": {"baseline": 3, "ours": 3, "upstream": 3},
        }
        expected_calibrated = copy.deepcopy(expected_raw)
        expected_calibrated["finished-only-query-hides-stalled-jobs"]["upstream"] = 1
        expected_calibrated["flag-cohort-confounded-by-payload-size"] = {
            "baseline": 1,
            "ours": 1,
            "upstream": 1,
        }
        self.assertEqual(raw_failures, expected_raw)
        self.assertEqual(calibrated_failures, expected_calibrated)
        self.assertEqual(report["analysis"]["raw_case_core_failures"], expected_raw)
        self.assertEqual(
            report["analysis"]["calibrated_case_core_failures"],
            expected_calibrated,
        )
        raw_mechanisms = self._expected_mechanisms(raw_failures)
        calibrated_mechanisms = self._expected_mechanisms(calibrated_failures)
        self.assertEqual(report["analysis"]["raw_mechanisms"], raw_mechanisms)
        self.assertEqual(
            report["analysis"]["calibrated_mechanisms"], calibrated_mechanisms
        )
        self.assertFalse(any(item["triggered"] for item in raw_mechanisms))
        self.assertFalse(any(item["triggered"] for item in calibrated_mechanisms))
        self.assertFalse(report["decision"]["candidate_design_open"])

        runtime = {
            arm["arm_id"]: arm["runtime"] for arm in report["experiment"]["arms"]
        }
        for name, left, right in (
            ("ours_vs_baseline_percent", "ours", "baseline"),
            ("upstream_vs_baseline_percent", "upstream", "baseline"),
            ("ours_vs_upstream_percent", "ours", "upstream"),
        ):
            expected = {}
            for field in ("tokens_total", "cost_total", "latency_ms_median"):
                a = runtime[left][field]["total"] if field == "tokens_total" else runtime[left][field]
                b = runtime[right][field]["total"] if field == "tokens_total" else runtime[right][field]
                expected[field] = round((a / b - 1) * 100, 1)
            self.assertEqual(report["analysis"]["efficiency"][name], expected)

    def test_active_cases_and_skill_state_match_decision(self):
        active = json.loads(ACTIVE.read_text(encoding="utf-8"))
        by_id = {case["id"]: case for case in active["cases"]}
        self.assertEqual(len(by_id), 19)
        for case in self.cases:
            current = by_id[case["id"]]
            self.assertEqual(current["prompt"], case["prompt"])
            self.assertEqual(current["expected_route"], "debug-evidence-triage")
            self.assertEqual(current["input"]["kind"], "synthetic")
            self.assertEqual(current["input"]["comparison_case_id"], case["id"])
            self.assertTrue(current["must_include"])
            self.assertTrue(current["must_avoid"])
        catalog = json.loads(
            (ROOT / "catalog/collection.json").read_text(encoding="utf-8")
        )
        entry = next(
            item for item in catalog["skills"] if item["id"] == "debug-evidence-triage"
        )
        self.assertEqual(
            (entry["version"], entry["status"], entry["evidence"]),
            ("0.1.1", "experimental", None),
        )
        total = sum(
            len(
                json.loads((ROOT / item["evaluation"]).read_text(encoding="utf-8"))[
                    "cases"
                ]
            )
            for item in catalog["skills"]
        )
        self.assertEqual(total, 172)
        decision = self.report["decision"]
        self.assertEqual(decision["active_cases_sha256"], sha(ACTIVE))
        self.assertEqual(
            decision["skill_package_sha256"],
            VALIDATOR["package_fingerprint"](SKILL),
        )
        self.assertFalse(
            any(
                decision[field]
                for field in (
                    "skill_changed",
                    "version_changed",
                    "verification_status_changed",
                )
            )
        )

    def test_ignored_runs_reproject_to_public_evidence_when_present(self):
        if not RUN.is_dir():
            self.skipTest("ignored Round 32 run is unavailable")
        self.assertTrue(PREFLIGHT_RUN.is_dir())
        experiment = self.report["experiment"]
        for name, expected in experiment["artifact_hashes"].items():
            self.assertEqual(sha(RUN / name), expected)
        frozen = json.loads((RUN / "frozen.json").read_text(encoding="utf-8"))
        meta = json.loads((RUN / "run-meta.json").read_text(encoding="utf-8"))
        summary = json.loads((RUN / "summary.json").read_text(encoding="utf-8"))
        preflight = json.loads(
            (PREFLIGHT_RUN / "summary.json").read_text(encoding="utf-8")
        )
        self.assertEqual(frozen["comparison_id"], self.protocol["id"])
        self.assertEqual(frozen["spec_sha256"], sha(COMPARISON / "promptfoo.json"))
        self.assertEqual(frozen["cases_sha256"], sha(COMPARISON / "cases.json"))
        self.assertEqual(
            frozen["selected_case_ids"], [case["id"] for case in self.cases]
        )
        self.assertEqual(
            sha(RUN / "prepared/promptfooconfig.json"),
            frozen["prepared_config_sha256"],
        )
        self.assertEqual(
            sha(RUN / "prepared/tests.json"), frozen["prepared_tests_sha256"]
        )
        self.assertEqual(
            frozen["constraints"],
            {
                "native_skill_discovery": True,
                "sandbox_mode": "read-only",
                "network_access": False,
                "web_search": "disabled",
                "isolated_git_root_per_arm": True,
                "isolated_user_home_per_arm": True,
                "host_apps_plugins": False,
                "evaluation_rubric_visible_to_agent": False,
                "implicit_skill_trace_assertions": False,
            },
        )
        frozen_arms = {item["id"]: item for item in frozen["arms"]}
        report_arms = {
            item["arm_id"]: item for item in experiment["arms"]
        }
        self._assert_frozen_package(frozen_arms["ours"], SKILL, report_arms["ours"])
        self._assert_frozen_package(
            frozen_arms["upstream"], UPSTREAM, report_arms["upstream"]
        )
        for package in (
            RUN / "prepared/skills/ours/debug-evidence-triage",
            RUN / "prepared/fixtures/ours/.agents/skills/debug-evidence-triage",
        ):
            self._assert_frozen_package(
                frozen_arms["ours"], package, report_arms["ours"]
            )
        for package in (
            RUN / "prepared/skills/upstream/systematic-debugging",
            RUN / "prepared/fixtures/upstream/.agents/skills/systematic-debugging",
        ):
            self._assert_frozen_package(
                frozen_arms["upstream"], package, report_arms["upstream"]
            )
        self.assertEqual(meta["repeat"], 3)
        self.assertEqual(meta["status"], "completed")
        self.assertEqual(
            (
                meta["expected_rows"],
                meta["result_rows"],
                meta["passed_rows"],
                meta["failed_rows"],
            ),
            (54, 54, 54, 0),
        )
        self.assertEqual(sum(command.count("eval") for command in meta["commands"]), 1)
        self.assertTrue(summary["infrastructure_valid"])
        self.assertEqual(sum(item["rows"] for item in summary["arms"]), 54)
        for arm in summary["arms"]:
            self.assertEqual(arm["rows"], 18)
            self.assertEqual(arm["provider_errors"], 0)
            self.assertEqual(arm["forbidden_tool_rows"], 0)
        self.assertTrue(preflight["infrastructure_valid"])
        self.assertEqual(sum(item["rows"] for item in preflight["arms"]), 3)
        self.assertEqual(
            experiment["preflight"]["summary_sha256"],
            sha(PREFLIGHT_RUN / "summary.json"),
        )

        packet = json.loads((RUN / "blind-review.json").read_text(encoding="utf-8"))
        key = json.loads((RUN / "blind-review-key.json").read_text(encoding="utf-8"))
        completed = json.loads(
            (RUN / "blind-review-completed-independent.json").read_text(
                encoding="utf-8"
            )
        )
        scored = json.loads(
            (RUN / "review-result-blind-review-completed-independent.json").read_text(
                encoding="utf-8"
            )
        )
        calibration = json.loads(
            (RUN / "review-calibration-independent.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            experiment["semantic_calibration"]["corrections"],
            calibration["corrections"],
        )
        for name, expected in calibration["source_bindings"].items():
            self.assertEqual(sha(RUN / name), expected)
        packet_by = {item["review_id"]: item for item in packet["items"]}
        key_by = {item["review_id"]: item for item in key["items"]}
        completed_by = {item["review_id"]: item for item in completed["reviews"]}
        scored_by = {item["review_id"]: item for item in scored["items"]}
        corrections = {
            (item["review_id"], item["candidate_id"], item["criterion_index"]): item
            for item in calibration["corrections"]
        }
        case_by = {case["id"]: case for case in self.cases}
        rebuilt = []
        for review_id in sorted(packet_by):
            source = packet_by[review_id]
            identities = {
                item["candidate_id"]: item
                for item in key_by[review_id]["candidates"]
            }
            scores = {
                item["candidate_id"]: item
                for item in scored_by[review_id]["candidates"]
            }
            review = completed_by[review_id]
            case = case_by[source["case_id"]]
            candidates = []
            for candidate in source["candidates"]:
                candidate_id = candidate["candidate_id"]
                identity = identities[candidate_id]
                raw = list(review["criteria_pass"][candidate_id])
                calibrated = list(raw)
                applied = []
                for index in range(4):
                    correction = corrections.get((review_id, candidate_id, index))
                    if correction:
                        calibrated[index] = True
                        applied.append(
                            {
                                "criterion_index": index,
                                "reason": correction["reason"],
                            }
                        )
                candidates.append(
                    {
                        "arm_id": identity["arm_id"],
                        "skill": identity["skill"],
                        "output": candidate["output"],
                        "output_sha256": hashlib.sha256(candidate["output"].encode()).hexdigest(),
                        "raw_criteria_pass": raw,
                        "calibrated_criteria_pass": calibrated,
                        "raw_passed": scores[candidate_id]["passed"],
                        "calibrated_passed": sum(calibrated),
                        "total": 4,
                        "raw_core_failure": any(not raw[index] for index in case["core_criteria"]),
                        "calibrated_core_failure": any(not calibrated[index] for index in case["core_criteria"]),
                        "preferred": review["preferred_candidate"] == candidate_id,
                        "calibrations": applied,
                    }
                )
            rebuilt.append(
                {
                    "review_id": review_id,
                    "case_id": source["case_id"],
                    "mechanism": case["mechanism"],
                    "repetition": source["repetition"],
                    "review_notes": review["notes"],
                    "candidates": sorted(
                        candidates, key=lambda item: ORDER[item["arm_id"]]
                    ),
                }
            )
        self.assertEqual(experiment["items"], rebuilt)
        reviewer = copy.deepcopy(completed["reviewer"])
        reviewer["allowed_files"] = [
            PureWindowsPath(path).name for path in reviewer["allowed_files"]
        ]
        self.assertEqual(experiment["blind_reviewer"], reviewer)

    def test_coordinated_mutations_fail_fixed_or_semantic_checks(self):
        for path, value in (
            (["decision", "candidate_design_open"], True),
            (["experiment", "freeze_commit"], "0" * 40),
            (["experiment", "semantic_calibration", "correction_count"], 11),
            (["scope", "collection_active_case_count"], 171),
        ):
            mutated = copy.deepcopy(self.report)
            target = mutated
            for key in path[:-1]:
                target = target[key]
            target[path[-1]] = value
            projection = {
                key: mutated[key]
                for key in (
                    "scope",
                    "experiment",
                    "analysis",
                    "decision",
                    "limitations",
                )
            }
            mutated["evidence_projection_sha256"] = object_sha(projection)
            self.assertNotEqual(
                mutated["evidence_projection_sha256"], EXPECTED_PROJECTION
            )

        mutated = copy.deepcopy(self.report)
        target = next(
            candidate
            for item in mutated["experiment"]["items"]
            for candidate in item["candidates"]
            if candidate["calibrations"]
        )
        target["calibrated_criteria_pass"] = list(target["raw_criteria_pass"])
        with self.assertRaises(AssertionError):
            raw = self._recompute_failures(mutated, "raw_criteria_pass")
            calibrated = self._recompute_failures(
                mutated, "calibrated_criteria_pass"
            )
            self.assertEqual(raw, self.report["analysis"]["raw_case_core_failures"])
            self.assertEqual(
                calibrated,
                self.report["analysis"]["calibrated_case_core_failures"],
            )


if __name__ == "__main__":
    unittest.main()
