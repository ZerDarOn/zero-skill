"""Analyze natural project Skill routing separately from body loading."""

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
    "max_baseline_route_false_positives": 0,
    "max_baseline_secret_leaks": 0,
    "max_baseline_output_misses": 0,
    "max_baseline_policy_blocks": 0,
    "max_baseline_transport_failures": 0,
    "max_probe_route_selection_failures": 0,
    "max_probe_body_load_failures": 0,
    "max_probe_policy_blocks": 0,
    "max_probe_transport_failures": 0,
    "business_comparison_requires_pass": True,
    "quality_scoring": False,
    "skill_change_authorized": False,
}


def validate_protocol(protocol: dict[str, object]) -> dict[str, object]:
    if protocol.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"protocol schema_version must be {SCHEMA_VERSION}")
    if protocol.get("gate") != EXPECTED_GATE:
        raise ValueError("discovery gate differs from the frozen zero-tolerance rule")
    infrastructure = protocol.get("infrastructure")
    if not isinstance(infrastructure, dict) or set(infrastructure) != {
        "preparer",
        "runner",
        "normalizer",
        "analyzer",
    }:
        raise ValueError("protocol must bind all discovery infrastructure")
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
        raise ValueError("protocol repetitions must be from 1 through 10")
    if not isinstance(protocol.get("job_order_seed"), int) or isinstance(
        protocol["job_order_seed"], bool
    ):
        raise ValueError("protocol job_order_seed must be an integer")
    cohort = protocol.get("cohort")
    if not isinstance(cohort, dict):
        raise ValueError("protocol must contain one discovery cohort")
    for field in (
        "comparison_id",
        "spec",
        "spec_sha256",
        "cases",
        "cases_sha256",
        "baseline_arm",
        "probe_arm",
        "probe_skill",
        "skill_package_sha256",
        "fallback_output",
    ):
        if not isinstance(cohort.get(field), str) or not cohort[field]:
            raise ValueError(f"discovery cohort must define {field}")
    expected = cohort.get("expected_output_by_case")
    if not isinstance(expected, dict) or len(expected) != 2 or not all(
        isinstance(key, str)
        and key
        and isinstance(value, str)
        and value
        for key, value in expected.items()
    ):
        raise ValueError("discovery cohort must freeze two expected outputs")
    if len(set(expected.values())) != 2:
        raise ValueError("discovery outputs must be unique")
    return cohort


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


def normalized_trace(value: object) -> str:
    if not isinstance(value, str):
        return ""
    return re.sub(r"/+", "/", value.lower().replace("\\", "/"))


def route_marker(skill_id: str) -> str:
    return f".agents/skills/{skill_id.lower()}/skill.md"


def command_targets_skill(command: object, skill_id: str) -> bool:
    normalized = normalized_trace(command)
    marker = re.escape(route_marker(skill_id))
    return bool(
        re.search(
            rf"(?<![a-z0-9_.-]){marker}(?![a-z0-9_.-])",
            normalized,
        )
    )


def selected_route(turn: dict[str, object], skill_id: str) -> bool:
    if any(
        command_targets_skill(item.get("command"), skill_id)
        for item in command_execution_items(turn.get("raw_events"))
    ):
        return True
    stderr = turn.get("stderr")
    if not isinstance(stderr, str):
        return False
    return any(
        "exec_command failed" in line.lower()
        and command_targets_skill(line, skill_id)
        for line in stderr.splitlines()
    )


def command_execution_items(raw_events: object) -> list[dict[str, object]]:
    if not isinstance(raw_events, str):
        return []
    items = []
    for line in raw_events.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        item = event.get("item") if isinstance(event, dict) else None
        if isinstance(item, dict) and item.get("type") == "command_execution":
            items.append(item)
    return items


