"""Integrity checks for the Round 29 article visual planning report."""

import copy
import hashlib
import json
from pathlib import Path, PureWindowsPath
import re
import runpy
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]
COMPARISON = (
    ROOT / "evaluations" / "comparisons" / "article-visual-plan-three-arm-22"
)
REPORT_PATH = (
    ROOT
    / "evaluations"
    / "reports"
    / "article-visual-plan-three-arm-round-29-diagnostic.json"
)
FORMAL_RUN = (
    ROOT
    / "evaluations"
    / "runs"
    / "article-visual-plan-three-arm-22-formal-20260913-v1"
)
PREFLIGHT_RUN = (
    ROOT
    / "evaluations"
    / "runs"
    / "article-visual-plan-three-arm-22-preflight-20260913-v1"
)
ACTIVE_CASES = ROOT / "evaluations" / "cases" / "article-visual-plan.json"
SKILL_PACKAGE = ROOT / "skills" / "creation" / "article-visual-plan"
UPSTREAM_COMMIT = "6b7a2e417500561a5ecdd0b168332f4142584617"
UPSTREAM_FIXTURE = (
    ROOT
    / "evaluations"
    / "fixtures"
    / "upstreams"
    / "baoyu-skills"
    / UPSTREAM_COMMIT
)
EXPECTED_PROJECTION_SHA256 = (
    "e7b528f9efdc6f80e4668082c830e4ff6d5061497253e92d08db91bf96d13c52"
)
VALIDATOR = runpy.run_path(str(ROOT / "scripts" / "validate_collection.py"))
ARM_ORDER = {"baseline": 0, "ours": 1, "upstream": 2}


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def sha256_object(value: object) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return sha256_bytes(encoded)


def evidence_projection(report: dict[str, object]) -> dict[str, object]:
    return {
        key: report[key]
        for key in ("scope", "experiment", "analysis", "decision", "limitations")
    }


def validate_public_round29_semantics(report: dict[str, object]) -> None:
    assert report["schema_version"] == 1
    assert report["report_id"] == (
        "article-visual-plan-three-arm-round-29-diagnostic"
    )
    scope = report["scope"]
    assert scope["formal_outputs"] == 54
    assert scope["blind_review_items"] == 18
    assert scope["criterion_booleans"] == 216

    experiment = report["experiment"]
    assert experiment["freeze_commit"] == (
        "527fccee203bbc3f18515c4d2c7c2881f8a7d1b0"
    )
    assert experiment["model"] == "gpt-5.6-sol"
    assert experiment["reasoning_effort"] == "medium"
    assert experiment["planned_repetitions"] == 3
    assert experiment["executed_repetitions"] == 3
    assert experiment["infrastructure_valid"] is True
    assert experiment["blind_reviewer"] == {
        "kind": "model-assisted-independent-task",
        "task_name": "round29_blind_review",
        "model": "gpt-5.6-sol",
        "reasoning_effort": "medium",
        "independent_human": False,
        "blind_to_arm_mapping": True,
        "prior_protocol_exposure": True,
        "prior_skill_revision_exposure": True,
        "allowed_files": ["blind-review.json", "blind-review-form.json"],
        "blind_file_boundary_clean": True,
        "unexpected_files_read": [],
    }

    expected_skills = {
        "baseline": None,
        "ours": "article-visual-plan",
        "upstream": "baoyu-article-illustrator",
    }
    seen_reviews = set()
    aggregates = {
        arm: {
            "outputs": 0,
            "perfect_outputs": 0,
            "criteria_passed": 0,
            "criteria_total": 0,
            "preferred_count": 0,
        }
        for arm in ARM_ORDER
    }
    for item in experiment["items"]:
        assert item["review_id"] not in seen_reviews
        seen_reviews.add(item["review_id"])
        assert item["review_id"] == f'{item["case_id"]}-r{item["repetition"]}'
        assert item["repetition"] in (1, 2, 3)
        assert {candidate["arm_id"] for candidate in item["candidates"]} == set(
            ARM_ORDER
        )
        for candidate in item["candidates"]:
            arm = candidate["arm_id"]
            criteria = candidate["criteria_pass"]
            assert candidate["skill"] == expected_skills[arm]
            assert len(criteria) == 4
            assert candidate["output_sha256"] == sha256_bytes(
                candidate["output"].encode("utf-8")
            )
            assert candidate["passed"] == sum(criteria)
            assert candidate["total"] == len(criteria)
            assert candidate["core_failure"] is False
            assert candidate["preferred"] is False
            aggregates[arm]["outputs"] += 1
            aggregates[arm]["perfect_outputs"] += candidate["passed"] == 4
            aggregates[arm]["criteria_passed"] += candidate["passed"]
            aggregates[arm]["criteria_total"] += candidate["total"]
            aggregates[arm]["preferred_count"] += candidate["preferred"]

    assert len(seen_reviews) == 18
    published_arms = {arm["arm_id"]: arm for arm in experiment["arms"]}
    assert set(published_arms) == set(ARM_ORDER)
    for arm, aggregate in aggregates.items():
        assert aggregate == {
            "outputs": 18,
            "perfect_outputs": 18,
            "criteria_passed": 72,
            "criteria_total": 72,
            "preferred_count": 0,
        }
        blind = published_arms[arm]["blind_review"]
        assert blind == {
            "arm_id": arm,
            "skill": expected_skills[arm],
            **aggregate,
            "criterion_pass_rate": 1.0,
        }
        runtime = published_arms[arm]["runtime"]
        assert runtime["id"] == arm
        assert runtime["rows"] == 18
        assert runtime["promptfoo_passed_rows"] == 18
        assert runtime["provider_errors"] == 0
        assert runtime["forbidden_tool_rows"] == 0

    analysis = report["analysis"]
    assert analysis["valid_output_count"] == 54
    assert analysis["all_preferences_tied"] is True
    assert analysis["ceiling_effect"] is True
    assert all(
        failures == {"baseline": 0, "ours": 0, "upstream": 0}
        for failures in analysis["case_core_failures"].values()
    )
    assert all(item["triggered"] is False for item in analysis["mechanisms"])

    decision = report["decision"]
    assert decision["candidate_design_open"] is False
    assert decision["skill_changed"] is False
    assert decision["version_changed"] is False
    assert decision["verification_status_changed"] is False
    assert decision["current_version"] == "0.1.0"
    assert decision["current_catalog_status"] == "experimental"
    assert decision["current_catalog_evidence"] is None

    assert sha256_object(evidence_projection(report)) == report[
        "evidence_projection_sha256"
    ]
    assert report["evidence_projection_sha256"] == EXPECTED_PROJECTION_SHA256


