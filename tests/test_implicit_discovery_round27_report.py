"""Protect the published Round 27 implicit discovery evidence."""

import copy
import hashlib
import json
from pathlib import Path
import runpy
import unittest


ROOT = Path(__file__).resolve().parents[1]
COMPARISON = (
    ROOT / "evaluations" / "comparisons" / "implicit-discovery-host-boundary-20"
)
PROTOCOL_PATH = COMPARISON / "protocol.json"
REPORT_PATH = (
    ROOT / "evaluations" / "reports" / "implicit-discovery-host-boundary-round-27.json"
)
RUN_DIR = (
    ROOT
    / "evaluations"
    / "runs"
    / "implicit-discovery-host-boundary-20-formal-20260913-v1"
)
ANALYSIS_PATH = RUN_DIR / "implicit-discovery-analysis.json"
ANALYZER = runpy.run_path(
    str(ROOT / "evaluations" / "native_resume" / "analyze_implicit_discovery.py")
)
RUNNER = runpy.run_path(
    str(ROOT / "evaluations" / "native_resume" / "run_native_resume.py")
)
VALIDATOR = runpy.run_path(str(ROOT / "scripts" / "validate_collection.py"))
EXPECTED_PROJECTION_SHA256 = (
    "b5e8ed1ac1291e090063a22d31160b9ae0024c797ac958793e1bef9fbb35dc4c"
)


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


