"""Check that the native Codex Windows sandbox can start a harmless command."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time


CANARY_TOKEN = "CODEX_WINDOWS_SANDBOX_CANARY_OK"
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
SANDBOX_FAILURE = re.compile(
    r"windows sandbox failed:\s*([^:\s]+):\s*([^\r\n]+)", re.IGNORECASE
)
DOCTOR_DETAIL_FIELDS = {
    "approval policy": "approval_policy",
    "denied-read restrictions": "denied_read_restrictions",
    "denied-read rules": "denied_read_rules",
    "error code": "error_code",
    "execve wrapper helper": "execve_wrapper_helper",
    "filesystem sandbox": "filesystem_sandbox",
    "network sandbox": "network_sandbox",
    "sandbox backend": "sandbox_backend",
    "sandbox provisioning": "sandbox_provisioning",
}


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def build_windows_canary_command(codex_path: str, workspace: Path) -> list[str]:
    script = (
        f"if ((Get-Location).Path) {{ Write-Output '{CANARY_TOKEN}' }}"
    )
    return [
        codex_path,
        "sandbox",
        "--permission-profile",
        ":read-only",
        "--cd",
        str(workspace),
        "powershell.exe",
        "-NoProfile",
        "-NonInteractive",
        "-Command",
        script,
    ]


def classify_windows_canary(
    exit_code: int | None,
    stdout: bytes,
    stderr: bytes,
    error: str | None,
) -> dict[str, object]:
    output = stdout.decode("utf-8", errors="replace").strip()
    error_text = stderr.decode("utf-8", errors="replace")
    if error is not None:
        return {
            "passed": False,
            "status": "canary-execution-error",
            "error_code": None,
            "error_detail": error,
        }
    failure = SANDBOX_FAILURE.search(error_text)
    if failure:
        return {
            "passed": False,
            "status": "sandbox-provisioning-failed",
            "error_code": failure.group(1),
            "error_detail": failure.group(2).strip(),
        }
    if "blocked by policy" in error_text.lower():
        return {
            "passed": False,
            "status": "command-policy-blocked",
            "error_code": None,
            "error_detail": "blocked by policy",
        }
    if exit_code == 0 and output == CANARY_TOKEN:
        return {
            "passed": True,
            "status": "ready",
            "error_code": None,
            "error_detail": None,
        }
    if exit_code == 0:
        return {
            "passed": False,
            "status": "canary-output-mismatch",
            "error_code": None,
            "error_detail": "successful process did not return the exact canary token",
        }
    return {
        "passed": False,
        "status": "canary-command-failed",
        "error_code": None,
        "error_detail": f"canary exited with code {exit_code}",
    }


def redact_text(value: str, workspace: Path, user_home: Path) -> str:
    replacements = [
        (str(workspace.resolve()), "<WORKSPACE>"),
        (str(workspace), "<WORKSPACE>"),
        (str(user_home.resolve()), "<USER_HOME>"),
        (str(user_home), "<USER_HOME>"),
    ]
    redacted = value
    for raw, marker in replacements:
        if raw:
            redacted = re.sub(re.escape(raw), marker, redacted, flags=re.IGNORECASE)
            redacted = re.sub(
                re.escape(raw.replace("\\", "/")),
                marker,
                redacted,
                flags=re.IGNORECASE,
            )
    return redacted


def safe_command(command: list[str], workspace: Path) -> list[str]:
    safe = []
    for index, part in enumerate(command):
        if index == 0:
            safe.append("<codex>")
        elif part.casefold() == str(workspace).casefold():
            safe.append("<WORKSPACE>")
        else:
            safe.append(part)
    return safe


def build_public_record(
    command: list[str],
    workspace: Path,
    user_home: Path,
    exit_code: int | None,
    stdout: bytes,
    stderr: bytes,
    error: str | None,
    duration_ms: int,
    codex_version: str,
    codex_version_probe_error: str | None = None,
) -> dict[str, object]:
    classification = classify_windows_canary(exit_code, stdout, stderr, error)
    public_classification = {
        key: redact_text(value, workspace, user_home)
        if isinstance(value, str)
        else value
        for key, value in classification.items()
    }
    normalized_stdout = redact_text(
        stdout.decode("utf-8", errors="replace"), workspace, user_home
    )
    normalized_stderr = redact_text(
        stderr.decode("utf-8", errors="replace"), workspace, user_home
    )
    normalized_error = (
        redact_text(error, workspace, user_home) if error is not None else None
    )
    return {
        "schema_version": 1,
        "platform": "windows",
        "purpose": "prove restricted native command startup before model evaluation",
        "permission_profile": ":read-only",
        "command": safe_command(command, workspace),
        "codex_version": redact_text(codex_version, workspace, user_home).strip(),
        "codex_version_probe_error": (
            redact_text(codex_version_probe_error, workspace, user_home)
            if codex_version_probe_error is not None
            else None
        ),
        "exit_code": exit_code,
        "error": normalized_error,
        "duration_ms": duration_ms,
        "stdout": normalized_stdout,
        "stderr": normalized_stderr,
        "raw_stdout_sha256": sha256_bytes(stdout),
        "raw_stderr_sha256": sha256_bytes(stderr),
        **public_classification,
    }


def project_doctor_sandbox(
    exit_code: int | None,
    stdout: bytes,
    stderr: bytes,
    workspace: Path | None = None,
    user_home: Path | None = None,
) -> dict[str, object]:
    base: dict[str, object] = {
        "schema_version": 1,
        "source": "codex doctor --json",
        "doctor_exit_code": exit_code,
        "raw_stdout_sha256": sha256_bytes(stdout),
        "raw_stderr_sha256": sha256_bytes(stderr),
    }
    try:
        payload = json.loads(stdout.decode("utf-8"))
        check = payload["checks"]["sandbox.helpers"]
        if not isinstance(check, dict) or not isinstance(check.get("details"), dict):
            raise ValueError("missing sandbox helper details")
    except (UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError, ValueError):
        return {
            **base,
            "diagnostic_available": False,
            "status": "invalid-doctor-output",
        }
    workspace = Path.cwd() if workspace is None else workspace
    user_home = Path.home() if user_home is None else user_home

    def public_value(value: object) -> object:
        if isinstance(value, str):
            return redact_text(value, workspace, user_home)
        if value is None or isinstance(value, (bool, int, float)):
            return value
        return None

    projection = {
        output_name: public_value(check["details"].get(input_name))
        for input_name, output_name in DOCTOR_DETAIL_FIELDS.items()
    }
    return {
        **base,
        "diagnostic_available": True,
        "status": public_value(check.get("status")),
        "summary": public_value(check.get("summary")),
        **projection,
        "remediation": public_value(check.get("remediation")),
    }


def restricted_environment() -> dict[str, str]:
    return {
        key: value for key, value in os.environ.items() if key.upper() in SAFE_ENV_KEYS
    }


def probe_codex_version(
    codex_path: str,
    workspace: Path,
    environment: dict[str, str],
    timeout_seconds: int,
    creationflags: int,
    run_command=subprocess.run,
) -> tuple[str, str | None]:
    try:
        completed = run_command(
            [codex_path, "--version"],
            cwd=workspace,
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout_seconds,
            creationflags=creationflags,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return "unavailable", f"timeout after {timeout_seconds} seconds"
    except OSError as exc:
        return "unavailable", f"{type(exc).__name__}: {exc}"
    if completed.returncode != 0:
        return "unavailable", f"version probe exited with code {completed.returncode}"
    value = completed.stdout.decode("utf-8", errors="replace").strip()
    if not value:
        return "unavailable", "version probe returned empty stdout"
    return value, None


def run_host_sandbox_preflight(
    codex_path: str,
    workspace: Path,
    timeout_seconds: int = 30,
) -> dict[str, object]:
    if os.name != "nt":
        return {
            "schema_version": 1,
            "platform": os.name,
            "purpose": "Windows native sandbox preflight",
            "passed": True,
            "status": "not-applicable",
        }
    workspace = workspace.resolve()
    environment = restricted_environment()
    creationflags = subprocess.CREATE_NO_WINDOW
    codex_version, version_error = probe_codex_version(
        codex_path,
        workspace,
        environment,
        timeout_seconds,
        creationflags,
    )
    command = build_windows_canary_command(codex_path, workspace)
    tick = time.monotonic()
    try:
        completed = subprocess.run(
            command,
            cwd=workspace,
            env=environment,
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
        error = f"timeout after {timeout_seconds} seconds"
    except OSError as exc:
        exit_code = None
        stdout = b""
        stderr = b""
        error = f"{type(exc).__name__}: {exc}"
    return build_public_record(
        command,
        workspace,
        Path.home(),
        exit_code,
        stdout,
        stderr,
        error,
        round((time.monotonic() - tick) * 1000),
        codex_version,
        version_error,
    )
