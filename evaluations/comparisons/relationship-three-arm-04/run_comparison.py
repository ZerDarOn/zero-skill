"""Run the frozen relationship three-arm inline-package pilot."""

from __future__ import annotations

import concurrent.futures
import datetime as dt
import hashlib
import json
from pathlib import Path
import random
import runpy
import secrets
import shutil
import subprocess
import tempfile
import time
import uuid


BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[2]
UPSTREAM = (
    ROOT
    / "evaluations"
    / "fixtures"
    / "upstreams"
    / "love-helper"
    / "1e391e26fd1c1bfee06e4daa9b439086a098a49b"
)
UPSTREAM_RUNTIME_FILES = (
    "relationship-copilot/SKILL.md",
    "relationship-copilot/references/human-progression-playbook.md",
    "relationship-stage-assessor/SKILL.md",
)
MAX_WORKERS = 2
TIMEOUT_SECONDS = 240


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def package_digest(files: dict[str, str]) -> str:
    digest = hashlib.sha256()
    for name in sorted(files):
        for data in (name.encode("utf-8"), files[name].encode("utf-8")):
            digest.update(len(data).to_bytes(8, "big"))
            digest.update(data)
    return digest.hexdigest()


def read_text_package(folder: Path) -> dict[str, str]:
    return {
        path.relative_to(folder).as_posix(): path.read_text(encoding="utf-8")
        for path in sorted(
            (item for item in folder.rglob("*") if item.is_file()),
            key=lambda item: item.relative_to(folder).as_posix(),
        )
    }


def validate_upstream(
    provenance: dict[str, object], upstream_root: Path = UPSTREAM
) -> None:
    files = provenance.get("files")
    if not isinstance(files, dict):
        raise ValueError("upstream provenance has no files map")
    for name, metadata in files.items():
        if not isinstance(name, str) or not isinstance(metadata, dict):
            raise ValueError("upstream provenance contains an invalid file record")
        path = upstream_root / name
        expected = metadata.get("sha256")
        if not path.is_file() or not isinstance(expected, str):
            raise ValueError(f"upstream provenance is incomplete for {name}")
        if sha256_file(path) != expected:
            raise ValueError(f"upstream bytes changed: {name}")


def build_prompt(
    common_prompt: str,
    case_prompt: str,
    package: dict[str, object] | None,
) -> str:
    package_text = ""
    if package is not None:
        package_text = (
            "\n\n<INLINE_SKILL_PACKAGE>\n"
            + json.dumps(package, ensure_ascii=False, sort_keys=True)
            + "\n</INLINE_SKILL_PACKAGE>"
        )
    return (
        common_prompt
        + package_text
        + "\n\n<USER_TASK>\n"
        + case_prompt
        + "\n</USER_TASK>"
    )


def valid_record(record: dict[str, object]) -> bool:
    return bool(
        record["exit_code"] == 0
        and str(record["raw_output"]).strip()
        and record["turn_completed"]
        and not record["tool_items"]
        and not record["error"]
    )


