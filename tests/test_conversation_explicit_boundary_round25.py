"""Protect the frozen and published Round 25 conversation confirmation."""

from collections import defaultdict
import copy
import hashlib
import json
from pathlib import Path
import runpy
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
COMPARISON = (
    ROOT
    / "evaluations"
    / "comparisons"
    / "conversation-explicit-boundary-two-arm-18"
)
REPORT_PATH = (
    ROOT
    / "evaluations"
    / "reports"
    / "conversation-explicit-boundary-round-25-confirmatory.json"
)
V1_RUN = (
    ROOT
    / "evaluations"
    / "runs"
    / "conversation-explicit-boundary-two-arm-18-formal-20260913-v1"
)
V2_RUN = (
    ROOT
    / "evaluations"
    / "runs"
    / "conversation-explicit-boundary-two-arm-18-formal-20260913-v2"
)
REVIEW_PATH = COMPARISON / "postscore-decision-review-independent.md"
PREPARE = runpy.run_path(
    str(ROOT / "evaluations" / "promptfoo" / "prepare_skill_comparison.py")
)
RUNNER = runpy.run_path(
    str(ROOT / "evaluations" / "native_resume" / "run_native_resume.py")
)
VALIDATOR = runpy.run_path(str(ROOT / "scripts" / "validate_collection.py"))
EXPECTED_PROJECTION_SHA256 = (
    "d7294dcd2b2e21f9d23ef21aae2d66ae2220e2d67855ac40383ca435aed4a2d6"
)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def sha256_text(value: str) -> str:
    return sha256_bytes(value.encode("utf-8"))


def sha256_object(value: object) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return sha256_bytes(encoded)


