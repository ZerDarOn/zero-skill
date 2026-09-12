"""Protect the published Round 23 Obsidian artifact diagnostic."""

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
    / "obsidian-artifact-preservation-round-23-diagnostic.json"
)
COMPARISON = (
    ROOT
    / "evaluations"
    / "comparisons"
    / "obsidian-artifact-preservation-three-arm-16"
)
FIXTURE = (
    ROOT
    / "evaluations"
    / "fixtures"
    / "upstreams"
    / "obsidian-skills"
    / "a1dc48e68138490d522c04cbf5822214c6eb1202"
)
VALIDATOR = runpy.run_path(str(ROOT / "scripts" / "validate_collection.py"))
EXPECTED_PROJECTION_SHA256 = (
    "55279e2d054664e3f9f137e7b705e6fd00f43fac407ab5383a2a504386a54930"
)
RUN_DIR = (
    ROOT
    / "evaluations"
    / "runs"
    / "obsidian-artifact-preservation-three-arm-16-promptfoo-20260912T194215Z-5dd7a2"
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


def exact_note_match(actual: str, expected: str) -> bool:
    assert expected.endswith("\n") and not expected.endswith("\n\n")
    return actual == expected or actual == expected[:-1]


def evidence_projection(report: dict[str, object]) -> dict[str, object]:
    experiment = report["experiment"]
    return {
        "freeze_commit": experiment["freeze_commit"],
        "source_hashes": experiment["source_hashes"],
        "prepared_hashes": experiment["prepared_hashes"],
        "artifact_hashes": experiment["artifact_hashes"],
        "review_hashes": experiment["review_hashes"],
        "upstream_provenance": experiment["upstream_provenance"],
        "metadata_correction": experiment["metadata_correction"],
        "blind_reviewer": experiment["blind_reviewer"],
        "postscore_review": experiment["postscore_review"],
        "arms": experiment["arms"],
        "items": experiment["items"],
        "analysis": report["analysis"],
        "decision": report["decision"],
    }


def recompute_aggregate(report: dict[str, object]) -> dict[str, dict[str, object]]:
    aggregate = {}
    for arm_id in ("baseline", "ours", "upstream"):
        candidates = [
            candidate
            for item in report["experiment"]["items"]
            for candidate in item["candidates"]
            if candidate["arm_id"] == arm_id
        ]
        aggregate[arm_id] = {
            "arm_id": arm_id,
            "skill": next(
                arm["skill"]
                for arm in report["experiment"]["arms"]
                if arm["arm_id"] == arm_id
            ),
            "outputs": len(candidates),
            "perfect_outputs": sum(
                all(candidate["criteria_pass"]) for candidate in candidates
            ),
            "criteria_passed": sum(
                sum(candidate["criteria_pass"]) for candidate in candidates
            ),
            "criteria_total": sum(
                len(candidate["criteria_pass"]) for candidate in candidates
            ),
            "preferred_count": sum(candidate["preferred"] for candidate in candidates),
        }
        total = aggregate[arm_id]["criteria_total"]
        aggregate[arm_id]["criterion_pass_rate"] = round(
            aggregate[arm_id]["criteria_passed"] / total, 4
        )
    return aggregate


def validate_report(report: dict[str, object]) -> None:
    assert report["schema_version"] == 1
    assert report["report_id"] == "obsidian-artifact-preservation-round-23-diagnostic"
    assert report["scope"] == {
        "skill_id": "obsidian-note-edit",
        "version": "0.1.0",
        "catalog_status": "experimental",
        "active_case_count": 10,
        "collection_active_case_count": 138,
        "formal_outputs": 54,
        "blind_review_items": 18,
        "criterion_booleans": 216,
    }
    experiment = report["experiment"]
    assert experiment["freeze_commit"] == "4f0581582d6132b30b808d929a57a76eaf37dfe2"
    assert experiment["model"] == "gpt-5.6-sol"
    assert experiment["reasoning_effort"] == "medium"
    assert experiment["infrastructure_valid"] is True
    assert experiment["planned_repetitions"] == 3
    assert experiment["executed_repetitions"] == 3
    assert len(experiment["items"]) == 18

    cases = json.loads((COMPARISON / "cases.json").read_text(encoding="utf-8"))
    case_by_id = {case["id"]: case for case in cases}
    assert experiment["source_hashes"] == {
        "promptfoo.json": sha256_file(COMPARISON / "promptfoo.json"),
        "cases.json": sha256_file(COMPARISON / "cases.json"),
    }

    candidates = []
    seen_review_ids = set()
    for item in experiment["items"]:
        assert item["review_id"] not in seen_review_ids
        seen_review_ids.add(item["review_id"])
        source = case_by_id[item["case_id"]]
        assert item["task"].endswith(source["prompt"])
        assert item["expected_note"] == source["expected_note"]
        assert item["expected_note_sha256"] == sha256_text(item["expected_note"])
        assert item["hard_criteria"] == source["hard_criteria"]
        assert item["mechanism"] == source["mechanism"]
        assert len(item["candidates"]) == 3
        for candidate in item["candidates"]:
            candidates.append(candidate)
            assert candidate["output_sha256"] == sha256_text(candidate["output"])
            parsed = json.loads(candidate["output"])
            assert set(parsed) == {"note", "message"}
            assert parsed["note"] == candidate["submission"]["note"]
            assert parsed["message"] == candidate["submission"]["message"]
            assert candidate["submission"]["parse_valid"] is True
            assert candidate["submission"]["schema_valid"] is True
            assert candidate["submission"]["parse_error"] is None
            assert candidate["submission"]["actual_note_sha256"] == sha256_text(
                parsed["note"]
            )
            exact = exact_note_match(parsed["note"], item["expected_note"])
            assert candidate["artifact_exact"] is exact
            assert candidate["criteria_pass"][0] is exact
            assert candidate["passed"] == sum(candidate["criteria_pass"])
            assert candidate["total"] == len(item["hard_criteria"]) == 4
            assert candidate["preferred"] == (
                item["preferred_candidate"] == candidate["candidate_id"]
            )
        preferred_arms = [
            candidate["arm_id"]
            for candidate in item["candidates"]
            if candidate["preferred"]
        ]
        assert item["preferred_arm"] == (preferred_arms[0] if preferred_arms else None)

    assert len(candidates) == 54
    assert sum(c["submission"]["parse_valid"] for c in candidates) == 54
    assert sum(c["submission"]["schema_valid"] for c in candidates) == 54
    assert sum(c["artifact_exact"] for c in candidates) == 54
    assert report["analysis"]["artifact_checks"] == {
        "parse_valid": 54,
        "schema_valid": 54,
        "artifact_exact": 54,
        "total": 54,
    }

    aggregate = recompute_aggregate(report)
    assert report["analysis"]["overall"]["baseline"] == aggregate["baseline"]
    assert report["analysis"]["overall"]["ours"] == aggregate["ours"]
    assert report["analysis"]["overall"]["upstream"] == aggregate["upstream"]
    overall = report["analysis"]["overall"]
    assert overall["no_unique_preference_count"] == 18
    assert overall["three_way_equal_items"] == 17
    assert overall["two_way_best_tie_items"] == 1
    assert aggregate["baseline"]["criteria_passed"] == 72
    assert aggregate["baseline"]["perfect_outputs"] == 18
    assert aggregate["ours"]["criteria_passed"] == 72
    assert aggregate["ours"]["perfect_outputs"] == 18
    assert aggregate["upstream"]["criteria_passed"] == 71
    assert aggregate["upstream"]["perfect_outputs"] == 17
    assert all(aggregate[arm]["preferred_count"] == 0 for arm in aggregate)

    gate = report["analysis"]["candidate_gate"]
    qualifying = defaultdict(list)
    for case_id, gate_case in gate["per_case"].items():
        ours = [
            candidate
            for item in experiment["items"]
            if item["case_id"] == case_id
            for candidate in item["candidates"]
            if candidate["arm_id"] == "ours"
        ]
        baseline = [
            candidate
            for item in experiment["items"]
            if item["case_id"] == case_id
            for candidate in item["candidates"]
            if candidate["arm_id"] == "baseline"
        ]
        ours_failures = sum(not candidate["criteria_pass"][0] for candidate in ours)
        baseline_failures = sum(
            not candidate["criteria_pass"][0] for candidate in baseline
        )
        assert gate_case["ours_core_failures"] == ours_failures == 0
        assert gate_case["baseline_core_failures"] == baseline_failures == 0
        qualifies = ours_failures >= 2 and baseline_failures <= 1
        assert gate_case["qualifies"] is qualifies
        if qualifies:
            qualifying[gate_case["mechanism"]].append(case_id)
    expected_qualifying = {
        mechanism: qualifying.get(mechanism, [])
        for mechanism in sorted(report["analysis"]["by_mechanism"])
    }
    assert gate["qualifying_cases_by_mechanism"] == expected_qualifying
    assert gate["qualifying_mechanisms"] == []
    assert gate["triggered"] is False
    assert report["decision"]["candidate_design_opened"] is False
    assert report["decision"]["skill_changed"] is False
    assert report["decision"]["version_changed"] is False
    assert report["decision"]["active_cases_added"] == 6

    correction = experiment["metadata_correction"]
    assert correction["reviews_identical"] is True
    assert correction["score_content_identical"] is True
    assert correction["scores_or_preferences_changed"] is False
    assert correction["post_reveal_metadata_only_correction"] is True
    assert (
        correction["original_reviews_projection_sha256"]
        == correction["corrected_reviews_projection_sha256"]
    )
    assert correction["original_reviewer_declaration"]["model"] == "gpt-6-astra"
    assert correction["original_reviewer_declaration"]["reasoning_effort"] == "high"
    reviewer = experiment["blind_reviewer"]
    assert reviewer["model"] == "gpt-5.6-sol"
    assert reviewer["reasoning_effort"] == "medium"
    assert reviewer["blind_file_boundary_clean"] is True
    assert reviewer["blind_to_arm_mapping"] is True
    assert reviewer["unexpected_files_read"] == []
    assert experiment["postscore_review"]["corrections"] == 0

    provenance = experiment["upstream_provenance"]
    assert provenance["commit"] == "a1dc48e68138490d522c04cbf5822214c6eb1202"
    assert provenance["license"] == "MIT"
    assert provenance["package_license_included"] is True
    assert provenance["source_bytes_modified"] is False
    assert provenance["provenance_sha256"] == sha256_file(FIXTURE / "provenance.json")
    assert provenance["package_sha256"] == VALIDATOR["package_fingerprint"](
        FIXTURE / "skills" / "obsidian-markdown"
    )
    ours = next(arm for arm in experiment["arms"] if arm["arm_id"] == "ours")
    assert ours["skill_package_sha256"] == VALIDATOR["package_fingerprint"](
        ROOT / "skills" / "productivity" / "obsidian-note-edit"
    )

    def percent(to_value, from_value):
        return round((to_value / from_value - 1) * 100, 1)

    def efficiency_delta(to_runtime, from_runtime):
        return {
            "total_tokens": {
                "from": from_runtime["tokens_total"]["total"],
                "to": to_runtime["tokens_total"]["total"],
                "delta": to_runtime["tokens_total"]["total"]
                - from_runtime["tokens_total"]["total"],
                "percent": percent(
                    to_runtime["tokens_total"]["total"],
                    from_runtime["tokens_total"]["total"],
                ),
            },
            "prompt_tokens_percent": percent(
                to_runtime["tokens_total"]["prompt"],
                from_runtime["tokens_total"]["prompt"],
            ),
            "completion_tokens_percent": percent(
                to_runtime["tokens_total"]["completion"],
                from_runtime["tokens_total"]["completion"],
            ),
            "cost_percent": percent(to_runtime["cost_total"], from_runtime["cost_total"]),
            "median_latency_percent": percent(
                to_runtime["latency_ms_median"], from_runtime["latency_ms_median"]
            ),
        }

    runtimes = {
        arm["arm_id"]: arm["runtime"] for arm in experiment["arms"]
    }
    assert report["analysis"]["cost_and_efficiency"] == {
        "ours_vs_baseline": efficiency_delta(runtimes["ours"], runtimes["baseline"]),
        "upstream_vs_baseline": efficiency_delta(
            runtimes["upstream"], runtimes["baseline"]
        ),
        "ours_vs_upstream": efficiency_delta(runtimes["ours"], runtimes["upstream"]),
    }

    for name, expected_hash in experiment["review_hashes"].items():
        assert expected_hash == sha256_file(COMPARISON / name)

    projection = evidence_projection(report)
    assert experiment["evidence_projection"]["sha256"] == EXPECTED_PROJECTION_SHA256
    assert sha256_object(projection) == EXPECTED_PROJECTION_SHA256


class ObsidianArtifactRound23Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))

    def test_published_report_recomputes(self):
        validate_report(self.report)

    def test_active_cases_and_catalog_state_match_report(self):
        active = json.loads(
            (ROOT / "evaluations" / "cases" / "obsidian-note-edit.json").read_text(
                encoding="utf-8"
            )
        )
        frozen = json.loads((COMPARISON / "cases.json").read_text(encoding="utf-8"))
        protocol = json.loads(
            (COMPARISON / "promptfoo.json").read_text(encoding="utf-8")
        )["common_prompt"]
        active_by_id = {case["id"]: case for case in active["cases"]}
        self.assertEqual(len(active_by_id), 10)
        for case in frozen:
            self.assertIn(case["id"], active_by_id)
            promoted = active_by_id[case["id"]]
            self.assertEqual(promoted["prompt"], protocol + "\n\n" + case["prompt"])
            self.assertEqual(promoted["expected_route"], "obsidian-note-edit")
            self.assertEqual(promoted["input"]["kind"], "synthetic")
            self.assertIn(
                "以固定note和message两字段JSON返回完整最终笔记与简短真实说明",
                promoted["must_include"],
            )
            self.assertIn(
                "输出JSON代码围栏、额外文字或虚构已执行的文件及应用操作",
                promoted["must_avoid"],
            )
        catalog = json.loads((ROOT / "catalog" / "collection.json").read_text(encoding="utf-8"))
        entry = next(skill for skill in catalog["skills"] if skill["id"] == "obsidian-note-edit")
        self.assertEqual(entry["version"], "0.1.0")
        self.assertEqual(entry["status"], "experimental")
        self.assertIsNone(entry["evidence"])
        total = 0
        for path in (ROOT / "evaluations" / "cases").glob("*.json"):
            suite = json.loads(path.read_text(encoding="utf-8"))
            if suite.get("stage") == "active":
                total += len(suite.get("cases", []))
        self.assertEqual(total, 138)

    def test_local_raw_run_hashes_match_when_artifacts_are_available(self):
        if not RUN_DIR.exists():
            self.skipTest("ignored raw Round 23 run is not present in this checkout")
        for name, expected_hash in self.report["experiment"]["artifact_hashes"].items():
            with self.subTest(artifact=name):
                self.assertEqual(sha256_file(RUN_DIR / name), expected_hash)

    def test_coordinated_evidence_mutations_are_rejected(self):
        mutations = []
        changed_output = copy.deepcopy(self.report)
        changed_output["experiment"]["items"][0]["candidates"][0]["output"] += " "
        mutations.append(changed_output)
        changed_expected = copy.deepcopy(self.report)
        changed_expected["experiment"]["items"][0]["expected_note"] += "\n"
        mutations.append(changed_expected)
        changed_score = copy.deepcopy(self.report)
        changed_score["experiment"]["items"][0]["candidates"][0]["criteria_pass"][1] = False
        mutations.append(changed_score)
        changed_gate = copy.deepcopy(self.report)
        changed_gate["analysis"]["candidate_gate"]["triggered"] = True
        mutations.append(changed_gate)
        changed_reviewer = copy.deepcopy(self.report)
        changed_reviewer["experiment"]["blind_reviewer"]["blind_file_boundary_clean"] = False
        mutations.append(changed_reviewer)
        changed_artifact_hash = copy.deepcopy(self.report)
        changed_artifact_hash["experiment"]["artifact_hashes"]["results.json"] = "0" * 64
        mutations.append(changed_artifact_hash)
        changed_provenance = copy.deepcopy(self.report)
        changed_provenance["experiment"]["upstream_provenance"]["provenance_sha256"] = "0" * 64
        mutations.append(changed_provenance)
        for index, mutated in enumerate(mutations):
            mutated["experiment"]["evidence_projection"]["sha256"] = sha256_object(
                evidence_projection(mutated)
            )
            with self.subTest(mutation=index):
                with self.assertRaises(AssertionError):
                    validate_report(mutated)


if __name__ == "__main__":
    unittest.main()
