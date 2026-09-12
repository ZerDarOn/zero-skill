"""Run frozen multi-turn comparisons with explicit native Codex session resume."""

from __future__ import annotations

import argparse
import concurrent.futures
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time


ROOT = Path(__file__).resolve().parents[2]
PROMPTFOO_DIR = Path(__file__).resolve().parents[1] / "promptfoo"
if str(PROMPTFOO_DIR) not in sys.path:
    sys.path.insert(0, str(PROMPTFOO_DIR))
from run_skill_comparison import package_sha256, verify_prepared  # noqa: E402

DEFAULT_AUTH_JSON = Path.home() / ".codex" / "auth.json"
SCHEMA_VERSION = 1
ALLOWED_ITEM_TYPES = {"agent_message", "reasoning"}
SAFE_ENV_KEYS = {
    "APPDATA",
    "COMSPEC",
    "LOCALAPPDATA",
    "NUMBER_OF_PROCESSORS",
    "PATH",
    "PATHEXT",
    "PROCESSOR_ARCHITECTURE",
    "PROGRAMDATA",
    "SYSTEMDRIVE",
    "SYSTEMROOT",
    "TEMP",
    "TMP",
    "USERNAME",
    "WINDIR",
}


def json_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def write_json(path: Path, value: object) -> None:
    path.write_bytes(json_bytes(value))


def write_json_once(path: Path, value: object) -> None:
    payload = json_bytes(value)
    if path.exists():
        if path.read_bytes() != payload:
            raise FileExistsError(f"refusing to overwrite different artifact: {path}")
        return
    path.write_bytes(payload)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def read_object(path: Path, label: str) -> dict[str, object]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"{label} is not readable JSON: {path}") from error
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a JSON object: {path}")
    return value


def resolve_inside(root: Path, raw_path: str, label: str) -> Path:
    candidate = Path(raw_path)
    resolved = (candidate if candidate.is_absolute() else root / candidate).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError as error:
        raise ValueError(f"{label} must stay inside the repository: {raw_path}") from error
    return resolved


def load_trajectory_cases(
    root: Path, frozen: dict[str, object]
) -> list[dict[str, object]]:
    cases_path_value = frozen.get("cases_path")
    if not isinstance(cases_path_value, str):
        raise ValueError("frozen evidence has no cases_path")
    cases_path = resolve_inside(root, cases_path_value, "frozen cases path")
    if not cases_path.is_file() or sha256_file(cases_path) != frozen.get("cases_sha256"):
        raise ValueError("frozen cases hash does not match source")
    value = json.loads(cases_path.read_text(encoding="utf-8"))
    if not isinstance(value, list) or not value:
        raise ValueError("trajectory cases must be a non-empty list")
    selected = frozen.get("selected_case_ids")
    if not isinstance(selected, list) or not all(isinstance(item, str) for item in selected):
        raise ValueError("frozen selected_case_ids is invalid")
    by_id: dict[str, dict[str, object]] = {}
    for case in value:
        if not isinstance(case, dict):
            raise ValueError("each trajectory case must be an object")
        case_id = case.get("id")
        turns = case.get("turns")
        criteria = case.get("hard_criteria")
        if not isinstance(case_id, str) or not case_id:
            raise ValueError("each trajectory case must have a non-empty id")
        if case_id in by_id:
            raise ValueError("trajectory case ids must be unique")
        if (
            not isinstance(turns, list)
            or not turns
            or not all(isinstance(turn, str) and turn for turn in turns)
        ):
            raise ValueError(f"case {case_id} must have non-empty string turns")
        if case.get("prompt") != turns[0]:
            raise ValueError(f"case {case_id} prompt must equal its first turn")
        if not isinstance(case.get("mechanism"), str) or not case["mechanism"]:
            raise ValueError(f"case {case_id} must identify a mechanism")
        if (
            not isinstance(criteria, list)
            or len(criteria) != 4
            or not all(isinstance(item, str) and item for item in criteria)
        ):
            raise ValueError(f"case {case_id} must freeze exactly four hard criteria")
        by_id[case_id] = case
    missing = [case_id for case_id in selected if case_id not in by_id]
    if missing:
        raise ValueError("frozen case selection contains unknown trajectory cases")
    if len(set(selected)) != len(selected):
        raise ValueError("frozen case selection contains duplicate ids")
    return [by_id[case_id] for case_id in selected]