def runner_json_sha256(value: object) -> str:
    encoded = (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    return sha256_bytes(encoded)


def evidence_projection(report: dict[str, object]) -> dict[str, object]:
    experiment = report["experiment"]
    return {
        "freeze_commit": experiment["freeze_commit"],
        "execution_infrastructure_commit": experiment[
            "execution_infrastructure_commit"
        ],
        "source_hashes": experiment["source_hashes"],
        "prepared_hashes": experiment["prepared_hashes"],
        "artifact_hashes": experiment["artifact_hashes"],
        "review_chain": experiment["review_chain"],
        "blind_reviewer": experiment["blind_reviewer"],
        "arms": experiment["arms"],
        "items": experiment["items"],
        "invalid_attempt": experiment["invalid_attempt"],
        "analysis": report["analysis"],
        "decision": report["decision"],
    }


def aggregate(report: dict[str, object]) -> dict[str, dict[str, object]]:
    result = {}
    for arm_id in ("baseline", "ours"):
        candidates = [
            candidate
            for item in report["experiment"]["items"]
            for candidate in item["candidates"]
            if candidate["arm_id"] == arm_id
        ]
        total = sum(candidate["total"] for candidate in candidates)
        passed = sum(candidate["passed"] for candidate in candidates)
        result[arm_id] = {
            "outputs": len(candidates),
            "perfect_outputs": sum(
                candidate["passed"] == candidate["total"] for candidate in candidates
            ),
            "criteria_passed": passed,
            "criteria_total": total,
            "preferred_count": sum(candidate["preferred"] for candidate in candidates),
            "criterion_pass_rate": round(passed / total, 4),
        }
    return result


def by_mechanism(report: dict[str, object]) -> dict[str, object]:
    result = defaultdict(dict)
    mechanisms = sorted(
        {item["mechanism"] for item in report["experiment"]["items"]}
    )
    for mechanism in mechanisms:
        for arm_id in ("baseline", "ours"):
            candidates = [
                candidate
                for item in report["experiment"]["items"]
                if item["mechanism"] == mechanism
                for candidate in item["candidates"]
                if candidate["arm_id"] == arm_id
            ]
            result[mechanism][arm_id] = {
                "outputs": len(candidates),
                "perfect_outputs": sum(
                    candidate["passed"] == candidate["total"]
                    for candidate in candidates
                ),
                "criteria_passed": sum(candidate["passed"] for candidate in candidates),
                "criteria_total": sum(candidate["total"] for candidate in candidates),
                "core_criterion_failures": sum(
                    not candidate["criteria_pass"][0] for candidate in candidates
                ),
            }
    return dict(result)


def recompute_gate(
    report: dict[str, object], spec: dict[str, object], cases: list[dict]
) -> dict[str, object]:
    per_case = {}
    qualifying = defaultdict(list)
    for source in cases:
        candidates = [
            candidate
            for item in report["experiment"]["items"]
            if item["case_id"] == source["id"]
            for candidate in item["candidates"]
        ]
        ours_failures = sum(
            not candidate["criteria_pass"][0]
            for candidate in candidates
            if candidate["arm_id"] == "ours"
        )
        baseline_failures = sum(
            not candidate["criteria_pass"][0]
            for candidate in candidates
            if candidate["arm_id"] == "baseline"
        )
        qualifies = (
            ours_failures >= spec["candidate_gate"]["ours_min_failures_per_case"]
            and baseline_failures
            <= spec["candidate_gate"]["baseline_max_failures_per_case"]
        )
        per_case[source["id"]] = {
            "mechanism": source["mechanism"],
            "ours_core_failures": ours_failures,
            "baseline_core_failures": baseline_failures,
            "qualifies": qualifies,
        }
        if qualifies:
            qualifying[source["mechanism"]].append(source["id"])
    mechanisms = sorted({source["mechanism"] for source in cases})
    grouped = {mechanism: qualifying.get(mechanism, []) for mechanism in mechanisms}
    required = spec["candidate_gate"]["cases_per_group"]
    qualifying_mechanisms = [
        mechanism for mechanism in mechanisms if len(grouped[mechanism]) == required
    ]
    return {
        "criterion_index": spec["candidate_gate"]["criterion_index"],
        "ours_min_failures_per_case": spec["candidate_gate"]
        ["ours_min_failures_per_case"],
        "baseline_max_failures_per_case": spec["candidate_gate"]
        ["baseline_max_failures_per_case"],
        "require_all_cases_in_mechanism": spec["candidate_gate"]
        ["require_all_cases_in_group"],
        "per_case": per_case,
        "qualifying_cases_by_mechanism": grouped,
        "qualifying_mechanisms": qualifying_mechanisms,
        "triggered": bool(qualifying_mechanisms),
    }


def percent(to_value: int | float, from_value: int | float) -> float | None:
    if from_value == 0:
        return None
    return round((to_value / from_value - 1) * 100, 1)


def validate_report(report: dict[str, object]) -> None:
    assert report["schema_version"] == 1
    assert report["report_id"] == "conversation-explicit-boundary-round-25-confirmatory"
    assert report["scope"] == {
        "skill_id": "conversation-rehearsal",
        "version": "0.1.1",
        "catalog_status": "experimental",
        "active_case_count": 15,
        "collection_active_case_count": 148,
        "formal_trajectories": 24,
        "formal_turns": 24,
        "blind_review_items": 12,
        "criterion_booleans": 96,
    }

    experiment = report["experiment"]
    assert experiment["freeze_commit"] == "34f959447fbe3d62ebfd9edff6493eb006cc6936"
    assert experiment["execution_infrastructure_commit"] == (
        "a1fe2c8a9d358656c34034dc296b6289fddf117d"
    )
    assert experiment["model"] == "gpt-5.6-sol"
    assert experiment["reasoning_effort"] == "medium"
    assert experiment["planned_repetitions"] == 3
    assert experiment["executed_repetitions"] == 3
    assert experiment["infrastructure_valid"] is True
    assert experiment["session"] == {
        "mode": "explicit-thread-id",
        "history_mode": "native-session-retains-actual-output",
        "resume_last_used": False,
        "ephemeral_used": False,
        "sandbox": "read-only",
        "network_access": False,
        "forbidden_tool_items": 0,
        "agent_message_count_per_turn": 1,
        "expected_trajectories": 24,
        "valid_trajectories": 24,
        "expected_turns": 24,
        "valid_turns": 24,
    }

    spec = json.loads((COMPARISON / "promptfoo.json").read_text(encoding="utf-8"))
    cases = json.loads((COMPARISON / "cases.json").read_text(encoding="utf-8"))
    case_by_id = {case["id"]: case for case in cases}
    assert experiment["source_hashes"] == {
        "promptfoo.json": sha256_file(COMPARISON / "promptfoo.json"),
        "cases.json": sha256_file(COMPARISON / "cases.json"),
    }
    assert experiment["prepared_hashes"] == {
        "config": "a00e231245b63d4939e30d7d6bb5eda20fcfedf1a740929c8c384bc238fcf351",
        "tests": "b31597a950711ab66701cd279a3daa6f6a091e13fc40de2260861fd83158844f",
    }
    review = experiment["review_chain"]["postscore_decision_review"]
    assert review["path"] == REVIEW_PATH.relative_to(ROOT).as_posix()
    assert review["sha256"] == sha256_file(REVIEW_PATH)
    assert review["independent"] is True
    assert review["score_corrections"] == 0

    reviewer = experiment["blind_reviewer"]
    assert reviewer["kind"] == "independent-model-blind-reviewer"
    assert reviewer["model"] == "gpt-5.6-sol"
    assert reviewer["reasoning_effort"] == "medium"
    assert reviewer["blind_file_boundary_clean"] is True
    assert reviewer["blind_to_arm_mapping"] is True
    assert reviewer["unexpected_files_read"] == []
    assert sorted(Path(path).name for path in reviewer["blind_files_read"]) == [
        "blind-review-form.json",
        "blind-review.json",
    ]

    assert len(experiment["items"]) == 12
    seen_review_ids = set()
    seen_trajectories = set()
    for item in experiment["items"]:
        assert item["review_id"] not in seen_review_ids
        seen_review_ids.add(item["review_id"])
        source = case_by_id[item["case_id"]]
        assert item["user_turns"] == source["turns"]
        assert item["user_turns_sha256"] == runner_json_sha256(source["turns"])
        assert item["hard_criteria"] == source["hard_criteria"]
        assert item["mechanism"] == source["mechanism"]
        assert item["purpose"] == source["purpose"]
        assert item["review_notes"].strip()
        assert item["preferred_candidate"] is None
        assert item["preferred_arm"] is None
        assert len(item["candidates"]) == 2
        for candidate in item["candidates"]:
            assert candidate["trajectory_id"] not in seen_trajectories
            seen_trajectories.add(candidate["trajectory_id"])
            assert len(candidate["outputs"]) == 1
            assert candidate["output_sha256s"] == [
                sha256_text(output) for output in candidate["outputs"]
            ]
            assert candidate["turn_technical_valid"] == [True]
            assert candidate["agent_message_counts"] == [1]
            assert candidate["criteria_pass"] == [True, True, True, True]
            assert candidate["passed"] == 4
            assert candidate["total"] == 4
            assert candidate["preferred"] is False
            if candidate["arm_id"] == "baseline":
                assert candidate["skill"] is None
                assert candidate["skill_package_sha256"] is None
            else:
                assert candidate["arm_id"] == "ours"
                assert candidate["skill"] == "conversation-rehearsal"
                assert candidate["skill_package_sha256"] == experiment["arms"][1][
                    "skill_package_sha256"
                ]
    assert len(seen_review_ids) == 12
    assert len(seen_trajectories) == 24

    recomputed = aggregate(report)
    assert report["analysis"]["overall"] == recomputed
    assert recomputed["baseline"]["criteria_passed"] == 48
    assert recomputed["baseline"]["perfect_outputs"] == 12
    assert recomputed["ours"]["criteria_passed"] == 48
    assert recomputed["ours"]["perfect_outputs"] == 12
    for arm in experiment["arms"]:
        assert arm["blind_score"] == recomputed[arm["arm_id"]]
    assert report["analysis"]["by_mechanism"] == by_mechanism(report)
    gate = recompute_gate(report, spec, cases)
    assert report["analysis"]["candidate_gate"] == gate
    assert gate["qualifying_mechanisms"] == []
    assert gate["triggered"] is False

    baseline = experiment["arms"][0]["runtime"]
    ours = experiment["arms"][1]["runtime"]
    baseline_tokens = baseline["tokens_total"]
    ours_tokens = ours["tokens_total"]
    baseline_total = baseline_tokens["input_tokens"] + baseline_tokens["output_tokens"]
    ours_total = ours_tokens["input_tokens"] + ours_tokens["output_tokens"]
    assert report["analysis"]["cost_and_efficiency"] == {
        "ours_vs_baseline": {
            "input_plus_output_tokens": {
                "from": baseline_total,
                "to": ours_total,
                "delta": ours_total - baseline_total,
                "percent": percent(ours_total, baseline_total),
            },
            "input_tokens_percent": percent(
                ours_tokens["input_tokens"], baseline_tokens["input_tokens"]
            ),
            "cached_input_tokens_percent": percent(
                ours_tokens["cached_input_tokens"],
                baseline_tokens["cached_input_tokens"],
            ),
            "output_tokens_percent": percent(
                ours_tokens["output_tokens"], baseline_tokens["output_tokens"]
            ),
            "reasoning_output_tokens": {
                "from": baseline_tokens["reasoning_output_tokens"],
                "to": ours_tokens["reasoning_output_tokens"],
                "delta": ours_tokens["reasoning_output_tokens"]
                - baseline_tokens["reasoning_output_tokens"],
                "percent": percent(
                    ours_tokens["reasoning_output_tokens"],
                    baseline_tokens["reasoning_output_tokens"],
                ),
            },
            "median_latency_percent": percent(
                ours["latency_ms_median_per_turn"],
                baseline["latency_ms_median_per_turn"],
            ),
            "price_or_cost_available": False,
        }
    }

    skill_path = ROOT / "skills" / "relationships" / "conversation-rehearsal"
    assert experiment["arms"][1]["skill_package_sha256"] == VALIDATOR[
        "package_fingerprint"
    ](skill_path)
    invalid = experiment["invalid_attempt"]
    assert invalid["run_id"].endswith("formal-20260913-v1")
    assert invalid["status"] == "infrastructure-invalid"
    assert invalid["quality_scored"] is False
    assert invalid["results_reused_in_scored_run"] is False
    assert invalid["valid_trajectories"] == 23
    assert invalid["invalid_trajectories"] == 1
    assert invalid["invalid_arm_id"] == "ours"
    assert invalid["agent_message_count"] == 2
    assert invalid["output_matches_unique_agent_message"] is False
    assert invalid["skill_read_blocked_by_policy"] is True
    assert invalid["repair_changed_validity_rule"] is False
    assert invalid["repair_commit"] == experiment["execution_infrastructure_commit"]

    decision = report["decision"]
    assert decision["candidate_design_opened"] is False
    assert decision["skill_changed"] is False
    assert decision["version_changed"] is False
    assert decision["status_changed"] is False
    assert decision["evidence_changed"] is False
    assert decision["active_cases_added"] == 4
    assert decision["invalid_attempt_disclosed"] is True

    projection = evidence_projection(report)
    assert experiment["evidence_projection"] == {
        "algorithm": "sha256-canonical-json-v1",
        "sha256": EXPECTED_PROJECTION_SHA256,
    }
    assert sha256_object(projection) == EXPECTED_PROJECTION_SHA256


class ConversationExplicitBoundaryRound25Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec = json.loads(
            (COMPARISON / "promptfoo.json").read_text(encoding="utf-8")
        )
        cls.cases = json.loads(
            (COMPARISON / "cases.json").read_text(encoding="utf-8")
        )
        cls.report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))

    def test_frozen_design_has_two_paired_mechanisms(self):
        self.assertEqual(
            self.spec["id"], "conversation-explicit-boundary-two-arm-18"
        )
        self.assertEqual(self.spec["model"], "gpt-5.6-sol")
        self.assertEqual(self.spec["reasoning_effort"], "medium")
        self.assertEqual(self.spec["repetitions"], 3)
        self.assertEqual([arm["id"] for arm in self.spec["arms"]], ["baseline", "ours"])

        case_ids = [case["id"] for case in self.cases]
        self.assertEqual(len(case_ids), len(set(case_ids)))
        mechanisms = {}
        for case in self.cases:
            mechanisms.setdefault(case["mechanism"], []).append(case["id"])
            self.assertEqual(case["prompt"], case["turns"][0])
            self.assertEqual(len(case["turns"]), 1)
            self.assertEqual(len(case["hard_criteria"]), 4)
            for criterion in case["hard_criteria"]:
                self.assertNotIn(criterion, case["prompt"])
        self.assertEqual(
            {name: len(ids) for name, ids in mechanisms.items()},
            {"explicit-boundary-clarity": 2, "generalized-fiction-control": 2},
        )
        self.assertEqual(len(self.cases) * len(self.spec["arms"]) * 3, 24)
        self.assertEqual(
            sum(len(case["turns"]) for case in self.cases)
            * len(self.spec["arms"])
            * 3,
            24,
        )
        self.assertEqual(
            sum(len(case["hard_criteria"]) for case in self.cases)
            * len(self.spec["arms"])
            * 3,
            96,
        )

    def test_candidate_gate_is_mechanism_paired_and_failure_specific(self):
        self.assertEqual(
            self.spec["candidate_gate"],
            {
                "group_field": "mechanism",
                "cases_per_group": 2,
                "criterion_index": 0,
                "ours_arm": "ours",
                "baseline_arm": "baseline",
                "ours_min_failures_per_case": 2,
                "baseline_max_failures_per_case": 1,
                "require_all_cases_in_group": True,
                "opens_candidate_design_only": True,
            },
        )

    def test_prepare_binds_sources_fixtures_and_prompt_isolation(self):
        runs_root = ROOT / "evaluations" / "runs"
        runs_root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=runs_root) as temporary:
            run_dir = Path(temporary) / "run"
            PREPARE["prepare_comparison"](
                ROOT,
                COMPARISON / "promptfoo.json",
                run_dir,
            )
            frozen = json.loads(
                (run_dir / "frozen.json").read_text(encoding="utf-8")
            )
            tests = json.loads(
                (run_dir / "prepared" / "tests.json").read_text(encoding="utf-8")
            )
            self.assertEqual(
                frozen["spec_sha256"], sha256_file(COMPARISON / "promptfoo.json")
            )
            self.assertEqual(
                frozen["cases_sha256"], sha256_file(COMPARISON / "cases.json")
            )
            self.assertEqual(
                frozen["arms"][1]["skill_package_sha256"],
                VALIDATOR["package_fingerprint"](
                    ROOT / "skills" / "relationships" / "conversation-rehearsal"
                ),
            )
            manifests = RUNNER["verify_execution_fixtures"](run_dir, frozen)
            self.assertEqual(manifests["baseline"], {})
            self.assertEqual(
                list(manifests["ours"]),
                [
                    ".agents/skills/conversation-rehearsal/SKILL.md",
                    ".agents/skills/conversation-rehearsal/references/example.md",
                ],
            )

            self.assertEqual(len(tests), 8)
            prompts = RUNNER["load_prepared_prompts"](run_dir, frozen)
            all_criteria = [
                criterion
                for case in self.cases
                for criterion in case["hard_criteria"]
            ]
            for test in tests:
                self.assertEqual(set(test["vars"]), {"prompt"})
                self.assertTrue(
                    all(
                        criterion not in test["vars"]["prompt"]
                        for criterion in all_criteria
                    )
                )
            for case in self.cases:
                baseline = prompts[(case["id"], "baseline")]
                ours = prompts[(case["id"], "ours")]
                self.assertNotIn("$conversation-rehearsal", baseline)
                self.assertIn("$conversation-rehearsal", ours)
                self.assertTrue(baseline.endswith(case["turns"][0]))
                self.assertTrue(ours.endswith(case["turns"][0]))

    def test_published_report_recomputes(self):
        validate_report(self.report)

    def test_active_cases_and_catalog_state_match_report(self):
        active = json.loads(
            (ROOT / "evaluations" / "cases" / "conversation-rehearsal.json").read_text(
                encoding="utf-8"
            )
        )
        active_by_id = {case["id"]: case for case in active["cases"]}
        self.assertGreaterEqual(
            len(active_by_id), self.report["scope"]["active_case_count"]
        )
        for source in self.cases:
            promoted = active_by_id[source["id"]]
            prepared = self.spec["common_prompt"] + "\n\n" + source["turns"][0]
            self.assertEqual(promoted["prompt"], prepared)
            self.assertEqual(promoted["input"], {"kind": "synthetic", "steps": [prepared]})
            self.assertEqual(promoted["expected_route"], "conversation-rehearsal")
            self.assertEqual(promoted["must_include"], source["hard_criteria"])
            self.assertEqual(len(promoted["must_avoid"]), 3)
            self.assertTrue(all(value.strip() for value in promoted["must_avoid"]))

        catalog = json.loads(
            (ROOT / "catalog" / "collection.json").read_text(encoding="utf-8")
        )
        entry = next(
            item for item in catalog["skills"] if item["id"] == "conversation-rehearsal"
        )
        self.assertEqual(entry["version"], "0.1.1")
        self.assertEqual(entry["status"], "experimental")
        self.assertIsNone(entry["evidence"])

        total = 0
        for path in (ROOT / "evaluations" / "cases").glob("*.json"):
            suite = json.loads(path.read_text(encoding="utf-8"))
            if suite.get("stage") == "active":
                total += len(suite.get("cases", []))
        self.assertGreaterEqual(
            total, self.report["scope"]["collection_active_case_count"]
        )

    def test_local_raw_run_hashes_match_when_artifacts_are_available(self):
        if not V2_RUN.exists() or not V1_RUN.exists():
            self.skipTest("ignored raw Round 25 runs are not present in this checkout")
        for name, expected in self.report["experiment"]["artifact_hashes"].items():
            with self.subTest(run="v2", artifact=name):
                self.assertEqual(sha256_file(V2_RUN / name), expected)
        invalid = self.report["experiment"]["invalid_attempt"]
        for name, expected in invalid["artifact_hashes"].items():
            with self.subTest(run="v1", artifact=name):
                self.assertEqual(sha256_file(V1_RUN / name), expected)

        v1_results = json.loads(
            (V1_RUN / "native-results.json").read_text(encoding="utf-8")
        )
        failed = [item for item in v1_results["trajectories"] if not item["technical_valid"]]
        self.assertEqual(len(failed), 1)
        self.assertEqual(failed[0]["trajectory_id"], invalid["invalid_trajectory_id"])
        turn = failed[0]["turns"][0]
        self.assertEqual(len(turn["agent_messages"]), 2)
        self.assertFalse(turn["output_matches_last_agent_message"])
        self.assertIn("blocked by policy", turn["stderr"])

    def test_coordinated_evidence_mutations_are_rejected(self):
        mutations = []
        changed_output = copy.deepcopy(self.report)
        changed_output["experiment"]["items"][0]["candidates"][0]["outputs"][0] += " "
        mutations.append(changed_output)
        changed_score = copy.deepcopy(self.report)
        changed_score["experiment"]["items"][0]["candidates"][0]["criteria_pass"][0] = False
        mutations.append(changed_score)
        changed_gate = copy.deepcopy(self.report)
        changed_gate["analysis"]["candidate_gate"]["triggered"] = True
        mutations.append(changed_gate)
        changed_failed_run = copy.deepcopy(self.report)
        changed_failed_run["experiment"]["invalid_attempt"]["quality_scored"] = True
        mutations.append(changed_failed_run)
        changed_review = copy.deepcopy(self.report)
        changed_review["experiment"]["review_chain"]["postscore_decision_review"][
            "sha256"
        ] = "0" * 64
        mutations.append(changed_review)
        for index, mutated in enumerate(mutations):
            mutated["experiment"]["evidence_projection"]["sha256"] = sha256_object(
                evidence_projection(mutated)
            )
            with self.subTest(mutation=index):
                with self.assertRaises(AssertionError):
                    validate_report(mutated)


if __name__ == "__main__":
    unittest.main()