def create_blind_artifacts(
    run_root: Path,
    protocol: dict[str, object],
    cases: list[dict[str, object]],
    records: list[dict[str, object]],
    package_meta: dict[str, dict[str, object]],
) -> dict[str, object]:
    packet_items = []
    key_items = []
    review_items = []
    randomizer = secrets.SystemRandom()
    for case in cases:
        for repetition in range(1, protocol["repetitions"] + 1):
            group = [
                record
                for record in records
                if record["case_id"] == case["id"]
                and record["repetition"] == repetition
            ]
            randomizer.shuffle(group)
            candidates = []
            mappings = []
            criteria_scores = {}
            for index, record in enumerate(group):
                candidate_id = chr(ord("A") + index)
                candidates.append(
                    {
                        "candidate_id": candidate_id,
                        "valid": record["valid"],
                        "output": record["raw_output"],
                    }
                )
                arm = package_meta[record["arm_id"]]
                mappings.append(
                    {
                        "candidate_id": candidate_id,
                        "arm_id": record["arm_id"],
                        "skill": arm["skill"],
                        "skill_package_sha256": arm["package_sha256"],
                    }
                )
                criteria_scores[candidate_id] = [None] * len(case["hard_criteria"])
            review_id = f"{case['id']}-r{repetition}"
            packet_items.append(
                {
                    "review_id": review_id,
                    "case_id": case["id"],
                    "repetition": repetition,
                    "purpose": case["purpose"],
                    "task": case["prompt"],
                    "hard_criteria": case["hard_criteria"],
                    "candidates": candidates,
                }
            )
            key_items.append({"review_id": review_id, "candidates": mappings})
            review_items.append(
                {
                    "review_id": review_id,
                    "criteria_pass": criteria_scores,
                    "preferred_candidate": None,
                    "notes": "",
                }
            )
    packet = {
        "schema_version": 1,
        "comparison_id": protocol["id"],
        "instructions": (
            "Score every candidate against every frozen criterion before opening "
            "blind-review-key.json. Use true or false for each criterion."
        ),
        "items": packet_items,
    }
    key = {
        "schema_version": 1,
        "comparison_id": protocol["id"],
        "warning": "Keep this mapping hidden until criterion scoring is complete.",
        "items": key_items,
    }
    form = {
        "schema_version": 1,
        "comparison_id": protocol["id"],
        "reviews": review_items,
    }
    write_json(run_root / "blind-review.json", packet)
    write_json(run_root / "blind-review-key.json", key)
    write_json(run_root / "blind-review-form.json", form)
    return {
        "packet": "blind-review.json",
        "packet_sha256": sha256_file(run_root / "blind-review.json"),
        "key": "blind-review-key.json",
        "key_sha256": sha256_file(run_root / "blind-review-key.json"),
        "form": "blind-review-form.json",
        "form_sha256": sha256_file(run_root / "blind-review-form.json"),
    }


