"""List and export registered skill packages as deterministic local ZIP files."""

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import sys
import tempfile
import zipfile

from validate_collection import package_fingerprint, validate_collection


EXPORTABLE_STATUSES = {"experimental", "verified"}
ALLOWED_TOP_LEVEL_DIRECTORIES = {"agents", "assets", "references", "scripts"}
SENSITIVE_NAMES = {".env", "credentials", "credentials.json", "id_rsa", "id_ed25519", "secrets", "secrets.json"}
FIXED_ZIP_TIME = (1980, 1, 1, 0, 0, 0)


class ExportError(ValueError):
    """Raised when an export cannot be completed safely."""


class ExportBatchError(ExportError):
    """Raised after a runtime export failure, retaining already published outputs."""

    def __init__(self, message, outputs, failed_output):
        super().__init__(message)
        self.outputs = list(outputs)
        self.failed_output = failed_output


def _load_records(repo_root):
    path = repo_root / "catalog/collection.json"
    try:
        collection = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ExportError(f"catalog read failed: {error}") from error
    records = collection.get("skills")
    if not isinstance(records, list):
        raise ExportError("catalog skills must be an array")
    indexed = {}
    for record in records:
        identifier = record.get("id") if isinstance(record, dict) else None
        if not identifier or identifier in indexed:
            raise ExportError("catalog has an invalid or duplicate skill id")
        indexed[identifier] = record
    return indexed


def list_exportable(repo_root):
    records = _load_records(Path(repo_root).resolve())
    return sorted(
        (record["id"], record["version"], record["status"])
        for record in records.values()
        if record.get("status") in EXPORTABLE_STATUSES
    )


def _is_link_or_reparse(path):
    info = path.lstat()
    attributes = getattr(info, "st_file_attributes", 0)
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    return path.is_symlink() or bool(attributes & reparse_flag)


def _reject_name(path):
    lowered = path.name.casefold()
    if path.name.startswith(".") or lowered in SENSITIVE_NAMES or lowered == "__pycache__":
        raise ExportError(f"unexpected or sensitive package member: {path.name}")


def _assert_plain_path(root, candidate, label):
    root = Path(os.path.abspath(root))
    candidate = Path(os.path.abspath(candidate))
    try:
        relative = candidate.relative_to(root)
    except ValueError as error:
        raise ExportError(f"{label} path escapes the repository: {candidate}") from error
    current = root
    if _is_link_or_reparse(current):
        raise ExportError(f"{label} root uses a link or reparse point: {current}")
    for part in relative.parts:
        current = current / part
        if current.exists() or current.is_symlink():
            if _is_link_or_reparse(current):
                raise ExportError(f"{label} path uses a link or reparse point: {current}")
    return candidate


def _resolve_package(repo_root, record):
    raw_path = record.get("path")
    if not isinstance(raw_path, str):
        raise ExportError("skill path must be a relative POSIX path")
    pure = PurePosixPath(raw_path)
    expected = PurePosixPath("skills") / record["category"] / record["id"] / "SKILL.md"
    if pure.is_absolute() or ".." in pure.parts or chr(92) in raw_path or ":" in raw_path or pure != expected:
        raise ExportError(f"skill path is invalid or escapes the repository: {raw_path}")
    entrypoint = repo_root.joinpath(*pure.parts)
    package = entrypoint.parent
    _assert_plain_path(repo_root, package, "source package")
    try:
        resolved = package.resolve(strict=True)
    except OSError as error:
        raise ExportError(f"package path is invalid: {package}") from error
    skills_root = (repo_root / "skills").resolve(strict=True)
    if not resolved.is_relative_to(skills_root):
        raise ExportError(f"package path escapes or uses a link/reparse point: {package}")
    if not entrypoint.is_file():
        raise ExportError(f"missing SKILL.md: {entrypoint}")
    return package


def _collect_files(package):
    files = []
    for child in sorted(package.iterdir(), key=lambda item: item.name):
        _reject_name(child)
        if _is_link_or_reparse(child):
            raise ExportError(f"link or reparse point is unsupported: {child}")
        if child.is_file():
            if child.name != "SKILL.md":
                raise ExportError(f"unexpected top-level package file: {child.name}")
            files.append(child)
            continue
        if not child.is_dir() or child.name not in ALLOWED_TOP_LEVEL_DIRECTORIES:
            raise ExportError(f"unexpected package member: {child.name}")
        for root, directories, names in os.walk(child, followlinks=False):
            root_path = Path(root)
            for name in sorted(directories):
                directory = root_path / name
                _reject_name(directory)
                if _is_link_or_reparse(directory):
                    raise ExportError(f"link or reparse point is unsupported: {directory}")
            for name in sorted(names):
                path = root_path / name
                _reject_name(path)
                if _is_link_or_reparse(path) or not path.is_file():
                    raise ExportError(f"link, reparse point, or non-file is unsupported: {path}")
                files.append(path)
    if package / "SKILL.md" not in files:
        raise ExportError(f"missing SKILL.md in package: {package}")
    return sorted(files, key=lambda path: path.relative_to(package).as_posix())


