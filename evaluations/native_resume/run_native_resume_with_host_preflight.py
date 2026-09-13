"""Run native resume evaluation only after its restricted host sandbox canary passes."""

from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path
import shutil
import sys
import time


NATIVE_RESUME_DIR = Path(__file__).resolve().parent
if str(NATIVE_RESUME_DIR) not in sys.path:
    sys.path.insert(0, str(NATIVE_RESUME_DIR))

from preflight_host_sandbox import run_host_sandbox_preflight  # noqa: E402
from run_native_resume import (  # noqa: E402
    DEFAULT_AUTH_JSON,
    ROOT,
    read_object,
    run_native_resume,
    sha256_file,
    verify_source_spec,
    write_json_once,
)


def require_host_preflight_flag(run_dir: Path) -> dict[str, object]:
    frozen_path = run_dir / "frozen.json"
    frozen = read_object(frozen_path, "frozen evidence")
    native = verify_source_spec(ROOT, frozen)
    value = native.get("require_host_sandbox_preflight")
    if value is not True:
        raise ValueError(
            "preflight wrapper requires native_resume.require_host_sandbox_preflight=true"
        )
    return frozen


def run_native_resume_with_host_preflight(
    run_dir: Path,
    auth_json: Path = DEFAULT_AUTH_JSON,
    repeat: int | None = None,
    max_workers: int | None = None,
    codex_path: str | None = None,
    git_path: str | None = None,
) -> dict[str, object]:
    run_dir = run_dir.resolve()
    if (run_dir / "run-meta.json").exists():
        raise FileExistsError(f"refusing to overwrite executed run: {run_dir}")
    preflight_path = run_dir / "host-sandbox-preflight.json"
    stop_path = run_dir / "host-preflight-stop.json"
    if preflight_path.exists() or stop_path.exists():
        raise FileExistsError(f"refusing to overwrite host preflight: {run_dir}")
    frozen = require_host_preflight_flag(run_dir)
    effective_codex = codex_path or shutil.which("codex.exe") or shutil.which("codex")
    if not effective_codex:
        raise RuntimeError("codex executable was not found")

    started_at = dt.datetime.now(dt.timezone.utc)
    tick = time.monotonic()
    preflight = run_host_sandbox_preflight(effective_codex, ROOT)
    write_json_once(preflight_path, preflight)
    if preflight.get("passed") is not True:
        stop = {
            "schema_version": 1,
            "comparison_id": frozen.get("comparison_id"),
            "status": "host-sandbox-preflight-blocked",
            "started_at": started_at.isoformat(),
            "finished_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "duration_ms": round((time.monotonic() - tick) * 1000),
            "frozen_sha256": sha256_file(run_dir / "frozen.json"),
            "host_sandbox_preflight_sha256": sha256_file(preflight_path),
            "host_sandbox_preflight_status": preflight.get("status"),
            "model_calls": 0,
            "result_trajectories": 0,
            "result_turns": 0,
        }
        write_json_once(stop_path, stop)
        raise RuntimeError(
            "host sandbox preflight failed before model execution: "
            f"{preflight.get('status')}"
        )

    return run_native_resume(
        run_dir,
        auth_json,
        repeat,
        max_workers,
        effective_codex,
        git_path,
    )


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
    run_native_resume_with_host_preflight(
        args.run_dir,
        args.auth_json,
        args.repeat,
        args.max_workers,
        args.codex_path,
        args.git_path,
    )


if __name__ == "__main__":
    main()
