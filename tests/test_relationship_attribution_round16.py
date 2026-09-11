"""Protect the published round-16 relationship attribution report."""

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
    / "relationship-attribution-round-16-diagnostic.json"
)
VALIDATOR = runpy.run_path(str(ROOT / "scripts" / "validate_collection.py"))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class RelationshipAttributionRound16ReportTests(unittest.TestCase):
    def test_report_recomputes_from_embedded_outputs_and_packages(self):
        report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
        self.assertEqual(
            report["scope"],
            {
                "skill_id": "relationship-review",
                "starting_version": "0.1.3",
                "final_version": "0.1.4",
                "catalog_status": "experimental",
                "active_case_count": 14,
                "collection_active_case_count": 102,
                "formal_outputs": 117,
                "blind_review_items": 45,
                "criterion_booleans": 351,
            },
        )

        expected = {
            "relationship-overcorrection-regression-08": {
                "baseline": (51, 54, 15, 18, 1, 172451),
                "ours": (51, 54, 15, 18, 8, 201781),
            },
            "relationship-attribution-regression-09": {
                "baseline": (72, 81, 18, 27, 5, 259556),
                "previous": (69, 81, 19, 27, 2, 302999),
                "candidate": (78, 81, 24, 27, 12, 298588),
            },
        }
        exposure = {
            "relationship-overcorrection-regression-08": (True, False),
            "relationship-attribution-regression-09": (True, True),
        }

        observed_outputs = 0
        observed_items = 0
        observed_booleans = 0
        for experiment in report["experiments"]:
            comparison_id = experiment["comparison_id"]
            comparison = ROOT / "evaluations" / "comparisons" / comparison_id
            self.assertTrue(experiment["infrastructure_valid"])
            for name, digest in experiment["source_hashes"].items():
                self.assertEqual(sha256_file(comparison / name), digest)
            for digest in experiment["prepared_hashes"].values():
                self.assertRegex(digest, r"^[0-9a-f]{64}$")
            for digest in experiment["artifact_hashes"].values():
                self.assertRegex(digest, r"^[0-9a-f]{64}$")

            reviewer = experiment["reviewer"]
            self.assertTrue(reviewer["blind_to_arm_mapping"])
            self.assertFalse(reviewer["independent_human"])
            self.assertEqual(
                (
                    reviewer["prior_protocol_exposure"],
                    reviewer["prior_skill_revision_exposure"],
                ),
                exposure[comparison_id],
            )

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
                    values = recomputed[candidate["arm_id"]]
                    values["outputs"] += 1
                    values["perfect_outputs"] += (
                        candidate["passed"] == candidate["total"]
                    )
                    values["criteria_passed"] += candidate["passed"]
                    values["criteria_total"] += candidate["total"]

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
        candidate_experiment = next(
            item
            for item in report["experiments"]
            if item["comparison_id"] == "relationship-attribution-regression-09"
        )
        new_case_ids = {
            "nested-handoff-report-chain",
            "partial-system-record-invitation",
            "corrected-draft-not-sent",
        }
        reused_case_ids = {
            "clear-labeled-return-date-one-line",
            "explicit-numbered-speaker-mapping",
            "conditional-options-without-clarification",
            "disputed-access-card-handoff",
            "mutual-specific-invitation",
            "decline-with-concrete-alternative",
        }

        def aggregate(case_ids):
            values = {
                arm_id: {
                    "criteria_passed": 0,
                    "criteria_total": 0,
                    "perfect_outputs": 0,
                    "outputs": 0,
                    "preferred_count": 0,
                }
                for arm_id in ("baseline", "previous", "candidate")
            }
            for item in candidate_experiment["items"]:
                if item["case_id"] not in case_ids:
                    continue
                if item["preferred_arm"] is not None:
                    values[item["preferred_arm"]]["preferred_count"] += 1
                for candidate in item["candidates"]:
                    arm = values[candidate["arm_id"]]
                    arm["criteria_passed"] += candidate["passed"]
                    arm["criteria_total"] += candidate["total"]
                    arm["perfect_outputs"] += (
                        candidate["passed"] == candidate["total"]
                    )
                    arm["outputs"] += 1
            return values

        new_totals = aggregate(new_case_ids)
        reused_totals = aggregate(reused_case_ids)
        self.assertEqual(
            new_totals,
            {
                "baseline": {
                    "criteria_passed": 21,
                    "criteria_total": 27,
                    "perfect_outputs": 3,
                    "outputs": 9,
                    "preferred_count": 2,
                },
                "previous": {
                    "criteria_passed": 17,
                    "criteria_total": 27,
                    "perfect_outputs": 3,
                    "outputs": 9,
                    "preferred_count": 0,
                },
                "candidate": {
                    "criteria_passed": 24,
                    "criteria_total": 27,
                    "perfect_outputs": 6,
                    "outputs": 9,
                    "preferred_count": 7,
                },
            },
        )
        self.assertEqual(
            reused_totals,
            {
                "baseline": {
                    "criteria_passed": 51,
                    "criteria_total": 54,
                    "perfect_outputs": 15,
                    "outputs": 18,
                    "preferred_count": 3,
                },
                "previous": {
                    "criteria_passed": 52,
                    "criteria_total": 54,
                    "perfect_outputs": 16,
                    "outputs": 18,
                    "preferred_count": 2,
                },
                "candidate": {
                    "criteria_passed": 54,
                    "criteria_total": 54,
                    "perfect_outputs": 18,
                    "outputs": 18,
                    "preferred_count": 5,
                },
            },
        )

        source_new = {arm_id: 0 for arm_id in new_totals}
        source_with_access = {arm_id: 0 for arm_id in new_totals}
        for item in candidate_experiment["items"]:
            for candidate in item["candidates"]:
                if item["case_id"] in new_case_ids:
                    passed = sum(candidate["criteria_pass"][:2])
                    source_new[candidate["arm_id"]] += passed
                    source_with_access[candidate["arm_id"]] += passed
                elif item["case_id"] == "disputed-access-card-handoff":
                    source_with_access[candidate["arm_id"]] += int(
                        candidate["criteria_pass"][0]
                    )
        self.assertEqual(
            source_new, {"baseline": 12, "previous": 8, "candidate": 15}
        )
        self.assertEqual(
            source_with_access,
            {"baseline": 12, "previous": 9, "candidate": 18},
        )
        self.assertEqual(
            report["analysis"]["candidate_stage"]["new_case_totals"][
                "version_0_1_4"
            ],
            {
                "criteria": (
                    f"{new_totals['candidate']['criteria_passed']}/"
                    f"{new_totals['candidate']['criteria_total']}"
                ),
                "perfect_outputs": (
                    f"{new_totals['candidate']['perfect_outputs']}/"
                    f"{new_totals['candidate']['outputs']}"
                ),
                "preferred": new_totals["candidate"]["preferred_count"],
            },
        )
        self.assertEqual(
            report["analysis"]["candidate_stage"]["reused_case_totals"][
                "version_0_1_4"
            ],
            {
                "criteria": (
                    f"{reused_totals['candidate']['criteria_passed']}/"
                    f"{reused_totals['candidate']['criteria_total']}"
                ),
                "perfect_outputs": (
                    f"{reused_totals['candidate']['perfect_outputs']}/"
                    f"{reused_totals['candidate']['outputs']}"
                ),
            },
        )
        self.assertEqual(
            report["analysis"]["residual"]["case_id"],
            "nested-handoff-report-chain",
        )
        self.assertEqual(
            report["analysis"]["residual"]["candidate_perfect_outputs"],
            "1/3",
        )

        catalog = json.loads(
            (ROOT / "catalog" / "collection.json").read_text(encoding="utf-8")
        )
        relationship = next(
            item for item in catalog["skills"] if item["id"] == "relationship-review"
        )
        self.assertEqual(relationship["version"], "0.1.4")
        self.assertEqual(relationship["status"], "experimental")
        self.assertIsNone(relationship["evidence"])
        current_skill = ROOT / "skills" / "relationships" / "relationship-review"
        self.assertEqual(
            VALIDATOR["package_fingerprint"](current_skill),
            report["decision"]["final_skill_package_sha256"],
        )

        relationship_cases = json.loads(
            (
                ROOT / "evaluations" / "cases" / "relationship-review.json"
            ).read_text(encoding="utf-8")
        )
        self.assertTrue(
            {
                "regression-nested-handoff-report-chain",
                "regression-partial-system-record-invitation",
                "regression-corrected-draft-not-sent",
            }.issubset({item["id"] for item in relationship_cases["cases"]})
        )


if __name__ == "__main__":
    unittest.main()
