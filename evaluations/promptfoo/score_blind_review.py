"""Validate a completed blind review and reveal aggregate scores by experiment arm."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


SCHEMA_VERSION = 1


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


def write_json_once(path: Path, value: object) -> None:
    payload = (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    if path.exists():
        if path.read_bytes() != payload:
            raise FileExistsError(f"refusing to overwrite different artifact: {path}")
        return
    path.write_bytes(payload)


def validate_artifact_hashes(
    run_dir: Path, summary: dict[str, object]
) -> tuple[dict[str, object], dict[str, object]]:
    review_meta = summary.get("blind_review")
    if not isinstance(review_meta, dict):
        raise ValueError("summary has no blind review metadata")
    if review_meta.get("packet") != "blind-review.json":
        raise ValueError("summary has an invalid blind review packet filename")
    if review_meta.get("key") != "blind-review-key.json":
        raise ValueError("summary has an invalid blind review key filename")
    packet_path = run_dir / "blind-review.json"
    key_path = run_dir / "blind-review-key.json"
    if sha256_file(packet_path) != review_meta.get("packet_sha256"):
        raise ValueError("blind review packet hash does not match summary")
    if sha256_file(key_path) != review_meta.get("key_sha256"):
        raise ValueError("blind review key hash does not match summary")
    return read_object(packet_path, "blind review packet"), read_object(
        key_path, "blind review key"
    )


def score_review(
    run_dir: Path, review_path: Path, output_path: Path | None = None
) -> dict[str, object]:
    run_dir = run_dir.resolve()
    review_path = review_path.resolve()
    summary = read_object(run_dir / "summary.json", "comparison summary")
    if summary.get("status") != "awaiting-human-review":
        raise ValueError("comparison is not ready for blind review")
    packet, key = validate_artifact_hashes(run_dir, summary)
    review = read_object(review_path, "completed blind review")
    if review.get("comparison_id") != summary.get("comparison_id"):
        raise ValueError("review comparison_id does not match summary")
    reviewer = review.get("reviewer")
    if (
        not isinstance(reviewer, dict)
        or not isinstance(reviewer.get("kind"), str)
        or not reviewer["kind"].strip()
    ):
        raise ValueError("review must identify reviewer.kind")
    packet_items = {
        item["review_id"]: item
        for item in packet.get("items", [])
        if isinstance(item, dict) and isinstance(item.get("review_id"), str)
    }
    key_items = {
        item["review_id"]: item
        for item in key.get("items", [])
        if isinstance(item, dict) and isinstance(item.get("review_id"), str)
    }
    reviews = review.get("reviews")
    if not isinstance(reviews, list) or not all(isinstance(item, dict) for item in reviews):
        raise ValueError("review must contain a reviews list")
    review_items = {
        item.get("review_id"): item
        for item in reviews
        if isinstance(item.get("review_id"), str)
    }
    if len(review_items) != len(reviews) or set(review_items) != set(packet_items):
        raise ValueError("review ids must match the blind packet exactly")
    if set(key_items) != set(packet_items):
        raise ValueError("blind review key does not match packet ids")

    aggregate: dict[str, dict[str, object]] = {}
    revealed_items = []
    for review_id in sorted(packet_items):
        packet_item = packet_items[review_id]
        key_item = key_items[review_id]
        review_item = review_items[review_id]
        candidates = packet_item.get("candidates")
        mappings = key_item.get("candidates")
        criteria = packet_item.get("hard_criteria")
        scores = review_item.get("criteria_pass")
        if not isinstance(candidates, list) or not isinstance(mappings, list):
            raise ValueError(f"invalid candidates for {review_id}")
        if not isinstance(criteria, list) or not isinstance(scores, dict):
            raise ValueError(f"invalid criteria scores for {review_id}")
        candidate_id_list = [
            candidate.get("candidate_id")
            for candidate in candidates
            if isinstance(candidate, dict)
        ]
        if (
            len(candidate_id_list) != len(candidates)
            or not all(
                isinstance(candidate_id, str) and candidate_id
                for candidate_id in candidate_id_list
            )
            or len(set(candidate_id_list)) != len(candidate_id_list)
        ):
            raise ValueError(
                f"candidate ids must be unique non-empty strings for {review_id}"
            )
        candidate_ids = set(candidate_id_list)
        mapping_by_candidate = {
            mapping.get("candidate_id"): mapping
            for mapping in mappings
            if isinstance(mapping, dict)
        }
        if len(mapping_by_candidate) != len(mappings):
            raise ValueError(f"candidate mappings must be unique for {review_id}")
        if set(scores) != candidate_ids or set(mapping_by_candidate) != candidate_ids:
            raise ValueError(f"candidate ids do not match for {review_id}")
        preferred = review_item.get("preferred_candidate")
        if preferred is not None and preferred not in candidate_ids:
            raise ValueError(f"preferred candidate is invalid for {review_id}")
        notes = review_item.get("notes", "")
        if not isinstance(notes, str):
            raise ValueError(f"review notes must be a string for {review_id}")
        revealed_candidates = []
        for candidate_id in sorted(candidate_ids):
            criterion_scores = scores[candidate_id]
            if (
                not isinstance(criterion_scores, list)
                or len(criterion_scores) != len(criteria)
                or not all(isinstance(value, bool) for value in criterion_scores)
            ):
                raise ValueError(
                    f"criteria scores for {review_id}/{candidate_id} must be booleans"
                )
            mapping = mapping_by_candidate[candidate_id]
            arm_id = mapping.get("arm_id")
            if not isinstance(arm_id, str):
                raise ValueError(f"missing arm mapping for {review_id}/{candidate_id}")
            passed = sum(criterion_scores)
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
            arm["perfect_outputs"] += passed == len(criteria)
            arm["criteria_passed"] += passed
            arm["criteria_total"] += len(criteria)
            arm["preferred_count"] += preferred == candidate_id
            revealed_candidates.append(
                {
                    "candidate_id": candidate_id,
                    "arm_id": arm_id,
                    "criteria_pass": criterion_scores,
                    "passed": passed,
                    "total": len(criteria),
                }
            )
        revealed_items.append(
            {
                "review_id": review_id,
                "preferred_candidate": preferred,
                "notes": notes,
                "candidates": revealed_candidates,
            }
        )
    arm_results = [aggregate[arm_id] for arm_id in sorted(aggregate)]
    for arm in arm_results:
        total = arm["criteria_total"]
        arm["criterion_pass_rate"] = (
            round(arm["criteria_passed"] / total, 4) if total else None
        )
    result = {
        "schema_version": SCHEMA_VERSION,
        "comparison_id": summary["comparison_id"],
        "review_sha256": sha256_file(review_path),
        "reviewer": reviewer,
        "status": "reviewed",
        "arms": arm_results,
        "items": revealed_items,
        "limitations": [
            "Criterion scoring reflects the named reviewer and is not an automatic verification claim.",
            "A canary or small sample does not establish a general skill ranking.",
        ],
    }
    destination = (
        output_path.resolve()
        if output_path is not None
        else run_dir / f"review-result-{review_path.stem}.json"
    )
    try:
        destination.relative_to(run_dir)
    except ValueError as error:
        raise ValueError(
            "review result output must stay inside the run directory"
        ) from error
    write_json_once(destination, result)
    print(f"[DONE] scored blind review at {destination}")
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", required=True, type=Path, dest="run_dir")
    parser.add_argument("--review", required=True, type=Path, dest="review_path")
    parser.add_argument("--output", type=Path, dest="output_path")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    score_review(args.run_dir, args.review_path, args.output_path)


if __name__ == "__main__":
    main()
