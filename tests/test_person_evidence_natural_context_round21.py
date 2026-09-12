"""Protect the published round-21 person-evidence diagnostic report."""

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
    / "person-evidence-natural-context-round-21-diagnostic.json"
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


def reviewer_projection(experiment):
    reviewer = experiment["reviewer"]
    return {
        key: reviewer[key]
        for key in (
            "kind",
            "blind_to_arm_mapping",
            "prior_protocol_exposure",
            "prior_skill_revision_exposure",
            "file_access_boundary_clean",
            "unexpected_files_read",
            "unexpected_file_identity_or_scoring_content",
            "process_deviation_note",
            "model",
            "reasoning_effort",
            "independent_human",
            "note",
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
        "schema": "round21-evidence-projection-v2",
        "freeze_commit": experiment["freeze_commit"],
        "model": experiment["model"],
        "reasoning_effort": experiment["reasoning_effort"],
        "source_hashes": experiment["source_hashes"],
        "prepared_hashes": experiment["prepared_hashes"],
        "artifact_hashes": experiment["artifact_hashes"],
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
                        "skill_package_sha256": candidate[
                            "skill_package_sha256"
                        ],
                        "output_sha256": candidate["output_sha256"],
                        "criteria_pass": candidate["criteria_pass"],
                    }
                    for candidate in item["candidates"]
                ],
            }
            for item in experiment["items"]
        ],
    }


