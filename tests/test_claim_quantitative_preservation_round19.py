"""Protect the published round-19 quantitative-preservation report."""

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
    / "claim-quantitative-preservation-round-19-diagnostic.json"
)
VALIDATOR = runpy.run_path(str(ROOT / "scripts" / "validate_collection.py"))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ClaimQuantitativePreservationRound19Tests(unittest.TestCase):
    def test_report_recomputes_results_and_current_state(self):
        report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
        self.assertEqual(
            report["scope"],
            {
                "skill_id": "claim-evidence-review",
                "version": "0.1.0",
                "catalog_status": "experimental",
                "active_case_count": 14,
                "collection_active_case_count": 116,
                "formal_outputs": 24,
                "blind_review_items": 12,
                "criterion_booleans": 72,
            },
        )

        experiment = report["experiment"]
        comparison = ROOT / "evaluations" / "comparisons" / experiment["comparison_id"]
        self.assertEqual(
            experiment["freeze_commit"],
            "704855f73c8b57ab595ebe1d89f54d09697f6e4e",
        )
        self.assertTrue(experiment["infrastructure_valid"])
        for name, digest in experiment["source_hashes"].items():
            self.assertEqual(sha256_file(comparison / name), digest)
        self.assertEqual(
            experiment["prepared_hashes"],
            {
                "config": "84a368d06a80e3ed6bbd4ca1ad8e42e5c965c121c23b7c646bb745a4d6e20a2f",
                "tests": "6955e83342613baf49cd9c4158d71208ed78d39c15745e6ff857c9eef2434f65",
            },
        )
        self.assertEqual(
            experiment["artifact_hashes"],
            {
                "frozen.json": "0c1056a331be9a6c7625a461abd805888dbd525c9dc35b052cea9ad9d847fffb",
                "results.json": "01aee7acf9c6cb72492216bef074e2885ed720755b6ea30fb0438c278d6d047c",
                "summary.json": "e37e1aec6a7a7d8a90491a3d05dfd2441563e2ed387b9e4f253e76fef510e23b",
                "blind-review.json": "5bd1790d480e399307719696c8a6989fd8216f0d603f2c651cb70621e20a5404",
                "blind-review-key.json": "803db50c9ef835abdad04462123fa5f2a45c465c8efca26a176645b12e82bc55",
                "blind-review-form.json": "1780723e5cf4530742141706c8963ace5bd90f626004d921f7571a66b3065c3c",
                "blind-review-completed-independent.json": "a46b97b98522824b6e83e03fd7b2b16ea27c44f465850f80d218e22c66f3c619",
                "review-result-blind-review-completed-independent.json": "b4d5e2429c2e576323070a6bb95660a035f6549518ca99b9be5fe8baffe1974d",
            },
        )
        reviewer = experiment["reviewer"]
        self.assertTrue(reviewer["blind_to_arm_mapping"])
        self.assertFalse(reviewer["independent_human"])
        self.assertTrue(reviewer["prior_protocol_exposure"])
        self.assertTrue(reviewer["prior_skill_revision_exposure"])

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
                "baseline": (35, 36, 11, 12, 2, 117890),
                "ours": (34, 36, 10, 12, 2, 130302),
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
        observed_booleans = 0
        for item in experiment["items"]:
            self.assertTrue(item["review_notes"].strip())
            self.assertNotIn("\ufffd", item["review_notes"])
            case = by_case.setdefault(
                item["case_id"],
                {arm_id: {key: 0 for key in recomputed[arm_id]} for arm_id in arms},
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
                for target in (
                    recomputed[candidate["arm_id"]],
                    case[candidate["arm_id"]],
                ):
                    target["criteria_passed"] += candidate["passed"]
                    target["criteria_total"] += candidate["total"]
                    target["perfect_outputs"] += candidate["passed"] == candidate["total"]
                    target["outputs"] += 1

        for arm_id, values in recomputed.items():
            published = arms[arm_id]["strict_blind_review"]
            self.assertEqual(values, {key: published[key] for key in values})
            evidence_path = arms[arm_id]["package_evidence_path"]
            if evidence_path is not None:
                self.assertEqual(
                    VALIDATOR["package_fingerprint"](ROOT / evidence_path),
                    arms[arm_id]["skill_package_sha256"],
                )
        self.assertEqual(len(experiment["items"]), 12)
        self.assertEqual(observed_booleans, 72)
        self.assertEqual(
            sum(item["runtime"]["rows"] for item in arms.values()), 24
        )
        self.assertEqual(report["analysis"]["overall"]["baseline"], recomputed["baseline"])
        self.assertEqual(report["analysis"]["overall"]["version_0_1_0"], recomputed["ours"])
        self.assertEqual(report["analysis"]["overall"]["ties"], 8)
        for case_id, values in by_case.items():
            self.assertEqual(
                report["analysis"]["by_case"][case_id],
                {"baseline": values["baseline"], "version_0_1_0": values["ours"]},
            )

        costs = report["analysis"]["cost_and_efficiency"]
        self.assertEqual(costs["total_token_delta"], 12412)
        self.assertEqual(costs["total_token_delta_percent"], 10.5)
        self.assertEqual(costs["completion_token_delta_percent"], 26.1)
        self.assertEqual(costs["cost_delta_percent"], 38.7)
        self.assertEqual(costs["latency_delta_percent"], -5.3)
        cross_round = report["analysis"]["cross_round_quantitative_fidelity_signal"]
        self.assertTrue(cross_round["exploratory"])
        self.assertEqual(cross_round["baseline_omissions"], 2)
        self.assertEqual(cross_round["version_0_1_0_omissions"], 4)
        self.assertEqual(
            sha256_file(ROOT / cross_round["prior_report_path"]),
            cross_round["prior_report_sha256"],
        )
        prior_report = json.loads(
            (ROOT / cross_round["prior_report_path"]).read_text(encoding="utf-8")
        )
        prior_signal = prior_report["analysis"]["numeric_fidelity_observation"]
        current_omissions = {
            "baseline": sum(
                values["baseline"]["criteria_total"]
                - values["baseline"]["criteria_passed"]
                for values in report["analysis"]["by_case"].values()
            ),
            "version_0_1_0": sum(
                values["version_0_1_0"]["criteria_total"]
                - values["version_0_1_0"]["criteria_passed"]
                for values in report["analysis"]["by_case"].values()
            ),
        }
        self.assertEqual(
            cross_round["baseline_omissions"],
            prior_signal["baseline"]["criteria_total"]
            - prior_signal["baseline"]["criteria_passed"]
            + current_omissions["baseline"],
        )
        self.assertEqual(
            cross_round["version_0_1_0_omissions"],
            prior_signal["version_0_1_0"]["criteria_total"]
            - prior_signal["version_0_1_0"]["criteria_passed"]
            + current_omissions["version_0_1_0"],
        )
        self.assertEqual(
            cross_round["related_topologies"],
            1 + len(report["analysis"]["by_case"]),
        )
        self.assertEqual(
            cross_round["outputs_per_arm"],
            prior_signal["baseline"]["outputs"]
            + report["analysis"]["overall"]["baseline"]["outputs"],
        )
        self.assertFalse(report["decision"]["skill_changed"])
        self.assertFalse(report["decision"]["version_changed"])
        self.assertEqual(report["decision"]["active_cases_added"], 4)

        catalog = json.loads(
            (ROOT / "catalog" / "collection.json").read_text(encoding="utf-8")
        )
        claim = next(item for item in catalog["skills"] if item["id"] == "claim-evidence-review")
        self.assertEqual((claim["version"], claim["status"], claim["evidence"]), ("0.1.0", "experimental", None))

        active_total = 0
        claim_suite = None
        for path in (ROOT / "evaluations" / "cases").glob("*.json"):
            suite = json.loads(path.read_text(encoding="utf-8"))
            if suite.get("stage") == "active":
                active_total += len(suite["cases"])
            if suite.get("skill_id") == "claim-evidence-review":
                claim_suite = suite
        # Later rounds may add cases. This historical test keeps its four frozen
        # cases bound; the newest report test owns the exact current totals.
        self.assertGreaterEqual(
            active_total, report["scope"]["collection_active_case_count"]
        )
        self.assertGreaterEqual(
            len(claim_suite["cases"]), report["scope"]["active_case_count"]
        )
        active_by_comparison = {
            item["input"]["comparison_case_id"]: item
            for item in claim_suite["cases"]
            if item.get("input", {}).get("comparison_case_id")
        }
        frozen_cases = json.loads((comparison / "cases.json").read_text(encoding="utf-8"))
        for frozen_case in frozen_cases:
            active_case = active_by_comparison[frozen_case["id"]]
            self.assertEqual(active_case["prompt"], frozen_case["prompt"])
            self.assertEqual(active_case["must_include"], frozen_case["hard_criteria"])


if __name__ == "__main__":
    unittest.main()