def verify_source_spec(root: Path, frozen: dict[str, object]) -> dict[str, object]:
    spec_value = frozen.get("spec_path")
    if not isinstance(spec_value, str):
        raise ValueError("frozen evidence has no spec_path")
    spec_path = resolve_inside(root, spec_value, "frozen spec path")
    if not spec_path.is_file() or sha256_file(spec_path) != frozen.get("spec_sha256"):
        raise ValueError("frozen spec hash does not match source")
    spec = read_object(spec_path, "comparison spec")
    native = spec.get("native_resume")
    if not isinstance(native, dict):
        raise ValueError("comparison spec has no native_resume configuration")
    if native.get("session_mode") != "explicit-thread-id":
        raise ValueError("native resume requires explicit-thread-id session mode")
    if native.get("forbid_last") is not True or native.get("forbid_ephemeral") is not True:
        raise ValueError("native resume must forbid --last and --ephemeral")
    return native


def tree_manifest(folder: Path) -> dict[str, str]:
    manifest: dict[str, str] = {}
    for current, directories, filenames in os.walk(folder, followlinks=False):
        current_path = Path(current)
        if current_path.is_symlink() or (
            getattr(current_path, "is_junction", None) and current_path.is_junction()
        ):
            raise ValueError(f"fixture links are unsupported: {current_path}")
        for name in directories:
            child = current_path / name
            if child.is_symlink() or (
                getattr(child, "is_junction", None) and child.is_junction()
            ):
                raise ValueError(f"fixture links are unsupported: {child}")
        for name in filenames:
            child = current_path / name
            if child.is_symlink() or (
                getattr(child, "is_junction", None) and child.is_junction()
            ):
                raise ValueError(f"fixture links are unsupported: {child}")
            manifest[child.relative_to(folder).as_posix()] = sha256_file(child)
    return dict(sorted(manifest.items()))


def verify_fixture_arm(
    run_dir: Path, arm: dict[str, object], fixture: Path
) -> dict[str, str]:
    if not fixture.is_dir():
        raise ValueError(f"missing prepared execution fixture: {fixture}")
    expected: dict[str, str] = {}
    skill_id = arm.get("skill")
    install_mode = arm.get("install_mode")
    if skill_id is not None and install_mode in {"project", "both"}:
        snapshot = run_dir / "prepared" / "skills" / arm["id"] / skill_id
        destination = fixture / ".agents" / "skills" / skill_id
        if package_sha256(destination) != arm.get("skill_package_sha256"):
            raise ValueError(f"execution fixture skill hash does not match frozen arm: {fixture}")
        for source in sorted(path for path in snapshot.rglob("*") if path.is_file()):
            relative = source.relative_to(snapshot)
            expected[(Path(".agents") / "skills" / skill_id / relative).as_posix()] = sha256_file(source)
    actual = tree_manifest(fixture)
    if actual != dict(sorted(expected.items())):
        raise ValueError(f"execution fixture files do not match frozen arm: {fixture}")
    return actual


def verify_execution_fixtures(
    run_dir: Path, frozen: dict[str, object]
) -> dict[str, dict[str, str]]:
    return {
        arm["id"]: verify_fixture_arm(
            run_dir, arm, run_dir / "prepared" / "fixtures" / arm["id"]
        )
        for arm in frozen["arms"]
    }


