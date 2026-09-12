"""Protect the published round-22 debug-evidence diagnostic report."""

import copy
import hashlib
import json
from pathlib import Path
import runpy
import unittest


ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = (
    ROOT
    / "evaluations"
    / "reports"
    / "debug-evidence-boundaries-round-22-diagnostic.json"
)
VALIDATOR = runpy.run_path(str(ROOT / "scripts" / "validate_collection.py"))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def text_sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def canonical_sha256(value) -> str:
    payload = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def raw_decision_projection(experiment):
    return {
        "schema": "round22-raw-decision-projection-v1",
        "reviewer": experiment["blind_reviewer"],
        "review_sha256": experiment["artifact_hashes"][
            "blind-review-completed-independent.json"
        ],
        "reviews": [
            {
                "review_id": item["review_id"],
                "criteria_pass": {
                    candidate["candidate_id"]: candidate["raw_criteria_pass"]
                    for candidate in item["candidates"]
                },
                "preferred_candidate": item["preferred_candidate"],
            }
            for item in experiment["items"]
        ],
    }


def calibrated_decision_projection(experiment):
    calibration = experiment["semantic_calibration"]
    return {
        "schema": "round22-calibrated-decision-projection-v1",
        "semantic_reviewer": calibration["reviewer"],
        "semantic_review_sha256": calibration["review_sha256"],
        "raw_decision_projection_sha256": experiment[
            "raw_decision_projection_sha256"
        ],
        "corrections": calibration["corrections"],
        "reviews": [
            {
                "review_id": item["review_id"],
                "criteria_pass": {
                    candidate["candidate_id"]: candidate[
                        "calibrated_criteria_pass"
                    ]
                    for candidate in item["candidates"]
                },
                "preferred_candidate": item["preferred_candidate"],
            }
            for item in experiment["items"]
        ],
    }


def evidence_projection(experiment):
    return {
        "schema": "round22-evidence-projection-v1",
        "freeze_commit": experiment["freeze_commit"],
        "model": experiment["model"],
        "reasoning_effort": experiment["reasoning_effort"],
        "source_hashes": experiment["source_hashes"],
        "prepared_hashes": experiment["prepared_hashes"],
        "artifact_hashes": experiment["artifact_hashes"],
        "prefreeze_review_sha256": experiment["prefreeze_review_sha256"],
        "blind_reviewer": experiment["blind_reviewer"],
        "semantic_reviewer": experiment["semantic_calibration"]["reviewer"],
        "semantic_review_sha256": experiment["semantic_calibration"][
            "review_sha256"
        ],
        "raw_decision_projection_sha256": experiment[
            "raw_decision_projection_sha256"
        ],
        "calibrated_decision_projection_sha256": experiment[
            "calibrated_decision_projection_sha256"
        ],
        "reviews": [
            {
                "review_id": item["review_id"],
                "case_id": item["case_id"],
                "repetition": item["repetition"],
                "task_sha256": text_sha256(item["task"]),
                "hard_criteria_sha256": canonical_sha256(item["hard_criteria"]),
                "preferred_candidate": item["preferred_candidate"],
                "candidates": [
                    {
                        "candidate_id": candidate["candidate_id"],
                        "arm_id": candidate["arm_id"],
                        "skill_package_sha256": candidate[
                            "skill_package_sha256"
                        ],
                        "output_sha256": candidate["output_sha256"],
                        "raw_criteria_pass": candidate["raw_criteria_pass"],
                        "calibrated_criteria_pass": candidate[
                            "calibrated_criteria_pass"
                        ],
                    }
                    for candidate in item["candidates"]
                ],
            }
            for item in experiment["items"]
        ],
    }


def blank_totals():
    return {
        "outputs": 0,
        "perfect_outputs": 0,
        "criteria_passed": 0,
        "criteria_total": 0,
        "preferred_count": 0,
    }