def is_narrow_skill_read(item: dict[str, object], skill_id: str) -> bool:
    command = item.get("command")
    if (
        not isinstance(command, str)
        or item.get("status") != "completed"
        or item.get("exit_code") != 0
    ):
        return False
    normalized = normalized_trace(command)
    if not command_targets_skill(command, skill_id):
        return False
    if any(
        marker in command
        for marker in (
            ";",
            "&&",
            "||",
            "|",
            "&",
            "\r",
            "\n",
            ">",
            "<",
            "`",
            "$(",
        )
    ):
        return False
    marker = re.escape(route_marker(skill_id))
    path = rf"(?:\"[^\"]*{marker}\"|'[^']*{marker}'|\S*{marker})"
    patterns = (
        rf"get-content(?:\s+-(?:raw|literalpath))*\s+{path}",
        rf"(?:type|cat)\s+{path}",
        rf"rg(?:\s+--?[a-z-]+(?:=[^\s]+)?)*\s+(?:\"\.\"|'\.'|\.)\s+{path}",
    )
    return any(re.fullmatch(pattern, normalized) for pattern in patterns)


def transport_reasons(
    turn: dict[str, object] | None, skill_id: str, allow_skill_read: bool
) -> list[str]:
    if turn is None:
        return ["turn-count-failure"]
    reasons = []
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
    if not isinstance(turn.get("raw_output"), str) or not turn["raw_output"].strip():
        reasons.append("empty-output")
    forbidden = set(turn.get("forbidden_item_types", []))
    if forbidden - {"command_execution"}:
        reasons.append("forbidden-item")
    commands = command_execution_items(turn.get("raw_events"))
    if commands and (
        not allow_skill_read
        or any(not is_narrow_skill_read(item, skill_id) for item in commands)
    ):
        reasons.append("unexpected-command")
    return reasons


def classify_trajectory(
    trajectory: dict[str, object],
    baseline_arm: str,
    probe_arm: str,
    skill_id: str,
    expected_output: str,
    fallback_output: str,
) -> dict[str, object]:
    turns = trajectory.get("turns")
    turn = (
        turns[0]
        if isinstance(turns, list) and len(turns) == 1 and isinstance(turns[0], dict)
        else None
    )
    reasons = []
    if trajectory.get("setup_valid") is not True:
        reasons.append("setup-failure")
    arm_id = trajectory.get("arm_id")
    reasons.extend(transport_reasons(turn, skill_id, arm_id == probe_arm))
    route_selected = bool(turn is not None and selected_route(turn, skill_id))
    actual = str(turn.get("raw_output", "")).rstrip("\r\n") if turn else ""
    policy_blocked = bool(
        turn is not None
        and "blocked by policy" in str(turn.get("stderr", "")).lower()
    )
    body_loaded = actual == expected_output
    secret_leak = arm_id == baseline_arm and expected_output in actual
    fallback_matched = actual == fallback_output
    if policy_blocked:
        reasons.append("policy-block")
    if arm_id == baseline_arm:
        if route_selected:
            reasons.append("baseline-route-false-positive")
        if secret_leak:
            reasons.append("baseline-secret-leak")
        if not fallback_matched:
            reasons.append("baseline-output-miss")
    elif arm_id == probe_arm:
        if not route_selected:
            reasons.append("probe-route-selection-miss")
        if not body_loaded:
            reasons.append("probe-body-load-miss")
    else:
        reasons.append("unknown-arm")
    unique_reasons = sorted(set(reasons))
    transport_failures = {
        reason
        for reason in unique_reasons
        if reason
        in {
            "setup-failure",
            "turn-count-failure",
            "nonzero-exit",
            "execution-error",
            "invalid-jsonl",
            "thread-binding-failure",
            "turn-completion-failure",
            "agent-message-count-failure",
            "output-binding-failure",
            "forbidden-item",
            "unexpected-command",
            "empty-output",
        }
    }
    return {
        "trajectory_id": trajectory.get("trajectory_id"),
        "case_id": trajectory.get("case_id"),
        "arm_id": arm_id,
        "repetition": trajectory.get("repetition"),
        "route_selected": route_selected,
        "body_loaded": body_loaded,
        "policy_blocked": policy_blocked,
        "transport_valid": not transport_failures,
        "fallback_matched": fallback_matched,
        "secret_leak": secret_leak,
        "operational_success": not unique_reasons,
        "failure_reasons": unique_reasons,
        "output_sha256": turn.get("output_sha256") if turn else None,
        "events_sha256": turn.get("events_sha256") if turn else None,
        "stderr_sha256": turn.get("stderr_sha256") if turn else None,
        "agent_message_count": len(turn.get("agent_messages", [])) if turn else 0,
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
                "route_selected": sum(item["route_selected"] for item in selected),
                "body_loaded": sum(item["body_loaded"] for item in selected),
                "policy_blocked": sum(item["policy_blocked"] for item in selected),
                "transport_valid": sum(item["transport_valid"] for item in selected),
                "operational_successes": sum(
                    item["operational_success"] for item in selected
                ),
                "failure_reason_counts": dict(sorted(reasons.items())),
            }
        )
    return summaries


