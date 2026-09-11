"""Protect the published round-17 nested-source report."""

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
    / "relationship-nested-source-round-17-diagnostic.json"
)
VALIDATOR = runpy.run_path(str(ROOT / "scripts" / "validate_collection.py"))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class RelationshipNestedSourceRound17ReportTests(unittest.TestCase):
    def test_report_recomputes_groups_outputs_and_current_state(self):
        report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
        self.assertEqual(
            report["scope"],
            {
                "skill_id": "relationship-review",
                "version": "0.1.4",
                "catalog_status": "experimental",
                "active_case_count": 18,
                "collection_active_case_count": 106,
                "formal_outputs": 24,
                "blind_review_items": 12,
                "criterion_booleans": 72,
            },
        )

        experiment = report["experiment"]
        comparison = (
            ROOT / "evaluations" / "comparisons" / experiment["comparison_id"]
        )
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
        self.assertTrue(reviewer["prior_protocol_exposure"])
        self.assertTrue(reviewer["prior_skill_revision_exposure"])
        self.assertIn("four literal tie strings", experiment["review_format_note"])

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
                "baseline": (32, 36, 8, 12, 2, 113563),
                "ours": (36, 36, 12, 12, 6, 135962),
            },
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
        observed_booleans = 0
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
                self.assertEqual(candidate["passed"], sum(candidate["criteria_pass"]))
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
        self.assertEqual(
            len(experiment["items"]), report["scope"]["blind_review_items"]
        )
        self.assertEqual(observed_booleans, report["scope"]["criterion_booleans"])

        multi_hop_ids = set(report["analysis"]["multi_hop_cases"]["case_ids"])
        control_id = report["analysis"]["direct_control"]["case_id"]

        def aggregate(case_ids):
            values = {
                arm_id: {
                    "criteria_passed": 0,
                    "criteria_total": 0,
                    "perfect_outputs": 0,
                    "outputs": 0,
                    "preferred_count": 0,
                }
                for arm_id in arms
            }
            for item in experiment["items"]:
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

        multi_hop_totals = aggregate(multi_hop_ids)
        self.assertEqual(
            multi_hop_totals,
            {
                "baseline": {
                    "criteria_passed": 23,
                    "criteria_total": 27,
                    "perfect_outputs": 5,
                    "outputs": 9,
                    "preferred_count": 2,
                },
                "ours": {
                    "criteria_passed": 27,
                    "criteria_total": 27,
                    "perfect_outputs": 9,
                    "outputs": 9,
                    "preferred_count": 6,
                },
            },
        )
        control_totals = aggregate({control_id})
        self.assertEqual(
            control_totals,
            {
                "baseline": {
                    "criteria_passed": 9,
                    "criteria_total": 9,
                    "perfect_outputs": 3,
                    "outputs": 3,
                    "preferred_count": 0,
                },
                "ours": {
                    "criteria_passed": 9,
                    "criteria_total": 9,
                    "perfect_outputs": 3,
                    "outputs": 3,
                    "preferred_count": 0,
                },
            },
        )
        def displayed(values):
            return {
                "criteria": (
                    f"{values['criteria_passed']}/{values['criteria_total']}"
                ),
                "perfect_outputs": (
                    f"{values['perfect_outputs']}/{values['outputs']}"
                ),
                "preferred": values["preferred_count"],
            }

        self.assertEqual(
            report["analysis"]["multi_hop_cases"]["baseline"],
            displayed(multi_hop_totals["baseline"]),
        )
        self.assertEqual(
            report["analysis"]["multi_hop_cases"]["version_0_1_4"],
            displayed(multi_hop_totals["ours"]),
        )
        self.assertEqual(
            report["analysis"]["direct_control"]["baseline"],
            displayed(control_totals["baseline"]),
        )
        self.assertEqual(
            report["analysis"]["direct_control"]["version_0_1_4"],
            displayed(control_totals["ours"]),
        )
        self.assertEqual(
            report["analysis"]["overall"]["baseline"],
            displayed(recomputed["baseline"]),
        )
        self.assertEqual(
            report["analysis"]["overall"]["version_0_1_4"],
            displayed(recomputed["ours"]),
        )
        self.assertEqual(report["analysis"]["overall"]["ties"], 4)
        self.assertEqual(report["analysis"]["direct_control"]["ties"], 3)

        self.assertEqual(
            report["analysis"]["prior_residual"]["case_id"],
            "nested-handoff-report-chain",
        )
        self.assertEqual(
            report["analysis"]["prior_residual"]["candidate_perfect_outputs"],
            "1/3",
        )
        self.assertFalse(report["decision"]["skill_changed"])
        self.assertFalse(report["decision"]["version_changed"])

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

        active_total = 0
        relationship_cases = None
        for path in (ROOT / "evaluations" / "cases").glob("*.json"):
            suite = json.loads(path.read_text(encoding="utf-8"))
            if suite.get("stage") == "active":
                active_total += len(suite["cases"])
            if suite.get("skill_id") == "relationship-review":
                relationship_cases = suite
        self.assertEqual(active_total, 106)
        self.assertEqual(len(relationship_cases["cases"]), 18)
        ids = {item["id"] for item in relationship_cases["cases"]}
        self.assertTrue(
            {
                "regression-relayed-release-window-group-note",
                "regression-corrected-nested-shift-report",
                "regression-partial-calendar-with-nested-update",
                "regression-direct-authoritative-update-control",
                "regression-nested-handoff-report-chain",
            }.issubset(ids)
        )


if __name__ == "__main__":
    unittest.main()
