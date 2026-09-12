"""Analyze repeated explicit Skill invocation as an operational experiment."""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[2]
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_native_resume import (  # noqa: E402
    json_bytes,
    ordered_jobs,
    read_object,
    resolve_inside,
    sha256_bytes,
    sha256_file,
    write_json_once,
)
from summarize_native_resume import normalize_trajectories  # noqa: E402


SCHEMA_VERSION = 1
EXPECTED_GATE = {
    "require_full_repetitions": True,
    "max_baseline_technical_failures": 0,
    "max_canary_skill_failures": 0,
    "max_canary_secret_leaks": 0,
    "max_business_skill_failures": 0,
    "quality_scoring": False,
    "skill_change_authorized": False,
}
PROCESS_PATH_MARKERS = ("skill.md", ".agents", "get-content")


def validate_protocol(protocol: dict[str, object]) -> list[dict[str, object]]:
    if protocol.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"protocol schema_version must be {SCHEMA_VERSION}")
    if protocol.get("gate") != EXPECTED_GATE:
        raise ValueError("operational gate differs from the frozen zero-tolerance rule")
    infrastructure = protocol.get("infrastructure")
    if not isinstance(infrastructure, dict) or set(infrastructure) != {
        "preparer",
        "runner",
        "normalizer",
        "analyzer",
    }:
        raise ValueError("protocol must bind preparer, runner, normalizer, and analyzer")
    for item in infrastructure.values():
        if (
            not isinstance(item, dict)
            or not isinstance(item.get("path"), str)
            or not item["path"]
            or not isinstance(item.get("sha256"), str)
            or len(item["sha256"]) != 64
        ):
            raise ValueError("protocol infrastructure bindings are invalid")
    repetitions = protocol.get("repetitions")
    if (
        not isinstance(repetitions, int)
        or isinstance(repetitions, bool)
        or not 1 <= repetitions <= 10
    ):
        raise ValueError("protocol repetitions must be an integer from 1 to 10")
    seed = protocol.get("job_order_seed")
    if not isinstance(seed, int) or isinstance(seed, bool):
        raise ValueError("protocol job_order_seed must be an integer")
    cohorts = protocol.get("cohorts")
    if not isinstance(cohorts, list) or len(cohorts) != 2:
        raise ValueError("protocol must contain exactly two cohorts")
    ids = []
    roles = []
    for cohort in cohorts:
        if not isinstance(cohort, dict):
            raise ValueError("protocol cohorts must be objects")
        cohort_id = cohort.get("id")
        role = cohort.get("role")
        if not isinstance(cohort_id, str) or not cohort_id:
            raise ValueError("each cohort must have an id")
        if role not in {"canary", "business"}:
            raise ValueError("cohort role must be canary or business")
        for field in (
            "comparison_id",
            "spec",
            "spec_sha256",
            "baseline_arm",
            "skill_arm",
            "skill_package_sha256",
        ):
            if not isinstance(cohort.get(field), str) or not cohort[field]:
                raise ValueError(f"cohort {cohort_id} must define {field}")
        if len(cohort["spec_sha256"]) != 64 or len(cohort["skill_package_sha256"]) != 64:
            raise ValueError(f"cohort {cohort_id} hashes must be SHA-256 values")
        expected = cohort.get("expected_output_by_case")
        if role == "canary":
            if not isinstance(expected, dict) or len(expected) != 2 or not all(
                isinstance(key, str)
                and key
                and isinstance(value, str)
                and value
                for key, value in expected.items()
            ):
                raise ValueError("canary cohort must freeze two expected outputs")
        elif expected not in (None, {}):
            raise ValueError("business cohort cannot define expected canary outputs")
        ids.append(cohort_id)
        roles.append(role)
    if len(set(ids)) != len(ids) or set(roles) != {"canary", "business"}:
        raise ValueError("protocol needs unique canary and business cohorts")
    return cohorts