def load_prepared_prompts(
    run_dir: Path, frozen: dict[str, object]
) -> dict[tuple[str, str], str]:
    tests_path = run_dir / "prepared" / "tests.json"
    value = json.loads(tests_path.read_text(encoding="utf-8"))
    if not isinstance(value, list):
        raise ValueError("prepared tests must be a list")
    prompts: dict[tuple[str, str], str] = {}
    for test in value:
        if not isinstance(test, dict):
            raise ValueError("prepared test entries must be objects")
        metadata = test.get("metadata")
        variables = test.get("vars")
        case_id = metadata.get("case_id") if isinstance(metadata, dict) else None
        arm_id = metadata.get("arm_id") if isinstance(metadata, dict) else None
        prompt = variables.get("prompt") if isinstance(variables, dict) else None
        key = (case_id, arm_id)
        if not isinstance(case_id, str) or not isinstance(arm_id, str):
            raise ValueError("prepared test is missing case/arm metadata")
        if not isinstance(prompt, str) or not prompt:
            raise ValueError("prepared test is missing its prompt")
        if key in prompts:
            raise ValueError(f"duplicate prepared prompt for {case_id}/{arm_id}")
        prompts[key] = prompt
    expected = {
        (case_id, arm["id"])
        for case_id in frozen["selected_case_ids"]
        for arm in frozen["arms"]
    }
    if set(prompts) != expected:
        raise ValueError("prepared prompts do not cover every case and arm exactly")
    return prompts


def codex_config_args(model: str, reasoning_effort: str) -> list[str]:
    return [
        "--ignore-user-config",
        "--ignore-rules",
        "--model",
        model,
        "-c",
        f'model_reasoning_effort="{reasoning_effort}"',
        "-c",
        'sandbox_mode="read-only"',
        "-c",
        'approval_policy="never"',
        "-c",
        "network_access=false",
        "-c",
        'web_search="disabled"',
        "-c",
        "features.apps=false",
        "-c",
        "features.plugins=false",
        "-c",
        "features.multi_agent=false",
        "-c",
        "apps._default.enabled=false",
    ]


def build_codex_command(
    codex_path: str,
    model: str,
    reasoning_effort: str,
    output_path: Path,
    thread_id: str | None = None,
) -> list[str]:
    common = codex_config_args(model, reasoning_effort)
    if thread_id is None:
        command = [
            codex_path,
            "exec",
            *common,
            "--sandbox",
            "read-only",
            "--json",
            "--output-last-message",
            str(output_path),
            "-",
        ]
    else:
        command = [
            codex_path,
            "exec",
            "resume",
            *common,
            "--json",
            "--output-last-message",
            str(output_path),
            thread_id,
            "-",
        ]
    if "--last" in command or "--ephemeral" in command:
        raise ValueError("native resume commands must not use --last or --ephemeral")
    if thread_id is not None and thread_id not in command:
        raise ValueError("resume command must contain the explicit thread id")
    return command


def safe_command(command: list[str], output_path: Path) -> list[str]:
    return [
        "<codex>" if index == 0 else "<OUTPUT>" if part == str(output_path) else part
        for index, part in enumerate(command)
    ]


def isolated_environment(home: Path) -> dict[str, str]:
    environment = {
        key: value for key, value in os.environ.items() if key.upper() in SAFE_ENV_KEYS
    }
    environment.update(
        {
            "CODEX_HOME": str(home / ".codex"),
            "HOME": str(home),
            "USERPROFILE": str(home),
        }
    )
    return environment


def parse_jsonl(raw: bytes) -> tuple[list[dict[str, object]], list[int]]:
    events = []
    invalid_lines = []
    for line_number, line in enumerate(raw.decode("utf-8", errors="replace").splitlines(), 1):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            invalid_lines.append(line_number)
            continue
        if not isinstance(event, dict):
            invalid_lines.append(line_number)
            continue
        events.append(event)
    return events, invalid_lines


def event_thread_ids(events: list[dict[str, object]]) -> list[str]:
    return [
        event["thread_id"]
        for event in events
        if event.get("type") == "thread.started"
        and isinstance(event.get("thread_id"), str)
        and event["thread_id"]
    ]


