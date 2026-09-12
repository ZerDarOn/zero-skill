"""Prefill the anonymous exact-note criterion without opening the arm key."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUNS_ROOT = ROOT / "evaluations" / "runs"
COMPARISON_ID = "obsidian-artifact-preservation-three-arm-16"
IDENTITY_KEYS = {
    "arm_id",
    "skill",
    "skill_package_sha256",
    "randomization_salt",
}


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def sha256_text(value: str) -> str:
    return sha256_bytes(value.encode("utf-8"))


def read_object(path: Path, label: str) -> dict[str, object]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(f"invalid {label}: {path}") from error
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a JSON object")
    return value


def write_json_once(path: Path, value: object) -> None:
    if path.exists():
        raise FileExistsError(f"refusing to overwrite artifact review: {path}")
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def parse_submission(raw: str) -> dict[str, object]:
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        return {
            "parse_valid": False,
            "schema_valid": False,
            "note": None,
            "message": None,
            "error": "invalid-json",
        }
    if not isinstance(value, dict):
        return {
            "parse_valid": True,
            "schema_valid": False,
            "note": None,
            "message": None,
            "error": "root-not-object",
        }
    note = value.get("note")
    message = value.get("message")
    if not isinstance(note, str):
        error = "note-not-string"
    elif not isinstance(message, str):
        error = "message-not-string"
    elif set(value) != {"note", "message"}:
        error = "unexpected-object-keys"
    elif not message.strip():
        error = "empty-message"
    else:
        error = None
    return {
        "parse_valid": True,
        "schema_valid": error is None,
        "note": note if isinstance(note, str) else None,
        "message": message if isinstance(message, str) else None,
        "error": error,
    }


def exact_note_match(actual: str | None, expected: str) -> bool:
    if actual is None or "\r" in actual or "\r" in expected:
        return False
    if not expected.endswith("\n") or expected.endswith("\n\n"):
        raise ValueError("expected_note must end in exactly one LF")
    return actual == expected or actual + "\n" == expected


def reject_identity_fields(value: object, label: str) -> None:
    if isinstance(value, dict):
        exposed = sorted(IDENTITY_KEYS.intersection(value))
        if exposed:
            raise ValueError(
                f"{label} exposes arm identity fields: {', '.join(exposed)}"
            )
        for child in value.values():
            reject_identity_fields(child, label)
    elif isinstance(value, list):
        for child in value:
            reject_identity_fields(child, label)


def build_prefill(
    packet: dict[str, object],
    blank_form: dict[str, object],
    cases: list[dict[str, object]],
) -> tuple[dict[str, object], dict[str, object]]:
    reject_identity_fields(packet, "blind packet")
    reject_identity_fields(blank_form, "blind form")
    if packet.get("comparison_id") != COMPARISON_ID:
        raise ValueError("blind packet comparison id does not match")
    if blank_form.get("comparison_id") != COMPARISON_ID:
        raise ValueError("blind form comparison id does not match")
    case_by_id = {case.get("id"): case for case in cases}
    if len(case_by_id) != len(cases) or None in case_by_id:
        raise ValueError("cases must have unique ids")
    reviews = blank_form.get("reviews")
    items = packet.get("items")
    if not isinstance(reviews, list) or not isinstance(items, list):
        raise ValueError("blind packet and form must contain lists")
    review_by_id = {
        review.get("review_id"): review
        for review in reviews
        if isinstance(review, dict)
    }
    if len(review_by_id) != len(reviews):
        raise ValueError("blind form has duplicate or invalid review ids")

    prefilled = copy.deepcopy(blank_form)
    prefilled_by_id = {
        review["review_id"]: review for review in prefilled["reviews"]
    }
    check_items = []
    for item in items:
        if not isinstance(item, dict):
            raise ValueError("blind packet item must be an object")
        review_id = item.get("review_id")
        case_id = item.get("case_id")
        if review_id not in review_by_id or case_id not in case_by_id:
            raise ValueError("blind packet references an unknown review or case")
        source = case_by_id[case_id]
        expected = source.get("expected_note")
        criteria = item.get("hard_criteria")
        if not isinstance(expected, str):
            raise ValueError(f"case {case_id} has no string expected_note")
        if criteria != source.get("hard_criteria") or not isinstance(criteria, list):
            raise ValueError(f"case {case_id} criteria differ from frozen source")
        if len(criteria) < 1:
            raise ValueError(f"case {case_id} has no artifact criterion")
        candidates = item.get("candidates")
        target_review = prefilled_by_id[review_id]
        target_scores = target_review.get("criteria_pass")
        if not isinstance(candidates, list) or not isinstance(target_scores, dict):
            raise ValueError("blind candidates or form scores are invalid")
        candidate_checks = []
        seen_candidates = set()
        for candidate in candidates:
            if not isinstance(candidate, dict):
                raise ValueError("blind candidate must be an object")
            candidate_id = candidate.get("candidate_id")
            raw = candidate.get("output")
            if (
                not isinstance(candidate_id, str)
                or candidate_id in seen_candidates
                or not isinstance(raw, str)
                or candidate_id not in target_scores
            ):
                raise ValueError("blind candidate id or output is invalid")
            seen_candidates.add(candidate_id)
            scores = target_scores[candidate_id]
            if not isinstance(scores, list) or len(scores) != len(criteria):
                raise ValueError("blind form criterion count does not match")
            if any(value is not None for value in scores):
                raise ValueError("blind form must be blank before artifact prefill")
            parsed = parse_submission(raw)
            artifact_exact = exact_note_match(parsed["note"], expected)
            scores[0] = artifact_exact
            candidate_checks.append(
                {
                    "candidate_id": candidate_id,
                    "output_sha256": sha256_text(raw),
                    "parse_valid": parsed["parse_valid"],
                    "schema_valid": parsed["schema_valid"],
                    "parse_error": parsed["error"],
                    "expected_note_sha256": sha256_text(expected),
                    "actual_note_sha256": (
                        sha256_text(parsed["note"])
                        if isinstance(parsed["note"], str)
                        else None
                    ),
                    "artifact_exact": artifact_exact,
                }
            )
        if set(target_scores) != seen_candidates:
            raise ValueError("blind packet and form candidate ids differ")
        check_items.append(
            {
                "review_id": review_id,
                "case_id": case_id,
                "repetition": item.get("repetition"),
                "criterion_number": 1,
                "candidates": candidate_checks,
            }
        )
    if set(review_by_id) != {item["review_id"] for item in check_items}:
        raise ValueError("blind packet and form review ids differ")
    checks = {
        "schema_version": 1,
        "comparison_id": COMPARISON_ID,
        "method": "strict JSON parse; compare note UTF-8 text exactly, allowing only omission of expected_note's single terminal LF",
        "arm_mapping_opened": False,
        "items": check_items,
    }
    return checks, prefilled


def prefill_run(run_dir: Path) -> tuple[Path, Path]:
    run_dir = run_dir.resolve()
    try:
        run_dir.relative_to(RUNS_ROOT.resolve())
    except ValueError as error:
        raise ValueError("run directory must stay under evaluations/runs") from error
    frozen = read_object(run_dir / "frozen.json", "frozen evidence")
    summary = read_object(run_dir / "summary.json", "summary")
    if frozen.get("comparison_id") != COMPARISON_ID:
        raise ValueError("frozen comparison id does not match")
    blind = summary.get("blind_review")
    if not isinstance(blind, dict):
        raise ValueError("summary has no blind review evidence")
    cases_path = frozen.get("cases_path")
    if not isinstance(cases_path, str):
        raise ValueError("frozen cases path is invalid")
    source_path = (ROOT / cases_path).resolve()
    try:
        source_path.relative_to(ROOT.resolve())
    except ValueError as error:
        raise ValueError("frozen cases path must stay inside the repository") from error
    if not source_path.is_file() or sha256_file(source_path) != frozen.get("cases_sha256"):
        raise ValueError("frozen cases source hash does not match")
    packet_path = run_dir / "blind-review.json"
    form_path = run_dir / "blind-review-form.json"
    if (
        sha256_file(packet_path) != blind.get("packet_sha256")
        or sha256_file(form_path) != blind.get("form_sha256")
    ):
        raise ValueError("blind packet or form hash does not match summary")
    cases_value = json.loads(source_path.read_text(encoding="utf-8"))
    if not isinstance(cases_value, list):
        raise ValueError("frozen cases must be a JSON list")
    checks, prefilled = build_prefill(
        read_object(packet_path, "blind packet"),
        read_object(form_path, "blind form"),
        cases_value,
    )
    checks_path = run_dir / "artifact-checks.json"
    prefilled_path = run_dir / "blind-review-form-artifact-prefilled.json"
    write_json_once(checks_path, checks)
    write_json_once(prefilled_path, prefilled)
    print(f"[DONE] artifact checks: {checks_path}")
    print(f"[DONE] prefilled review: {prefilled_path}")
    return checks_path, prefilled_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", required=True, type=Path, dest="run_dir")
    args = parser.parse_args()
    prefill_run(args.run_dir)


if __name__ == "__main__":
    main()
