"""Verify the current engineering fixtures in fresh Python processes."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

BASE = Path(__file__).resolve().parent
CASES = ("memo", "document")
MODULES = ("test_public", "test_acceptance")


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def fixture_files():
    return [
        path for path in sorted((BASE / "fixtures").rglob("*"))
        if path.is_file() and "__pycache__" not in path.parts
    ]


def fixture_fingerprint():
    digest = hashlib.sha256()
    for path in fixture_files():
        relative = path.relative_to(BASE / "fixtures").as_posix().encode("utf-8")
        content = path.read_bytes()
        for data in (relative, content):
            digest.update(len(data).to_bytes(8, "big"))
            digest.update(data)
    return digest.hexdigest()


def run_suite(case, variant, module):
    source = BASE / "fixtures" / case
    with tempfile.TemporaryDirectory(prefix="zero-engineering-fixture-current-") as raw:
        work = Path(raw)
        for path in (source / "public").iterdir():
            if path.is_file():
                shutil.copyfile(path, work / path.name)
        shutil.copyfile(source / "heldout" / "test_acceptance.py", work / "test_acceptance.py")
        if variant == "reference":
            shutil.copyfile(source / "heldout" / f"reference_{case}.py", work / f"{case}.py")
        process = subprocess.run(
            [sys.executable, "-B", "-m", "unittest", module, "-v"],
            cwd=work,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=20,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    text = (process.stdout + process.stderr).decode("utf-8", errors="replace")
    match = re.search(r"Ran (\d+) tests? in", text)
    expected_exit = 1 if variant == "original" else 0
    return {
        "case": case,
        "variant": variant,
        "module": module,
        "exit_code": process.returncode,
        "expected_exit_code": expected_exit,
        "tests_run": int(match.group(1)) if match else 0,
        "expectation_met": process.returncode == expected_exit,
        "stdout_sha256": sha256(process.stdout),
        "stderr_sha256": sha256(process.stderr),
    }


def build_report():
    files = fixture_files()
    results = [
        run_suite(case, variant, module)
        for case in CASES
        for variant in ("original", "reference")
        for module in MODULES
    ]
    if not all(item["expectation_met"] and item["tests_run"] > 0 for item in results):
        raise SystemExit("fixture verification failed")
    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "scope": "Current LF-normalized public and held-out fixtures; historical partial-mutant evidence remains in fixture-verification.json.",
        "fixture_tree_sha256": fixture_fingerprint(),
        "source_sha256": {
            path.relative_to(BASE).as_posix(): sha256(path.read_bytes())
            for path in files
        },
        "results": results,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = json.dumps(build_report(), ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_bytes(report.encode("utf-8"))
        print(args.output)
    else:
        print(report, end="")


if __name__ == "__main__":
    main()
