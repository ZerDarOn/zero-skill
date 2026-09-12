"""Protect the published round-20 quantitative confirmation report."""

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
    / "claim-quantitative-confirmatory-round-20-diagnostic.json"
)
VALIDATOR = runpy.run_path(str(ROOT / "scripts" / "validate_collection.py"))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha256(value) -> str:
    payload = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def text_sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def reviewer_projection(experiment):
    reviewer = experiment["reviewer"]
    return {
        key: reviewer[key]
        for key in (
            "kind",
            "blind_to_arm_mapping",
            "prior_protocol_exposure",
            "prior_skill_revision_exposure",
            "prior_skill_revision_exposure_note",
        )
    }


def decision_projection(experiment):
    return {
        "reviewer": reviewer_projection(experiment),
        "reviews": [
            {
                "review_id": item["review_id"],
                "criteria_pass": {
                    candidate["candidate_id"]: candidate["criteria_pass"]
                    for candidate in item["candidates"]
                },
                "preferred_candidate": item["preferred_candidate"],
            }
            for item in experiment["items"]
        ],
    }


def evidence_projection(experiment):
    return {
        "schema": "round20-evidence-projection-v1",
        "freeze_commit": experiment["freeze_commit"],
        "source_hashes": experiment["source_hashes"],
        "reviewer": reviewer_projection(experiment),
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
                        "skill_package_sha256": candidate["skill_package_sha256"],
                        "output_sha256": candidate["output_sha256"],
                        "criteria_pass": candidate["criteria_pass"],
                    }
                    for candidate in item["candidates"]
                ],
            }
            for item in experiment["items"]
        ],
    }