def main() -> None:
    protocol = json.loads((BASE / "protocol.json").read_text(encoding="utf-8"))
    cases = json.loads((BASE / "cases.json").read_text(encoding="utf-8"))
    executable = shutil.which("codex.exe") or shutil.which("codex")
    if not executable:
        raise RuntimeError("codex executable not found")
    provenance = json.loads((UPSTREAM / "provenance.json").read_text(encoding="utf-8"))
    validate_upstream(provenance)

    ours_folder = ROOT / "skills" / "relationships" / "relationship-review"
    ours_files = read_text_package(ours_folder)
    upstream_files = {
        name: (UPSTREAM / name).read_text(encoding="utf-8")
        for name in UPSTREAM_RUNTIME_FILES
    }
    packages = {
        "baseline": None,
        "ours": {"entrypoint": "SKILL.md", "files": ours_files},
        "upstream": {
            "entrypoint": "relationship-copilot/SKILL.md",
            "files": upstream_files,
        },
    }
    fingerprint = runpy.run_path(
        str(ROOT / "scripts" / "validate_collection.py")
    )["package_fingerprint"]
    collection = json.loads((ROOT / "catalog" / "collection.json").read_text(encoding="utf-8"))
    ours_record = next(item for item in collection["skills"] if item["id"] == "relationship-review")
    package_meta = {
        "baseline": {"skill": None, "package_sha256": None},
        "ours": {
            "skill": "relationship-review",
            "version": ours_record["version"],
            "package_sha256": fingerprint(ours_folder),
        },
        "upstream": {
            "skill": "relationship-copilot",
            "version": provenance["commit"],
            "package_sha256": package_digest(upstream_files),
        },
    }
    run_root = (
        ROOT
        / "evaluations"
        / "runs"
        / f"{protocol['id']}-{uuid.uuid4().hex[:8]}"
    )
    run_root.mkdir(parents=True)
    version = subprocess.run(
        [executable, "--version"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    ).stdout.strip()
    frozen = {
        "schema_version": 1,
        "frozen_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "protocol": protocol,
        "cases": cases,
        "packages": packages,
        "package_meta": package_meta,
        "upstream_provenance": provenance,
        "codex_version": version,
        "source_hashes": {
            name: sha256_file(BASE / name)
            for name in ("protocol.json", "cases.json", "run_comparison.py")
        },
    }
    write_json(run_root / "frozen.json", frozen)

    jobs = [
        (case, arm_id, repetition)
        for case in cases
        for arm_id in protocol["arms"]
        for repetition in range(1, protocol["repetitions"] + 1)
    ]
    random.Random(protocol["run_order_seed"]).shuffle(jobs)

    def execute(job: tuple[dict[str, object], str, int]) -> dict[str, object]:
        case, arm_id, repetition = job
        attempt_id = uuid.uuid4().hex
        attempt_dir = run_root / attempt_id
        attempt_dir.mkdir()
        prompt = build_prompt(
            protocol["common_prompt"], case["prompt"], packages[arm_id]
        )
        prompt_bytes = prompt.encode("utf-8")
        (attempt_dir / "prompt.txt").write_bytes(prompt_bytes)
        with tempfile.TemporaryDirectory(prefix="zero-relationship-comparison-") as work:
            command = [
                executable,
                "exec",
                "--ephemeral",
                "--ignore-user-config",
                "--skip-git-repo-check",
                "--sandbox",
                "read-only",
                "--model",
                protocol["model"],
                "-c",
                f'model_reasoning_effort="{protocol["reasoning_effort"]}"',
                "--json",
                "--output-last-message",
                str(attempt_dir / "final.txt"),
                "--cd",
                work,
                "-",
            ]
            started_at = dt.datetime.now(dt.timezone.utc).isoformat()
            tick = time.monotonic()
            try:
                completed = subprocess.run(
                    command,
                    input=prompt_bytes,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=TIMEOUT_SECONDS,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                    check=False,
                )
                exit_code = completed.returncode
                stdout = completed.stdout
                stderr = completed.stderr
                error = None
            except subprocess.TimeoutExpired as failure:
                exit_code = None
                stdout = failure.stdout or b""
                stderr = failure.stderr or b""
                error = "timeout; no retry"
        duration_ms = round((time.monotonic() - tick) * 1000)
        (attempt_dir / "events.jsonl").write_bytes(stdout)
        (attempt_dir / "stderr.txt").write_bytes(stderr)
        output = (
            (attempt_dir / "final.txt").read_bytes()
            if (attempt_dir / "final.txt").is_file()
            else b""
        )
        events = []
        for line in stdout.decode("utf-8", errors="replace").splitlines():
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        completed_events = [event for event in events if event.get("type") == "turn.completed"]
        tool_items = [
            event
            for event in events
            if event.get("item", {}).get("type")
            in {"command_execution", "mcp_tool_call", "web_search", "file_change"}
        ]
        record = {
            "attempt_id": attempt_id,
            "case_id": case["id"],
            "arm_id": arm_id,
            "repetition": repetition,
            "prompt_sha256": sha256_bytes(prompt_bytes),
            "raw_output": output.decode("utf-8", errors="replace"),
            "output_sha256": sha256_bytes(output),
            "events_sha256": sha256_bytes(stdout),
            "stderr_sha256": sha256_bytes(stderr),
            "exit_code": exit_code,
            "error": error,
            "turn_completed": bool(completed_events),
            "started_at": started_at,
            "duration_ms": duration_ms,
            "usage": completed_events[-1].get("usage") if completed_events else None,
            "tool_items": tool_items,
        }
        record["valid"] = valid_record(record)
        write_json(attempt_dir / "record.json", record)
        print(
            f"Finished {case['id']} arm={arm_id} "
            f"repetition={repetition} valid={record['valid']}",
            flush=True,
        )
        return record

    print(f"RUN_ROOT {run_root}", flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        records = list(pool.map(execute, jobs))
    write_json(run_root / "records.json", records)
    blind_meta = create_blind_artifacts(
        run_root, protocol, cases, records, package_meta
    )
    valid = all(record["valid"] for record in records)
    summary = {
        "schema_version": 1,
        "comparison_id": protocol["id"],
        "status": "awaiting-human-review" if valid else "infrastructure-invalid",
        "records": len(records),
        "valid_records": sum(record["valid"] for record in records),
        "frozen_sha256": sha256_file(run_root / "frozen.json"),
        "records_sha256": sha256_file(run_root / "records.json"),
        "blind_review": blind_meta,
        "package_meta": package_meta,
    }
    write_json(run_root / "summary.json", summary)
    print(
        f"COMPLETE {len(records)} valid={summary['valid_records']} status={summary['status']}",
        flush=True,
    )
    if not valid:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