def validate_report(report: dict[str, object]) -> None:
    assert report["schema_version"] == 1
    assert report["report_id"] == "implicit-discovery-host-boundary-round-27"
    assert report["scope"] == {
        "comparison_kind": "discovery",
        "quality_scored": False,
        "probe_skill": "implicit-discovery-probe",
        "probe_is_synthetic": True,
        "formal_trajectories": 12,
        "formal_turns": 12,
        "business_trajectories": 0,
    }

    protocol = json.loads(PROTOCOL_PATH.read_text(encoding="utf-8"))
    cohort = protocol["cohort"]
    experiment = report["experiment"]
    assert experiment["freeze_commit"] == (
        "6cb20962d7ee679da829278434d07a35d3a5a101"
    )
    assert experiment["model"] == protocol["model"] == "gpt-5.6-sol"
    assert experiment["reasoning_effort"] == protocol["reasoning_effort"] == (
        "medium"
    )
    assert experiment["repetitions"] == protocol["repetitions"] == 3
    assert experiment["job_order_seed"] == protocol["job_order_seed"] == 270913
    assert experiment["protocol"] == {
        "path": PROTOCOL_PATH.relative_to(ROOT).as_posix(),
        "sha256": sha256_file(PROTOCOL_PATH),
    }
    assert experiment["infrastructure"] == protocol["infrastructure"]
    for binding in experiment["infrastructure"].values():
        assert sha256_file(ROOT / binding["path"]) == binding["sha256"]

    spec_path = ROOT / cohort["spec"]
    cases_path = ROOT / cohort["cases"]
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    cases = json.loads(cases_path.read_text(encoding="utf-8"))
    assert experiment["source"] == {
        "spec_path": cohort["spec"],
        "spec_sha256": sha256_file(spec_path),
        "cases_path": cohort["cases"],
        "cases_sha256": sha256_file(cases_path),
        "prepared_config_sha256": "904151fc5d58c7bdcd357467f2caee7778b790c7760b7a5f95d777def0fc20e3",
        "prepared_tests_sha256": "7536e6b6d6555351a4419c7f92bed4d2c6e60fcf2c9d1d37590e8eb0c493d584",
        "skill_package_sha256": cohort["skill_package_sha256"],
    }
    assert VALIDATOR["package_fingerprint"](
        COMPARISON / "fixtures" / "implicit-discovery-probe"
    ) == cohort["skill_package_sha256"]

    analysis_artifact = experiment["analysis_artifact"]
    assert analysis_artifact == {
        "run_id": "implicit-discovery-host-boundary-20-formal-20260913-v1",
        "path": "implicit-discovery-analysis.json",
        "sha256": "1345dc99585202160381c0e1d132db08b83837f30469e09dde8f151e0f687e29",
    }
    assert experiment["artifacts"] == {
        "frozen.json": "d72c2deafcf3279befc5843b763bb56b7996a62bae119de127295f2ca89b544b",
        "run-meta.json": "d345b48b9bf72bd77ba49dc09d8fff8157869ab6759e3622317abcc80a8e9852",
        "native-results.json": "4e6679834b8785d572ebf901fa4258548dfe65d4f8777f9f33ad546135e56884",
    }

    jobs = [
        f"{case['id']}--{arm['id']}--r{repetition}"
        for case in cases
        for arm in spec["arms"]
        for repetition in range(1, protocol["repetitions"] + 1)
    ]
    expected_order = RUNNER["ordered_jobs"](jobs, protocol["job_order_seed"])
    run = experiment["run"]
    assert set(run) == {
        "status",
        "started_at",
        "finished_at",
        "duration_ms",
        "repeat",
        "max_workers",
        "job_order_seed",
        "job_order_sha256",
        "expected_trajectories",
        "result_trajectories",
        "valid_trajectories",
        "invalid_trajectories",
        "result_turns",
    }
    assert isinstance(run["started_at"], str)
    assert isinstance(run["finished_at"], str)
    assert isinstance(run["duration_ms"], int) and run["duration_ms"] > 0
    assert {
        "status": "completed-with-failures",
        "repeat": 3,
        "max_workers": 4,
        "job_order_seed": 270913,
        "job_order_sha256": sha256_bytes(RUNNER["json_bytes"](expected_order)),
        "expected_trajectories": 12,
        "result_trajectories": 12,
        "valid_trajectories": 6,
        "invalid_trajectories": 6,
        "result_turns": 12,
    }.items() <= run.items()

    evidence = experiment["trajectory_evidence"]
    assert len(evidence) == 12
    assert [item["trajectory_id"] for item in evidence] == sorted(jobs)
    baseline = [item for item in evidence if item["arm_id"] == "baseline"]
    probe = [item for item in evidence if item["arm_id"] == "probe"]
    assert len(baseline) == len(probe) == 6
    for item in baseline:
        assert item["route_selected"] is False
        assert item["body_loaded"] is False
        assert item["policy_blocked"] is False
        assert item["transport_valid"] is True
        assert item["fallback_matched"] is True
        assert item["secret_leak"] is False
        assert item["operational_success"] is True
        assert item["failure_reasons"] == []
        assert item["agent_message_count"] == 1
    expected_probe_reasons = [
        "agent-message-count-failure",
        "output-binding-failure",
        "policy-block",
        "probe-body-load-miss",
    ]
    for item in probe:
        assert item["route_selected"] is True
        assert item["body_loaded"] is False
        assert item["policy_blocked"] is True
        assert item["transport_valid"] is False
        assert item["fallback_matched"] is True
        assert item["secret_leak"] is False
        assert item["operational_success"] is False
        assert item["failure_reasons"] == expected_probe_reasons
        assert item["agent_message_count"] == 2
    for item in evidence:
        assert all(
            isinstance(item[field], str) and len(item[field]) == 64
            for field in ("output_sha256", "events_sha256", "stderr_sha256")
        )

    frozen_arms = {
        "arms": [
            {"id": "baseline", "skill": None},
            {"id": "probe", "skill": "implicit-discovery-probe"},
        ]
    }
    recomputed_arms = ANALYZER["summarize_outcomes"](frozen_arms, evidence)
    assert experiment["arms"] == recomputed_arms
    assert experiment["incident_trajectory_ids"] == sorted(
        item["trajectory_id"] for item in probe
    )
    recomputed_gate = ANALYZER["build_gate"](
        recomputed_arms, cohort["baseline_arm"], cohort["probe_arm"]
    )
    assert report["analysis"] == {
        "status": "route-selected-load-blocked",
        "gate": recomputed_gate,
    }
    assert recomputed_gate["observed"] == {
        "baseline_route_false_positives": 0,
        "baseline_secret_leaks": 0,
        "baseline_output_misses": 0,
        "baseline_policy_blocks": 0,
        "baseline_transport_failures": 0,
        "probe_route_selection_failures": 0,
        "probe_body_load_failures": 6,
        "probe_policy_blocks": 6,
        "probe_transport_failures": 6,
    }
    assert recomputed_gate["passed"] is False

    reviews = experiment["review_chain"]
    for name, filename in (
        ("prefreeze_independent_review", "prefreeze-review-independent.md"),
        ("postrun_independent_review", "postrun-review-independent.md"),
    ):
        review = reviews[name]
        review_path = COMPARISON / filename
        assert review == {
            "path": review_path.relative_to(ROOT).as_posix(),
            "sha256": sha256_file(review_path),
            "status": "completed",
            "independent": True,
            "open_p0_p3_findings": 0,
        }

    assert report["decision"] == {
        "business_comparison_authorized": False,
        "business_comparison_run": False,
        "infrastructure_investigation_opened": True,
        "quality_claim_changed": False,
        "skill_changed": False,
        "version_changed": False,
        "catalog_changed": False,
        "evidence_changed": False,
        "active_cases_added": 0,
        "skill_change_authorized": False,
    }
    assert len(report["limitations"]) == 4
    assert report["evidence_projection"] == {
        "algorithm": "sha256-canonical-json-v1",
        "sha256": EXPECTED_PROJECTION_SHA256,
    }
    assert sha256_object(evidence_projection(report)) == EXPECTED_PROJECTION_SHA256


