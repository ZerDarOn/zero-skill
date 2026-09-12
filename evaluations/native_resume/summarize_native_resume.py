"""Validate native-resume evidence and build a trajectory-level blind packet."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import secrets
import statistics
import sys


ROOT = Path(__file__).resolve().parents[2]
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_native_resume import (  # noqa: E402
    agent_messages,
    event_thread_ids,
    forbidden_item_types,
    item_types,
    json_bytes,
    load_prepared_prompts,
    load_trajectory_cases,
    parse_jsonl,
    read_object,
    sha256_bytes,
    sha256_file,
    verify_execution_fixtures,
    verify_prepared,
    verify_source_spec,
    write_json_once,
)

SCHEMA_VERSION = 1


def numeric(value: object) -> int:
    return int(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else 0


def validate_turn(
    turn: dict[str, object],
    index: int,
    source_message: str,
    expected_prompt: str,
    expected_thread_id: str | None,
    prior_hashes: list[str],
) -> tuple[bool, str | None]:
    if turn.get("turn_index") != index:
        raise ValueError("trajectory turns are missing or out of order")
    if turn.get("source_user_message") != source_message:
        raise ValueError("turn source user message does not match the frozen trajectory")
    if turn.get("submitted_prompt") != expected_prompt:
        raise ValueError("turn submitted prompt does not match the prepared/current user message")
    if turn.get("prompt_sha256") != sha256_bytes(expected_prompt.encode("utf-8")):
        raise ValueError("turn prompt hash does not match submitted prompt")
    output = turn.get("raw_output")
    events_text = turn.get("raw_events")
    stderr = turn.get("stderr")
    if not all(isinstance(value, str) for value in (output, events_text, stderr)):
        raise ValueError("turn output, events, and stderr must be strings")
    if turn.get("output_sha256") != sha256_bytes(output.encode("utf-8")):
        raise ValueError("turn output hash does not match raw output")
    if turn.get("events_sha256") != sha256_bytes(events_text.encode("utf-8")):
        raise ValueError("turn events hash does not match raw events")
    if turn.get("stderr_sha256") != sha256_bytes(stderr.encode("utf-8")):
        raise ValueError("turn stderr hash does not match raw stderr")
    if turn.get("prior_output_sha256") != prior_hashes:
        raise ValueError("turn prior-output hash chain does not match actual earlier outputs")
    if turn.get("expected_thread_id") != expected_thread_id:
        raise ValueError("turn expected thread id does not match trajectory state")
    events, invalid_lines = parse_jsonl(events_text.encode("utf-8"))
    thread_ids = event_thread_ids(events)
    types = item_types(events)
    forbidden = forbidden_item_types(types)
    completed = [event for event in events if event.get("type") == "turn.completed"]
    observed_thread_id = thread_ids[0] if len(thread_ids) == 1 else None
    thread_matches = observed_thread_id is not None and (
        expected_thread_id is None or observed_thread_id == expected_thread_id
    )
    if turn.get("invalid_jsonl_lines") != invalid_lines:
        raise ValueError("stored invalid JSONL lines do not match raw events")
    if turn.get("event_thread_ids") != thread_ids:
        raise ValueError("stored event thread ids do not match raw events")
    if turn.get("thread_id") != observed_thread_id:
        raise ValueError("stored thread id does not match raw events")
    if turn.get("thread_matches_expected") is not thread_matches:
        raise ValueError("stored thread match result is inconsistent")
    if turn.get("item_types") != types:
        raise ValueError("stored item types do not match raw events")
    if turn.get("forbidden_item_types") != forbidden:
        raise ValueError("stored forbidden item types do not match raw events")
    messages = agent_messages(events)
    output_matches_last_message = (
        len(messages) == 1
        and output.rstrip("\r\n") == messages[0].rstrip("\r\n")
    )
    if turn.get("agent_messages") != messages:
        raise ValueError("stored agent messages do not match raw events")
    if turn.get("output_matches_last_agent_message") is not output_matches_last_message:
        raise ValueError("stored output-to-event binding is inconsistent")
    expected_usage = completed[0].get("usage") if len(completed) == 1 else None
    if turn.get("usage") != expected_usage:
        raise ValueError("stored usage does not match completion event")
    technical_valid = (
        turn.get("exit_code") == 0
        and turn.get("error") is None
        and bool(output)
        and not invalid_lines
        and len(thread_ids) == 1
        and thread_matches
        and len(completed) == 1
        and output_matches_last_message
        and not forbidden
    )
    if turn.get("technical_valid") is not technical_valid:
        raise ValueError("stored turn technical validity is inconsistent")
    command = turn.get("command")
    if not isinstance(command, list) or not all(isinstance(part, str) for part in command):
        raise ValueError("stored command must be a string list")
    if "--last" in command or "--ephemeral" in command:
        raise ValueError("stored native resume command uses a forbidden session selector")
    if 'sandbox_mode="read-only"' not in command:
        raise ValueError("every native command must explicitly retain read-only sandbox mode")
    if command[-1:] != ["-"]:
        raise ValueError("native command must read exactly the current user message from stdin")
    if index == 1:
        if command[:2] != ["<codex>", "exec"] or "resume" in command:
            raise ValueError("first turn command is not a fresh explicit session")
        if "--sandbox" not in command or "read-only" not in command:
            raise ValueError("first turn command is missing the read-only sandbox")
    else:
        if command[:3] != ["<codex>", "exec", "resume"]:
            raise ValueError("later turn command does not use native resume")
        if command[-2] != expected_thread_id or command.count(expected_thread_id) != 1:
            raise ValueError("later turn command has an invalid explicit thread selector")
    return technical_valid, observed_thread_id


def normalize_trajectories(
    run_dir: Path, root: Path = ROOT
) -> tuple[
    dict[str, object],
    dict[str, object],
    list[dict[str, object]],
    list[dict[str, object]],
]:
    run_dir = run_dir.resolve()
    frozen = read_object(run_dir / "frozen.json", "frozen evidence")
    run_meta = read_object(run_dir / "run-meta.json", "run metadata")
    verify_prepared(run_dir, frozen)
    fixture_manifests = verify_execution_fixtures(run_dir, frozen)
    if run_meta.get("execution_fixture_manifests") != fixture_manifests:
        raise ValueError("run metadata execution fixture manifests are inconsistent")
    verify_source_spec(root, frozen)
    cases = load_trajectory_cases(root, frozen)
    prompts = load_prepared_prompts(run_dir, frozen)
    if run_meta.get("frozen_sha256") != sha256_file(run_dir / "frozen.json"):
        raise ValueError("frozen evidence hash does not match run metadata")
    if not str(run_meta.get("status", "")).startswith("completed"):
        raise ValueError("run metadata does not describe a completed evaluation")
    if run_meta.get("resume_last_used") is not False or run_meta.get("ephemeral_used") is not False:
        raise ValueError("run metadata does not preserve explicit persistent sessions")
    results_path = run_dir / "native-results.json"
    if run_meta.get("results_sha256") != sha256_file(results_path):
        raise ValueError("native results hash does not match run metadata")
    payload = read_object(results_path, "native results")
    if payload.get("comparison_id") != frozen.get("comparison_id"):
        raise ValueError("native results comparison id does not match frozen evidence")
    trajectories = payload.get("trajectories")
    if not isinstance(trajectories, list) or not all(isinstance(item, dict) for item in trajectories):
        raise ValueError("native results must contain trajectory objects")
    repeat = run_meta.get("repeat")
    if not isinstance(repeat, int) or isinstance(repeat, bool) or not 1 <= repeat <= frozen["repetitions"]:
        raise ValueError("run metadata repeat is invalid")
    case_by_id = {case["id"]: case for case in cases}
    arm_by_id = {arm["id"]: arm for arm in frozen["arms"]}
    expected_keys = {
        (case["id"], arm["id"], repetition)
        for case in cases
        for arm in frozen["arms"]
        for repetition in range(1, repeat + 1)
    }
    seen_keys = set()
    seen_thread_ids: dict[str, str] = {}
    for trajectory in trajectories:
        key = (
            trajectory.get("case_id"),
            trajectory.get("arm_id"),
            trajectory.get("repetition"),
        )
        if key in seen_keys:
            raise ValueError("native results contain a duplicate trajectory")
        seen_keys.add(key)
        if key not in expected_keys:
            raise ValueError("native results contain an unknown trajectory")
        case = case_by_id[key[0]]
        arm = arm_by_id[key[1]]
        expected_id = f"{key[0]}--{key[1]}--r{key[2]}"
        if trajectory.get("trajectory_id") != expected_id:
            raise ValueError("trajectory id is inconsistent with case/arm/repetition")
        if trajectory.get("mechanism") != case["mechanism"]:
            raise ValueError("trajectory mechanism differs from frozen case")
        if trajectory.get("purpose") != case.get("purpose"):
            raise ValueError("trajectory purpose differs from frozen case")
        if trajectory.get("hard_criteria") != case["hard_criteria"]:
            raise ValueError("trajectory criteria differ from frozen case")
        if trajectory.get("source_user_turns") != case["turns"]:
            raise ValueError("trajectory user turns differ from frozen case")
        if trajectory.get("source_user_turns_sha256") != sha256_bytes(json_bytes(case["turns"])):
            raise ValueError("trajectory user-turn hash is inconsistent")
        if trajectory.get("skill") != arm.get("skill"):
            raise ValueError("trajectory skill identity differs from frozen arm")
        if trajectory.get("skill_package_sha256") != arm.get("skill_package_sha256"):
            raise ValueError("trajectory skill package differs from frozen arm")
        turns = trajectory.get("turns")
        if not isinstance(turns, list) or not all(isinstance(turn, dict) for turn in turns):
            raise ValueError("trajectory turns must be objects")
        thread_id = None
        prior_hashes: list[str] = []
        all_turns_valid = True
        for index, turn in enumerate(turns, 1):
            source_message = case["turns"][index - 1]
            expected_prompt = prompts[(case["id"], arm["id"])] if index == 1 else source_message
            turn_valid, observed = validate_turn(
                turn,
                index,
                source_message,
                expected_prompt,
                thread_id,
                prior_hashes,
            )
            all_turns_valid = all_turns_valid and turn_valid
            if index == 1 and observed is not None:
                thread_id = observed
            prior_hashes.append(turn["output_sha256"])
        expected_trajectory_valid = (
            trajectory.get("setup_valid") is True
            and len(turns) == len(case["turns"])
            and all_turns_valid
            and isinstance(thread_id, str)
        )
        if trajectory.get("technical_valid") is not expected_trajectory_valid:
            raise ValueError("stored trajectory technical validity is inconsistent")
        if trajectory.get("thread_id") != thread_id:
            raise ValueError("stored trajectory thread id is inconsistent")
        if thread_id is not None:
            previous = seen_thread_ids.get(thread_id)
            if previous is not None and previous != expected_id:
                raise ValueError("thread id is reused across trajectories")
            seen_thread_ids[thread_id] = expected_id
    if seen_keys != expected_keys:
        raise ValueError("native results do not cover every frozen trajectory")
    if run_meta.get("expected_trajectories") != len(expected_keys):
        raise ValueError("run metadata expected trajectory count is inconsistent")
    if run_meta.get("result_trajectories") != len(trajectories):
        raise ValueError("run metadata result trajectory count is inconsistent")
    expected_turns = sum(len(case["turns"]) for case in cases) * len(frozen["arms"]) * repeat
    actual_turns = sum(len(trajectory["turns"]) for trajectory in trajectories)
    if run_meta.get("expected_turns") != expected_turns or run_meta.get("result_turns") != actual_turns:
        raise ValueError("run metadata turn counts are inconsistent")
    valid_count = sum(trajectory["technical_valid"] for trajectory in trajectories)
    if run_meta.get("valid_trajectories") != valid_count:
        raise ValueError("run metadata valid trajectory count is inconsistent")
    if run_meta.get("invalid_trajectories") != len(trajectories) - valid_count:
        raise ValueError("run metadata invalid trajectory count is inconsistent")
    return frozen, run_meta, cases, trajectories


def arm_summaries(
    frozen: dict[str, object], trajectories: list[dict[str, object]]
) -> list[dict[str, object]]:
    summaries = []
    for arm in frozen["arms"]:
        selected = [item for item in trajectories if item["arm_id"] == arm["id"]]
        turns = [turn for trajectory in selected for turn in trajectory["turns"]]
        durations = [turn["duration_ms"] for turn in turns]
        usage_keys = sorted(
            {
                key
                for turn in turns
                if isinstance(turn.get("usage"), dict)
                for key in turn["usage"]
            }
        )
        summaries.append(
            {
                "id": arm["id"],
                "skill": arm.get("skill"),
                "install_mode": arm.get("install_mode"),
                "invocation": arm.get("invocation"),
                "skill_package_sha256": arm.get("skill_package_sha256"),
                "trajectories": len(selected),
                "valid_trajectories": sum(item["technical_valid"] for item in selected),
                "turns": len(turns),
                "valid_turns": sum(turn["technical_valid"] for turn in turns),
                "latency_ms_median_per_turn": (
                    round(statistics.median(durations), 2) if durations else None
                ),
                "tokens_total": {
                    key: sum(numeric(turn.get("usage", {}).get(key)) for turn in turns)
                    for key in usage_keys
                },
            }
        )
    return summaries


def anonymized_review(
    frozen: dict[str, object],
    cases: list[dict[str, object]],
    trajectories: list[dict[str, object]],
    randomization_salt: str | None = None,
) -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    randomization_salt = randomization_salt or secrets.token_hex(32)
    arm_by_id = {arm["id"]: arm for arm in frozen["arms"]}
    case_by_id = {case["id"]: case for case in cases}
    group_keys = sorted({(item["case_id"], item["repetition"]) for item in trajectories})
    packet_items = []
    key_items = []
    review_forms = []
    for case_id, repetition in group_keys:
        rows = [
            item
            for item in trajectories
            if item["case_id"] == case_id and item["repetition"] == repetition
        ]
        rows.sort(
            key=lambda item: hashlib.sha256(
                f"{randomization_salt}:{case_id}:{repetition}:{item['arm_id']}".encode()
            ).hexdigest()
        )
        candidates = []
        mappings = []
        for index, trajectory in enumerate(rows):
            candidate_id = chr(ord("A") + index)
            candidates.append(
                {
                    "candidate_id": candidate_id,
                    "turns": [
                        {
                            "turn_index": turn["turn_index"],
                            "assistant_output": turn["raw_output"],
                        }
                        for turn in trajectory["turns"]
                    ],
                }
            )
            arm = arm_by_id[trajectory["arm_id"]]
            mappings.append(
                {
                    "candidate_id": candidate_id,
                    "arm_id": trajectory["arm_id"],
                    "skill": arm.get("skill"),
                    "skill_package_sha256": arm.get("skill_package_sha256"),
                    "trajectory_id": trajectory["trajectory_id"],
                    "thread_id": trajectory["thread_id"],
                }
            )
        case = case_by_id[case_id]
        review_id = f"{case_id}-r{repetition}"
        packet_items.append(
            {
                "review_id": review_id,
                "case_id": case_id,
                "repetition": repetition,
                "mechanism": case["mechanism"],
                "purpose": case.get("purpose"),
                "user_turns": [
                    {"turn_index": index, "user_message": message}
                    for index, message in enumerate(case["turns"], 1)
                ],
                "hard_criteria": case["hard_criteria"],
                "candidates": candidates,
            }
        )
        key_items.append({"review_id": review_id, "candidates": mappings})
        review_forms.append(
            {
                "review_id": review_id,
                "criteria_pass": {
                    candidate["candidate_id"]: [None] * len(case["hard_criteria"])
                    for candidate in candidates
                },
                "preferred_candidate": None,
                "notes": "",
            }
        )
    packet = {
        "schema_version": SCHEMA_VERSION,
        "comparison_id": frozen["comparison_id"],
        "instructions": (
            "Blindly score each complete trajectory against every frozen criterion. "
            "Read user and assistant turns in order. Use true or false for each criterion "
            "before opening blind-review-key.json. Preference may be null when tied."
        ),
        "items": packet_items,
    }
    key = {
        "schema_version": SCHEMA_VERSION,
        "comparison_id": frozen["comparison_id"],
        "warning": "Keep this mapping hidden until criterion scoring is complete.",
        "randomization_salt": randomization_salt,
        "items": key_items,
    }
    form = {
        "schema_version": SCHEMA_VERSION,
        "comparison_id": frozen["comparison_id"],
        "reviews": review_forms,
    }
    return packet, key, form


def summarize_native_resume(run_dir: Path, root: Path = ROOT) -> dict[str, object]:
    run_dir = run_dir.resolve()
    frozen, run_meta, cases, trajectories = normalize_trajectories(run_dir, root)
    infrastructure_valid = all(item["technical_valid"] for item in trajectories)
    key_path = run_dir / "blind-review-key.json"
    salt = None
    if key_path.is_file():
        existing_key = read_object(key_path, "blind review key")
        candidate = existing_key.get("randomization_salt")
        if (
            not isinstance(candidate, str)
            or len(candidate) != 64
            or any(character not in "0123456789abcdef" for character in candidate)
        ):
            raise ValueError("blind review key has invalid randomization salt")
        salt = candidate
    packet, key, form = anonymized_review(frozen, cases, trajectories, salt)
    packet_path = run_dir / "blind-review.json"
    form_path = run_dir / "blind-review-form.json"
    write_json_once(packet_path, packet)
    write_json_once(key_path, key)
    write_json_once(form_path, form)
    summary = {
        "schema_version": SCHEMA_VERSION,
        "comparison_id": frozen["comparison_id"],
        "comparison_kind": "quality",
        "status": "awaiting-human-review" if infrastructure_valid else "infrastructure-invalid",
        "results_sha256": run_meta["results_sha256"],
        "planned_repetitions": frozen["repetitions"],
        "executed_repetitions": run_meta["repeat"],
        "session_mode": "explicit-thread-id",
        "history_mode": "native-session-retains-actual-output",
        "infrastructure_valid": infrastructure_valid,
        "trajectory_count": len(trajectories),
        "turn_count": sum(len(item["turns"]) for item in trajectories),
        "arms": arm_summaries(frozen, trajectories),
        "blind_review": {
            "unit": "complete-trajectory",
            "packet": packet_path.name,
            "packet_sha256": sha256_file(packet_path),
            "key": key_path.name,
            "key_sha256": sha256_file(key_path),
            "form": form_path.name,
            "form_sha256": sha256_file(form_path),
        },
    }
    write_json_once(run_dir / "summary.json", summary)
    print(f"[DONE] native resume summary: {summary['status']} ({run_dir})")
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", required=True, type=Path, dest="run_dir")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summarize_native_resume(args.run_dir)


if __name__ == "__main__":
    main()


