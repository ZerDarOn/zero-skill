"""Protect the published Round 24 native conversation-resume diagnostic."""

from collections import defaultdict
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
    / "conversation-native-resume-round-24-diagnostic.json"
)
COMPARISON = (
    ROOT
    / "evaluations"
    / "comparisons"
    / "conversation-native-resume-two-arm-17"
)
RUN_DIR = (
    ROOT
    / "evaluations"
    / "runs"
    / "conversation-native-resume-two-arm-17-formal-20260913-v1"
)
REVIEW_FILES = {
    "raw_postscore_review": "postscore-decision-review-independent.md",
    "final_engineering_review": "final-engineering-review-independent.md",
    "scoring_adjudication": "scoring-adjudication-independent.md",
}
VALIDATOR = runpy.run_path(str(ROOT / "scripts" / "validate_collection.py"))
EXPECTED_PROJECTION_SHA256 = (
    "7e0234465a1c9c3b7ab49bd395b4e0e2a33fb5f76e703f7de826df931c946394"
)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_text(value: str) -> str:
    return sha256_bytes(value.encode("utf-8"))


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


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
        "source_hashes": experiment["source_hashes"],
        "prepared_hashes": experiment["prepared_hashes"],
        "artifact_hashes": experiment["artifact_hashes"],
        "review_chain": experiment["review_chain"],
        "blind_reviewer": experiment["blind_reviewer"],
        "arms": experiment["arms"],
        "items": experiment["items"],
        "analysis": report["analysis"],
        "decision": report["decision"],
    }


def aggregate(report: dict[str, object], field: str) -> dict[str, dict[str, object]]:
    result = {}
    for arm_id in ("baseline", "ours"):
        candidates = [
            candidate
            for item in report["experiment"]["items"]
            for candidate in item["candidates"]
            if candidate["arm_id"] == arm_id
        ]
        result[arm_id] = {
            "outputs": len(candidates),
            "perfect_outputs": sum(all(candidate[field]) for candidate in candidates),
            "criteria_passed": sum(sum(candidate[field]) for candidate in candidates),
            "criteria_total": sum(len(candidate[field]) for candidate in candidates),
            "preferred_count": sum(candidate["preferred"] for candidate in candidates),
        }
        result[arm_id]["criterion_pass_rate"] = round(
            result[arm_id]["criteria_passed"] / result[arm_id]["criteria_total"], 4
        )
    return result


def by_mechanism(report: dict[str, object], field: str) -> dict[str, object]:
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
                "perfect_outputs": sum(all(candidate[field]) for candidate in candidates),
                "criteria_passed": sum(sum(candidate[field]) for candidate in candidates),
                "criteria_total": sum(len(candidate[field]) for candidate in candidates),
                "core_criterion_failures": sum(
                    not candidate[field][0] for candidate in candidates
                ),
            }
    return dict(result)


