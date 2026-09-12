"""Protect the published Round 26 operational reliability evidence."""

from collections import Counter
import copy
import hashlib
import json
from pathlib import Path
import runpy
import statistics
import unittest


ROOT = Path(__file__).resolve().parents[1]
COMPARISON = (
    ROOT / "evaluations" / "comparisons" / "explicit-invocation-reliability-19"
)
PROTOCOL_PATH = COMPARISON / "protocol.json"
REPORT_PATH = (
    ROOT / "evaluations" / "reports" / "explicit-invocation-reliability-round-26.json"
)
REVIEW_PATH = COMPARISON / "postrun-review-independent.md"
RUNS = {
    "canary": (
        ROOT
        / "evaluations"
        / "runs"
        / "explicit-invocation-canary-formal-20260913-v1"
    ),
    "business": (
        ROOT
        / "evaluations"
        / "runs"
        / "conversation-explicit-operational-formal-20260913-v1"
    ),
}
ANALYSIS_PATH = RUNS["canary"] / "invocation-reliability-analysis.json"
ANALYZER = runpy.run_path(
    str(ROOT / "evaluations" / "native_resume" / "analyze_invocation_reliability.py")
)
RUNNER = runpy.run_path(
    str(ROOT / "evaluations" / "native_resume" / "run_native_resume.py")
)
VALIDATOR = runpy.run_path(str(ROOT / "scripts" / "validate_collection.py"))
EXPECTED_PROJECTION_SHA256 = (
    "bea59feef62e2fe840a84db430df7ce2d7bbeeb709b6a62d76a9e95d034aaeb9"
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


def evidence_projection(report: dict[str, object]) -> dict[str, object]:
    return {
        key: report[key]
        for key in ("scope", "experiment", "analysis", "decision", "limitations")
    }


def summarized_evidence(cohort: dict[str, object]) -> list[dict[str, object]]:
    summaries = []
    for published_arm in cohort["arms"]:
        selected = [
            item
            for item in cohort["trajectory_evidence"]
            if item["arm_id"] == published_arm["arm_id"]
        ]
        reasons = Counter(
            reason for item in selected for reason in item["failure_reasons"]
        )
        summaries.append(
            {
                "arm_id": published_arm["arm_id"],
                "skill": published_arm["skill"],
                "attempts": len(selected),
                "operational_successes": sum(
                    item["operational_success"] for item in selected
                ),
                "operational_failures": sum(
                    not item["operational_success"] for item in selected
                ),
                "technical_valid": sum(item["technical_valid"] for item in selected),
                "failure_reason_counts": dict(sorted(reasons.items())),
            }
        )
    return summaries


def validate_report(report: dict[str, object]) -> None:
    assert report["schema_version"] == 1
    assert report["report_id"] == "explicit-invocation-reliability-round-26"
    assert report["scope"] == {
        "comparison_kind": "operational",
        "quality_scored": False,
        "skill_id": "conversation-rehearsal",
        "version": "0.1.1",
        "catalog_status": "experimental",
        "cohorts": 2,
        "formal_trajectories": 80,
        "formal_turns": 80,
    }

    protocol = json.loads(PROTOCOL_PATH.read_text(encoding="utf-8"))
    experiment = report["experiment"]
    assert experiment["freeze_commit"] == (
        "c773fb138b8a08848a151bbd0061258a49a2e039"
    )
    assert experiment["model"] == protocol["model"] == "gpt-5.6-sol"
    assert experiment["reasoning_effort"] == protocol["reasoning_effort"] == (
        "medium"
    )
    assert experiment["repetitions"] == protocol["repetitions"] == 10
    assert experiment["job_order_seed"] == protocol["job_order_seed"] == 260913
    assert experiment["protocol"] == {
        "path": PROTOCOL_PATH.relative_to(ROOT).as_posix(),
        "sha256": sha256_file(PROTOCOL_PATH),
    }
    assert experiment["infrastructure"] == protocol["infrastructure"]
    for binding in experiment["infrastructure"].values():
        assert sha256_file(ROOT / binding["path"]) == binding["sha256"]
    assert experiment["analysis_artifact"] == {
        "run_id": "explicit-invocation-canary-formal-20260913-v1",
        "path": "invocation-reliability-analysis.json",
        "sha256": "d551882dc00a64c4ef20fdfa27c614df3b5d4153b6732f59b9c2d616b0a92e35",
    }

    review = experiment["review_chain"]["postrun_independent_review"]
    assert review == {
        "path": REVIEW_PATH.relative_to(ROOT).as_posix(),
        "sha256": sha256_file(REVIEW_PATH),
        "status": "completed",
        "independent": True,
        "open_p0_p3_findings": 0,
        "closed_findings": 1,
    }

    protocol_by_id = {item["id"]: item for item in protocol["cohorts"]}
    cohorts = experiment["cohorts"]
    assert [item["id"] for item in cohorts] == ["canary", "business"]
    all_trajectory_ids = set()
    for cohort in cohorts:
        frozen_cohort = protocol_by_id[cohort["id"]]
        spec_path = ROOT / frozen_cohort["spec"]
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
        cases_path = spec_path.parent / spec["cases"]
        cases = json.loads(cases_path.read_text(encoding="utf-8"))
        assert cohort["role"] == frozen_cohort["role"]
        assert cohort["comparison_id"] == frozen_cohort["comparison_id"]
        assert cohort["source"]["spec_path"] == frozen_cohort["spec"]
        assert cohort["source"]["spec_sha256"] == sha256_file(spec_path)
        assert cohort["source"]["cases_path"] == cases_path.relative_to(
            ROOT
        ).as_posix()
        assert cohort["source"]["cases_sha256"] == sha256_file(cases_path)
        assert cohort["source"]["skill_package_sha256"] == frozen_cohort[
            "skill_package_sha256"
        ]

        jobs = [
            f"{case['id']}--{arm['id']}--r{repetition}"
            for case in cases
            for arm in spec["arms"]
            for repetition in range(1, protocol["repetitions"] + 1)
        ]
        expected_order = RUNNER["ordered_jobs"](jobs, protocol["job_order_seed"])
        assert set(cohort["run"]) == {
            "status",
            "started_at",
            "finished_at",
            "duration_ms",
            "repetitions",
            "max_workers",
            "job_order_seed",
            "job_order_sha256",
            "expected_trajectories",
            "result_trajectories",
            "valid_trajectories",
            "invalid_trajectories",
        }
        assert cohort["run"]["status"] == "completed"
        assert isinstance(cohort["run"]["started_at"], str)
        assert isinstance(cohort["run"]["finished_at"], str)
        assert isinstance(cohort["run"]["duration_ms"], int)
        assert cohort["run"]["duration_ms"] > 0
        assert {
            "status": "completed",
            "repetitions": 10,
            "max_workers": 4,
            "job_order_seed": 260913,
            "job_order_sha256": sha256_bytes(RUNNER["json_bytes"](expected_order)),
            "expected_trajectories": 40,
            "result_trajectories": 40,
            "valid_trajectories": 40,
            "invalid_trajectories": 0,
        }.items() <= cohort["run"].items()
        evidence = cohort["trajectory_evidence"]
        assert len(evidence) == 40
        assert [item["trajectory_id"] for item in evidence] == sorted(jobs)
        assert not all_trajectory_ids.intersection(jobs)
        all_trajectory_ids.update(jobs)
        for item in evidence:
            assert item["operational_success"] is True
            assert item["technical_valid"] is True
            assert item["failure_reasons"] == []
            assert item["agent_message_count"] == 1
            assert all(
                isinstance(item[field], str) and len(item[field]) == 64
                for field in ("output_sha256", "events_sha256", "stderr_sha256")
            )
        assert summarized_evidence(cohort) == cohort["arms"]
        assert cohort["incidents"] == []
        assert sum(item["trajectories"] for item in cohort["runtime"]) == 40

        if cohort["role"] == "canary":
            expected = frozen_cohort["expected_output_by_case"]
            for item in evidence:
                if item["arm_id"] == frozen_cohort["skill_arm"]:
                    assert item["output_sha256"] == sha256_text(
                        expected[item["case_id"]]
                    )

    assert len(all_trajectory_ids) == 80
    probe_path = COMPARISON / "fixtures" / "explicit-invocation-probe"
    business_path = ROOT / "skills" / "relationships" / "conversation-rehearsal"
    assert VALIDATOR["package_fingerprint"](probe_path) == protocol_by_id["canary"][
        "skill_package_sha256"
    ]
    assert VALIDATOR["package_fingerprint"](business_path) == protocol_by_id[
        "business"
    ]["skill_package_sha256"]

    gate_cohorts = [
        {
            "role": cohort["role"],
            "baseline_arm": protocol_by_id[cohort["id"]]["baseline_arm"],
            "skill_arm": protocol_by_id[cohort["id"]]["skill_arm"],
            "arms": cohort["arms"],
        }
        for cohort in cohorts
    ]
    recomputed_gate = ANALYZER["build_gate"](gate_cohorts)
    assert report["analysis"] == {
        "status": "qualified",
        "gate": recomputed_gate,
    }
    assert recomputed_gate["observed"] == {
        "baseline_technical_failures": 0,
        "canary_skill_failures": 0,
        "canary_secret_leaks": 0,
        "business_skill_failures": 0,
    }
    assert recomputed_gate["passed"] is True
    assert report["decision"] == {
        "explicit_loading_qualified": True,
        "business_transport_qualified": True,
        "infrastructure_investigation_opened": False,
        "quality_claim_changed": False,
        "skill_changed": False,
        "version_changed": False,
        "catalog_status_changed": False,
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


class ExplicitInvocationReliabilityRound26ReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))

    def test_report_recomputes_from_published_evidence(self):
        validate_report(self.report)

    def test_catalog_and_business_skill_remain_unchanged(self):
        catalog = json.loads(
            (ROOT / "catalog" / "collection.json").read_text(encoding="utf-8")
        )
        entry = next(
            item for item in catalog["skills"] if item["id"] == "conversation-rehearsal"
        )
        self.assertEqual(entry["version"], "0.1.1")
        self.assertEqual(entry["status"], "experimental")
        self.assertIsNone(entry["evidence"])

    def test_local_raw_runs_recompute_when_available(self):
        if not all(path.exists() for path in RUNS.values()):
            self.skipTest("ignored raw Round 26 runs are not present in this checkout")
        protocol = json.loads(PROTOCOL_PATH.read_text(encoding="utf-8"))
        protocol_by_id = {item["id"]: item for item in protocol["cohorts"]}
        report_by_id = {
            item["id"]: item for item in self.report["experiment"]["cohorts"]
        }
        recomputed = []
        for cohort_id, run_dir in RUNS.items():
            published = report_by_id[cohort_id]
            for name, expected_hash in published["artifacts"].items():
                self.assertEqual(sha256_file(run_dir / name), expected_hash)
            frozen, _, _, trajectories = ANALYZER["normalize_trajectories"](
                run_dir, ROOT
            )
            config = protocol_by_id[cohort_id]
            expected_by_case = config.get("expected_output_by_case", {})
            outcomes = [
                ANALYZER["classify_trajectory"](
                    trajectory,
                    config["role"],
                    config["baseline_arm"],
                    config["skill_arm"],
                    expected_by_case.get(trajectory["case_id"]),
                )
                for trajectory in trajectories
            ]
            self.assertEqual(
                sorted(outcomes, key=lambda item: item["trajectory_id"]),
                published["trajectory_evidence"],
            )
            self.assertEqual(
                ANALYZER["summarize_outcomes"](frozen, outcomes), published["arms"]
            )
            recomputed.append({
                "id": cohort_id,
                "role": config["role"],
                "baseline_arm": config["baseline_arm"],
                "skill_arm": config["skill_arm"],
                "arms": published["arms"],
            })
            for runtime in published["runtime"]:
                selected = [
                    item for item in trajectories if item["arm_id"] == runtime["arm_id"]
                ]
                self.assertEqual(
                    statistics.median(item["turns"][0]["duration_ms"] for item in selected),
                    runtime["median_latency_ms"],
                )
                for token_name, total in runtime["tokens_total"].items():
                    self.assertEqual(
                        sum(
                            item["turns"][0]["usage"].get(token_name, 0)
                            for item in selected
                        ),
                        total,
                    )
        self.assertEqual(
            ANALYZER["build_gate"](recomputed), self.report["analysis"]["gate"]
        )
        self.assertEqual(
            sha256_file(ANALYSIS_PATH),
            self.report["experiment"]["analysis_artifact"]["sha256"],
        )
        raw_analysis = json.loads(ANALYSIS_PATH.read_text(encoding="utf-8"))
        self.assertEqual(raw_analysis["status"], self.report["analysis"]["status"])
        self.assertEqual(raw_analysis["gate"], self.report["analysis"]["gate"])

    def test_coordinated_evidence_mutations_are_rejected(self):
        mutations = []
        changed_trajectory = copy.deepcopy(self.report)
        changed_trajectory["experiment"]["cohorts"][0]["trajectory_evidence"][0][
            "operational_success"
        ] = False
        mutations.append(changed_trajectory)
        changed_gate = copy.deepcopy(self.report)
        changed_gate["analysis"]["gate"]["passed"] = False
        mutations.append(changed_gate)
        changed_review = copy.deepcopy(self.report)
        changed_review["experiment"]["review_chain"]["postrun_independent_review"][
            "sha256"
        ] = "0" * 64
        mutations.append(changed_review)
        changed_decision = copy.deepcopy(self.report)
        changed_decision["decision"]["quality_claim_changed"] = True
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