def completed_event_count(raw_events: object) -> int:
    if not isinstance(raw_events, str):
        return 0
    count = 0
    for line in raw_events.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        count += isinstance(event, dict) and event.get("type") == "turn.completed"
    return count


def discloses_skill_process(output: str) -> bool:
    lowered = output.lower()
    if any(marker in lowered for marker in PROCESS_PATH_MARKERS):
        return True
    return bool(
        re.search(r"(?:加载|读取|运行|使用).{0,12}(?:skill|技能)", lowered)
        or re.search(
            r"\b(?:load|loading|read|run|use|using)(?:\W+\w+){0,3}\W+skill\b",
            lowered,
        )
    )


def classify_trajectory(
    trajectory: dict[str, object],
    role: str,
    baseline_arm: str,
    skill_arm: str,
    expected_output: str | None,
) -> dict[str, object]:
    reasons = []
    turns = trajectory.get("turns")
    if trajectory.get("setup_valid") is not True:
        reasons.append("setup-failure")
    if not isinstance(turns, list) or len(turns) != 1 or not isinstance(turns[0], dict):
        reasons.append("turn-count-failure")
        turn = None
    else:
        turn = turns[0]
    if turn is not None:
        if turn.get("exit_code") != 0:
            reasons.append("nonzero-exit")
        if turn.get("error") is not None:
            reasons.append("execution-error")
        if turn.get("invalid_jsonl_lines"):
            reasons.append("invalid-jsonl")
        if len(turn.get("event_thread_ids", [])) != 1 or turn.get(
            "thread_matches_expected"
        ) is not True:
            reasons.append("thread-binding-failure")
        if completed_event_count(turn.get("raw_events")) != 1:
            reasons.append("turn-completion-failure")
        messages = turn.get("agent_messages")
        if not isinstance(messages, list) or len(messages) != 1:
            reasons.append("agent-message-count-failure")
        if turn.get("output_matches_last_agent_message") is not True:
            reasons.append("output-binding-failure")
        if turn.get("forbidden_item_types"):
            reasons.append("forbidden-item")
        stderr = turn.get("stderr")
        if isinstance(stderr, str) and "blocked by policy" in stderr.lower():
            reasons.append("policy-block")
        if turn.get("technical_valid") is not True:
            reasons.append("technical-invalid")

        actual = str(turn.get("raw_output", "")).rstrip("\r\n")
        if discloses_skill_process(actual):
            reasons.append("skill-process-disclosure")
        arm_id = trajectory.get("arm_id")
        if role == "canary" and arm_id == skill_arm and actual != expected_output:
            reasons.append("canary-output-miss")
        if (
            role == "canary"
            and arm_id == baseline_arm
            and isinstance(expected_output, str)
            and expected_output in actual
        ):
            reasons.append("canary-secret-leak")
    unique_reasons = sorted(set(reasons))
    return {
        "trajectory_id": trajectory.get("trajectory_id"),
        "case_id": trajectory.get("case_id"),
        "arm_id": trajectory.get("arm_id"),
        "repetition": trajectory.get("repetition"),
        "operational_success": not unique_reasons,
        "technical_valid": trajectory.get("technical_valid") is True,
        "failure_reasons": unique_reasons,
        "output_sha256": turn.get("output_sha256") if turn is not None else None,
        "events_sha256": turn.get("events_sha256") if turn is not None else None,
        "stderr_sha256": turn.get("stderr_sha256") if turn is not None else None,
        "agent_message_count": (
            len(turn.get("agent_messages", [])) if turn is not None else 0
        ),
    }