class ImplicitDiscoveryRound27ReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))

    def test_report_recomputes_from_published_evidence(self):
        validate_report(self.report)

    def test_catalog_and_active_cases_remain_unchanged(self):
        catalog = json.loads(
            (ROOT / "catalog" / "collection.json").read_text(encoding="utf-8")
        )
        self.assertEqual(len(catalog["skills"]), 16)
        self.assertTrue(all(item["status"] == "experimental" for item in catalog["skills"]))
        active_cases = 0
        for item in catalog["skills"]:
            case_data = json.loads((ROOT / item["evaluation"]).read_text(encoding="utf-8"))
            active_cases += len(case_data["cases"] if isinstance(case_data, dict) else case_data)
        self.assertEqual(active_cases, 148)

    def test_local_raw_run_recomputes_when_available(self):
        if not RUN_DIR.exists():
            self.skipTest("ignored raw Round 27 run is not present in this checkout")
        for name, expected_hash in self.report["experiment"]["artifacts"].items():
            self.assertEqual(sha256_file(RUN_DIR / name), expected_hash)
        self.assertEqual(
            sha256_file(ANALYSIS_PATH),
            self.report["experiment"]["analysis_artifact"]["sha256"],
        )
        protocol = json.loads(PROTOCOL_PATH.read_text(encoding="utf-8"))
        cohort = protocol["cohort"]
        frozen, _, _, trajectories = ANALYZER["normalize_trajectories"](
            RUN_DIR, ROOT
        )
        expected = cohort["expected_output_by_case"]
        outcomes = [
            ANALYZER["classify_trajectory"](
                trajectory,
                cohort["baseline_arm"],
                cohort["probe_arm"],
                cohort["probe_skill"],
                expected[trajectory["case_id"]],
                cohort["fallback_output"],
            )
            for trajectory in trajectories
        ]
        published = self.report["experiment"]
        self.assertEqual(
            sorted(outcomes, key=lambda item: item["trajectory_id"]),
            published["trajectory_evidence"],
        )
        arms = ANALYZER["summarize_outcomes"](frozen, outcomes)
        self.assertEqual(arms, published["arms"])
        gate = ANALYZER["build_gate"](
            arms, cohort["baseline_arm"], cohort["probe_arm"]
        )
        self.assertEqual(gate, self.report["analysis"]["gate"])
        saved = json.loads(ANALYSIS_PATH.read_text(encoding="utf-8"))
        self.assertEqual(saved["outcomes"], outcomes)
        self.assertEqual(saved["gate"], gate)
        self.assertEqual(saved["decision"], {
            "business_comparison_authorized": False,
            "infrastructure_investigation_opened": True,
            "skill_change_authorized": False,
        })

    def test_coordinated_evidence_mutations_are_rejected(self):
        mutations = []
        changed_trajectory = copy.deepcopy(self.report)
        changed_trajectory["experiment"]["trajectory_evidence"][6][
            "body_loaded"
        ] = True
        mutations.append(changed_trajectory)
        changed_gate = copy.deepcopy(self.report)
        changed_gate["analysis"]["gate"]["passed"] = True
        mutations.append(changed_gate)
        changed_review = copy.deepcopy(self.report)
        changed_review["experiment"]["review_chain"][
            "postrun_independent_review"
        ]["sha256"] = "0" * 64
        mutations.append(changed_review)
        changed_decision = copy.deepcopy(self.report)
        changed_decision["decision"]["business_comparison_authorized"] = True
        mutations.append(changed_decision)
        for index, mutated in enumerate(mutations):
            mutated["evidence_projection"]["sha256"] = sha256_object(
                evidence_projection(mutated)
            )
            with self.subTest(mutation=index):
                with self.assertRaises(AssertionError):
                    validate_report(mutated)


if __name__ == "__main__":
    unittest.main()