def recompute_gate(
    report: dict[str, object], spec: dict[str, object], cases: list[dict], field: str
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
            not candidate[field][0]
            for candidate in candidates
            if candidate["arm_id"] == "ours"
        )
        baseline_failures = sum(
            not candidate[field][0]
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


def percent(to_value: int | float, from_value: int | float) -> float:
    return round((to_value / from_value - 1) * 100, 1)


def validate_report(report: dict[str, object]) -> None:
    assert report["schema_version"] == 1
    assert report["report_id"] == "conversation-native-resume-round-24-diagnostic"
    assert report["scope"] == {
        "skill_id": "conversation-rehearsal",
        "version": "0.1.1",
        "catalog_status": "experimental",
        "active_case_count": 11,
        "collection_active_case_count": 144,
        "formal_trajectories": 36,
        "formal_turns": 84,
        "blind_review_items": 18,
        "raw_criterion_booleans": 144,
        "calibrated_criterion_booleans": 144,
    }

    experiment = report["experiment"]
    assert experiment["freeze_commit"] == "497d06a6ac6f7afaf7c5cd9da9a784bc2a501e01"
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
        "tools_used": False,
        "expected_trajectories": 36,
        "valid_trajectories": 36,
        "expected_turns": 84,
        "valid_turns": 84,
    }

    spec = json.loads((COMPARISON / "promptfoo.json").read_text(encoding="utf-8"))
    cases = json.loads((COMPARISON / "cases.json").read_text(encoding="utf-8"))
    case_by_id = {case["id"]: case for case in cases}
    assert experiment["source_hashes"] == {
        "promptfoo.json": sha256_file(COMPARISON / "promptfoo.json"),
        "cases.json": sha256_file(COMPARISON / "cases.json"),
    }
    assert experiment["prepared_hashes"] == {
        "config": "8926237fa2fd14ad7a1b44e8716b5ba3bade73dfd08caf36297cffff2c7f9469",
        "tests": "fb2d2593475b52bd74b5923714f8444c349f46a0b3e99bd6e6008d931b8d52eb",
    }
    assert set(experiment["review_chain"]) == set(REVIEW_FILES)
    for key, name in REVIEW_FILES.items():
        review = experiment["review_chain"][key]
        assert review["path"] == (COMPARISON / name).relative_to(ROOT).as_posix()
        assert review["sha256"] == sha256_file(COMPARISON / name)
        assert review["independent"] is True
    assert experiment["review_chain"]["raw_postscore_review"][
        "conclusion_superseded"
    ] is True

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

    assert len(experiment["items"]) == 18
    seen_review_ids = set()
    seen_trajectories = set()
    changed = []
    for item in experiment["items"]:
        assert item["review_id"] not in seen_review_ids
        seen_review_ids.add(item["review_id"])
        source = case_by_id[item["case_id"]]
        assert item["user_turns"] == source["turns"]
        assert item["user_turns_sha256"] == runner_json_sha256(source["turns"])
        assert item["hard_criteria"] == source["hard_criteria"]
        assert item["mechanism"] == source["mechanism"]
        assert item["purpose"] == source["purpose"]
        assert item["raw_review_notes"].strip()
        assert len(item["candidates"]) == 2
        for candidate in item["candidates"]:
            assert candidate["trajectory_id"] not in seen_trajectories
            seen_trajectories.add(candidate["trajectory_id"])
            assert len(candidate["outputs"]) == len(source["turns"])
            assert candidate["output_sha256s"] == [
                sha256_text(output) for output in candidate["outputs"]
            ]
            assert candidate["turn_technical_valid"] == [True] * len(source["turns"])
            assert candidate["raw_passed"] == sum(candidate["raw_criteria_pass"])
            assert candidate["calibrated_passed"] == sum(
                candidate["calibrated_criteria_pass"]
            )
            assert len(candidate["raw_criteria_pass"]) == 4
            assert len(candidate["calibrated_criteria_pass"]) == 4
            assert candidate["total"] == 4
            if candidate["raw_criteria_pass"] != candidate["calibrated_criteria_pass"]:
                changed.append((item["review_id"], candidate["candidate_id"]))
                assert item["case_id"] == "decline-exact-real-person-imitation"
                assert candidate["arm_id"] == "ours"
                assert candidate["raw_criteria_pass"] == [False, True, True, True]
                assert candidate["calibrated_criteria_pass"] == [True, True, True, True]
            assert candidate["preferred"] == (
                item["preferred_candidate"] == candidate["candidate_id"]
            )
            if candidate["arm_id"] == "baseline":
                assert candidate["skill"] is None
                assert candidate["skill_package_sha256"] is None
            else:
                assert candidate["arm_id"] == "ours"
                assert candidate["skill"] == "conversation-rehearsal"
                assert candidate["skill_package_sha256"] == experiment["arms"][1][
                    "skill_package_sha256"
                ]
        preferred_arms = [
            candidate["arm_id"]
            for candidate in item["candidates"]
            if candidate["preferred"]
        ]
        assert item["preferred_arm"] == (
            preferred_arms[0] if preferred_arms else None
        )
    assert len(seen_trajectories) == 36
    assert sorted(review_id for review_id, _ in changed) == [
        f"decline-exact-real-person-imitation-r{index}" for index in range(1, 4)
    ]

    raw = report["analysis"]["raw_blind_review"]
    calibrated = report["analysis"]["calibrated_semantic_review"]
    raw_aggregate = aggregate(report, "raw_criteria_pass")
    calibrated_aggregate = aggregate(report, "calibrated_criteria_pass")
    for layer, expected in ((raw, raw_aggregate), (calibrated, calibrated_aggregate)):
        assert layer["overall"]["baseline"] == expected["baseline"]
        assert layer["overall"]["ours"] == expected["ours"]
        assert layer["overall"]["no_unique_preference_count"] == 15
        assert layer["overall"]["unique_preference_count"] == 3
    assert raw_aggregate["baseline"]["criteria_passed"] == 72
    assert raw_aggregate["baseline"]["perfect_outputs"] == 18
    assert raw_aggregate["ours"]["criteria_passed"] == 69
    assert raw_aggregate["ours"]["perfect_outputs"] == 15
    assert calibrated_aggregate["baseline"]["criteria_passed"] == 72
    assert calibrated_aggregate["baseline"]["perfect_outputs"] == 18
    assert calibrated_aggregate["ours"]["criteria_passed"] == 72
    assert calibrated_aggregate["ours"]["perfect_outputs"] == 18
    assert raw["by_mechanism"] == by_mechanism(report, "raw_criteria_pass")
    assert calibrated["by_mechanism"] == by_mechanism(
        report, "calibrated_criteria_pass"
    )

    raw_gate = recompute_gate(report, spec, cases, "raw_criteria_pass")
    calibrated_gate = recompute_gate(report, spec, cases, "calibrated_criteria_pass")
    assert raw["candidate_gate"] == raw_gate
    assert raw_gate["qualifying_cases_by_mechanism"] == {
        "evidence-boundary": ["decline-exact-real-person-imitation"],
        "phase-boundary": [],
        "state-isolation": [],
    }
    assert raw_gate["triggered"] is False
    assert calibrated["candidate_gate"] == calibrated_gate
    assert all(not value["qualifies"] for value in calibrated_gate["per_case"].values())
    assert calibrated_gate["qualifying_mechanisms"] == []
    assert calibrated_gate["triggered"] is False
    assert len(calibrated["calibrations"]) == 3
    assert calibrated["adjudication"] == experiment["review_chain"][
        "scoring_adjudication"
    ]

    for arm in experiment["arms"]:
        assert arm["raw_blind_score"] == raw_aggregate[arm["arm_id"]]
        assert arm["calibrated_score"] == calibrated_aggregate[arm["arm_id"]]
    ours_arm = next(arm for arm in experiment["arms"] if arm["arm_id"] == "ours")
    assert ours_arm["skill_package_sha256"] == VALIDATOR["package_fingerprint"](
        ROOT / "skills" / "relationships" / "conversation-rehearsal"
    )

    preference = report["analysis"]["observed_expression_preference"]
    assert preference["case_id"] == "decline-exact-real-person-imitation"
    assert preference["baseline_preferred_count"] == 3
    assert preference["ours_preferred_count"] == 0
    assert "not a frozen hard-criterion failure" in preference["interpretation"]

    baseline_runtime = experiment["arms"][0]["runtime"]
    ours_runtime = experiment["arms"][1]["runtime"]
    baseline_tokens = baseline_runtime["tokens_total"]
    ours_tokens = ours_runtime["tokens_total"]
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
                ours_tokens["cached_input_tokens"], baseline_tokens["cached_input_tokens"]
            ),
            "output_tokens_percent": percent(
                ours_tokens["output_tokens"], baseline_tokens["output_tokens"]
            ),
            "reasoning_output_tokens_percent": percent(
                ours_tokens["reasoning_output_tokens"],
                baseline_tokens["reasoning_output_tokens"],
            ),
            "median_latency_percent": percent(
                ours_runtime["latency_ms_median_per_turn"],
                baseline_runtime["latency_ms_median_per_turn"],
            ),
            "price_or_cost_available": False,
        }
    }

    decision = report["decision"]
    assert decision["public_score_layer"] == "calibrated_semantic_review"
    assert decision["raw_blind_score_preserved"] is True
    assert decision["calibrated_items"] == 3
    assert decision["candidate_design_opened"] is False
    assert decision["skill_changed"] is False
    assert decision["version_changed"] is False
    assert decision["status_changed"] is False
    assert decision["evidence_changed"] is False
    assert decision["active_cases_added"] == 6

    projection = evidence_projection(report)
    assert experiment["evidence_projection"]["sha256"] == EXPECTED_PROJECTION_SHA256
    assert sha256_object(projection) == EXPECTED_PROJECTION_SHA256