class PersonEvidenceNaturalContextRound21Tests(unittest.TestCase):
    def setUp(self):
        self.report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
        self.experiment = self.report["experiment"]

    def test_report_recomputes_scores_gate_and_current_state(self):
        report = self.report
        experiment = self.experiment
        self.assertEqual(
            report["scope"],
            {
                "skill_id": "person-evidence-analysis",
                "version": "0.1.2",
                "catalog_status": "experimental",
                "active_case_count": 16,
                "collection_active_case_count": 125,
                "formal_outputs": 36,
                "blind_review_items": 18,
                "criterion_booleans": 144,
            },
        )
        self.assertEqual(
            experiment["freeze_commit"],
            "359ef9533d8a7bc316e38659f53b18db10df5e9c",
        )
        self.assertTrue(experiment["infrastructure_valid"])

        comparison = (
            ROOT / "evaluations" / "comparisons" / experiment["comparison_id"]
        )
        expected_source_hashes = {
            "promptfoo.json": "66ae3f8150e95be66349ab81e92423b8024112578350594b8b9445d6820dd326",
            "cases.json": "aeb630efe886455460d4e48ea0679374985de6681104c043e294308fe83c03aa",
        }
        self.assertEqual(experiment["source_hashes"], expected_source_hashes)
        for name, digest in expected_source_hashes.items():
            self.assertEqual(sha256_file(comparison / name), digest)
        self.assertEqual(
            experiment["prepared_hashes"],
            {
                "config": "411832f0e579382bd695be9446e64589be56311bee459af452b2572f25421bb5",
                "tests": "59e12afdf36c860ee3ca7dd79bb005f73946bba1649fc2737a26003916ed4d7e",
            },
        )
        self.assertEqual(
            experiment["artifact_hashes"],
            {
                "frozen.json": "99d1d449f5d8a3bc68059781f7f8de8cc5e6c5099af476168ad590a6877f549b",
                "results.json": "3c123b3e7e8ed46376e859372a9e1c73967356f1e978edeeae6f6c10aee6b36c",
                "summary.json": "b9ee591c846335e8be3ef5a71e32dbde94c2cd06335c68194587a74d96bb56fd",
                "blind-review.json": "0b28a724c12212cd69d443cec9ede64409409412eb5a35451e023869c0121872",
                "blind-review-key.json": "ff670bfb9aaa2e8ce8f992aaba3b1b94d7b97dd70fe8558de7614bdfdbe53ed8",
                "blind-review-form.json": "29ea2fbc253086e348c98013f3bf02babdea2016033ad7975793c344493be6e3",
                "blind-review-completed-independent.json": "7dcc6fd4c069367170da20c1663f445c0b8c0aa3a0ff1ca4ca541a917ed092dc",
                "review-result-blind-review-completed-independent.json": "421226f077a8c598936df2937058b2432e8dea73f34de900ea21dfcc251e8bfa",
            },
        )

        reviewer = experiment["reviewer"]
        self.assertTrue(reviewer["blind_to_arm_mapping"])
        self.assertFalse(reviewer["file_access_boundary_clean"])
        self.assertFalse(reviewer["unexpected_file_identity_or_scoring_content"])
        self.assertEqual(
            reviewer["unexpected_files_read"],
            ["$CODEX_HOME/skills/repo-conventions/SKILL.md"],
        )
        self.assertIn("outside the requested", reviewer["process_deviation_note"])
        self.assertEqual(reviewer["model"], "gpt-5.6-sol")
        self.assertEqual(reviewer["reasoning_effort"], "medium")
        self.assertFalse(reviewer["independent_human"])
        self.assertTrue(reviewer["note"].strip())
        self.assertEqual(
            canonical_sha256(decision_projection(experiment)),
            experiment["decision_projection_sha256"],
        )
        self.assertEqual(
            experiment["decision_projection_sha256"],
            "ee69dc7b83f16f3b8b321e431152f2590b04dc0ec25b0ab470a241cb6fa4341a",
        )
        self.assertEqual(
            canonical_sha256(evidence_projection(experiment)),
            experiment["evidence_projection"]["sha256"],
        )
        self.assertEqual(
            experiment["evidence_projection"]["sha256"],
            "bfd195f4b80c331dd8d9836a6dffb7399938061a7fe28b417e85bb4f2e29e41f",
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
                "baseline": (67, 72, 13, 18, 3, 175515),
                "ours": (70, 72, 16, 18, 5, 199884),
            },
        )

        spec = json.loads((comparison / "promptfoo.json").read_text(encoding="utf-8"))
        frozen_cases = json.loads(
            (comparison / "cases.json").read_text(encoding="utf-8")
        )
        frozen_by_id = {case["id"]: case for case in frozen_cases}
        core_index = {
            "self-report-cause-and-follow-through": 1,
            "supervisor-label-and-mixed-decisions": 0,
            "incident-recommendation-and-accountability": 1,
            "community-location-and-organization": 1,
            "bounded-listening-pattern-with-exception": 0,
            "two-sentence-source-and-counterevidence": 1,
        }
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
        by_case = {}
        observed_booleans = 0
        for item in experiment["items"]:
            frozen_case = frozen_by_id[item["case_id"]]
            self.assertEqual(item["purpose"], frozen_case["purpose"])
            self.assertEqual(item["hard_criteria"], frozen_case["hard_criteria"])
            self.assertEqual(
                item["task"], spec["common_prompt"] + "\n\n" + frozen_case["prompt"]
            )
            self.assertTrue(item["review_notes"].strip())
            self.assertNotIn("\ufffd", item["review_notes"])
            case = by_case.setdefault(
                item["case_id"],
                {
                    arm_id: {
                        **{key: 0 for key in recomputed[arm_id]},
                        "core_errors": 0,
                    }
                    for arm_id in arms
                },
            )
            if item["preferred_arm"] is not None:
                recomputed[item["preferred_arm"]]["preferred_count"] += 1
                case[item["preferred_arm"]]["preferred_count"] += 1
            for candidate in item["candidates"]:
                self.assertEqual(
                    text_sha256(candidate["output"]), candidate["output_sha256"]
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
                case[candidate["arm_id"]]["core_errors"] += not candidate[
                    "criteria_pass"
                ][core_index[item["case_id"]]]

        self.assertEqual(len(experiment["items"]), 18)
        self.assertEqual(observed_booleans, 144)
        self.assertEqual(sum(a["runtime"]["rows"] for a in arms.values()), 36)
        for arm_id, values in recomputed.items():
            published = arms[arm_id]["strict_blind_review"]
            self.assertEqual(values, {key: published[key] for key in values})
            evidence_path = arms[arm_id]["package_evidence_path"]
            if evidence_path:
                self.assertEqual(
                    VALIDATOR["package_fingerprint"](ROOT / evidence_path),
                    arms[arm_id]["skill_package_sha256"],
                )
        self.assertEqual(report["analysis"]["overall"]["ties"], 10)
        for case_id, values in by_case.items():
            published = report["analysis"]["by_case"][case_id]
            self.assertEqual(published["baseline"], values["baseline"])
            self.assertEqual(published["version_0_1_2"], values["ours"])

        gate = report["analysis"]["candidate_gate"]
        self.assertFalse(gate["triggered"])
        self.assertEqual(gate["qualifying_mechanisms"], [])
        self.assertEqual(
            gate["diagnostic_only_cases"],
            ["bounded-listening-pattern-with-exception"],
        )
        for case_id, values in by_case.items():
            self.assertEqual(
                gate["per_case"][case_id]["baseline_core_errors"],
                values["baseline"]["core_errors"],
            )
            self.assertEqual(
                gate["per_case"][case_id]["version_0_1_2_core_errors"],
                values["ours"]["core_errors"],
            )

        self.assertEqual(
            report["analysis"]["cost_and_efficiency"],
            {
                "baseline_total_tokens": 175515,
                "version_0_1_2_total_tokens": 199884,
                "total_token_delta": 24369,
                "total_token_delta_percent": 13.9,
                "prompt_token_delta_percent": 13.1,
                "completion_token_delta_percent": 70.7,
                "cost_delta_percent": 31.4,
                "latency_delta_percent": 21.9,
            },
        )
        self.assertFalse(report["decision"]["skill_changed"])
        self.assertFalse(report["decision"]["version_changed"])
        self.assertFalse(report["decision"]["candidate_design_opened"])
        self.assertEqual(report["decision"]["active_cases_added"], 6)

        catalog = json.loads(
            (ROOT / "catalog" / "collection.json").read_text(encoding="utf-8")
        )
        person = next(
            item for item in catalog["skills"] if item["id"] == "person-evidence-analysis"
        )
        self.assertEqual(
            (person["version"], person["status"], person["evidence"]),
            ("0.1.2", "experimental", None),
        )
        active_total = 0
        person_suite = None
        for path in (ROOT / "evaluations" / "cases").glob("*.json"):
            suite = json.loads(path.read_text(encoding="utf-8"))
            if suite.get("stage") == "active":
                active_total += len(suite["cases"])
            if suite.get("skill_id") == "person-evidence-analysis":
                person_suite = suite
        self.assertGreaterEqual(
            active_total, report["scope"]["collection_active_case_count"]
        )
        self.assertGreaterEqual(
            len(person_suite["cases"]), report["scope"]["active_case_count"]
        )

    def test_new_active_cases_preserve_frozen_prompts_and_criteria(self):
        comparison = (
            ROOT
            / "evaluations"
            / "comparisons"
            / "person-evidence-natural-context-forward-14"
        )
        frozen = json.loads((comparison / "cases.json").read_text(encoding="utf-8"))
        active = json.loads(
            (ROOT / "evaluations" / "cases" / "person-evidence-analysis.json").read_text(
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
            self.assertTrue(case["must_avoid"])

    def test_evidence_projection_detects_coordinated_mutations(self):
        expected = self.experiment["evidence_projection"]["sha256"]

        changed_source = copy.deepcopy(self.report)
        changed_source["experiment"]["source_hashes"]["cases.json"] = "0" * 64
        self.assertNotEqual(
            canonical_sha256(evidence_projection(changed_source["experiment"])),
            expected,
        )

        changed_criteria = copy.deepcopy(self.report)
        changed_criteria["experiment"]["items"][0]["hard_criteria"][0] += " altered"
        self.assertNotEqual(
            canonical_sha256(evidence_projection(changed_criteria["experiment"])),
            expected,
        )

        changed_output = copy.deepcopy(self.report)
        candidate = changed_output["experiment"]["items"][0]["candidates"][0]
        candidate["output"] += " altered"
        candidate["output_sha256"] = text_sha256(candidate["output"])
        self.assertNotEqual(
            canonical_sha256(evidence_projection(changed_output["experiment"])),
            expected,
        )

        changed_score = copy.deepcopy(self.report)
        candidate = changed_score["experiment"]["items"][0]["candidates"][0]
        candidate["criteria_pass"][0] = not candidate["criteria_pass"][0]
        self.assertNotEqual(
            canonical_sha256(evidence_projection(changed_score["experiment"])),
            expected,
        )

        changed_disclosure = copy.deepcopy(self.report)
        changed_disclosure["experiment"]["reviewer"]["file_access_boundary_clean"] = True
        self.assertNotEqual(
            canonical_sha256(evidence_projection(changed_disclosure["experiment"])),
            expected,
        )

        changed_human = copy.deepcopy(self.report)
        changed_human["experiment"]["reviewer"]["independent_human"] = True
        self.assertNotEqual(
            canonical_sha256(evidence_projection(changed_human["experiment"])),
            expected,
        )

        changed_model = copy.deepcopy(self.report)
        changed_model["experiment"]["reviewer"]["model"] = "different-model"
        self.assertNotEqual(
            canonical_sha256(evidence_projection(changed_model["experiment"])),
            expected,
        )

        changed_prepared = copy.deepcopy(self.report)
        changed_prepared["experiment"]["prepared_hashes"]["tests"] = "0" * 64
        self.assertNotEqual(
            canonical_sha256(evidence_projection(changed_prepared["experiment"])),
            expected,
        )

        changed_artifact = copy.deepcopy(self.report)
        changed_artifact["experiment"]["artifact_hashes"]["results.json"] = "0" * 64
        self.assertNotEqual(
            canonical_sha256(evidence_projection(changed_artifact["experiment"])),
            expected,
        )


if __name__ == "__main__":
    unittest.main()