def item_types(events: list[dict[str, object]]) -> list[str]:
    values = []
    for event in events:
        item = event.get("item")
        item_type = item.get("type") if isinstance(item, dict) else None
        if isinstance(item_type, str):
            values.append(item_type)
    return values


def agent_messages(events: list[dict[str, object]]) -> list[str]:
    messages = []
    for event in events:
        item = event.get("item")
        if (
            isinstance(item, dict)
            and item.get("type") == "agent_message"
            and isinstance(item.get("text"), str)
        ):
            messages.append(item["text"])
    return messages


def forbidden_item_types(types: list[str]) -> list[str]:
    return sorted({item_type for item_type in types if item_type not in ALLOWED_ITEM_TYPES})


def execute_turn(
    command: list[str],
    prompt: str,
    cwd: Path,
    environment: dict[str, str],
    output_path: Path,
    timeout_seconds: int,
    expected_thread_id: str | None,
) -> dict[str, object]:
    prompt_bytes = prompt.encode("utf-8")
    started_at = dt.datetime.now(dt.timezone.utc).isoformat()
    tick = time.monotonic()
    creationflags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            env=environment,
            input=prompt_bytes,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout_seconds,
            creationflags=creationflags,
            check=False,
        )
        exit_code = completed.returncode
        stdout = completed.stdout
        stderr = completed.stderr
        error = None
    except subprocess.TimeoutExpired as exc:
        exit_code = None
        stdout = exc.stdout or b""
        stderr = exc.stderr or b""
        error = f"timeout after {timeout_seconds} seconds; no retry"
    duration_ms = round((time.monotonic() - tick) * 1000)
    output = output_path.read_bytes() if output_path.is_file() else b""
    events, invalid_lines = parse_jsonl(stdout)
    thread_ids = event_thread_ids(events)
    types = item_types(events)
    forbidden = forbidden_item_types(types)
    completed_events = [event for event in events if event.get("type") == "turn.completed"]
    messages = agent_messages(events)
    output_text = output.decode("utf-8", errors="replace")
    output_matches_last_message = (
        len(messages) == 1
        and output_text.rstrip("\r\n") == messages[0].rstrip("\r\n")
    )
    observed_thread_id = thread_ids[0] if len(thread_ids) == 1 else None
    thread_matches = (
        observed_thread_id is not None
        and (expected_thread_id is None or observed_thread_id == expected_thread_id)
    )
    technical_valid = (
        exit_code == 0
        and error is None
        and bool(output)
        and not invalid_lines
        and len(thread_ids) == 1
        and thread_matches
        and len(completed_events) == 1
        and output_matches_last_message
        and not forbidden
    )
    return {
        "started_at": started_at,
        "finished_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "duration_ms": duration_ms,
        "prompt_sha256": sha256_bytes(prompt_bytes),
        "raw_output": output_text,
        "output_sha256": sha256_bytes(output),
        "raw_events": stdout.decode("utf-8", errors="replace"),
        "events_sha256": sha256_bytes(stdout),
        "stderr": stderr.decode("utf-8", errors="replace"),
        "stderr_sha256": sha256_bytes(stderr),
        "exit_code": exit_code,
        "error": error,
        "invalid_jsonl_lines": invalid_lines,
        "event_thread_ids": thread_ids,
        "thread_id": observed_thread_id,
        "thread_matches_expected": thread_matches,
        "item_types": types,
        "forbidden_item_types": forbidden,
        "agent_messages": messages,
        "output_matches_last_agent_message": output_matches_last_message,
        "usage": completed_events[0].get("usage") if len(completed_events) == 1 else None,
        "technical_valid": technical_valid,
    }


def initialize_fixture(
    run_dir: Path,
    arm: dict[str, object],
    source: Path,
    destination: Path,
    git_path: str,
) -> tuple[bool, str]:
    shutil.copytree(source, destination)
    verify_fixture_arm(run_dir, arm, destination)
    creationflags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    completed = subprocess.run(
        [git_path, "init", "--quiet", "--initial-branch=main"],
        cwd=destination,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        creationflags=creationflags,
        check=False,
    )
    return completed.returncode == 0, completed.stderr.decode("utf-8", errors="replace")