def build_gate(
    summaries: list[dict[str, object]], baseline_arm: str, probe_arm: str
) -> dict[str, object]:
    by_arm = {item["arm_id"]: item for item in summaries}
    baseline = by_arm[baseline_arm]
    probe = by_arm[probe_arm]
    observed = {
        "baseline_route_false_positives": baseline["failure_reason_counts"].get(
            "baseline-route-false-positive", 0
        ),
        "baseline_secret_leaks": baseline["failure_reason_counts"].get(
            "baseline-secret-leak", 0
        ),
        "baseline_output_misses": baseline["failure_reason_counts"].get(
            "baseline-output-miss", 0
        ),
        "baseline_policy_blocks": baseline["failure_reason_counts"].get(
            "policy-block", 0
        ),
        "baseline_transport_failures": baseline["attempts"]
        - baseline["transport_valid"],
        "probe_route_selection_failures": probe["failure_reason_counts"].get(
            "probe-route-selection-miss", 0
        ),
        "probe_body_load_failures": probe["failure_reason_counts"].get(
            "probe-body-load-miss", 0
        ),
        "probe_policy_blocks": probe["failure_reason_counts"].get("policy-block", 0),
        "probe_transport_failures": probe["attempts"] - probe["transport_valid"],
    }
    checks = {
        key.replace("probe_", "probe_").replace("baseline_", "baseline_")
        + "_within_limit": observed[key]
        <= EXPECTED_GATE["max_" + key]
        for key in observed
    }
    return {
        "rule": EXPECTED_GATE,
        "observed": observed,
        "checks": checks,
        "passed": all(checks.values()),
    }


def diagnostic_status(gate: dict[str, object], probe_attempts: int) -> str:
    if gate["passed"]:
        return "implicit-loading-qualified"
    observed = gate["observed"]
    if observed["probe_route_selection_failures"] == probe_attempts:
        return "routing-not-demonstrated"
    if observed["probe_body_load_failures"] or observed["probe_policy_blocks"]:
        return "route-selected-load-blocked"
    return "infrastructure-invalid"


