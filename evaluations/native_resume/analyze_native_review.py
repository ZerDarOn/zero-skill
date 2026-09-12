"""Recompute native-resume blind scores and apply the frozen mechanism gate."""

from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_native_resume import (  # noqa: E402
    read_object,
    resolve_inside,
    sha256_file,
    write_json_once,
)
from summarize_native_resume import anonymized_review, normalize_trajectories  # noqa: E402

SCHEMA_VERSION = 1


def validate_gate_config(spec: dict[str, object]) -> dict[str, object]:
    gate = spec.get("candidate_gate")
    expected = {
        "group_field": "mechanism",
        "cases_per_group": 2,
        "criterion_index": 0,
        "ours_arm": "ours",
        "baseline_arm": "baseline",
        "ours_min_failures_per_case": 2,
        "baseline_max_failures_per_case": 1,
        "require_all_cases_in_group": True,
        "opens_candidate_design_only": True,
    }
    if gate != expected:
        raise ValueError("comparison candidate gate differs from the frozen Round 24 rule")
    return gate


def unique_index(
    items: object, label: str, key_name: str
) -> dict[str, dict[str, object]]:
    if not isinstance(items, list) or not all(isinstance(item, dict) for item in items):
        raise ValueError(f"{label} must be a list of objects")
    indexed = {}
    for item in items:
        key = item.get(key_name)
        if not isinstance(key, str) or not key or key in indexed:
            raise ValueError(f"{label} contains a missing or duplicate {key_name}")
        indexed[key] = item
    return indexed