def run_trajectory(
    run_dir: Path,
    execution_root: Path,
    frozen: dict[str, object],
    case: dict[str, object],
    arm: dict[str, object],
    repetition: int,
    prepared_prompt: str,
    auth_json: Path,
    codex_path: str,
    git_path: str,
    timeout_seconds: int,
) -> dict[str, object]:
    case_id = case["id"]
    arm_id = arm["id"]
    trajectory_id = f"{case_id}--{arm_id}--r{repetition}"
    evidence_dir = run_dir / "trajectories" / trajectory_id
    evidence_dir.mkdir(parents=True, exist_ok=False)
    work = execution_root / "workspaces" / trajectory_id
    home = execution_root / "homes" / trajectory_id
    fixture_source = run_dir / "prepared" / "fixtures" / arm_id
    valid_git, git_stderr = initialize_fixture(
        run_dir, arm, fixture_source, work, git_path
    )
    (evidence_dir / "git-init-stderr.txt").write_text(git_stderr, encoding="utf-8")
    codex_home = home / ".codex"
    codex_home.mkdir(parents=True)
    shutil.copyfile(auth_json, codex_home / "auth.json")
    if arm.get("install_mode") in {"home", "both"}:
        skill_id = arm.get("skill")
        source = run_dir / "prepared" / "skills" / arm_id / str(skill_id)
        destination = home / ".agents" / "skills" / str(skill_id)
        shutil.copytree(source, destination)
        if package_sha256(destination) != arm.get("skill_package_sha256"):
            raise ValueError("home execution skill copy differs from frozen package")
    package_hash = arm.get("skill_package_sha256")
    result: dict[str, object] = {
        "trajectory_id": trajectory_id,
        "case_id": case_id,
        "arm_id": arm_id,
        "repetition": repetition,
        "mechanism": case["mechanism"],
        "purpose": case.get("purpose"),
        "hard_criteria": case["hard_criteria"],
        "source_user_turns": case["turns"],
        "source_user_turns_sha256": sha256_bytes(json_bytes(case["turns"])),
        "skill": arm.get("skill"),
        "skill_package_sha256": package_hash,
        "thread_id": None,
        "setup_valid": valid_git,
        "setup_error": None if valid_git else "git init failed",
        "turns": [],
        "technical_valid": False,
    }
    if not valid_git:
        write_json(evidence_dir / "trajectory.json", result)
        return result
    environment = isolated_environment(home)
    thread_id = None
    prior_output_hashes: list[str] = []
    source_turns = case["turns"]
    for index, source_user_message in enumerate(source_turns, 1):
        submitted_prompt = prepared_prompt if index == 1 else source_user_message
        output_path = evidence_dir / f"turn-{index}-final.txt"
        command = build_codex_command(
            codex_path,
            frozen["model"],
            frozen["reasoning_effort"],
            output_path,
            thread_id,
        )
        record = execute_turn(
            command,
            submitted_prompt,
            work,
            environment,
            output_path,
            timeout_seconds,
            thread_id,
        )
        (evidence_dir / f"turn-{index}-events.jsonl").write_bytes(
            record["raw_events"].encode("utf-8")
        )
        (evidence_dir / f"turn-{index}-stderr.txt").write_bytes(
            record["stderr"].encode("utf-8")
        )
        record.update(
            {
                "turn_index": index,
                "source_user_message": source_user_message,
                "submitted_prompt": submitted_prompt,
                "context_mode": (
                    "initial-prepared-prompt"
                    if index == 1
                    else "native-resume-current-user-message-only"
                ),
                "expected_thread_id": thread_id,
                "prior_output_sha256": list(prior_output_hashes),
                "command": safe_command(command, output_path),
            }
        )
        write_json(evidence_dir / f"turn-{index}-record.json", record)
        result["turns"].append(record)
        if not record["technical_valid"]:
            break
        if thread_id is None:
            thread_id = record["thread_id"]
            result["thread_id"] = thread_id
        prior_output_hashes.append(record["output_sha256"])
    result["technical_valid"] = (
        valid_git
        and len(result["turns"]) == len(source_turns)
        and all(turn["technical_valid"] for turn in result["turns"])
        and isinstance(result["thread_id"], str)
    )
    write_json(evidence_dir / "trajectory.json", result)
    print(
        f"[TRAJECTORY] {trajectory_id} turns={len(result['turns'])}/{len(source_turns)} "
        f"valid={result['technical_valid']}",
        flush=True,
    )
    return result