class DebugEvidenceBoundariesRound22Tests(unittest.TestCase):
    def setUp(self):
        self.report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
        self.experiment = self.report["experiment"]

    def test_report_recomputes_both_score_layers_gate_and_current_state(self):
        report = self.report
        experiment = self.experiment
        self.assertEqual(
            report["scope"],
            {
                "skill_id": "debug-evidence-triage",
                "version": "0.1.1",
                "catalog_status": "experimental",
                "active_case_count": 13,
                "collection_active_case_count": 132,
                "formal_outputs": 42,
                "blind_review_items": 21,
                "criterion_booleans": 168,
            },
        )
        self.assertEqual(
            experiment["freeze_commit"],
            "c77052ac93bcae3e7fa76d48dda3ab49b6fbb923",
        )
        self.assertTrue(experiment["infrastructure_valid"])

        comparison = (
            ROOT / "evaluations" / "comparisons" / experiment["comparison_id"]
        )
        expected_source_hashes = {
            "promptfoo.json": "5eaba662bf78f8ae33c719c52c051d134c4120f63b98d05e513b940fd431fc00",
            "cases.json": "89cfa5ab0cda187374faeb041df654b67cbb50092a24e0aeab4b3e0c6ef54d78",
        }
        self.assertEqual(experiment["source_hashes"], expected_source_hashes)
        for name, digest in expected_source_hashes.items():
            self.assertEqual(sha256_file(comparison / name), digest)
        self.assertEqual(
            experiment["prepared_hashes"],
            {
                "config": "e1a9a7288dbcd16dcb36582a694a6d4a5af75e17cab5e4b2827ef28445071822",
                "tests": "3edf06cbe3623a6107b33cd348fca187171d7bcef733e929d9d6fd97defd44a0",
            },
        )
        self.assertEqual(
            experiment["artifact_hashes"],
            {
                "frozen.json": "fc53dc6b2ff9ca8d836e290c4545c41619309b63efadf6baa01303c4d402e3f4",
                "results.json": "f25cdfc9caab3b9fa859bdae0f7b2ca9a3ff01f9dfb24ba521ba9df7b43245a3",
                "summary.json": "c98b9b98428b5febd3a898e77d184694018b77f435c78b7084c62799b73e3276",
                "blind-review.json": "7d884f39ee41b0ccee6862713d7bff1a7f8e1a06c176a9a6074b7cfc41b1c61e",
                "blind-review-key.json": "463d7e38e1739e27a11788e2556bee2a9f83707a59cc150fe852a479cd48a837",
                "blind-review-form.json": "dbdceaf4e2178f51ef0f0a27d0123f104f8c9f54a0e726eccba40a7ac10675ed",
                "blind-review-completed-independent.json": "ec994548d35cc0c521e2f112bccc8c82360f621a78f53c2d9cb45e684da4b2ba",
                "review-result-blind-review-completed-independent.json": "14c466d8b8c6a6913ff9a779070c5a66ea56379256bc7b2f5143c924f2a532a6",
            },
        )
        self.assertEqual(
            experiment["prefreeze_review_sha256"],
            "21777abc0477f9f6fb9bb0d72c0e87c6575381d0374603cc93b043e1a899f9b0",
        )
        self.assertEqual(
            sha256_file(comparison / "prefreeze-review-independent.md"),
            experiment["prefreeze_review_sha256"],
        )
        self.assertEqual(
            experiment["semantic_calibration"]["review_sha256"],
            "9ee88ea817f386a77fb023ce7a5efa0c64ee3894e5b63e18dedc304c45878110",
        )
        self.assertEqual(
            sha256_file(comparison / "postscore-decision-review-independent.md"),
            experiment["semantic_calibration"]["review_sha256"],
        )

        blind = experiment["blind_reviewer"]
        self.assertTrue(blind["blind_to_arm_mapping"])
        self.assertFalse(blind["prior_protocol_exposure"])
        self.assertFalse(blind["prior_skill_revision_exposure"])
        self.assertTrue(blind["blind_file_boundary_clean"])
        self.assertEqual(
            blind["allowed_files"],
            ["blind-review-form.json", "blind-review.json"],
        )
        self.assertEqual(blind["unexpected_files_read"], [])
        self.assertEqual(blind["task_name"], "round22_blind_review")
        self.assertEqual(blind["model"], "gpt-5.6-sol")
        self.assertEqual(blind["reasoning_effort"], "medium")
        self.assertFalse(blind["independent_human"])
        self.assertTrue(blind["note"].strip())

        calibration = experiment["semantic_calibration"]
        semantic = calibration["reviewer"]
        self.assertEqual(semantic["task_name"], "round22_prefreeze_review")
        self.assertTrue(semantic["prior_protocol_exposure"])
        self.assertTrue(semantic["prior_skill_revision_exposure"])
        self.assertFalse(semantic["independent_human"])
        self.assertTrue(semantic["note"].strip())
        self.assertEqual(calibration["correction_count"], 6)
        self.assertFalse(calibration["raw_artifacts_modified"])
        self.assertFalse(calibration["preferences_recomputed"])

        self.assertEqual(
            canonical_sha256(raw_decision_projection(experiment)),
            experiment["raw_decision_projection_sha256"],
        )
        self.assertEqual(
            experiment["raw_decision_projection_sha256"],
            "2a772f1b17a1f6417e293dd123a1b6c66b87633325ad9a9b65d97fd899dd5e00",
        )
        self.assertEqual(
            canonical_sha256(calibrated_decision_projection(experiment)),
            experiment["calibrated_decision_projection_sha256"],
        )
        self.assertEqual(
            experiment["calibrated_decision_projection_sha256"],
            "c4c5a2287dec86563cd56b67d7c29648020b7ec6a32f4267eb7499bc77cbef20",
        )
        self.assertEqual(
            canonical_sha256(evidence_projection(experiment)),
            experiment["evidence_projection"]["sha256"],
        )
        self.assertEqual(
            experiment["evidence_projection"]["sha256"],
            "0cdfc6b9250f73a4306466c000bfe9b83f6bfad070d67386bb1cf0217aef5483",
        )

        frozen_cases = json.loads(
            (comparison / "cases.json").read_text(encoding="utf-8")
        )
        frozen_by_id = {case["id"]: case for case in frozen_cases}
        spec = json.loads((comparison / "promptfoo.json").read_text(encoding="utf-8"))
        core_index = {
            case_id: number - 1
            for case_id, number in report["analysis"]["candidate_gate"][
                "core_criterion_number"
            ].items()
        }
        totals = {
            mode: {arm: blank_totals() for arm in ("baseline", "ours")}
            for mode in ("raw", "calibrated")
        }
        by_case = {
            mode: {
                case_id: {
                    arm: {**blank_totals(), "core_errors": 0}
                    for arm in ("baseline", "ours")
                }
                for case_id in frozen_by_id
            }
            for mode in ("raw", "calibrated")
        }
        correction_keys = set()
        observed_booleans = 0
        for item in experiment["items"]:
            source = frozen_by_id[item["case_id"]]
            self.assertEqual(item["purpose"], source["purpose"])
            self.assertEqual(item["hard_criteria"], source["hard_criteria"])
            self.assertEqual(
                item["task"], spec["common_prompt"] + "\n\n" + source["prompt"]
            )
            self.assertTrue(item["review_notes"].strip())
            self.assertNotIn("\ufffd", item["review_notes"])
            if item["preferred_arm"] is not None:
                for mode in totals:
                    totals[mode][item["preferred_arm"]]["preferred_count"] += 1
                    by_case[mode][item["case_id"]][item["preferred_arm"]][
                        "preferred_count"
                    ] += 1
            for candidate in item["candidates"]:
                self.assertEqual(
                    text_sha256(candidate["output"]), candidate["output_sha256"]
                )
                self.assertEqual(
                    candidate["raw_passed"], sum(candidate["raw_criteria_pass"])
                )
                self.assertEqual(
                    candidate["calibrated_passed"],
                    sum(candidate["calibrated_criteria_pass"]),
                )
                self.assertEqual(candidate["total"], len(candidate["raw_criteria_pass"]))
                observed_booleans += candidate["total"]
                differences = [
                    index
                    for index, (raw, calibrated) in enumerate(
                        zip(
                            candidate["raw_criteria_pass"],
                            candidate["calibrated_criteria_pass"],
                        )
                    )
                    if raw != calibrated
                ]
                if differences:
                    self.assertEqual(
                        item["case_id"], "timeout-idempotency-key-not-enforcement"
                    )
                    self.assertEqual(differences, [0])
                    self.assertFalse(candidate["raw_criteria_pass"][0])
                    self.assertTrue(candidate["calibrated_criteria_pass"][0])
                    correction_keys.add((item["review_id"], candidate["candidate_id"]))
                for mode in ("raw", "calibrated"):
                    values = candidate[mode + "_criteria_pass"]
                    for target in (
                        totals[mode][candidate["arm_id"]],
                        by_case[mode][item["case_id"]][candidate["arm_id"]],
                    ):
                        target["outputs"] += 1
                        target["perfect_outputs"] += sum(values) == len(values)
                        target["criteria_passed"] += sum(values)
                        target["criteria_total"] += len(values)
                    by_case[mode][item["case_id"]][candidate["arm_id"]][
                        "core_errors"
                    ] += not values[core_index[item["case_id"]]]

        self.assertEqual(len(experiment["items"]), 21)
        self.assertEqual(observed_booleans, 168)
        self.assertEqual(len(correction_keys), 6)
        self.assertEqual(
            correction_keys,
            {
                (correction["review_id"], correction["candidate_id"])
                for correction in calibration["corrections"]
            },
        )
        for mode in totals:
            for arm_id in totals[mode]:
                totals[mode][arm_id]["criterion_pass_rate"] = round(
                    totals[mode][arm_id]["criteria_passed"]
                    / totals[mode][arm_id]["criteria_total"],
                    4,
                )

        self.assertEqual(
            totals["raw"]["baseline"], report["analysis"]["raw_overall"]["baseline"]
        )
        self.assertEqual(
            totals["raw"]["ours"], report["analysis"]["raw_overall"]["version_0_1_1"]
        )
        self.assertEqual(
            totals["calibrated"]["baseline"],
            report["analysis"]["calibrated_overall"]["baseline"],
        )
        self.assertEqual(
            totals["calibrated"]["ours"],
            report["analysis"]["calibrated_overall"]["version_0_1_1"],
        )
        self.assertEqual(report["analysis"]["raw_overall"]["ties"], 15)
        self.assertEqual(report["analysis"]["calibrated_overall"]["ties"], 15)

        for case_id in frozen_by_id:
            for mode in ("raw", "calibrated"):
                published = report["analysis"]["by_case"][case_id][mode]
                self.assertEqual(published["baseline"], by_case[mode][case_id]["baseline"])
                self.assertEqual(
                    published["version_0_1_1"], by_case[mode][case_id]["ours"]
                )
                gate = report["analysis"]["candidate_gate"][
                    "raw_blind_review"
                    if mode == "raw"
                    else "calibrated_semantic_review"
                ]["per_case"][case_id]
                self.assertEqual(
                    gate["baseline_core_errors"],
                    by_case[mode][case_id]["baseline"]["core_errors"],
                )
                self.assertEqual(
                    gate["version_0_1_1_core_errors"],
                    by_case[mode][case_id]["ours"]["core_errors"],
                )

        gate = report["analysis"]["candidate_gate"]
        self.assertFalse(gate["raw_blind_review"]["triggered"])
        self.assertFalse(gate["calibrated_semantic_review"]["triggered"])
        self.assertFalse(gate["triggered_in_either_view"])
        self.assertEqual(
            gate["diagnostic_only_cases"],
            ["decisive-substring-role-reproduction"],
        )
        self.assertEqual(
            report["analysis"]["cost_and_efficiency"],
            {
                "baseline_total_tokens": 209450,
                "version_0_1_1_total_tokens": 231822,
                "total_token_delta": 22372,
                "total_token_delta_percent": 10.7,
                "prompt_token_delta_percent": 10.9,
                "completion_token_delta_percent": 5.0,
                "cost_delta_percent": 21.7,
                "latency_delta_percent": 25.3,
            },
        )
        self.assertFalse(report["decision"]["skill_changed"])
        self.assertFalse(report["decision"]["version_changed"])
        self.assertFalse(report["decision"]["candidate_design_opened"])
        self.assertEqual(report["decision"]["active_cases_added"], 7)

        catalog = json.loads(
            (ROOT / "catalog" / "collection.json").read_text(encoding="utf-8")
        )
        debug = next(
            item for item in catalog["skills"] if item["id"] == "debug-evidence-triage"
        )
        self.assertEqual(
            (debug["version"], debug["status"], debug["evidence"]),
            ("0.1.1", "experimental", None),
        )
        self.assertEqual(
            VALIDATOR["package_fingerprint"](
                ROOT / "skills" / "engineering" / "debug-evidence-triage"
            ),
            "5c880634b3b728ec83a26efdc7f186c33f1196a1e6c6cfce6ea29cf4d2862e72",
        )
        active_total = 0
        debug_suite = None
        for path in (ROOT / "evaluations" / "cases").glob("*.json"):
            suite = json.loads(path.read_text(encoding="utf-8"))
            if suite.get("stage") == "active":
                active_total += len(suite["cases"])
            if suite.get("skill_id") == "debug-evidence-triage":
                debug_suite = suite
        self.assertGreaterEqual(
            active_total, report["scope"]["collection_active_case_count"]
        )
        self.assertGreaterEqual(
            len(debug_suite["cases"]), report["scope"]["active_case_count"]
        )

    def test_new_active_cases_preserve_frozen_prompts_and_criteria(self):
        comparison = (
            ROOT
            / "evaluations"
            / "comparisons"
            / "debug-evidence-boundaries-forward-15"
        )
        frozen = json.loads((comparison / "cases.json").read_text(encoding="utf-8"))
        active = json.loads(
            (ROOT / "evaluations" / "cases" / "debug-evidence-triage.json").read_text(
                encoding="utf-8"
            )
        )
        active_by_id = {case["id"]: case for case in active["cases"]}
        for source in frozen:
            case = active_by_id["regression-" + source["id"]]
            self.assertEqual(case["prompt"], source["prompt"])
            self.assertEqual(case["must_include"], source["hard_criteria"])
            self.assertEqual(case["input"]["kind"], "synthetic")
            self.assertEqual(case["input"]["comparison_case_id"], source["id"])
            self.assertEqual(case["expected_route"], "debug-evidence-triage")
            self.assertTrue(case["must_avoid"])

    def test_evidence_projection_detects_raw_calibrated_and_reviewer_mutations(self):
        expected = self.experiment["evidence_projection"]["sha256"]

        mutations = []
        changed = copy.deepcopy(self.report)
        changed["experiment"]["source_hashes"]["cases.json"] = "0" * 64
        mutations.append(changed)

        changed = copy.deepcopy(self.report)
        changed["experiment"]["artifact_hashes"]["results.json"] = "0" * 64
        mutations.append(changed)

        changed = copy.deepcopy(self.report)
        candidate = changed["experiment"]["items"][0]["candidates"][0]
        candidate["output"] += " altered"
        candidate["output_sha256"] = text_sha256(candidate["output"])
        mutations.append(changed)

        changed = copy.deepcopy(self.report)
        candidate = changed["experiment"]["items"][0]["candidates"][0]
        candidate["raw_criteria_pass"][0] = not candidate["raw_criteria_pass"][0]
        mutations.append(changed)

        changed = copy.deepcopy(self.report)
        timeout_item = next(
            item
            for item in changed["experiment"]["items"]
            if item["case_id"] == "timeout-idempotency-key-not-enforcement"
        )
        timeout_item["candidates"][0]["calibrated_criteria_pass"][0] = False
        mutations.append(changed)

        changed = copy.deepcopy(self.report)
        changed["experiment"]["blind_reviewer"]["task_name"] = "different-task"
        mutations.append(changed)

        changed = copy.deepcopy(self.report)
        changed["experiment"]["blind_reviewer"]["blind_file_boundary_clean"] = False
        mutations.append(changed)

        changed = copy.deepcopy(self.report)
        changed["experiment"]["semantic_calibration"]["reviewer"][
            "task_name"
        ] = "different-task"
        mutations.append(changed)

        changed = copy.deepcopy(self.report)
        changed["experiment"]["semantic_calibration"]["reviewer"]["note"] += " altered"
        mutations.append(changed)

        changed = copy.deepcopy(self.report)
        changed["experiment"]["semantic_calibration"]["review_sha256"] = "0" * 64
        mutations.append(changed)

        for changed in mutations:
            self.assertNotEqual(
                canonical_sha256(evidence_projection(changed["experiment"])),
                expected,
            )


if __name__ == "__main__":
    unittest.main()