class ClaimQuantitativeConfirmatoryRound20Tests(unittest.TestCase):
    def test_report_recomputes_scores_gate_and_current_state(self):
        report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
        self.assertEqual(
            report["scope"],
            {
                "skill_id": "claim-evidence-review",
                "version": "0.1.0",
                "catalog_status": "experimental",
                "active_case_count": 17,
                "collection_active_case_count": 119,
                "formal_outputs": 30,
                "blind_review_items": 15,
                "criterion_booleans": 90,
            },
        )

        experiment = report["experiment"]
        comparison = ROOT / "evaluations" / "comparisons" / experiment["comparison_id"]
        self.assertEqual(
            experiment["freeze_commit"],
            "8b72878a41b6963fd411b1619adf308b79c439d9",
        )
        self.assertTrue(experiment["infrastructure_valid"])
        expected_source_hashes = {
            "promptfoo.json": "83ab64fea30ea4f45db2df89afd7423de6ccf01bc852e58e1a7765ce86a5c94f",
            "cases.json": "55ab72fc651d7fd917e581162c8fa542431865cc8bb5ad398dea9bc9e13c7b6e",
        }
        self.assertEqual(experiment["source_hashes"], expected_source_hashes)
        for name, digest in expected_source_hashes.items():
            self.assertEqual(sha256_file(comparison / name), digest)
        self.assertEqual(
            experiment["prepared_hashes"],
            {
                "config": "58f7530c9c9d068868519599e4619e0bcd3aa0836f2689dbb2bef382a25d811c",
                "tests": "f868590322310d82567abd9e76de63114deeb570fea5930c72b2ce98aeebc999",
            },
        )
        self.assertEqual(
            experiment["artifact_hashes"],
            {
                "frozen.json": "6ef387d97154f1712acdfea793164755e8beae86c296a92cf4feea0987768aff",
                "results.json": "061d17ee0bffb218e537ef8b518ba67f4bdf79983da5c9b937510d975a721bdd",
                "summary.json": "f2987c5b5e64f55d8e0b3e63d4df2648b054155067e567991ac96ffb6a9e1729",
                "blind-review.json": "5e8308731200aca7d9bb6ec574843bd61b8dab39ac6ed5c6ff68f607bb8bed39",
                "blind-review-key.json": "97bce904d4e400d9d676c70aa586ec42dc3a823a5f02b54b5571dde9fefb64fe",
                "blind-review-form.json": "44bdd9230e3acfc7b2fb9d9defe38959ddc7b6fc4f8f584bb25346312a2099c0",
                "blind-review-completed-independent.json": "eb99153e7df14e36f8bd782460f190ca25d8ef969bc6792024b7be8f663200fe",
                "review-result-blind-review-completed-independent.json": "407e40fc11987f170c5c63dbfd066be9dc872c0b35d7c7de58d701b25370bf42",
            },
        )
        self.assertEqual(
            experiment["decision_projection_sha256"],
            "18290d5de78ac8a32e4a00f4ebe1c54a2b24e91fbe047eb4c0d298a931e9d121",
        )
        reviewer = experiment["reviewer"]
        self.assertTrue(reviewer["blind_to_arm_mapping"])
        self.assertFalse(reviewer["independent_human"])
        self.assertTrue(reviewer["prior_protocol_exposure"])
        self.assertTrue(reviewer["prior_skill_revision_exposure"])
        self.assertEqual(
            canonical_sha256(decision_projection(experiment)),
            experiment["decision_projection_sha256"],
        )
        self.assertEqual(
            experiment["evidence_projection"],
            {
                "schema": "round20-evidence-projection-v1",
                "canonicalization": "UTF-8 JSON with ensure_ascii=false, sorted keys, and separators comma/colon",
                "sha256": "412449a205c54e2c0308e8f4a59e5f035d309e96daddad0af9c8191a94622c97",
            },
        )
        self.assertEqual(
            canonical_sha256(evidence_projection(experiment)),
            experiment["evidence_projection"]["sha256"],
        )

        arms = {item["arm_id"]: item for item in experiment["arms"]}
        self.assertEqual(
            {
                arm_id: (
                    item["strict_blind_review"]["criteria_passed"],
                    item["strict_blind_review"]["criteria_total"],
                    item["strict_blind_review"]["perfect_outputs"],
                    item["strict_blind_review"]["outputs"],
                    item["strict_blind_review"]["preferred_count"],
                    item["runtime"]["tokens_total"]["total"],
                )
                for arm_id, item in arms.items()
            },
            {
                "baseline": (44, 45, 14, 15, 1, 147025),
                "ours": (45, 45, 15, 15, 7, 160611),
            },
        )

        recomputed = {
            arm_id: {
                "criteria_passed": 0,
                "criteria_total": 0,
                "perfect_outputs": 0,
                "outputs": 0,
                "preferred_count": 0,
            }
            for arm_id in arms
        }
        by_case = {}
        core_index = {
            "equal-rate-different-denominators": 1,
            "corrected-and-missing-denominators": 0,
            "strict-table-two-batches": 1,
        }
        frozen_spec = json.loads(
            (comparison / "promptfoo.json").read_text(encoding="utf-8")
        )
        frozen_cases = json.loads(
            (comparison / "cases.json").read_text(encoding="utf-8")
        )
        frozen_by_id = {case["id"]: case for case in frozen_cases}
        observed_booleans = 0
        for item in experiment["items"]:
            frozen_case = frozen_by_id[item["case_id"]]
            self.assertEqual(item["purpose"], frozen_case["purpose"])
            self.assertEqual(item["hard_criteria"], frozen_case["hard_criteria"])
            self.assertEqual(
                item["task"],
                frozen_spec["common_prompt"] + "\n\n" + frozen_case["prompt"],
            )
            self.assertTrue(item["review_notes"].strip())
            self.assertNotIn("\ufffd", item["review_notes"])
            case = by_case.setdefault(
                item["case_id"],
                {
                    arm_id: {
                        **{key: 0 for key in recomputed[arm_id]},
                        "core_omissions": 0,
                    }
                    for arm_id in arms
                },
            )
            if item["preferred_arm"] is not None:
                recomputed[item["preferred_arm"]]["preferred_count"] += 1
                case[item["preferred_arm"]]["preferred_count"] += 1
            for candidate in item["candidates"]:
                self.assertEqual(
                    hashlib.sha256(candidate["output"].encode("utf-8")).hexdigest(),
                    candidate["output_sha256"],
                )
                self.assertEqual(candidate["passed"], sum(candidate["criteria_pass"]))
                self.assertEqual(candidate["total"], len(candidate["criteria_pass"]))
                observed_booleans += candidate["total"]
                for target in (recomputed[candidate["arm_id"]], case[candidate["arm_id"]]):
                    target["criteria_passed"] += candidate["passed"]
                    target["criteria_total"] += candidate["total"]
                    target["perfect_outputs"] += candidate["passed"] == candidate["total"]
                    target["outputs"] += 1
                case[candidate["arm_id"]]["core_omissions"] += not candidate[
                    "criteria_pass"
                ][core_index[item["case_id"]]]

        for arm_id, values in recomputed.items():
            published = arms[arm_id]["strict_blind_review"]
            self.assertEqual(values, {key: published[key] for key in values})
            evidence_path = arms[arm_id]["package_evidence_path"]
            if evidence_path is not None:
                self.assertEqual(
                    VALIDATOR["package_fingerprint"](ROOT / evidence_path),
                    arms[arm_id]["skill_package_sha256"],
                )
        self.assertEqual(len(experiment["items"]), 15)
        self.assertEqual(observed_booleans, 90)
        self.assertEqual(sum(item["runtime"]["rows"] for item in arms.values()), 30)
        self.assertEqual(report["analysis"]["overall"]["baseline"], {**recomputed["baseline"], "criterion_pass_rate": 0.9778})
        self.assertEqual(report["analysis"]["overall"]["version_0_1_0"], {**recomputed["ours"], "criterion_pass_rate": 1.0})
        self.assertEqual(report["analysis"]["overall"]["ties"], 7)
        for case_id, values in by_case.items():
            self.assertEqual(
                report["analysis"]["by_case"][case_id],
                {"baseline": values["baseline"], "version_0_1_0": values["ours"]},
            )

        gate = report["analysis"]["candidate_gate"]
        self.assertEqual(gate["qualifying_cases"], [])
        self.assertFalse(gate["triggered"])
        self.assertFalse(gate["prior_exploratory_signal_included"])
        for case_id, values in by_case.items():
            self.assertEqual(
                gate["per_case"][case_id],
                {
                    "baseline_core_omissions": values["baseline"]["core_omissions"],
                    "version_0_1_0_core_omissions": values["ours"]["core_omissions"],
                },
            )

        costs = report["analysis"]["cost_and_efficiency"]
        self.assertEqual(costs["total_token_delta"], 13586)
        self.assertEqual(costs["total_token_delta_percent"], 9.2)
        self.assertEqual(costs["completion_token_delta_percent"], 29.8)
        self.assertEqual(costs["cost_delta_percent"], -0.7)
        self.assertEqual(costs["latency_delta_percent"], 2.1)
        self.assertFalse(report["decision"]["skill_changed"])
        self.assertFalse(report["decision"]["version_changed"])
        self.assertFalse(report["decision"]["candidate_design_opened"])
        self.assertEqual(report["decision"]["active_cases_added"], 3)

        catalog = json.loads(
            (ROOT / "catalog" / "collection.json").read_text(encoding="utf-8")
        )
        claim = next(item for item in catalog["skills"] if item["id"] == "claim-evidence-review")
        self.assertEqual(
            (claim["version"], claim["status"], claim["evidence"]),
            ("0.1.0", "experimental", None),
        )
        active_total = 0
        claim_suite = None
        for path in (ROOT / "evaluations" / "cases").glob("*.json"):
            suite = json.loads(path.read_text(encoding="utf-8"))
            if suite.get("stage") == "active":
                active_total += len(suite["cases"])
            if suite.get("skill_id") == "claim-evidence-review":
                claim_suite = suite
        self.assertGreaterEqual(
            active_total, report["scope"]["collection_active_case_count"]
        )
        self.assertEqual(len(claim_suite["cases"]), 17)
        active_by_comparison = {
            item["input"]["comparison_case_id"]: item
            for item in claim_suite["cases"]
            if item.get("input", {}).get("comparison_case_id")
        }
        for frozen_case in frozen_cases:
            active_case = active_by_comparison[frozen_case["id"]]
            self.assertEqual(active_case["prompt"], frozen_case["prompt"])
            self.assertEqual(active_case["must_include"], frozen_case["hard_criteria"])

    def test_evidence_projection_detects_coordinated_mutations(self):
        report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
        expected = report["experiment"]["evidence_projection"]["sha256"]

        mutations = []

        changed_source = copy.deepcopy(report)
        changed_source["experiment"]["source_hashes"]["cases.json"] = "0" * 64
        mutations.append(changed_source)

        changed_criterion = copy.deepcopy(report)
        changed_criterion["experiment"]["items"][0]["hard_criteria"][0] += " changed"
        mutations.append(changed_criterion)

        changed_output = copy.deepcopy(report)
        candidate = changed_output["experiment"]["items"][0]["candidates"][0]
        candidate["output"] += " changed"
        candidate["output_sha256"] = text_sha256(candidate["output"])
        mutations.append(changed_output)

        changed_score = copy.deepcopy(report)
        score = changed_score["experiment"]["items"][0]["candidates"][0][
            "criteria_pass"
        ]
        score[0] = not score[0]
        mutations.append(changed_score)

        for mutated in mutations:
            self.assertNotEqual(
                canonical_sha256(evidence_projection(mutated["experiment"])),
                expected,
            )


if __name__ == "__main__":
    unittest.main()