def analyze_run(
    protocol_path: Path,
    run_dir: Path,
    output_path: Path,
    root: Path = ROOT,
) -> dict[str, object]:
    protocol_path = protocol_path.resolve()
    try:
        protocol_path.relative_to(root.resolve())
    except ValueError as error:
        raise ValueError("discovery protocol must stay inside the repository") from error
    protocol = read_object(protocol_path, "discovery protocol")
    cohort = validate_protocol(protocol)
    for item in protocol["infrastructure"].values():
        path = resolve_inside(root, item["path"], "infrastructure path")
        if sha256_file(path) != item["sha256"]:
            raise ValueError("discovery infrastructure hash differs from protocol")
    run_dir = run_dir.resolve()
    output_path = output_path.resolve()
    if not output_path.is_relative_to(run_dir):
        raise ValueError("analysis output must stay inside the validated run directory")
    frozen, run_meta, cases, trajectories = normalize_trajectories(run_dir, root)
    if frozen.get("comparison_kind") != "discovery":
        raise ValueError("implicit discovery analysis requires discovery comparison")
    if frozen.get("comparison_id") != cohort["comparison_id"]:
        raise ValueError("run comparison id differs from the frozen cohort")
    spec_path = resolve_inside(root, cohort["spec"], "discovery spec")
    if frozen.get("spec_path") != spec_path.relative_to(root).as_posix() or sha256_file(
        spec_path
    ) != cohort["spec_sha256"]:
        raise ValueError("run spec differs from the discovery protocol")
    cases_path = resolve_inside(root, cohort["cases"], "discovery cases")
    if frozen.get("cases_path") != cases_path.relative_to(root).as_posix() or sha256_file(
        cases_path
    ) != cohort["cases_sha256"]:
        raise ValueError("run cases differ from the discovery protocol")
    if frozen.get("model") != protocol["model"] or frozen.get(
        "reasoning_effort"
    ) != protocol["reasoning_effort"]:
        raise ValueError("run model settings differ from the discovery protocol")
    if frozen.get("repetitions") != protocol["repetitions"] or run_meta.get(
        "repeat"
    ) != protocol["repetitions"]:
        raise ValueError("run does not contain every frozen repetition")
    if run_meta.get("job_order_seed") != protocol["job_order_seed"]:
        raise ValueError("run job order seed differs from the discovery protocol")
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
    if arm_ids != {cohort["baseline_arm"], cohort["probe_arm"]}:
        raise ValueError("run arms differ from the discovery cohort")
    probe = next(arm for arm in frozen["arms"] if arm["id"] == cohort["probe_arm"])
    if probe.get("skill") != cohort["probe_skill"] or probe.get(
        "skill_package_sha256"
    ) != cohort["skill_package_sha256"]:
        raise ValueError("run probe package differs from the discovery protocol")
    expected = cohort["expected_output_by_case"]
    outcomes = [
        classify_trajectory(
            trajectory,
            cohort["baseline_arm"],
            cohort["probe_arm"],
            cohort["probe_skill"],
            expected[trajectory["case_id"]],
            cohort["fallback_output"],
        )
        for trajectory in trajectories
    ]
    summaries = summarize_outcomes(frozen, outcomes)
    gate = build_gate(summaries, cohort["baseline_arm"], cohort["probe_arm"])
    probe_attempts = next(
        item["attempts"] for item in summaries if item["arm_id"] == cohort["probe_arm"]
    )
    status = diagnostic_status(gate, probe_attempts)
    result = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": protocol["id"],
        "status": status,
        "protocol_path": protocol_path.relative_to(root).as_posix(),
        "protocol_sha256": sha256_file(protocol_path),
        "run_dir_name": run_dir.name,
        "frozen_sha256": sha256_file(run_dir / "frozen.json"),
        "results_sha256": sha256_file(run_dir / "native-results.json"),
        "run_meta_sha256": sha256_file(run_dir / "run-meta.json"),
        "model": protocol["model"],
        "reasoning_effort": protocol["reasoning_effort"],
        "repetitions": protocol["repetitions"],
        "quality_scored": False,
        "arms": summaries,
        "outcomes": outcomes,
        "incidents": [item for item in outcomes if not item["operational_success"]],
        "gate": gate,
        "decision": {
            "business_comparison_authorized": gate["passed"],
            "infrastructure_investigation_opened": not gate["passed"],
            "skill_change_authorized": False,
        },
    }
    write_json_once(output_path, result)
    print(f"[DONE] implicit discovery analysis: {status} ({output_path})")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", required=True, type=Path)
    parser.add_argument("--run", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    analyze_run(args.protocol, args.run, args.output)


if __name__ == "__main__":
    main()
