"""Protect the published round-15 relationship report and historical packages."""

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
    / "relationship-boundary-round-15-diagnostic.json"
)
VALIDATOR = runpy.run_path(str(ROOT / "scripts" / "validate_collection.py"))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class RelationshipBoundaryRound15ReportTests(unittest.TestCase):
    def test_report_recomputes_from_sources_outputs_and_packages(self):
        report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
        self.assertEqual(
            report["scope"],
            {
                "skill_id": "relationship-review",
                "starting_version": "0.1.1",
                "final_version": "0.1.3",
                "catalog_status": "experimental",
                "active_case_count": 11,
                "collection_active_case_count": 99,
                "formal_outputs": 72,
                "blind_review_items": 30,
                "criterion_booleans": 216,
            },
        )

        expected = {
            "relationship-boundary-regression-05": {
                "baseline": (38, 54, 8, 18, 1, 172801),
                "ours": (39, 54, 9, 18, 3, 196627),
            },
            "relationship-boundary-regression-06": {
                "baseline": (12, 27, 0, 9, 0, 86065),
                "previous": (12, 27, 0, 9, 0, 98230),
                "candidate": (23, 27, 7, 9, 9, 100225),
            },
            "relationship-speaker-mapping-regression-07": {
                "baseline": (0, 9, 0, 3, 0, 28413),
                "previous": (7, 9, 2, 3, 0, 33689),
                "candidate": (9, 9, 3, 3, 1, 33058),
            },
        }

        observed_outputs = 0
        observed_items = 0
        observed_booleans = 0
        for experiment in report["experiments"]:
            comparison_id = experiment["comparison_id"]
            comparison = ROOT / "evaluations" / "comparisons" / comparison_id
            for name, digest in experiment["source_hashes"].items():
                self.assertEqual(sha256_file(comparison / name), digest)

            arms = {item["arm_id"]: item for item in experiment["arms"]}
            observed_outputs += sum(item["runtime"]["rows"] for item in arms.values())
            observed_items += len(experiment["items"])
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
                expected[comparison_id],
            )

            recomputed = {
                arm_id: {
                    "outputs": 0,
                    "perfect_outputs": 0,
                    "criteria_passed": 0,
                    "criteria_total": 0,
                    "preferred_count": 0,
                }
                for arm_id in arms
            }
            for item in experiment["items"]:
                self.assertTrue(item["review_notes"].strip())
                if item["preferred_arm"] is not None:
                    recomputed[item["preferred_arm"]]["preferred_count"] += 1
                for candidate in item["candidates"]:
                    output = candidate["output"]
                    self.assertEqual(
                        hashlib.sha256(output.encode("utf-8")).hexdigest(),
                        candidate["output_sha256"],
                    )
                    self.assertEqual(
                        candidate["passed"], sum(candidate["criteria_pass"])
                    )
                    self.assertEqual(
                        candidate["total"], len(candidate["criteria_pass"])
                    )
                    observed_booleans += candidate["total"]
                    arm = recomputed[candidate["arm_id"]]
                    arm["outputs"] += 1
                    arm["perfect_outputs"] += (
                        candidate["passed"] == candidate["total"]
                    )
                    arm["criteria_passed"] += candidate["passed"]
                    arm["criteria_total"] += candidate["total"]

            for arm_id, values in recomputed.items():
                published = arms[arm_id]["strict_blind_review"]
                self.assertEqual(
                    values,
                    {key: published[key] for key in values},
                )
                evidence_path = arms[arm_id]["package_evidence_path"]
                package_digest = arms[arm_id]["skill_package_sha256"]
                if evidence_path is None:
                    self.assertIsNone(package_digest)
                else:
                    self.assertEqual(
                        VALIDATOR["package_fingerprint"](ROOT / evidence_path),
                        package_digest,
                    )

        self.assertEqual(observed_outputs, report["scope"]["formal_outputs"])
        self.assertEqual(observed_items, report["scope"]["blind_review_items"])
        self.assertEqual(observed_booleans, report["scope"]["criterion_booleans"])

        catalog = json.loads(
            (ROOT / "catalog" / "collection.json").read_text(encoding="utf-8")
        )
        relationship = next(
            item for item in catalog["skills"] if item["id"] == "relationship-review"
        )
        self.assertEqual(relationship["status"], "experimental")
        historical_skill = (
            ROOT
            / "evaluations"
            / "comparisons"
            / "relationship-attribution-regression-09"
            / "packages"
            / "relationship-review-0.1.3"
        )
        self.assertEqual(
            VALIDATOR["package_fingerprint"](historical_skill),
            report["decision"]["final_skill_package_sha256"],
        )

if __name__ == "__main__":
    unittest.main()
