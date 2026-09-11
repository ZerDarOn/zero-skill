"""Protect the published round-18 claim-evidence report."""

import hashlib
import json
from pathlib import Path
import runpy
import unittest


ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = (
    ROOT / "evaluations" / "reports" / "claim-evidence-round-18-diagnostic.json"
)
VALIDATOR = runpy.run_path(str(ROOT / "scripts" / "validate_collection.py"))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ClaimEvidenceRound18ReportTests(unittest.TestCase):
    def test_report_recomputes_scores_outputs_and_current_state(self):
        report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
        self.assertEqual(
            report["scope"],
            {
                "skill_id": "claim-evidence-review",
                "version": "0.1.0",
                "catalog_status": "experimental",
                "active_case_count": 10,
                "collection_active_case_count": 112,
                "formal_outputs": 36,
                "blind_review_items": 18,
                "criterion_booleans": 108,
            },
        )

        experiment = report["experiment"]
        comparison = ROOT / "evaluations" / "comparisons" / experiment["comparison_id"]
        self.assertTrue(experiment["infrastructure_valid"])
        self.assertEqual(
            experiment["freeze_commit"],
            "2dd75b3753748e0f40181d76fa152667d335e828",
        )
        for name, digest in experiment["source_hashes"].items():
            self.assertEqual(sha256_file(comparison / name), digest)
        self.assertEqual(
            experiment["prepared_hashes"],
            {
                "config": "022ff47a8494cf8b9f8e2000cd52cd1a32b0073c3728526353fa96980822aa9b",
                "tests": "17df805fa08a5cd95bb111da3eab40a02e1931f5f86da982d6c6d951dafc01af",
            },
        )
        self.assertEqual(
            experiment["artifact_hashes"],
            {
                "frozen.json": "4bb782ca3610c2af1235b565832b4062c1096a58d36b6bca21b73d9b04300765",
                "results.json": "458c3feff44d7e681a9dce79ae6edc9408e1a61c9d7de6169cef7e666ea365b5",
                "summary.json": "e00fbc7992a0f4469ef07e30b9f99506289b9fbdb11894d9b1e80ce286b6c4f2",
                "blind-review.json": "d735dca7e7b2ab97c8978d2e4a7854d1d137c0076b8f56c8730e111b40dacb40",
                "blind-review-key.json": "f4b72e0c4cf4754cfbe2e4ee96eb4d08289499926b5de0886cd9a67aae5b6963",
                "blind-review-form.json": "6c070810ef57170d1fd20d02241955fc881c615aba66e8c99e4ea4eb70b47fc0",
                "blind-review-completed-independent.json": "329600fc55413fc660308c7e6fcef6c00b0632f6d214a822cff972d64f1a3d22",
                "review-result-blind-review-completed-independent.json": "406900023e607a1c9eb896f9542c569be6b1fad734ae0608d2df5ec856a1f35d",
                "review-result-blind-review-completed-independent-encoding-fixed.json": "e0dc48418b37b6ee197e51e96edd0f74f6136c613447f68a66b8d6496fa19f3a",
            },
        )

        reviewer = experiment["reviewer"]
        self.assertTrue(reviewer["blind_to_arm_mapping"])
        self.assertFalse(reviewer["independent_human"])
        self.assertTrue(reviewer["prior_protocol_exposure"])
        self.assertTrue(reviewer["prior_skill_revision_exposure"])
        self.assertIn("failed before reveal", experiment["review_artifact_note"])
        self.assertIn("UTF-8", experiment["review_artifact_note"])

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
                "baseline": (52, 54, 16, 18, 3, 177055),
                "ours": (52, 54, 16, 18, 7, 229099),
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
            self.assertTrue(
                any("\u4e00" <= char <= "\u9fff" for char in item["review_notes"])
            )
            case = by_case.setdefault(
                item["case_id"],
                {
                    arm_id: {
                        "criteria_passed": 0,
                        "criteria_total": 0,
                        "perfect_outputs": 0,
                        "outputs": 0,
                        "preferred_count": 0,
                    }
                    for arm_id in arms
                },
            )
            if item["preferred_arm"] is not None:
                recomputed[item["preferred_arm"]]["preferred_count"] += 1
                case[item["preferred_arm"]]["preferred_count"] += 1
            for candidate in item["candidates"]:
                output = candidate["output"]
                self.assertEqual(
                    hashlib.sha256(output.encode("utf-8")).hexdigest(),
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
                    target["perfect_outputs"] += (
                        candidate["passed"] == candidate["total"]
                    )
                    target["outputs"] += 1

        decision_projection = {
            "reviewer": {
                key: reviewer[key]
                for key in (
                    "kind",
                    "blind_to_arm_mapping",
                    "prior_protocol_exposure",
                    "prior_skill_revision_exposure",
                    "prior_skill_revision_exposure_note",
                )
            },
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
        decision_projection_sha256 = hashlib.sha256(
            json.dumps(
                decision_projection,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        self.assertEqual(
            experiment["decision_projection_sha256"],
            decision_projection_sha256,
        )

        for arm_id, values in recomputed.items():
            published = arms[arm_id]["strict_blind_review"]
            self.assertEqual(values, {key: published[key] for key in values})
            evidence_path = arms[arm_id]["package_evidence_path"]
            package_digest = arms[arm_id]["skill_package_sha256"]
            if evidence_path is None:
                self.assertIsNone(package_digest)
            else:
                self.assertEqual(
                    VALIDATOR["package_fingerprint"](ROOT / evidence_path),
                    package_digest,
                )

        self.assertEqual(
            sum(item["runtime"]["rows"] for item in arms.values()),
            report["scope"]["formal_outputs"],
        )
        self.assertEqual(len(experiment["items"]), report["scope"]["blind_review_items"])
        self.assertEqual(observed_booleans, report["scope"]["criterion_booleans"])
        self.assertEqual(
            report["analysis"]["overall"]["baseline"], recomputed["baseline"]
        )
        self.assertEqual(
            report["analysis"]["overall"]["version_0_1_0"], recomputed["ours"]
        )
        self.assertEqual(report["analysis"]["overall"]["ties"], 8)
        for case_id, values in by_case.items():
            self.assertEqual(
                report["analysis"]["by_case"][case_id],
                {
                    "baseline": values["baseline"],
                    "version_0_1_0": values["ours"],
                },
            )

        costs = report["analysis"]["cost_and_efficiency"]
        self.assertEqual(costs["total_token_delta"], 52044)
        self.assertEqual(costs["total_token_delta_percent"], 29.4)
        self.assertEqual(costs["completion_token_delta_percent"], 108.2)
        self.assertEqual(costs["cost_delta_percent"], 53.4)
        self.assertEqual(costs["latency_delta_percent"], 19.7)
        self.assertEqual(
            report["analysis"]["numeric_fidelity_observation"]["case_id"],
            "shared-data-with-new-analysis",
        )
        self.assertFalse(report["decision"]["skill_changed"])
        self.assertFalse(report["decision"]["version_changed"])
        self.assertEqual(report["decision"]["active_cases_added"], 6)

        catalog = json.loads(
            (ROOT / "catalog" / "collection.json").read_text(encoding="utf-8")
        )
        claim = next(
            item for item in catalog["skills"] if item["id"] == "claim-evidence-review"
        )
        self.assertEqual(claim["version"], "0.1.0")
        self.assertEqual(claim["status"], "experimental")
        self.assertIsNone(claim["evidence"])

        claim_cases = None
        for path in (ROOT / "evaluations" / "cases").glob("*.json"):
            suite = json.loads(path.read_text(encoding="utf-8"))
            if suite.get("skill_id") == "claim-evidence-review":
                claim_cases = suite
        ids = {item["id"] for item in claim_cases["cases"]}
        self.assertTrue(
            {
                "regression-shared-data-with-new-analysis",
                "regression-metric-scoped-correction",
                "regression-scoped-absence-in-limited-log",
                "regression-composition-reversal",
                "regression-embedded-instruction-and-link-boundary",
                "regression-matched-strong-evidence-control",
            }.issubset(ids)
        )
        active_by_comparison_id = {
            item["input"]["comparison_case_id"]: item
            for item in claim_cases["cases"]
            if "comparison_case_id" in item.get("input", {})
        }
        frozen_cases = json.loads(
            (comparison / "cases.json").read_text(encoding="utf-8")
        )
        self.assertTrue(
            {item["id"] for item in frozen_cases}.issubset(active_by_comparison_id)
        )
        for frozen_case in frozen_cases:
            active_case = active_by_comparison_id[frozen_case["id"]]
            self.assertEqual(active_case["prompt"], frozen_case["prompt"])
            self.assertEqual(
                active_case["must_include"], frozen_case["hard_criteria"]
            )


if __name__ == "__main__":
    unittest.main()
