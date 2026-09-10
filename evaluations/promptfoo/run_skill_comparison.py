"""Run a prepared Promptfoo comparison outside the repository with isolated auth."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time


PROMPTFOO_PACKAGE = "promptfoo"
DEFAULT_AUTH_JSON = Path.home() / ".codex" / "auth.json"


def write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def package_sha256(folder: Path) -> str:
    if not folder.is_dir():
        raise ValueError(f"missing frozen skill package: {folder}")
    digest = hashlib.sha256()
    files = sorted(
        (path for path in folder.rglob("*") if path.is_file()),
        key=lambda path: path.relative_to(folder).as_posix(),
    )
    for path in files:
        if path.is_symlink() or (
            getattr(path, "is_junction", None) and path.is_junction()
        ):
            raise ValueError(f"frozen skill package links are unsupported: {path}")
        for data in (
            path.relative_to(folder).as_posix().encode("utf-8"),
            path.read_bytes(),
        ):
            digest.update(len(data).to_bytes(8, "big"))
            digest.update(data)
    return digest.hexdigest()

def verify_prepared(run_dir: Path, frozen: dict[str, object]) -> None:
    checks = (
        (
            run_dir / "prepared" / "promptfooconfig.json",
            frozen.get("prepared_config_sha256"),
            "prepared config hash",
        ),
        (
            run_dir / "prepared" / "tests.json",
            frozen.get("prepared_tests_sha256"),
            "prepared tests hash",
        ),
    )
    for path, expected, label in checks:
        if not path.is_file() or sha256_file(path) != expected:
            raise ValueError(f"{label} does not match frozen evidence: {path}")
    for arm in frozen.get("arms", []):
        if not arm.get("skill"):
            continue
        snapshot = (
            run_dir
            / "prepared"
            / "skills"
            / arm["id"]
            / arm["skill"]
        )
        if package_sha256(snapshot) != arm.get("skill_package_sha256"):
            raise ValueError(
                f"prepared skill hash does not match frozen evidence: {snapshot}"
            )


def load_result_rows(path: Path) -> list[dict[str, object]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"Promptfoo result is not readable JSON: {path}") from error
    results = payload.get("results") if isinstance(payload, dict) else None
    rows = results.get("results") if isinstance(results, dict) else None
    if not isinstance(rows, list):
        raise ValueError(f"Promptfoo result has no result rows: {path}")
    return rows

def promptfoo_command(
    npx_path: str,
    version: str,
    action: str,
    repeat: int,
) -> list[str]:
    base = [npx_path, "--yes", f"{PROMPTFOO_PACKAGE}@{version}"]
    if action == "validate":
        return base + ["validate", "config", "-c", "promptfooconfig.json"]
    if action == "eval":
        return base + [
            "eval",
            "-c",
            "promptfooconfig.json",
            "--repeat",
            str(repeat),
            "--no-cache",
            "-o",
            "results.json",
            "-o",
            "results.html",
        ]
    raise ValueError(f"unsupported Promptfoo action: {action}")


def safe_command(command: list[str]) -> list[str]:
    return ["<npx>" if index == 0 else part for index, part in enumerate(command)]


def execute(
    command: list[str],
    execution_root: Path,
    environment: dict[str, str],
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=execution_root,
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def run_comparison(
    run_dir: Path,
    auth_json: Path,
    npx_path: str,
    repeat: int | None = None,
    git_path: str | None = None,
) -> dict[str, object]:
    run_dir = run_dir.resolve()
    auth_json = auth_json.resolve()
    frozen_path = run_dir / "frozen.json"
    if not frozen_path.is_file():
        raise ValueError(f"missing frozen evidence: {frozen_path}")
    frozen = json.loads(frozen_path.read_text(encoding="utf-8"))
    verify_prepared(run_dir, frozen)
    if not auth_json.is_file():
        raise ValueError(f"Codex auth file does not exist: {auth_json}")
    effective_repeat = frozen["repetitions"] if repeat is None else repeat
    if not isinstance(effective_repeat, int) or isinstance(effective_repeat, bool) or not 1 <= effective_repeat <= 10:
        raise ValueError("repeat must be an integer from 1 to 10")
    if (run_dir / "run-meta.json").exists():
        raise FileExistsError(f"refusing to overwrite executed run: {run_dir}")
    effective_git_path = git_path or shutil.which("git")
    if not effective_git_path:
        raise RuntimeError("git was not found; isolated repo skill discovery requires it")

    started_at = dt.datetime.now(dt.timezone.utc)
    tick = time.monotonic()
    version = frozen["promptfoo_version"]
    validation_command = promptfoo_command(npx_path, version, "validate", effective_repeat)
    eval_command = promptfoo_command(npx_path, version, "eval", effective_repeat)
    metadata: dict[str, object] = {
        "schema_version": 1,
        "comparison_id": frozen["comparison_id"],
        "started_at": started_at.isoformat(),
        "promptfoo_version": version,
        "frozen_sha256": sha256_file(frozen_path),
        "repeat": effective_repeat,
        "auth_mode": "temporary-isolated-copy",
        "execution_workspace": "system-temporary-directory",
        "workspace_initialization": "git-init-per-arm",
        "home_isolation": "HOME-USERPROFILE-CODEX_HOME-per-arm",
        "host_integrations": "apps-plugins-multi-agent-disabled",
        "commands": [safe_command(validation_command), safe_command(eval_command)],
        "validation_exit_code": None,
        "exit_code": None,
        "duration_ms": None,
        "results_sha256": None,
        "html_sha256": None,
    }
    write_json(run_dir / "run-meta.json", metadata)

    with tempfile.TemporaryDirectory(prefix="zero-skill-promptfoo-") as temporary:
        execution_root = Path(temporary)
        shutil.copytree(run_dir / "prepared", execution_root, dirs_exist_ok=True)
        evaluation_homes = execution_root / "evaluation-homes"
        evaluation_homes.mkdir()
        for arm in frozen["arms"]:
            fixture = execution_root / "fixtures" / arm["id"]
            initialized = subprocess.run(
                [effective_git_path, "init", "--quiet", "--initial-branch=main"],
                cwd=fixture,
                env=os.environ.copy(),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
            )
            if initialized.returncode != 0:
                metadata["status"] = "runtime-error"
                metadata["duration_ms"] = round((time.monotonic() - tick) * 1000)
                metadata["finished_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
                metadata["setup_error"] = f"git init failed for isolated arm {arm['id']}"
                write_json(run_dir / "run-meta.json", metadata)
                raise RuntimeError(
                    f"git init failed for isolated arm {arm['id']}: "
                    + initialized.stderr.strip()
                )
            arm_home = evaluation_homes / arm["id"]
            codex_home = arm_home / ".codex"
            codex_home.mkdir(parents=True)
            shutil.copyfile(auth_json, codex_home / "auth.json")
            if arm.get("install_mode") in {"home", "both"}:
                source = execution_root / "skills" / arm["id"] / arm["skill"]
                destination = arm_home / ".agents" / "skills" / arm["skill"]
                shutil.copytree(source, destination)
        promptfoo_home = execution_root / "promptfoo-home"
        promptfoo_home.mkdir()
        environment = os.environ.copy()
        environment.update(
            {
                "EVAL_HOME_BASE": str(evaluation_homes),
                "PROMPTFOO_CONFIG_DIR": str(promptfoo_home),
                "PROMPTFOO_DISABLE_TELEMETRY": "true",
                "PROMPTFOO_DISABLE_REMOTE_GENERATION": "true",
            }
        )

        print("[RUN] validating frozen Promptfoo configuration", flush=True)
        validation = execute(validation_command, execution_root, environment)
        (run_dir / "validate-stdout.txt").write_text(validation.stdout, encoding="utf-8")
        (run_dir / "validate-stderr.txt").write_text(validation.stderr, encoding="utf-8")
        metadata["validation_exit_code"] = validation.returncode
        write_json(run_dir / "run-meta.json", metadata)
        if validation.returncode != 0:
            metadata["status"] = "validation-error"
            metadata["exit_code"] = validation.returncode
            metadata["duration_ms"] = round((time.monotonic() - tick) * 1000)
            metadata["finished_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
            write_json(run_dir / "run-meta.json", metadata)
            raise RuntimeError(
                f"Promptfoo config validation failed; see {run_dir / 'validate-stderr.txt'}"
            )

        print(
            f"[RUN] executing {frozen['comparison_id']} with repeat={effective_repeat}",
            flush=True,
        )
        completed = execute(eval_command, execution_root, environment)
        (run_dir / "promptfoo-stdout.txt").write_text(completed.stdout, encoding="utf-8")
        (run_dir / "promptfoo-stderr.txt").write_text(completed.stderr, encoding="utf-8")
        for name in ("results.json", "results.html"):
            source = execution_root / name
            if source.is_file():
                shutil.copyfile(source, run_dir / name)
        metadata["exit_code"] = completed.returncode
        metadata["duration_ms"] = round((time.monotonic() - tick) * 1000)
        metadata["finished_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
        results_path = run_dir / "results.json"
        if not results_path.is_file():
            metadata["status"] = "runtime-error"
            write_json(run_dir / "run-meta.json", metadata)
            raise RuntimeError(
                f"Promptfoo produced no results; see {run_dir / 'promptfoo-stderr.txt'}"
            )
        try:
            rows = load_result_rows(results_path)
        except ValueError as error:
            metadata["status"] = "invalid-results"
            write_json(run_dir / "run-meta.json", metadata)
            raise RuntimeError(str(error)) from error
        expected_rows = (
            len(frozen["selected_case_ids"]) * len(frozen["arms"]) * effective_repeat
        )
        if len(rows) != expected_rows:
            metadata["status"] = "incomplete-results"
            metadata["expected_rows"] = expected_rows
            metadata["result_rows"] = len(rows)
            write_json(run_dir / "run-meta.json", metadata)
            raise RuntimeError(
                f"Promptfoo produced {len(rows)} of {expected_rows} expected rows"
            )
        passed_rows = sum(row.get("success") is True for row in rows)
        metadata["expected_rows"] = expected_rows
        metadata["result_rows"] = len(rows)
        metadata["passed_rows"] = passed_rows
        metadata["failed_rows"] = len(rows) - passed_rows
        metadata["status"] = (
            "completed" if passed_rows == len(rows) else "completed-with-failures"
        )
        metadata["results_sha256"] = sha256_file(results_path)
        if (run_dir / "results.html").is_file():
            metadata["html_sha256"] = sha256_file(run_dir / "results.html")
        write_json(run_dir / "run-meta.json", metadata)

    print(
        f"[DONE] Promptfoo results preserved at {run_dir} ({metadata['status']})",
        flush=True,
    )
    return metadata


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", required=True, type=Path, dest="run_dir")
    parser.add_argument("--auth-json", type=Path, default=DEFAULT_AUTH_JSON)
    parser.add_argument("--npx", dest="npx_path", default=shutil.which("npx.cmd") or shutil.which("npx"))
    parser.add_argument("--repeat", type=int)
    parser.add_argument("--git", dest="git_path", default=shutil.which("git"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.npx_path:
        raise RuntimeError("npx was not found")
    run_comparison(
        args.run_dir,
        args.auth_json,
        args.npx_path,
        args.repeat,
        args.git_path,
    )


if __name__ == "__main__":
    main()