def summarize_outcomes(
    frozen: dict[str, object], outcomes: list[dict[str, object]]
) -> list[dict[str, object]]:
    summaries = []
    for arm in frozen["arms"]:
        selected = [item for item in outcomes if item["arm_id"] == arm["id"]]
        reasons = Counter(
            reason for item in selected for reason in item["failure_reasons"]
        )
        summaries.append(
            {
                "arm_id": arm["id"],
                "skill": arm.get("skill"),
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


def build_gate(cohorts: list[dict[str, object]]) -> dict[str, object]:
    by_role = {item["role"]: item for item in cohorts}
    canary = by_role["canary"]
    business = by_role["business"]

    def arm(cohort: dict[str, object], arm_id: str) -> dict[str, object]:
        return next(item for item in cohort["arms"] if item["arm_id"] == arm_id)

    baseline_failures = sum(
        arm(cohort, cohort["baseline_arm"])["attempts"]
        - arm(cohort, cohort["baseline_arm"])["technical_valid"]
        for cohort in cohorts
    )
    canary_skill_failures = arm(canary, canary["skill_arm"])[
        "operational_failures"
    ]
    canary_secret_leaks = arm(canary, canary["baseline_arm"])[
        "failure_reason_counts"
    ].get("canary-secret-leak", 0)
    business_skill_failures = arm(business, business["skill_arm"])[
        "operational_failures"
    ]
    checks = {
        "baseline_technical_failures_within_limit": baseline_failures
        <= EXPECTED_GATE["max_baseline_technical_failures"],
        "canary_skill_failures_within_limit": canary_skill_failures
        <= EXPECTED_GATE["max_canary_skill_failures"],
        "canary_secret_leaks_within_limit": canary_secret_leaks
        <= EXPECTED_GATE["max_canary_secret_leaks"],
        "business_skill_failures_within_limit": business_skill_failures
        <= EXPECTED_GATE["max_business_skill_failures"],
    }
    return {
        "rule": EXPECTED_GATE,
        "observed": {
            "baseline_technical_failures": baseline_failures,
            "canary_skill_failures": canary_skill_failures,
            "canary_secret_leaks": canary_secret_leaks,
            "business_skill_failures": business_skill_failures,
        },
        "checks": checks,
        "passed": all(checks.values()),
    }


def require_output_inside_runs(output_path: Path, run_dirs: list[Path]) -> Path:
    resolved = output_path.resolve()
    if not any(resolved.is_relative_to(run_dir.resolve()) for run_dir in run_dirs):
        raise ValueError("analysis output must stay inside a validated run directory")
    return resolved


def analyze_runs(
    protocol_path: Path,
    run_dirs: dict[str, Path],
    output_path: Path,
    root: Path = ROOT,
) -> dict[str, object]:
    protocol_path = protocol_path.resolve()
    try:
        protocol_path.relative_to(root.resolve())
    except ValueError as error:
        raise ValueError("operational protocol must stay inside the repository") from error
    protocol = read_object(protocol_path, "operational protocol")
    cohorts = validate_protocol(protocol)
    for item in protocol["infrastructure"].values():
        path = resolve_inside(root, item["path"], "infrastructure path")
        if sha256_file(path) != item["sha256"]:
            raise ValueError("operational infrastructure hash differs from protocol")
    if set(run_dirs) != {cohort["id"] for cohort in cohorts}:
        raise ValueError("run mapping must cover every frozen cohort exactly")
    resolved_run_dirs = {key: value.resolve() for key, value in run_dirs.items()}
    output_path = require_output_inside_runs(
        output_path, list(resolved_run_dirs.values())
    )
    analyzed = []
    for cohort in cohorts:
        run_dir = resolved_run_dirs[cohort["id"]]
        frozen, run_meta, cases, trajectories = normalize_trajectories(run_dir, root)
        if frozen.get("comparison_kind") != "operational":
            raise ValueError("reliability analysis requires operational comparisons")
        if frozen.get("comparison_id") != cohort["comparison_id"]:
            raise ValueError("run comparison id differs from the frozen cohort")
        spec_path = resolve_inside(root, cohort["spec"], "cohort spec")
        if frozen.get("spec_path") != spec_path.relative_to(root).as_posix():
            raise ValueError("run spec path differs from the frozen cohort")
        if sha256_file(spec_path) != cohort["spec_sha256"]:
            raise ValueError("cohort spec hash differs from the operational protocol")
        if frozen.get("model") != protocol["model"] or frozen.get(
            "reasoning_effort"
        ) != protocol["reasoning_effort"]:
            raise ValueError("run model settings differ from the operational protocol")
        if frozen.get("repetitions") != protocol["repetitions"] or run_meta.get(
            "repeat"
        ) != protocol["repetitions"]:
            raise ValueError("run does not contain every frozen repetition")
        if run_meta.get("job_order_seed") != protocol["job_order_seed"]:
            raise ValueError("run job order seed differs from the operational protocol")
        jobs = [
            f"{case['id']}--{arm['id']}--r{repetition}"
            for case in cases
            for arm in frozen["arms"]
            for repetition in range(1, protocol["repetitions"] + 1)
        ]
        expected_order = ordered_jobs(jobs, protocol["job_order_seed"])
        if run_meta.get("job_order") != expected_order or run_meta.get(
            "job_order_sha256"
        ) != sha256_bytes(json_bytes(expected_order)):
            raise ValueError("run job order does not match the frozen shuffle")
        arm_ids = {arm["id"] for arm in frozen["arms"]}
        if arm_ids != {cohort["baseline_arm"], cohort["skill_arm"]}:
            raise ValueError("run arms differ from the frozen cohort")
        skill_arm = next(
            arm for arm in frozen["arms"] if arm["id"] == cohort["skill_arm"]
        )
        if skill_arm.get("skill_package_sha256") != cohort["skill_package_sha256"]:
            raise ValueError("run Skill package differs from the operational protocol")
        expected_by_case = cohort.get("expected_output_by_case", {})
        outcomes = [
            classify_trajectory(
                trajectory,
                cohort["role"],
                cohort["baseline_arm"],
                cohort["skill_arm"],
                expected_by_case.get(trajectory["case_id"]),
            )
            for trajectory in trajectories
        ]
        analyzed.append(
            {
                "id": cohort["id"],
                "role": cohort["role"],
                "comparison_id": cohort["comparison_id"],
                "run_dir_name": run_dir.name,
                "frozen_sha256": sha256_file(run_dir / "frozen.json"),
                "results_sha256": sha256_file(run_dir / "native-results.json"),
                "run_meta_sha256": sha256_file(run_dir / "run-meta.json"),
                "baseline_arm": cohort["baseline_arm"],
                "skill_arm": cohort["skill_arm"],
                "arms": summarize_outcomes(frozen, outcomes),
                "incidents": [item for item in outcomes if not item["operational_success"]],
            }
        )
    gate = build_gate(analyzed)
    result = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": protocol["id"],
        "status": "qualified" if gate["passed"] else "reliability-issue-observed",
        "protocol_path": protocol_path.relative_to(root).as_posix(),
        "protocol_sha256": sha256_file(protocol_path),
        "model": protocol["model"],
        "reasoning_effort": protocol["reasoning_effort"],
        "repetitions": protocol["repetitions"],
        "quality_scored": False,
        "cohorts": analyzed,
        "gate": gate,
        "decision": {
            "explicit_loading_qualified": gate["passed"],
            "infrastructure_investigation_opened": not gate["passed"],
            "skill_change_authorized": False,
        },
    }
    write_json_once(output_path, result)
    print(f"[DONE] invocation reliability analysis: {result['status']} ({output_path})")
    return result


def parse_run(value: str) -> tuple[str, Path]:
    cohort_id, separator, raw_path = value.partition("=")
    if not separator or not cohort_id or not raw_path:
        raise argparse.ArgumentTypeError("runs must use COHORT=PATH")
    return cohort_id, Path(raw_path)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", required=True, type=Path)
    parser.add_argument("--run", action="append", required=True, type=parse_run)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    run_dirs = dict(args.run)
    if len(run_dirs) != len(args.run):
        raise ValueError("run mapping contains duplicate cohort ids")
    analyze_runs(args.protocol, run_dirs, args.output)


if __name__ == "__main__":
    main()