def run_native_resume(
    run_dir: Path,
    auth_json: Path = DEFAULT_AUTH_JSON,
    repeat: int | None = None,
    max_workers: int | None = None,
    codex_path: str | None = None,
    git_path: str | None = None,
) -> dict[str, object]:
    run_dir = run_dir.resolve()
    auth_json = auth_json.resolve()
    frozen_path = run_dir / "frozen.json"
    if not frozen_path.is_file():
        raise ValueError(f"missing frozen evidence: {frozen_path}")
    if (run_dir / "run-meta.json").exists():
        raise FileExistsError(f"refusing to overwrite executed run: {run_dir}")
    frozen = read_object(frozen_path, "frozen evidence")
    verify_prepared(run_dir, frozen)
    fixture_manifests = verify_execution_fixtures(run_dir, frozen)
    native = verify_source_spec(ROOT, frozen)
    cases = load_trajectory_cases(ROOT, frozen)
    prompts = load_prepared_prompts(run_dir, frozen)
    if not auth_json.is_file():
        raise ValueError(f"Codex auth file does not exist: {auth_json}")
    effective_repeat = frozen["repetitions"] if repeat is None else repeat
    if (
        not isinstance(effective_repeat, int)
        or isinstance(effective_repeat, bool)
        or not 1 <= effective_repeat <= frozen["repetitions"]
    ):
        raise ValueError("repeat must be from 1 through the frozen repetition count")
    effective_workers = native.get("max_workers", 4) if max_workers is None else max_workers
    if not isinstance(effective_workers, int) or isinstance(effective_workers, bool) or not 1 <= effective_workers <= 8:
        raise ValueError("max_workers must be an integer from 1 to 8")
    timeout_seconds = native.get("timeout_seconds_per_turn", 240)
    if not isinstance(timeout_seconds, int) or isinstance(timeout_seconds, bool) or timeout_seconds < 30:
        raise ValueError("timeout_seconds_per_turn must be an integer of at least 30")
    effective_codex = codex_path or shutil.which("codex.exe") or shutil.which("codex")
    effective_git = git_path or shutil.which("git")
    if not effective_codex:
        raise RuntimeError("codex executable was not found")
    if not effective_git:
        raise RuntimeError("git executable was not found")

    started_at = dt.datetime.now(dt.timezone.utc)
    tick = time.monotonic()
    jobs = [
        (case, arm, repetition)
        for case in cases
        for arm in frozen["arms"]
        for repetition in range(1, effective_repeat + 1)
    ]
    expected_turns = sum(len(case["turns"]) for case, _, _ in jobs)
    metadata: dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "comparison_id": frozen["comparison_id"],
        "status": "running",
        "started_at": started_at.isoformat(),
        "frozen_sha256": sha256_file(frozen_path),
        "repeat": effective_repeat,
        "max_workers": effective_workers,
        "timeout_seconds_per_turn": timeout_seconds,
        "session_mode": "explicit-thread-id",
        "resume_last_used": False,
        "ephemeral_used": False,
        "history_mode": "native-session-retains-actual-output",
        "auth_mode": "temporary-isolated-copy-per-trajectory",
        "execution_workspace": "system-temporary-directory",
        "workspace_initialization": "git-init-per-trajectory",
        "home_isolation": "HOME-USERPROFILE-CODEX_HOME-per-trajectory",
        "host_integrations": "apps-plugins-multi-agent-disabled",
        "execution_fixture_manifests": fixture_manifests,
        "environment_policy": "allowlisted-host-variables-plus-isolated-home",
        "expected_trajectories": len(jobs),
        "expected_turns": expected_turns,
        "results_sha256": None,
    }
    write_json(run_dir / "run-meta.json", metadata)
    results: list[dict[str, object]] = []
    with tempfile.TemporaryDirectory(prefix="zero-skill-native-resume-") as temporary:
        execution_root = Path(temporary)
        (execution_root / "workspaces").mkdir()
        (execution_root / "homes").mkdir()

        def execute_job(job: tuple[dict[str, object], dict[str, object], int]):
            case, arm, repetition = job
            try:
                return run_trajectory(
                    run_dir,
                    execution_root,
                    frozen,
                    case,
                    arm,
                    repetition,
                    prompts[(case["id"], arm["id"])],
                    auth_json,
                    effective_codex,
                    effective_git,
                    timeout_seconds,
                )
            except Exception as error:  # preserve job-level infrastructure failures
                trajectory_id = f"{case['id']}--{arm['id']}--r{repetition}"
                evidence_dir = run_dir / "trajectories" / trajectory_id
                evidence_dir.mkdir(parents=True, exist_ok=True)
                failed = {
                    "trajectory_id": trajectory_id,
                    "case_id": case["id"],
                    "arm_id": arm["id"],
                    "repetition": repetition,
                    "mechanism": case["mechanism"],
                    "purpose": case.get("purpose"),
                    "hard_criteria": case["hard_criteria"],
                    "source_user_turns": case["turns"],
                    "source_user_turns_sha256": sha256_bytes(json_bytes(case["turns"])),
                    "skill": arm.get("skill"),
                    "skill_package_sha256": arm.get("skill_package_sha256"),
                    "thread_id": None,
                    "setup_valid": False,
                    "setup_error": f"{type(error).__name__}: {error}",
                    "turns": [],
                    "technical_valid": False,
                }
                write_json(evidence_dir / "trajectory.json", failed)
                print(f"[TRAJECTORY] {trajectory_id} error={failed['setup_error']}", flush=True)
                return failed

        with concurrent.futures.ThreadPoolExecutor(max_workers=effective_workers) as pool:
            for result in pool.map(execute_job, jobs):
                results.append(result)
    results.sort(key=lambda item: (item["case_id"], item["arm_id"], item["repetition"]))
    payload = {
        "schema_version": SCHEMA_VERSION,
        "comparison_id": frozen["comparison_id"],
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "trajectories": results,
    }
    results_path = run_dir / "native-results.json"
    write_json_once(results_path, payload)
    valid_count = sum(result["technical_valid"] for result in results)
    actual_turns = sum(len(result["turns"]) for result in results)
    metadata.update(
        {
            "status": (
                "completed" if valid_count == len(results) else "completed-with-failures"
            ),
            "finished_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "duration_ms": round((time.monotonic() - tick) * 1000),
            "result_trajectories": len(results),
            "valid_trajectories": valid_count,
            "invalid_trajectories": len(results) - valid_count,
            "result_turns": actual_turns,
            "results_sha256": sha256_file(results_path),
        }
    )
    write_json(run_dir / "run-meta.json", metadata)
    print(
        f"[DONE] native resume results at {run_dir} "
        f"({valid_count}/{len(results)} trajectories valid)",
        flush=True,
    )
    return metadata


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", required=True, type=Path, dest="run_dir")
    parser.add_argument("--auth-json", type=Path, default=DEFAULT_AUTH_JSON)
    parser.add_argument("--repeat", type=int)
    parser.add_argument("--max-workers", type=int)
    parser.add_argument("--codex", dest="codex_path")
    parser.add_argument("--git", dest="git_path")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_native_resume(
        args.run_dir,
        args.auth_json,
        args.repeat,
        args.max_workers,
        args.codex_path,
        args.git_path,
    )


if __name__ == "__main__":
    main()