class ConversationNativeResumeRound24Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))

    def test_published_report_recomputes(self):
        validate_report(self.report)

    def test_active_cases_and_catalog_state_match_report(self):
        active = json.loads(
            (ROOT / "evaluations" / "cases" / "conversation-rehearsal.json").read_text(
                encoding="utf-8"
            )
        )
        cases = json.loads((COMPARISON / "cases.json").read_text(encoding="utf-8"))
        protocol = json.loads(
            (COMPARISON / "promptfoo.json").read_text(encoding="utf-8")
        )["common_prompt"]
        active_by_id = {case["id"]: case for case in active["cases"]}
        self.assertGreaterEqual(
            len(active_by_id), self.report["scope"]["active_case_count"]
        )
        for source in cases:
            promoted = active_by_id[source["id"]]
            prepared_turns = [
                protocol + "\n\n" + source["turns"][0], *source["turns"][1:]
            ]
            self.assertEqual(promoted["prompt"], prepared_turns[0])
            self.assertEqual(
                promoted["input"], {"kind": "synthetic", "steps": prepared_turns}
            )
            self.assertEqual(promoted["expected_route"], "conversation-rehearsal")
            self.assertEqual(promoted["must_include"], source["hard_criteria"])
            self.assertEqual(len(promoted["must_avoid"]), 3)
            self.assertTrue(all(item.strip() for item in promoted["must_avoid"]))
        decline = active_by_id["decline-exact-real-person-imitation"]
        self.assertFalse(
            any("\u4e0d\u8bf4\u660e\u771f\u4eba\u6a21\u4eff\u4e0e\u8bfb\u5fc3\u8fb9\u754c" in item for item in decline["must_avoid"])
        )
        self.assertTrue(
            any("\u7cbe\u786e\u6a21\u4eff" in item for item in decline["must_avoid"])
        )

        catalog = json.loads(
            (ROOT / "catalog" / "collection.json").read_text(encoding="utf-8")
        )
        entry = next(
            skill for skill in catalog["skills"] if skill["id"] == "conversation-rehearsal"
        )
        self.assertEqual(
            (entry["version"], entry["status"], entry["evidence"]),
            ("0.1.1", "experimental", None),
        )
        total = 0
        for path in (ROOT / "evaluations" / "cases").glob("*.json"):
            suite = json.loads(path.read_text(encoding="utf-8"))
            if suite.get("stage") == "active":
                total += len(suite.get("cases", []))
        self.assertGreaterEqual(
            total, self.report["scope"]["collection_active_case_count"]
        )

    def test_local_raw_run_hashes_match_when_artifacts_are_available(self):
        if not RUN_DIR.exists():
            self.skipTest("ignored raw Round 24 run is not present in this checkout")
        frozen = json.loads((RUN_DIR / "frozen.json").read_text(encoding="utf-8"))
        self.assertEqual(
            self.report["experiment"]["prepared_hashes"],
            {
                "config": frozen["prepared_config_sha256"],
                "tests": frozen["prepared_tests_sha256"],
            },
        )
        for name, expected_hash in self.report["experiment"]["artifact_hashes"].items():
            with self.subTest(artifact=name):
                self.assertEqual(sha256_file(RUN_DIR / name), expected_hash)

    def test_coordinated_evidence_mutations_are_rejected(self):
        mutations = []
        changed_output = copy.deepcopy(self.report)
        candidate = changed_output["experiment"]["items"][0]["candidates"][0]
        candidate["outputs"][0] += " "
        candidate["output_sha256s"][0] = sha256_text(candidate["outputs"][0])
        mutations.append(changed_output)
        changed_score = copy.deepcopy(self.report)
        candidate = changed_score["experiment"]["items"][0]["candidates"][0]
        candidate["calibrated_criteria_pass"][0] = False
        candidate["calibrated_passed"] = sum(candidate["calibrated_criteria_pass"])
        mutations.append(changed_score)
        changed_gate = copy.deepcopy(self.report)
        changed_gate["analysis"]["calibrated_semantic_review"]["candidate_gate"][
            "triggered"
        ] = True
        mutations.append(changed_gate)
        changed_review = copy.deepcopy(self.report)
        changed_review["experiment"]["review_chain"]["scoring_adjudication"][
            "sha256"
        ] = "0" * 64
        mutations.append(changed_review)
        changed_artifact = copy.deepcopy(self.report)
        changed_artifact["experiment"]["artifact_hashes"]["native-results.json"] = (
            "0" * 64
        )
        mutations.append(changed_artifact)
        for index, mutated in enumerate(mutations):
            mutated["experiment"]["evidence_projection"]["sha256"] = sha256_object(
                evidence_projection(mutated)
            )
            with self.subTest(mutation=index):
                with self.assertRaises(AssertionError):
                    validate_report(mutated)


if __name__ == "__main__":
    unittest.main()
