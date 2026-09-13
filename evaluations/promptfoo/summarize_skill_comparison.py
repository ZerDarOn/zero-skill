"""Validate Promptfoo results and build an anonymized human-review packet."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import secrets
import statistics


SCHEMA_VERSION = 1
FORBIDDEN_ITEM_TYPES = {
    "command_execution",
    "file_change",
    "mcp_tool_call",
    "web_search_call",
}


def json_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def write_json_once(path: Path, value: object) -> None:
    payload = json_bytes(value)
    if path.exists():
        if path.read_bytes() != payload:
            raise FileExistsError(f"refusing to overwrite different artifact: {path}")
        return
    path.write_bytes(payload)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_object(path: Path, label: str) -> dict[str, object]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"{label} is not readable JSON: {path}") from error
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a JSON object: {path}")
    return value


def result_rows(payload: dict[str, object]) -> list[dict[str, object]]:
    results = payload.get("results")
    rows = results.get("results") if isinstance(results, dict) else None
    if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
        raise ValueError("Promptfoo result has no valid result rows")
    return rows


def raw_response(row: dict[str, object]) -> dict[str, object]:
    response = row.get("response")
    raw = response.get("raw") if isinstance(response, dict) else None
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except json.JSONDecodeError:
            return {}
    return raw if isinstance(raw, dict) else {}


def response_output(row: dict[str, object]) -> str:
    response = row.get("response")
    output = response.get("output") if isinstance(response, dict) else None
    return output if isinstance(output, str) else ""


def response_metadata(row: dict[str, object]) -> dict[str, object]:
    response = row.get("response")
    metadata = response.get("metadata") if isinstance(response, dict) else None
    return metadata if isinstance(metadata, dict) else {}


def skill_call_names(row: dict[str, object], field: str) -> list[str]:
    calls = response_metadata(row).get(field)
    if not isinstance(calls, list):
        return []
    return sorted(
        {
            call["name"]
            for call in calls
            if isinstance(call, dict)
            and isinstance(call.get("name"), str)
            and call["name"]
        }
    )


def numeric(value: object) -> float:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    return 0.0


def item_types(row: dict[str, object]) -> list[str]:
    items = raw_response(row).get("items")
    if not isinstance(items, list):
        return []
    return [
        item["type"]
        for item in items
        if isinstance(item, dict) and isinstance(item.get("type"), str)
    ]


def forbidden_types(types: list[str]) -> list[str]:
    return sorted(
        {
            item_type
            for item_type in types
            if item_type in FORBIDDEN_ITEM_TYPES
            or "web_search" in item_type
            or item_type.startswith("codex_apps")
        }
    )


def expected_equals(row: dict[str, object]) -> str | None:
    test_case = row.get("testCase")
    assertions = test_case.get("assert") if isinstance(test_case, dict) else None
    if not isinstance(assertions, list):
        return None
    for assertion in assertions:
        if (
            isinstance(assertion, dict)
            and assertion.get("type") == "equals"
            and isinstance(assertion.get("value"), str)
        ):
            return assertion["value"]
    return None


def normalize_rows(
    rows: list[dict[str, object]],
    frozen: dict[str, object],
    effective_repetitions: int | None = None,
) -> list[dict[str, object]]:
    arms = frozen.get("arms")
    case_ids = frozen.get("selected_case_ids")
    repetitions = (
        effective_repetitions
        if effective_repetitions is not None
        else frozen.get("repetitions")
    )
    if not isinstance(arms, list) or not isinstance(case_ids, list):
        raise ValueError("frozen evidence has invalid arms or case ids")
    if not isinstance(repetitions, int) or isinstance(repetitions, bool):
        raise ValueError("frozen evidence has invalid repetitions")
    arm_ids = {
        arm.get("id") for arm in arms if isinstance(arm, dict) and arm.get("id")
    }
    counters: dict[tuple[str, str], int] = {}
    normalized: list[dict[str, object]] = []
    for row in rows:
        metadata = row.get("metadata")
        provider = row.get("provider")
        case_id = metadata.get("case_id") if isinstance(metadata, dict) else None
        arm_id = metadata.get("arm_id") if isinstance(metadata, dict) else None
        provider_label = provider.get("label") if isinstance(provider, dict) else None
        if case_id not in case_ids or arm_id not in arm_ids:
            raise ValueError("result row has unknown or missing case_id/arm_id metadata")
        if provider_label != arm_id:
            raise ValueError(
                f"result provider {provider_label!r} does not match arm {arm_id!r}"
            )
        key = (case_id, arm_id)
        repetition = counters.get(key, 0) + 1
        counters[key] = repetition
        if repetition > repetitions:
            raise ValueError(f"too many rows for {case_id}/{arm_id}")
        parsed_raw = raw_response(row)
        types = item_types(row)
        token_usage = row.get("tokenUsage")
        response = row.get("response")
        has_complete_response = (
            isinstance(response, dict)
            and isinstance(response.get("output"), str)
            and isinstance(parsed_raw.get("items"), list)
        )
        normalized.append(
            {
                "case_id": case_id,
                "arm_id": arm_id,
                "repetition": repetition,
                "output": response_output(row),
                "prompt": (
                    row.get("vars", {}).get("prompt", "")
                    if isinstance(row.get("vars"), dict)
                    else ""
                ),
                "purpose": metadata.get("purpose") if isinstance(metadata, dict) else None,
                "hard_criteria": (
                    metadata.get("hard_criteria", [])
                    if isinstance(metadata, dict)
                    else []
                ),
                "invocation": (
                    metadata.get("invocation") if isinstance(metadata, dict) else None
                ),
                "promptfoo_passed": row.get("success") is True,
                "provider_error": not has_complete_response,
                "expected_output": expected_equals(row),
                "cost": numeric(row.get("cost")),
                "latency_ms": numeric(row.get("latencyMs")),
                "tokens": {
                    key: numeric(token_usage.get(key))
                    for key in ("total", "prompt", "completion", "cached")
                }
                if isinstance(token_usage, dict)
                else {},
                "item_types": types,
                "forbidden_item_types": forbidden_types(types),
                "skill_calls": skill_call_names(row, "skillCalls"),
                "attempted_skill_calls": skill_call_names(
                    row, "attemptedSkillCalls"
                ),
            }
        )
    expected_keys = {
        (case_id, arm_id)
        for case_id in case_ids
        for arm_id in arm_ids
    }
    if set(counters) != expected_keys or any(
        counters[key] != repetitions for key in expected_keys
    ):
        raise ValueError("result rows do not cover every frozen case/arm/repetition")
    return normalized


def arm_summaries(
    normalized: list[dict[str, object]], frozen: dict[str, object]
) -> list[dict[str, object]]:
    summaries = []
    for arm in frozen["arms"]:
        arm_rows = [row for row in normalized if row["arm_id"] == arm["id"]]
        latencies = [row["latency_ms"] for row in arm_rows]
        token_keys = sorted(
            {key for row in arm_rows for key in row.get("tokens", {}).keys()}
        )
        summaries.append(
            {
                "id": arm["id"],
                "skill": arm.get("skill"),
                "install_mode": arm.get("install_mode"),
                "invocation": arm.get("invocation"),
                "rows": len(arm_rows),
                "promptfoo_passed_rows": sum(
                    row["promptfoo_passed"] for row in arm_rows
                ),
                "provider_errors": sum(row["provider_error"] for row in arm_rows),
                "forbidden_tool_rows": sum(
                    bool(row["forbidden_item_types"]) for row in arm_rows
                ),
                "rows_with_expected_skill_call": (
                    sum(arm.get("skill") in row["skill_calls"] for row in arm_rows)
                    if arm.get("skill")
                    else 0
                ),
                "skill_calls": sorted(
                    {name for row in arm_rows for name in row["skill_calls"]}
                ),
                "attempted_skill_calls": sorted(
                    {
                        name
                        for row in arm_rows
                        for name in row["attempted_skill_calls"]
                    }
                ),
                "cost_total": round(sum(row["cost"] for row in arm_rows), 8),
                "latency_ms_median": round(statistics.median(latencies), 2),
                "tokens_total": {
                    key: int(sum(row.get("tokens", {}).get(key, 0) for row in arm_rows))
                    for key in token_keys
                },
            }
        )
    return summaries


def discovery_gate(
    normalized: list[dict[str, object]], frozen: dict[str, object]
) -> dict[str, object]:
    baseline_ids = [arm["id"] for arm in frozen["arms"] if not arm.get("skill")]
    skill_ids = [arm["id"] for arm in frozen["arms"] if arm.get("skill")]
    if len(baseline_ids) != 1 or not skill_ids:
        raise ValueError("discovery comparison needs one baseline and at least one skill arm")
    arm_by_id = {arm["id"]: arm for arm in frozen["arms"]}
    target_skills = {
        arm["skill"] for arm in frozen["arms"] if arm.get("skill")
    }
    checks = []
    for row in normalized:
        expected = row["expected_output"]
        if not isinstance(expected, str):
            raise ValueError("discovery rows require an equals assertion")
        matched = row["output"].strip() == expected
        should_match = row["arm_id"] in skill_ids
        arm = arm_by_id[row["arm_id"]]
        expected_skill = arm.get("skill")
        skill_trace_expected = should_match and arm.get("invocation") == "implicit"
        skill_trace_matched = (
            expected_skill in row["skill_calls"] if skill_trace_expected else None
        )
        unexpected_skill_calls = sorted(target_skills.intersection(row["skill_calls"]))
        trace_passed = (
            not skill_trace_expected or skill_trace_matched is True
        ) and (should_match or not unexpected_skill_calls)
        passed = (
            matched == should_match
            and trace_passed
            and not row["forbidden_item_types"]
        )
        checks.append(
            {
                "case_id": row["case_id"],
                "arm_id": row["arm_id"],
                "expected_behavior": "match-hidden-token" if should_match else "miss-hidden-token",
                "skill_trace_expected": skill_trace_expected,
                "skill_trace_matched": skill_trace_matched,
                "skill_calls": row["skill_calls"],
                "attempted_skill_calls": row["attempted_skill_calls"],
                "unexpected_skill_calls": unexpected_skill_calls,
                "passed": passed,
                "forbidden_item_types": row["forbidden_item_types"],
            }
        )
    return {
        "status": "passed" if all(check["passed"] for check in checks) else "failed",
        "checks": checks,
    }


def implicit_routing_gate(
    normalized: list[dict[str, object]], frozen: dict[str, object]
) -> dict[str, object]:
    implicit_arms = {
        arm["id"]: arm["skill"]
        for arm in frozen["arms"]
        if arm.get("skill") and arm.get("invocation") == "implicit"
    }
    if not implicit_arms:
        return {"status": "not-applicable", "checks": []}
    target_skills = set(implicit_arms.values())
    baseline_ids = {
        arm["id"] for arm in frozen["arms"] if not arm.get("skill")
    }
    checks = []
    for row in normalized:
        arm_id = row["arm_id"]
        expected_skill = implicit_arms.get(arm_id)
        if expected_skill is None and arm_id not in baseline_ids:
            continue
        relevant_calls = sorted(target_skills.intersection(row["skill_calls"]))
        unexpected_calls = [
            name for name in relevant_calls if name != expected_skill
        ]
        passed = (
            expected_skill in relevant_calls and not unexpected_calls
            if expected_skill is not None
            else not relevant_calls
        )
        checks.append(
            {
                "case_id": row["case_id"],
                "arm_id": arm_id,
                "repetition": row["repetition"],
                "expected_skill": expected_skill,
                "skill_calls": row["skill_calls"],
                "attempted_skill_calls": row["attempted_skill_calls"],
                "unexpected_skill_calls": unexpected_calls,
                "passed": passed,
            }
        )
    return {
        "status": "passed" if checks and all(check["passed"] for check in checks) else "failed",
        "checks": checks,
    }

def anonymized_review(
    normalized: list[dict[str, object]],
    frozen: dict[str, object],
    randomization_salt: str | None = None,
) -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    arm_by_id = {arm["id"]: arm for arm in frozen["arms"]}
    randomization_salt = randomization_salt or secrets.token_hex(32)
    items = []
    keys = []
    review_forms = []
    group_keys = sorted(
        {(row["case_id"], row["repetition"]) for row in normalized}
    )
    for case_id, repetition in group_keys:
        rows = [
            row
            for row in normalized
            if row["case_id"] == case_id and row["repetition"] == repetition
        ]
        rows.sort(
            key=lambda row: hashlib.sha256(
                f"{randomization_salt}:{case_id}:{repetition}:{row['arm_id']}".encode()
            ).hexdigest()
        )
        candidates = []
        mappings = []
        for index, row in enumerate(rows):
            candidate_id = chr(ord("A") + index)
            candidates.append({"candidate_id": candidate_id, "output": row["output"]})
            arm = arm_by_id[row["arm_id"]]
            mappings.append(
                {
                    "candidate_id": candidate_id,
                    "arm_id": row["arm_id"],
                    "skill": arm.get("skill"),
                    "skill_package_sha256": arm.get("skill_package_sha256"),
                }
            )
        sample = rows[0]
        review_id = f"{case_id}-r{repetition}"
        baseline_row = next(
            (row for row in rows if not arm_by_id[row["arm_id"]].get("skill")),
            sample,
        )
        items.append(
            {
                "review_id": review_id,
                "case_id": case_id,
                "repetition": repetition,
                "purpose": sample["purpose"],
                "task": baseline_row["prompt"],
                "hard_criteria": sample["hard_criteria"],
                "candidates": candidates,
            }
        )
        keys.append({"review_id": review_id, "candidates": mappings})
        review_forms.append(
            {
                "review_id": review_id,
                "criteria_pass": {
                    candidate["candidate_id"]: [None] * len(sample["hard_criteria"])
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
            "Blindly score each candidate against every frozen criterion before "
            "opening blind-review-key.json. Use true or false for each criterion."
        ),
        "items": items,
    }
    key = {
        "schema_version": SCHEMA_VERSION,
        "comparison_id": frozen["comparison_id"],
        "warning": "Keep this mapping hidden until criterion scoring is complete.",
        "randomization_salt": randomization_salt,
        "items": keys,
    }
    form = {
        "schema_version": SCHEMA_VERSION,
        "comparison_id": frozen["comparison_id"],
        "reviews": review_forms,
    }
    return packet, key, form


def summarize_comparison(run_dir: Path) -> dict[str, object]:
    run_dir = run_dir.resolve()
    frozen = read_object(run_dir / "frozen.json", "frozen evidence")
    run_meta = read_object(run_dir / "run-meta.json", "run metadata")
    if run_meta.get("frozen_sha256") != sha256_file(run_dir / "frozen.json"):
        raise ValueError("frozen evidence hash does not match run metadata")
    results_path = run_dir / "results.json"
    results_hash = sha256_file(results_path)
    if run_meta.get("results_sha256") != results_hash:
        raise ValueError("results hash does not match run metadata")
    if not str(run_meta.get("status", "")).startswith("completed"):
        raise ValueError("run metadata does not describe a completed evaluation")
    if frozen.get("comparison_kind", "quality") == "operational":
        raise ValueError(
            "operational comparisons require the dedicated invocation analyzer"
        )
    executed_repetitions = run_meta.get("repeat")
    if (
        not isinstance(executed_repetitions, int)
        or isinstance(executed_repetitions, bool)
        or not 1 <= executed_repetitions <= 10
    ):
        raise ValueError("run metadata has invalid repeat")
    normalized = normalize_rows(
        result_rows(read_object(results_path, "results")),
        frozen,
        executed_repetitions,
    )
    infrastructure_valid = not any(
        row["provider_error"] or row["forbidden_item_types"] for row in normalized
    )
    summary: dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "comparison_id": frozen["comparison_id"],
        "comparison_kind": frozen.get("comparison_kind", "quality"),
        "results_sha256": results_hash,
        "planned_repetitions": frozen.get("repetitions"),
        "executed_repetitions": executed_repetitions,
        "infrastructure_valid": infrastructure_valid,
        "arms": arm_summaries(normalized, frozen),
    }
    if frozen.get("comparison_kind", "quality") == "discovery":
        gate = discovery_gate(normalized, frozen)
        summary["discovery_gate"] = gate
        summary["status"] = gate["status"] if infrastructure_valid else "failed"
    else:
        routing = implicit_routing_gate(normalized, frozen)
        summary["routing_gate"] = routing
        packet_path = run_dir / "blind-review.json"
        key_path = run_dir / "blind-review-key.json"
        form_path = run_dir / "blind-review-form.json"
        randomization_salt = None
        if key_path.is_file():
            existing_key = read_object(key_path, "blind review key")
            candidate_salt = existing_key.get("randomization_salt")
            if (
                not isinstance(candidate_salt, str)
                or len(candidate_salt) != 64
                or any(character not in "0123456789abcdef" for character in candidate_salt)
            ):
                raise ValueError("blind review key has invalid randomization salt")
            randomization_salt = candidate_salt
        packet, key, form = anonymized_review(
            normalized, frozen, randomization_salt
        )
        write_json_once(packet_path, packet)
        write_json_once(key_path, key)
        write_json_once(form_path, form)
        if not infrastructure_valid:
            summary["status"] = "infrastructure-invalid"
        elif routing["status"] == "failed":
            summary["status"] = "routing-failed"
        else:
            summary["status"] = "awaiting-human-review"
        summary["blind_review"] = {
            "packet": packet_path.name,
            "packet_sha256": sha256_file(packet_path),
            "key": key_path.name,
            "key_sha256": sha256_file(key_path),
            "form": form_path.name,
            "form_sha256": sha256_file(form_path),
        }
    write_json_once(run_dir / "summary.json", summary)
    print(f"[DONE] comparison summary: {summary['status']} ({run_dir})")
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", required=True, type=Path, dest="run_dir")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summarize_comparison(args.run_dir)


if __name__ == "__main__":
    main()