class ArticleVisualRound29Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
        cls.protocol = json.loads(
            (COMPARISON / "promptfoo.json").read_text(encoding="utf-8")
        )
        cls.frozen_cases = json.loads(
            (COMPARISON / "cases.json").read_text(encoding="utf-8")
        )

    def test_report_scope_and_source_bindings_match_repository(self):
        report = self.report
        self.assertEqual(report["schema_version"], 1)
        self.assertEqual(
            report["report_id"],
            "article-visual-plan-three-arm-round-29-diagnostic",
        )
        self.assertEqual(
            report["scope"],
            {
                "skill_id": "article-visual-plan",
                "version": "0.1.0",
                "catalog_status": "experimental",
                "catalog_evidence": None,
                "prior_active_case_count": 4,
                "active_case_count": 10,
                "collection_active_case_count": 154,
                "formal_outputs": 54,
                "blind_review_items": 18,
                "criterion_booleans": 216,
            },
        )
        experiment = report["experiment"]
        self.assertEqual(experiment["comparison_id"], self.protocol["id"])
        self.assertEqual(experiment["model"], self.protocol["model"])
        self.assertEqual(
            experiment["reasoning_effort"], self.protocol["reasoning_effort"]
        )
        self.assertEqual(experiment["planned_repetitions"], 3)
        self.assertEqual(experiment["executed_repetitions"], 3)
        self.assertTrue(experiment["infrastructure_valid"])

        bindings = experiment["source_hashes"]
        source_paths = {
            "promptfoo.json": COMPARISON / "promptfoo.json",
            "cases.json": COMPARISON / "cases.json",
            "active-cases.json": ACTIVE_CASES,
            "SKILL.md": SKILL_PACKAGE / "SKILL.md",
            "upstream-provenance.json": UPSTREAM_FIXTURE / "provenance.json",
        }
        self.assertEqual(set(bindings), set(source_paths))
        for name, path in source_paths.items():
            self.assertEqual(sha256_file(path), bindings[name], name)

        for name, expected in experiment["review_hashes"].items():
            self.assertEqual(sha256_file(COMPARISON / name), expected, name)

    def test_public_items_recompute_to_three_equal_ceiling_arms(self):
        case_by_id = {case["id"]: case for case in self.frozen_cases}
        aggregates = {
            arm: {
                "outputs": 0,
                "perfect_outputs": 0,
                "criteria_passed": 0,
                "criteria_total": 0,
                "preferred_count": 0,
            }
            for arm in ("baseline", "ours", "upstream")
        }
        core_failures = {
            case_id: {arm: 0 for arm in aggregates} for case_id in case_by_id
        }
        items = self.report["experiment"]["items"]
        self.assertEqual(len(items), 18)
        self.assertEqual(len({item["review_id"] for item in items}), 18)
        for item in items:
            source_case = case_by_id[item["case_id"]]
            self.assertEqual(item["mechanism"], source_case["mechanism"])
            self.assertIn(item["repetition"], (1, 2, 3))
            self.assertEqual(
                {candidate["arm_id"] for candidate in item["candidates"]},
                set(aggregates),
            )
            for candidate in item["candidates"]:
                arm = candidate["arm_id"]
                criteria = candidate["criteria_pass"]
                passed = sum(criteria)
                core_failure = any(
                    not criteria[index] for index in source_case["core_criteria"]
                )
                self.assertEqual(len(criteria), 4)
                self.assertEqual(sha256_bytes(candidate["output"].encode()), candidate["output_sha256"])
                self.assertEqual(candidate["passed"], passed)
                self.assertEqual(candidate["total"], len(criteria))
                self.assertEqual(candidate["core_failure"], core_failure)
                aggregates[arm]["outputs"] += 1
                aggregates[arm]["perfect_outputs"] += passed == len(criteria)
                aggregates[arm]["criteria_passed"] += passed
                aggregates[arm]["criteria_total"] += len(criteria)
                aggregates[arm]["preferred_count"] += candidate["preferred"]
                core_failures[item["case_id"]][arm] += core_failure

        published_arms = {
            arm["arm_id"]: arm["blind_review"]
            for arm in self.report["experiment"]["arms"]
        }
        for arm, aggregate in aggregates.items():
            expected = {"arm_id": arm, **aggregate, "criterion_pass_rate": 1.0}
            expected["skill"] = published_arms[arm]["skill"]
            self.assertEqual(published_arms[arm], expected)
            self.assertEqual(aggregate["outputs"], 18)
            self.assertEqual(aggregate["perfect_outputs"], 18)
            self.assertEqual(aggregate["criteria_passed"], 72)
            self.assertEqual(aggregate["preferred_count"], 0)

        self.assertEqual(self.report["analysis"]["case_core_failures"], core_failures)
        self.assertTrue(self.report["analysis"]["all_preferences_tied"])
        self.assertTrue(self.report["analysis"]["ceiling_effect"])

    def test_frozen_gate_recomputes_false_for_every_mechanism(self):
        failures = self.report["analysis"]["case_core_failures"]
        protocol_gate = self.protocol["decision_gate"]
        by_mechanism: dict[str, list[str]] = {}
        for case in self.frozen_cases:
            by_mechanism.setdefault(case["mechanism"], []).append(case["id"])

        published = {
            item["mechanism"]: item
            for item in self.report["analysis"]["mechanisms"]
        }
        self.assertEqual(set(published), set(by_mechanism))
        for mechanism, case_ids in by_mechanism.items():
            ours_met = all(
                failures[case_id]["ours"]
                >= protocol_gate["ours_min_core_failures_per_case"]
                for case_id in case_ids
            )
            baseline_met = all(
                failures[case_id]["baseline"]
                <= protocol_gate["baseline_max_core_failures_per_case"]
                for case_id in case_ids
            )
            self.assertEqual(len(case_ids), protocol_gate["minimum_cases_in_same_mechanism"])
            self.assertEqual(published[mechanism]["ours_threshold_met"], ours_met)
            self.assertEqual(
                published[mechanism]["baseline_threshold_met"], baseline_met
            )
            self.assertEqual(
                published[mechanism]["triggered"], ours_met and baseline_met
            )
            self.assertFalse(published[mechanism]["triggered"])
        self.assertEqual(self.report["analysis"]["decision_gate"], protocol_gate)
        self.assertEqual(self.report["analysis"]["valid_output_count"], 54)
        self.assertFalse(self.report["decision"]["candidate_design_open"])

    def test_efficiency_percentages_recompute_from_runtime_summaries(self):
        arms = {
            item["arm_id"]: item["runtime"]
            for item in self.report["experiment"]["arms"]
        }

        def percent(comparison: str, reference: str, field: str) -> float:
            if field == "tokens_total":
                numerator = arms[comparison][field]["total"]
                denominator = arms[reference][field]["total"]
            else:
                numerator = arms[comparison][field]
                denominator = arms[reference][field]
            return round((numerator / denominator - 1) * 100, 1)

        expected = {
            "ours_vs_baseline_percent": {
                field: percent("ours", "baseline", field)
                for field in ("tokens_total", "cost_total", "latency_ms_median")
            },
            "upstream_vs_baseline_percent": {
                field: percent("upstream", "baseline", field)
                for field in ("tokens_total", "cost_total", "latency_ms_median")
            },
            "ours_vs_upstream_percent": {
                field: percent("ours", "upstream", field)
                for field in ("tokens_total", "cost_total", "latency_ms_median")
            },
        }
        published = self.report["analysis"]["efficiency"]
        for key, values in expected.items():
            self.assertEqual(published[key], values)

    def test_regression_cases_are_forward_only_and_catalog_stays_experimental(self):
        active = json.loads(ACTIVE_CASES.read_text(encoding="utf-8"))
        active_by_id = {case["id"]: case for case in active["cases"]}
        self.assertEqual(len(active_by_id), 10)
        for case in self.frozen_cases:
            published = active_by_id[case["id"]]
            self.assertEqual(published["prompt"], case["prompt"])
            self.assertEqual(published["must_include"], case["hard_criteria"])
            self.assertEqual(published["expected_route"], "article-visual-plan")

        catalog = json.loads(
            (ROOT / "catalog" / "collection.json").read_text(encoding="utf-8")
        )
        entry = next(item for item in catalog["skills"] if item["id"] == "article-visual-plan")
        self.assertEqual(entry["version"], "0.1.0")
        self.assertEqual(entry["status"], "experimental")
        self.assertIsNone(entry["evidence"])
        total = sum(
            len(json.loads((ROOT / item["evaluation"]).read_text(encoding="utf-8"))["cases"])
            for item in catalog["skills"]
        )
        self.assertEqual(total, 154)
        decision = self.report["decision"]
        self.assertEqual(decision["active_case_count_after"], len(active_by_id))
        self.assertEqual(decision["active_cases_sha256"], sha256_file(ACTIVE_CASES))
        self.assertFalse(decision["skill_changed"])
        self.assertFalse(decision["version_changed"])
        self.assertFalse(decision["verification_status_changed"])

    def test_skill_and_upstream_package_fingerprints_are_bound(self):
        decision = self.report["decision"]
        ours = VALIDATOR["package_fingerprint"](SKILL_PACKAGE)
        upstream_package = UPSTREAM_FIXTURE / "skills" / "baoyu-article-illustrator"
        upstream = VALIDATOR["package_fingerprint"](upstream_package)
        self.assertEqual(ours, decision["skill_package_sha256"])
        self.assertEqual(
            ours,
            next(
                arm["skill_package_sha256"]
                for arm in self.report["experiment"]["arms"]
                if arm["arm_id"] == "ours"
            ),
        )
        provenance = self.report["experiment"]["upstream_provenance"]
        self.assertEqual(provenance["commit"], UPSTREAM_COMMIT)
        self.assertEqual(provenance["license"], "MIT")
        self.assertTrue(provenance["package_license_included"])
        self.assertFalse(provenance["source_bytes_modified"])
        self.assertEqual(provenance["package_sha256"], upstream)
        self.assertEqual(
            provenance["provenance_sha256"],
            sha256_file(UPSTREAM_FIXTURE / "provenance.json"),
        )

    def test_evidence_projection_is_fixed_and_report_has_no_local_path(self):
        validate_public_round29_semantics(self.report)
        self.assertEqual(
            sha256_object(evidence_projection(self.report)),
            self.report["evidence_projection_sha256"],
        )
        self.assertEqual(
            self.report["evidence_projection_sha256"], EXPECTED_PROJECTION_SHA256
        )
        rendered = REPORT_PATH.read_text(encoding="utf-8")
        self.assertIsNone(re.search(r"[A-Za-z]:\\\\", rendered))
        self.assertNotIn("C:\\Users", rendered)
        self.assertNotIn("D:\\Code", rendered)
        self.assertNotIn("15005", rendered)
        self.assertNotIn("thread_id", rendered)

    def test_freeze_commit_exists_and_is_an_ancestor_when_git_is_available(self):
        if not (ROOT / ".git").exists():
            self.skipTest("Git metadata is not available in this checkout")
        commit = self.report["experiment"]["freeze_commit"]
        object_type = subprocess.run(
            ["git", "cat-file", "-t", commit],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertEqual(object_type.stdout.strip(), "commit")
        subprocess.run(
            ["git", "merge-base", "--is-ancestor", commit, "HEAD"],
            cwd=ROOT,
            check=True,
            capture_output=True,
        )
        frozen_paths = {
            "promptfoo.json": "evaluations/comparisons/article-visual-plan-three-arm-22/promptfoo.json",
            "cases.json": "evaluations/comparisons/article-visual-plan-three-arm-22/cases.json",
            "SKILL.md": "skills/creation/article-visual-plan/SKILL.md",
            "upstream-provenance.json": (
                "evaluations/fixtures/upstreams/baoyu-skills/"
                f"{UPSTREAM_COMMIT}/provenance.json"
            ),
        }
        for name, path in frozen_paths.items():
            content = subprocess.run(
                ["git", "show", f"{commit}:{path}"],
                cwd=ROOT,
                check=True,
                capture_output=True,
            ).stdout
            self.assertEqual(
                sha256_bytes(content),
                self.report["experiment"]["source_hashes"][name],
                name,
            )

    def test_coordinated_public_evidence_mutations_are_rejected(self):
        mutations = []

        changed_score = copy.deepcopy(self.report)
        candidate = changed_score["experiment"]["items"][0]["candidates"][1]
        candidate["output"] += " [tampered]"
        candidate["output_sha256"] = sha256_bytes(candidate["output"].encode("utf-8"))
        candidate["criteria_pass"][0] = False
        candidate["passed"] = 3
        candidate["core_failure"] = True
        changed_score["experiment"]["arms"][1]["blind_review"].update(
            {
                "perfect_outputs": 17,
                "criteria_passed": 71,
                "criterion_pass_rate": 71 / 72,
            }
        )
        changed_score["analysis"]["ceiling_effect"] = False
        mutations.append(changed_score)

        changed_mapping = copy.deepcopy(self.report)
        first_candidates = changed_mapping["experiment"]["items"][0]["candidates"]
        first_candidates[0]["arm_id"], first_candidates[1]["arm_id"] = (
            first_candidates[1]["arm_id"],
            first_candidates[0]["arm_id"],
        )
        mutations.append(changed_mapping)

        changed_runtime = copy.deepcopy(self.report)
        changed_runtime["experiment"]["arms"][1]["runtime"]["tokens_total"][
            "total"
        ] += 1000
        changed_runtime["analysis"]["efficiency"]["ours_vs_baseline_percent"][
            "tokens_total"
        ] = round(
            (
                changed_runtime["experiment"]["arms"][1]["runtime"][
                    "tokens_total"
                ]["total"]
                / changed_runtime["experiment"]["arms"][0]["runtime"][
                    "tokens_total"
                ]["total"]
                - 1
            )
            * 100,
            1,
        )
        mutations.append(changed_runtime)

        changed_reviewer = copy.deepcopy(self.report)
        changed_reviewer["experiment"]["blind_reviewer"]["independent_human"] = True
        mutations.append(changed_reviewer)

        changed_decision = copy.deepcopy(self.report)
        changed_decision["decision"]["candidate_design_open"] = True
        changed_decision["decision"]["skill_changed"] = True
        mutations.append(changed_decision)

        changed_freeze = copy.deepcopy(self.report)
        changed_freeze["experiment"]["freeze_commit"] = "0" * 40
        mutations.append(changed_freeze)

        for index, mutated in enumerate(mutations):
            mutated["evidence_projection_sha256"] = sha256_object(
                evidence_projection(mutated)
            )
            with self.subTest(mutation=index):
                with self.assertRaises(AssertionError):
                    validate_public_round29_semantics(mutated)

    def test_ignored_runs_reproject_to_public_evidence_when_present(self):
        if not FORMAL_RUN.is_dir():
            self.skipTest("ignored Round 29 formal run is not available")
        experiment = self.report["experiment"]
        for name, expected in experiment["artifact_hashes"].items():
            self.assertEqual(sha256_file(FORMAL_RUN / name), expected, name)
        self.assertEqual(
            sha256_file(FORMAL_RUN / "prepared" / "promptfooconfig.json"),
            experiment["prepared_hashes"]["config"],
        )
        self.assertEqual(
            sha256_file(FORMAL_RUN / "prepared" / "tests.json"),
            experiment["prepared_hashes"]["tests"],
        )

        summary = json.loads((FORMAL_RUN / "summary.json").read_text(encoding="utf-8"))
        packet = json.loads(
            (FORMAL_RUN / "blind-review.json").read_text(encoding="utf-8")
        )
        key = json.loads(
            (FORMAL_RUN / "blind-review-key.json").read_text(encoding="utf-8")
        )
        completed = json.loads(
            (
                FORMAL_RUN / "blind-review-completed-independent.json"
            ).read_text(encoding="utf-8")
        )
        scored = json.loads(
            (
                FORMAL_RUN
                / "review-result-blind-review-completed-independent.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(scored["review_sha256"], sha256_file(
            FORMAL_RUN / "blind-review-completed-independent.json"
        ))
        self.assertEqual(scored["reviewer"], completed["reviewer"])

        summary_arms = {arm["id"]: arm for arm in summary["arms"]}
        scored_arms = {arm["arm_id"]: arm for arm in scored["arms"]}
        for public_arm in experiment["arms"]:
            arm = public_arm["arm_id"]
            self.assertEqual(public_arm["runtime"], summary_arms[arm])
            self.assertEqual(public_arm["blind_review"], scored_arms[arm])

        packet_by_id = {item["review_id"]: item for item in packet["items"]}
        key_by_id = {item["review_id"]: item for item in key["items"]}
        completed_by_id = {
            item["review_id"]: item for item in completed["reviews"]
        }
        scored_by_id = {item["review_id"]: item for item in scored["items"]}
        frozen_by_id = {case["id"]: case for case in self.frozen_cases}
        expected_items = []
        for review_id in sorted(packet_by_id):
            packet_item = packet_by_id[review_id]
            key_candidates = {
                candidate["candidate_id"]: candidate
                for candidate in key_by_id[review_id]["candidates"]
            }
            completed_item = completed_by_id[review_id]
            scored_candidates = {
                candidate["candidate_id"]: candidate
                for candidate in scored_by_id[review_id]["candidates"]
            }
            case = frozen_by_id[packet_item["case_id"]]
            candidates = []
            for packet_candidate in packet_item["candidates"]:
                candidate_id = packet_candidate["candidate_id"]
                identity = key_candidates[candidate_id]
                score = scored_candidates[candidate_id]
                criteria = completed_item["criteria_pass"][candidate_id]
                self.assertEqual(score["arm_id"], identity["arm_id"])
                self.assertEqual(score["criteria_pass"], criteria)
                self.assertEqual(score["passed"], sum(criteria))
                self.assertEqual(score["total"], len(criteria))
                candidates.append(
                    {
                        "arm_id": identity["arm_id"],
                        "skill": identity["skill"],
                        "output": packet_candidate["output"],
                        "output_sha256": sha256_bytes(
                            packet_candidate["output"].encode("utf-8")
                        ),
                        "criteria_pass": criteria,
                        "passed": score["passed"],
                        "total": score["total"],
                        "core_failure": any(
                            not criteria[index] for index in case["core_criteria"]
                        ),
                        "preferred": completed_item["preferred_candidate"]
                        == candidate_id,
                    }
                )
            expected_items.append(
                {
                    "review_id": review_id,
                    "case_id": packet_item["case_id"],
                    "mechanism": case["mechanism"],
                    "repetition": packet_item["repetition"],
                    "candidates": sorted(
                        candidates, key=lambda item: ARM_ORDER[item["arm_id"]]
                    ),
                }
            )
        self.assertEqual(experiment["items"], expected_items)

        expected_reviewer = copy.deepcopy(completed["reviewer"])
        expected_reviewer["allowed_files"] = [
            PureWindowsPath(path).name for path in expected_reviewer["allowed_files"]
        ]
        self.assertEqual(experiment["blind_reviewer"], expected_reviewer)
        self.assertEqual(summary["blind_review"]["key_sha256"], sha256_file(
            FORMAL_RUN / "blind-review-key.json"
        ))
        self.assertEqual(summary["blind_review"]["packet_sha256"], sha256_file(
            FORMAL_RUN / "blind-review.json"
        ))
        self.assertEqual(summary["blind_review"]["form_sha256"], sha256_file(
            FORMAL_RUN / "blind-review-form.json"
        ))
        if PREFLIGHT_RUN.is_dir():
            self.assertEqual(
                sha256_file(PREFLIGHT_RUN / "summary.json"),
                experiment["preflight"]["summary_sha256"],
            )


if __name__ == "__main__":
    unittest.main()
