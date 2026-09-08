"""Validate this repository's JSON records and deliberately small skill format."""

import argparse
from datetime import date
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys
from urllib.parse import unquote, urlsplit

ID_PATTERN = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
VERSION_PATTERN = re.compile(r"\d+\.\d+\.\d+")
LINK_PATTERN = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
FORMS = {"analysis", "perspective", "simulation", "workflow", "tool"}
STATUSES = {"draft", "experimental", "verified", "archived"}
SKILL_FIELDS = {"id", "category", "form", "version", "path", "status", "tags", "upstream_ids", "evaluation", "evidence"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def valid_id(value):
    return isinstance(value, str) and len(value) <= 63 and ID_PATTERN.fullmatch(value) is not None


def unique_strings(value, label, allow_empty=True):
    require(isinstance(value, list) and all(nonempty(item) for item in value), f"{label}: expected string array")
    require(len(value) == len(set(value)), f"{label}: duplicate values")
    require(allow_empty or value, f"{label}: must not be empty")
    return set(value)


def read_json(path):
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError(f"{path}: JSON read failed: {error}") from error
    require(isinstance(value, dict), f"{path}: expected JSON object")
    require(type(value.get("schema_version")) is int and value["schema_version"] == 1, f"{path}: unsupported schema_version")
    return value


def relative_file(root, value):
    require(nonempty(value), "path: expected nonempty relative path")
    pure = PurePosixPath(value)
    require(not pure.is_absolute() and ".." not in pure.parts and "\\" not in value and ":" not in value, f"path escapes or is nonportable: {value}")
    candidate = root / value
    require(candidate.resolve().is_relative_to(root.resolve()), f"path escapes root: {value}")
    require(candidate.is_file(), f"missing file: {value}")
    return candidate


def check_date(value, label):
    require(nonempty(value), f"{label}: missing date")
    try:
        require(date.fromisoformat(value).isoformat() == value, f"{label}: use YYYY-MM-DD")
    except ValueError as error:
        raise ValueError(f"{label}: invalid date {value}") from error


def indexed_records(value, label):
    require(isinstance(value, list), f"{label}: expected array")
    indexed = {}
    for record in value:
        require(isinstance(record, dict), f"{label}: expected record object")
        identifier = record.get("id")
        require(valid_id(identifier), f"{label}: invalid id {identifier!r}")
        require(identifier not in indexed, f"{label}: duplicate id {identifier}")
        indexed[identifier] = record
    return indexed


def package_fingerprint(folder):
    require(folder.is_dir(), f"missing package directory: {folder}")
    digest = hashlib.sha256()
    for path in sorted(folder.rglob("*"), key=lambda item: item.relative_to(folder).as_posix()):
        require(not path.is_symlink(), f"package symlink is unsupported: {path}")
        if path.is_file():
            # Separate and length-prefix both fields to avoid ambiguous concatenations.
            for data in (path.relative_to(folder).as_posix().encode("utf-8"), path.read_bytes()):
                digest.update(len(data).to_bytes(8, "big"))
                digest.update(data)
    return digest.hexdigest()


def validate_upstream(record):
    for field in ("url", "evidence_url"):
        value = record.get(field)
        require(nonempty(value) and urlsplit(value).scheme == "https" and urlsplit(value).hostname, f"upstream {record['id']}: invalid {field}")
    check_date(record.get("observed_on"), "upstream observed_on")
    require(record.get("review_level") in ("readme-reviewed", "entrypoint-reviewed"), "upstream: unknown review_level")
    require(record.get("imported") is False, "upstream imports require a future provenance format; current foundation only supports references")
    require(record.get("revision") is None or nonempty(record["revision"]), "upstream: invalid revision")
    require(record.get("license_declared") is None or nonempty(record["license_declared"]), "upstream: invalid license")
    for field in ("adopt", "caveat", "stars_display"):
        require(nonempty(record.get(field)), f"upstream: missing {field}")


def validate_markdown(package):
    for path in package.rglob("*"):
        require(not path.is_symlink(), f"package symlink is unsupported: {path}")
        if not path.is_file() or path.suffix != ".md":
            continue
        content = path.read_text(encoding="utf-8")
        require(not re.search(r"\{\{.+?\}\}|\bTODO\b|\bTBD\b", content), f"{path}: unfinished placeholder")
        for target in LINK_PATTERN.findall(content):
            target = target.strip().strip("<>")
            parsed = urlsplit(target)
            if parsed.scheme in ("https", "http", "mailto") or target.startswith("#"):
                continue
            require(not parsed.scheme, f"{path}: unsupported link {target}")
            local = unquote(parsed.path)
            require(not Path(local).is_absolute() and "\\" not in local, f"{path}: absolute link {target}")
            destination = (path.parent / local).resolve()
            require(destination.is_relative_to(package.resolve()), f"{path}: link escapes package: {target}")
            require(destination.exists(), f"{path}: missing reference: {target}")


def validate_entrypoint(path, identifier):
    content = path.read_text(encoding="utf-8")
    lines = content.splitlines()
    require(lines and lines[0] == "---", f"{path}: missing frontmatter")
    require("---" in lines[1:], f"{path}: unclosed frontmatter")
    end = lines.index("---", 1)
    fields = {}
    for line in lines[1:end]:
        key, separator, value = line.partition(":")
        require(separator and key not in fields, f"{path}: invalid or duplicate frontmatter key")
        fields[key] = value.strip()
    require(set(fields) == {"name", "description"}, f"{path}: only name and description frontmatter supported")
    require(fields["name"] == identifier, f"{path}: name must match id")
    try:
        description = json.loads(fields["description"])
    except json.JSONDecodeError as error:
        raise ValueError(f"{path}: description must be a JSON-quoted single-line string") from error
    require(nonempty(description), f"{path}: empty description")
    require(nonempty("\n".join(lines[end + 1:])), f"{path}: empty body")
    validate_markdown(path.parent)


def validate_cases(path):
    suite = read_json(path)
    require(valid_id(suite.get("skill_id")), f"{path}: invalid skill_id")
    require(suite.get("stage") in ("planned", "active"), f"{path}: invalid stage")
    cases = indexed_records(suite.get("cases"), str(path))
    require(cases, f"{path}: cases must not be empty")
    for case in cases.values():
        require(nonempty(case.get("prompt")), f"{path}: missing prompt")
        require(isinstance(case.get("input"), dict) and case["input"].get("kind") == "synthetic", f"{path}: public cases require synthetic input")
        require(case.get("expected_route") in (None, suite["skill_id"]), f"{path}: invalid expected_route")
        unique_strings(case.get("must_include"), "must_include", allow_empty=False)
        unique_strings(case.get("must_avoid"), "must_avoid", allow_empty=False)
    return suite, set(cases)


def validate_report(root, record, entrypoint, case_ids):
    report = read_json(relative_file(root, record["evidence"]))
    require(report.get("skill_id") == record["id"] and report.get("skill_version") == record["version"], "report: skill or version mismatch")
    require(report.get("package_sha256") == package_fingerprint(entrypoint.parent), "report: package fingerprint mismatch")
    cases_path = relative_file(root, record["evaluation"])
    require(report.get("cases_sha256") == hashlib.sha256(cases_path.read_bytes()).hexdigest(), "report: cases fingerprint mismatch")
    check_date(report.get("run_date"), "report run_date")
    for field in ("host", "model", "reviewer"):
        require(nonempty(report.get(field)), f"report: missing {field}")
    require(report.get("comparison") == "baseline-and-skill", "report: missing baseline comparison")
    results = report.get("results")
    require(isinstance(results, list), "report: results must be an array")
    observed = set()
    for result in results:
        require(isinstance(result, dict), "report: result must be an object")
        case_id = result.get("case_id")
        require(valid_id(case_id) and case_id not in observed, "report: invalid or duplicate case_id")
        observed.add(case_id)
        for field in ("baseline_output", "skill_output", "rationale"):
            require(nonempty(result.get(field)), f"report: missing {field}")
        require(type(result.get("passed")) is bool, "report: passed must be boolean")
        if record["status"] == "verified":
            require(result["passed"], "verified report: failing case")
    require(observed == case_ids, "report: case coverage mismatch")


def validate_skill(root, record, categories, forms, upstream_ids):
    require(set(record) == SKILL_FIELDS, f"{record['id']}: invalid record fields")
    require(isinstance(record["category"], str) and record["category"] in categories, f"{record['id']}: invalid category")
    require(isinstance(record["form"], str) and record["form"] in forms, f"{record['id']}: invalid form")
    require(isinstance(record["status"], str) and record["status"] in STATUSES, f"{record['id']}: invalid status")
    require(nonempty(record["version"]) and VERSION_PATTERN.fullmatch(record["version"]), "skill: invalid version")
    unique_strings(record["tags"], "tags")
    require(unique_strings(record["upstream_ids"], "upstream_ids") <= upstream_ids, "skill: unknown upstream")
    expected = f"skills/{record['category']}/{record['id']}/SKILL.md"
    require(record["path"] == expected, f"skill: path must be {expected}")
    entrypoint = relative_file(root, record["path"])
    validate_entrypoint(entrypoint, record["id"])
    case_ids = set()
    if record["evaluation"] is not None:
        suite, case_ids = validate_cases(relative_file(root, record["evaluation"]))
        require(suite["skill_id"] == record["id"] and suite["stage"] == "active", "skill: evaluation must be active and match id")
    if record["status"] == "verified":
        require(record["evaluation"] is not None and record["evidence"] is not None, "verified skill requires evaluation and evidence")
    if record["evidence"] is not None:
        require(case_ids, "report requires evaluation cases")
        validate_report(root, record, entrypoint, case_ids)


def validate_collection(root):
    root = Path(root).resolve()
    errors = []

    def capture(label, action):
        try:
            return action()
        except (ValueError, OSError, UnicodeError) as error:
            errors.append(f"{label}: {error}")
            return None

    collection = capture("collection", lambda: read_json(root / "catalog/collection.json"))
    sources = capture("upstreams", lambda: read_json(root / "catalog/upstreams.json"))
    if collection is None or sources is None:
        return errors
    categories = capture("categories", lambda: indexed_records(collection.get("categories"), "categories"))
    skills = capture("skills", lambda: indexed_records(collection.get("skills"), "skills"))
    upstreams = capture("upstreams", lambda: indexed_records(sources.get("upstreams"), "upstreams"))
    forms = capture("forms", lambda: unique_strings(collection.get("forms"), "forms", allow_empty=False))
    if any(item is None for item in (categories, skills, upstreams, forms)):
        return errors
    capture("forms", lambda: require(forms <= FORMS, "unknown capability form"))
    capture("categories", lambda: require(bool(categories), "must not be empty"))
    for category in categories.values():
        capture(category["id"], lambda c=category: require(nonempty(c.get("title")) and nonempty(c.get("description")), "category needs title and description"))
    for upstream in upstreams.values():
        capture(upstream["id"], lambda u=upstream: validate_upstream(u))
    for skill in skills.values():
        capture(skill["id"], lambda s=skill: validate_skill(root, s, set(categories), forms, set(upstreams)))
    registered = {record.get("path") for record in skills.values() if isinstance(record.get("path"), str)}
    for path in (root / "skills").rglob("SKILL.md"):
        relative = path.relative_to(root).as_posix()
        if relative not in registered:
            errors.append(f"unregistered skill: {relative}")
    for path in (root / "evaluations/cases").rglob("*.json"):
        capture(str(path.relative_to(root)), lambda p=path: validate_cases(p))
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    fingerprints = parser.add_mutually_exclusive_group()
    fingerprints.add_argument("--fingerprint", help="Print a package fingerprint relative to root")
    fingerprints.add_argument("--cases-fingerprint", help="Print a case-file fingerprint relative to root")
    args = parser.parse_args()
    if args.cases_fingerprint:
        try:
            case_path = relative_file(args.root, args.cases_fingerprint)
            validate_cases(case_path)
            print(hashlib.sha256(case_path.read_bytes()).hexdigest())
        except (ValueError, OSError) as error:
            print(f"[FAIL] {error}", file=sys.stderr)
            return 1
        return 0
    if args.fingerprint:
        try:
            entrypoint = relative_file(args.root, args.fingerprint.rstrip("/") + "/SKILL.md")
            print(package_fingerprint(entrypoint.parent))
        except (ValueError, OSError) as error:
            print(f"[FAIL] {error}", file=sys.stderr)
            return 1
        return 0
    errors = validate_collection(args.root)
    for error in errors:
        print(f"[FAIL] {error}", file=sys.stderr)
    if not errors:
        print("[PASS] Collection structure valid. Behavioral evaluation is separate.")
    return int(bool(errors))


if __name__ == "__main__":
    sys.exit(main())