def recompute_review(
    frozen: dict[str, object],
    cases: list[dict[str, object]],
    packet: dict[str, object],
    key: dict[str, object],
    review: dict[str, object],
    scored: dict[str, object],
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    packet_items = unique_index(packet.get("items"), "blind packet items", "review_id")
    key_items = unique_index(key.get("items"), "blind key items", "review_id")
    review_items = unique_index(review.get("reviews"), "completed review items", "review_id")
    scored_items = unique_index(scored.get("items"), "scored review items", "review_id")
    expected_ids = {
        f"{case['id']}-r{repetition}"
        for case in cases
        for repetition in range(1, frozen["repetitions"] + 1)
    }
    if not all(
        set(items) == expected_ids
        for items in (packet_items, key_items, review_items, scored_items)
    ):
        raise ValueError("blind review artifacts do not cover every frozen trajectory item")
    case_by_id = {case["id"]: case for case in cases}
    aggregate: dict[str, dict[str, object]] = {}
    revealed = []
    for review_id in sorted(expected_ids):
        packet_item = packet_items[review_id]
        key_item = key_items[review_id]
        review_item = review_items[review_id]
        scored_item = scored_items[review_id]
        case_id = packet_item.get("case_id")
        if case_id not in case_by_id:
            raise ValueError("blind packet contains an unknown case")
        case = case_by_id[case_id]
        if packet_item.get("hard_criteria") != case["hard_criteria"]:
            raise ValueError("blind packet criteria differ from frozen case")
        mappings = unique_index(
            key_item.get("candidates"), f"blind key candidates for {review_id}", "candidate_id"
        )
        score_candidates = unique_index(
            scored_item.get("candidates"),
            f"scored candidates for {review_id}",
            "candidate_id",
        )
        criterion_scores = review_item.get("criteria_pass")
        if not isinstance(criterion_scores, dict):
            raise ValueError("completed review lacks criterion scores")
        if set(mappings) != set(score_candidates) or set(mappings) != set(criterion_scores):
            raise ValueError("candidate identities differ across review artifacts")
        preferred = review_item.get("preferred_candidate")
        if scored_item.get("preferred_candidate") != preferred:
            raise ValueError("scored preference differs from completed review")
        candidates = []
        for candidate_id in sorted(mappings):
            mapping = mappings[candidate_id]
            candidate = score_candidates[candidate_id]
            scores = criterion_scores[candidate_id]
            if candidate.get("arm_id") != mapping.get("arm_id"):
                raise ValueError("scored candidate arm differs from blind key")
            if candidate.get("criteria_pass") != scores:
                raise ValueError("scored criteria differ from completed review")
            if (
                not isinstance(scores, list)
                or len(scores) != len(case["hard_criteria"])
                or not all(isinstance(value, bool) for value in scores)
            ):
                raise ValueError("completed review criteria must be frozen-length booleans")
            arm_id = mapping["arm_id"]
            passed = sum(scores)
            arm = aggregate.setdefault(
                arm_id,
                {
                    "arm_id": arm_id,
                    "skill": mapping.get("skill"),
                    "outputs": 0,
                    "perfect_outputs": 0,
                    "criteria_passed": 0,
                    "criteria_total": 0,
                    "preferred_count": 0,
                },
            )
            arm["outputs"] += 1
            arm["perfect_outputs"] += passed == len(scores)
            arm["criteria_passed"] += passed
            arm["criteria_total"] += len(scores)
            arm["preferred_count"] += preferred == candidate_id
            candidates.append(
                {
                    "candidate_id": candidate_id,
                    "arm_id": arm_id,
                    "criteria_pass": scores,
                    "passed": passed,
                    "total": len(scores),
                    "preferred": preferred == candidate_id,
                }
            )
        revealed.append(
            {
                "review_id": review_id,
                "case_id": case_id,
                "repetition": packet_item["repetition"],
                "mechanism": case["mechanism"],
                "preferred_candidate": preferred,
                "notes": review_item.get("notes", ""),
                "candidates": candidates,
            }
        )
    arm_results = [aggregate[arm_id] for arm_id in sorted(aggregate)]
    for arm in arm_results:
        arm["criterion_pass_rate"] = round(
            arm["criteria_passed"] / arm["criteria_total"], 4
        )
    if scored.get("arms") != arm_results:
        raise ValueError("scored arm aggregate does not recompute from completed review")
    return revealed, arm_results


def compute_candidate_gate(
    cases: list[dict[str, object]],
    revealed: list[dict[str, object]],
    gate: dict[str, object],
) -> dict[str, object]:
    cases_by_mechanism: dict[str, list[str]] = defaultdict(list)
    per_case = {}
    for case in cases:
        case_id = case["id"]
        mechanism = case[gate["group_field"]]
        cases_by_mechanism[mechanism].append(case_id)
        candidates = [
            candidate
            for item in revealed
            if item["case_id"] == case_id
            for candidate in item["candidates"]
        ]
        failures = {
            arm_id: sum(
                not candidate["criteria_pass"][gate["criterion_index"]]
                for candidate in candidates
                if candidate["arm_id"] == arm_id
            )
            for arm_id in (gate["ours_arm"], gate["baseline_arm"])
        }
        qualifies = (
            failures[gate["ours_arm"]] >= gate["ours_min_failures_per_case"]
            and failures[gate["baseline_arm"]]
            <= gate["baseline_max_failures_per_case"]
        )
        per_case[case_id] = {
            "mechanism": mechanism,
            "ours_core_failures": failures[gate["ours_arm"]],
            "baseline_core_failures": failures[gate["baseline_arm"]],
            "qualifies": qualifies,
        }
    if any(len(case_ids) != gate["cases_per_group"] for case_ids in cases_by_mechanism.values()):
        raise ValueError("frozen mechanisms do not contain the required paired cases")
    qualifying_by_mechanism = {
        mechanism: [case_id for case_id in case_ids if per_case[case_id]["qualifies"]]
        for mechanism, case_ids in sorted(cases_by_mechanism.items())
    }
    triggered = [
        mechanism
        for mechanism, case_ids in qualifying_by_mechanism.items()
        if len(case_ids) == gate["cases_per_group"]
    ]
    return {
        "criterion_index": gate["criterion_index"],
        "ours_min_failures_per_case": gate["ours_min_failures_per_case"],
        "baseline_max_failures_per_case": gate["baseline_max_failures_per_case"],
        "require_all_cases_in_mechanism": gate["require_all_cases_in_group"],
        "per_case": per_case,
        "qualifying_cases_by_mechanism": qualifying_by_mechanism,
        "qualifying_mechanisms": triggered,
        "triggered": bool(triggered),
    }


def analyze_review(
    run_dir: Path,
    review_path: Path,
    review_result_path: Path,
    output_path: Path | None = None,
    root: Path = ROOT,
) -> dict[str, object]:
    run_dir = run_dir.resolve()
    review_path = review_path.resolve()
    review_result_path = review_result_path.resolve()
    for path, label in ((review_path, "review"), (review_result_path, "review result")):
        try:
            path.relative_to(run_dir)
        except ValueError as error:
            raise ValueError(f"{label} must stay inside the run directory") from error
    frozen, run_meta, cases, trajectories = normalize_trajectories(run_dir, root)
    if not all(item["technical_valid"] for item in trajectories):
        raise ValueError("candidate gate cannot analyze an infrastructure-invalid run")
    if run_meta["repeat"] != frozen["repetitions"]:
        raise ValueError("candidate gate requires all frozen repetitions")
    spec_path = resolve_inside(root, frozen["spec_path"], "frozen spec path")
    gate = validate_gate_config(read_object(spec_path, "comparison spec"))
    summary = read_object(run_dir / "summary.json", "native resume summary")
    if summary.get("status") != "awaiting-human-review":
        raise ValueError("native resume summary is not reviewable")
    packet = read_object(run_dir / "blind-review.json", "blind packet")
    key = read_object(run_dir / "blind-review-key.json", "blind key")
    if sha256_file(run_dir / "blind-review.json") != summary["blind_review"]["packet_sha256"]:
        raise ValueError("blind packet hash differs from summary")
    if sha256_file(run_dir / "blind-review-key.json") != summary["blind_review"]["key_sha256"]:
        raise ValueError("blind key hash differs from summary")
    salt = key.get("randomization_salt")
    if (
        not isinstance(salt, str)
        or len(salt) != 64
        or any(character not in "0123456789abcdef" for character in salt)
    ):
        raise ValueError("blind key has an invalid randomization salt")
    expected_packet, expected_key, _ = anonymized_review(
        frozen, cases, trajectories, salt
    )
    if packet != expected_packet:
        raise ValueError("blind packet does not match native trajectories")
    if key != expected_key:
        raise ValueError("blind key does not match native trajectories")
    review = read_object(review_path, "completed review")
    scored = read_object(review_result_path, "review result")
    if scored.get("status") != "reviewed":
        raise ValueError("review result is not complete")
    if scored.get("comparison_id") != frozen["comparison_id"]:
        raise ValueError("review result comparison id differs from frozen evidence")
    if scored.get("review_sha256") != sha256_file(review_path):
        raise ValueError("review result does not bind the completed review")
    if scored.get("reviewer") != review.get("reviewer"):
        raise ValueError("reviewer metadata differs between review and scored result")
    revealed, arms = recompute_review(frozen, cases, packet, key, review, scored)
    gate_result = compute_candidate_gate(cases, revealed, gate)
    preferred_count = sum(
        item["preferred_candidate"] is not None for item in revealed
    )
    result = {
        "schema_version": SCHEMA_VERSION,
        "comparison_id": frozen["comparison_id"],
        "status": "analyzed",
        "results_sha256": run_meta["results_sha256"],
        "review_sha256": sha256_file(review_path),
        "review_result_sha256": sha256_file(review_result_path),
        "reviewer": scored.get("reviewer"),
        "arms": arms,
        "items": revealed,
        "preference": {
            "items_with_unique_preference": preferred_count,
            "items_without_unique_preference": len(revealed) - preferred_count,
        },
        "candidate_gate": gate_result,
        "decision": {
            "candidate_design_opened": gate_result["triggered"],
            "skill_changed": False,
            "version_changed": False,
        },
        "limitations": [
            "The gate opens candidate design only; it does not by itself justify a skill upgrade.",
            "Results cover synthetic trajectories on one model and reasoning setting.",
        ],
    }
    destination = (
        output_path.resolve()
        if output_path is not None
        else run_dir / "native-review-analysis.json"
    )
    try:
        destination.relative_to(run_dir)
    except ValueError as error:
        raise ValueError("analysis output must stay inside the run directory") from error
    write_json_once(destination, result)
    print(f"[DONE] native resume review analysis at {destination}")
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", required=True, type=Path, dest="run_dir")
    parser.add_argument("--review", required=True, type=Path, dest="review_path")
    parser.add_argument("--review-result", required=True, type=Path, dest="review_result_path")
    parser.add_argument("--output", type=Path, dest="output_path")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    analyze_review(
        args.run_dir,
        args.review_path,
        args.review_result_path,
        args.output_path,
    )


if __name__ == "__main__":
    main()