def _zip_info(name):
    info = zipfile.ZipInfo(name, FIXED_ZIP_TIME)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.create_system = 3
    info.external_attr = 0o100644 << 16
    return info


def _snapshot_files(package, files):
    return tuple((path.relative_to(package).as_posix(), path.read_bytes()) for path in files)


def _snapshot_fingerprint(snapshot):
    digest = hashlib.sha256()
    for relative, content in snapshot:
        for data in (relative.encode("utf-8"), content):
            digest.update(len(data).to_bytes(8, "big"))
            digest.update(data)
    return digest.hexdigest()


def _build_manifest(record, package, snapshot):
    file_hashes = {
        relative: hashlib.sha256(content).hexdigest()
        for relative, content in snapshot
    }
    return {
        "schema_version": 1,
        "skill_id": record["id"],
        "version": record["version"],
        "category": record["category"],
        "status": record["status"],
        "source_entrypoint": record["path"],
        "package_sha256": _snapshot_fingerprint(snapshot),
        "files": file_hashes,
        "upstream_ids": record.get("upstream_ids", []),
        "license": "unspecified",
    }


def _write_archive(temp_path, record, package, snapshot):
    manifest = _build_manifest(record, package, snapshot)
    manifest_bytes = (json.dumps(manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    with zipfile.ZipFile(temp_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        archive.writestr(_zip_info("bundle-manifest.json"), manifest_bytes)
        for relative, content in snapshot:
            member = f"{record['id']}/{relative}"
            archive.writestr(_zip_info(member), content)


def export_selected(repo_root, skill_ids, output_dir):
    repo_root = Path(os.path.abspath(repo_root))
    output_dir = _assert_plain_path(repo_root, output_dir, "output")
    records = _load_records(repo_root)
    if not skill_ids:
        raise ExportError("no skills selected")
    if len(skill_ids) != len(set(skill_ids)):
        raise ExportError("duplicate skill ids are not allowed")
    selected = []
    for identifier in skill_ids:
        record = records.get(identifier)
        if record is None:
            raise ExportError(f"unknown skill id: {identifier}")
        if record.get("status") not in EXPORTABLE_STATUSES:
            raise ExportError(f"skill is not exportable in status {record.get('status')}: {identifier}")
        package = _resolve_package(repo_root, record)
        files = _collect_files(package)
        snapshot = _snapshot_files(package, files)
        destination = output_dir / f"{identifier}-{record['version']}.zip"
        if destination.exists():
            raise ExportError(f"output already exists: {destination}")
        selected.append((record, package, snapshot, destination))

    output_dir.mkdir(parents=True, exist_ok=True)
    _assert_plain_path(repo_root, output_dir, "output")
    outputs = []
    for record, package, snapshot, destination in selected:
        handle, raw_temp = tempfile.mkstemp(prefix=".skill-export-", suffix=".tmp", dir=output_dir)
        os.close(handle)
        temp_path = Path(raw_temp)
        try:
            _write_archive(temp_path, record, package, snapshot)
            try:
                os.link(temp_path, destination)
            except FileExistsError as error:
                raise ExportError(f"output already exists: {destination}") from error
            except OSError as error:
                raise ExportError(f"atomic archive publish failed for {destination}: {error}") from error
            outputs.append(destination)
        except ExportBatchError:
            raise
        except Exception as error:
            raise ExportBatchError(
                f"export failed for {destination}: {error}",
                outputs,
                destination,
            ) from error
        finally:
            temp_path.unlink(missing_ok=True)
    return outputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--list", action="store_true", help="List exportable registered skills without writing files.")
    selection.add_argument("--skill", action="append", help="Export one registered experimental or verified skill.")
    selection.add_argument("--all", action="store_true", help="Export every registered experimental or verified skill.")
    args = parser.parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    try:
        validation_errors = validate_collection(repo_root)
        if validation_errors:
            raise ExportError("repository validation failed: " + "; ".join(validation_errors))
        if args.list:
            for identifier, version, status in list_exportable(repo_root):
                print(f"{identifier}\t{version}\t{status}")
            return 0
        identifiers = [item[0] for item in list_exportable(repo_root)] if args.all else args.skill
        for output in export_selected(repo_root, identifiers, repo_root / "dist"):
            print(output.relative_to(repo_root).as_posix())
        return 0
    except ExportBatchError as error:
        for output in error.outputs:
            print(output.relative_to(repo_root).as_posix())
        print(f"[FAIL] {error}", file=sys.stderr)
        return 1
    except ExportError as error:
        print(f"[FAIL] {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
