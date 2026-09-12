"""Prepare a frozen Promptfoo workspace for native Codex skill comparison."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import time
import uuid


ROOT = Path(__file__).resolve().parents[2]
PROMPTFOO_VERSION = "0.123.0"
SCHEMA_VERSION = 1
ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]*$")
REASONING_LEVELS = {"minimal", "low", "medium", "high", "xhigh", "max"}
INSTALL_MODES = {"project", "home", "both"}
INVOCATION_MODES = {"implicit", "explicit"}
COMPARISON_KINDS = {"quality", "discovery"}
SANDBOX_MODES = {"read-only", "workspace-write"}
DIRECTORY_REPLACE_RETRY_DELAYS = (0.05, 0.1, 0.2, 0.4, 0.8)


def write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def replace_directory(staging: Path, output_dir: Path) -> None:
    """Publish a prepared directory despite short-lived Windows file locks."""
    for delay in (*DIRECTORY_REPLACE_RETRY_DELAYS, None):
        try:
            os.replace(staging, output_dir)
            return
        except PermissionError:
            if delay is None or output_dir.exists():
                raise
            time.sleep(delay)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def is_link_or_junction(path: Path) -> bool:
    if path.is_symlink():
        return True
    is_junction = getattr(path, "is_junction", None)
    return bool(is_junction and is_junction())


def package_files(folder: Path) -> list[Path]:
    if not folder.is_dir() or not (folder / "SKILL.md").is_file():
        raise ValueError(f"skill source must be a directory containing SKILL.md: {folder}")
    files: list[Path] = []
    for current, directories, filenames in os.walk(folder, followlinks=False):
        current_path = Path(current)
        if is_link_or_junction(current_path):
            raise ValueError(f"skill package links are unsupported: {current_path}")
        for name in sorted(directories):
            child = current_path / name
            if is_link_or_junction(child):
                raise ValueError(f"skill package links are unsupported: {child}")
        for name in sorted(filenames):
            child = current_path / name
            if is_link_or_junction(child):
                raise ValueError(f"skill package links are unsupported: {child}")
            files.append(child)
    return sorted(files, key=lambda item: item.relative_to(folder).as_posix())


def package_sha256(folder: Path) -> str:
    digest = hashlib.sha256()
    for path in package_files(folder):
        for data in (
            path.relative_to(folder).as_posix().encode("utf-8"),
            path.read_bytes(),
        ):
            digest.update(len(data).to_bytes(8, "big"))
            digest.update(data)
    return digest.hexdigest()


def package_manifest(folder: Path) -> list[dict[str, object]]:
    return [
        {
            "path": path.relative_to(folder).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        }
        for path in package_files(folder)
    ]


def resolve_inside(repo_root: Path, base: Path, raw_path: str, label: str) -> Path:
    candidate = Path(raw_path)
    resolved = (candidate if candidate.is_absolute() else base / candidate).resolve()
    try:
        resolved.relative_to(repo_root)
    except ValueError as error:
        raise ValueError(f"{label} must stay inside the repository: {raw_path}") from error
    return resolved


def validate_spec(spec: dict[str, object]) -> None:
    if spec.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"schema_version must be {SCHEMA_VERSION}")
    comparison_id = spec.get("id")
    if not isinstance(comparison_id, str) or not ID_PATTERN.fullmatch(comparison_id):
        raise ValueError("comparison id must use lowercase letters, digits, and hyphens")
    if spec.get("comparison_kind", "quality") not in COMPARISON_KINDS:
        raise ValueError("comparison_kind must be quality or discovery")
    if not isinstance(spec.get("model"), str) or not spec["model"].strip():
        raise ValueError("model must be a non-empty string")
    if spec.get("reasoning_effort") not in REASONING_LEVELS:
        raise ValueError("reasoning_effort is unsupported")
    repetitions = spec.get("repetitions")
    if not isinstance(repetitions, int) or isinstance(repetitions, bool) or not 1 <= repetitions <= 10:
        raise ValueError("repetitions must be an integer from 1 to 10")
    if not isinstance(spec.get("common_prompt"), str):
        raise ValueError("common_prompt must be a string")
    if spec.get("sandbox_mode", "read-only") not in SANDBOX_MODES:
        raise ValueError("sandbox_mode must be read-only or workspace-write")
    if not isinstance(spec.get("cases"), str) or not spec["cases"]:
        raise ValueError("cases must name a JSON file")
    arms = spec.get("arms")
    if not isinstance(arms, list) or len(arms) < 2:
        raise ValueError("at least two arms are required")
    arm_ids = [arm.get("id") if isinstance(arm, dict) else None for arm in arms]
    if any(not isinstance(arm_id, str) or not ID_PATTERN.fullmatch(arm_id) for arm_id in arm_ids):
        raise ValueError("arm ids must use lowercase letters, digits, and hyphens")
    if len(set(arm_ids)) != len(arm_ids):
        raise ValueError("arm ids must be unique")
    if not any(isinstance(arm, dict) and arm.get("skill") is None for arm in arms):
        raise ValueError("one arm must be a no-skill baseline")
    if not any(isinstance(arm, dict) and isinstance(arm.get("skill"), dict) for arm in arms):
        raise ValueError("one arm must contain a skill")
    for arm in arms:
        skill = arm.get("skill")
        if skill is None:
            continue
        if not isinstance(skill, dict):
            raise ValueError(f"arm {arm['id']} skill must be an object or null")
        if skill.get("install_mode", "project") not in INSTALL_MODES:
            raise ValueError(f"arm {arm['id']} has an invalid install_mode")
        if skill.get("invocation", "implicit") not in INVOCATION_MODES:
            raise ValueError(f"arm {arm['id']} has an invalid invocation mode")


def load_cases(path: Path, selected_case_ids: set[str] | None) -> list[dict[str, object]]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, list) or not value:
        raise ValueError("cases file must contain a non-empty list")
    case_ids: list[str] = []
    cases: list[dict[str, object]] = []
    for case in value:
        if not isinstance(case, dict):
            raise ValueError("each case must be an object")
        case_id = case.get("id")
        if not isinstance(case_id, str) or not case_id:
            raise ValueError("each case must have a non-empty id")
        if not isinstance(case.get("prompt"), str) or not case["prompt"]:
            raise ValueError(f"case {case_id} must have a non-empty prompt")
        criteria = case.get("hard_criteria")
        if not isinstance(criteria, list) or not criteria or not all(
            isinstance(item, str) and item for item in criteria
        ):
            raise ValueError(f"case {case_id} must have non-empty hard_criteria")
        case_ids.append(case_id)
        if selected_case_ids is None or case_id in selected_case_ids:
            cases.append(case)
    if len(set(case_ids)) != len(case_ids):
        raise ValueError("case ids must be unique")
    if selected_case_ids is not None:
        missing = sorted(selected_case_ids - set(case_ids))
        if missing:
            raise ValueError("unknown case ids: " + ", ".join(missing))
    if not cases:
        raise ValueError("case selection is empty")
    return cases


def copy_package(source: Path, destination: Path) -> None:
    for path in package_files(source):
        relative = path.relative_to(source)
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)


def build_provider(
    arm_id: str, model: str, reasoning_effort: str, sandbox_mode: str
) -> dict[str, object]:
    isolated_home = f"{{{{ env.EVAL_HOME_BASE }}}}/{arm_id}"
    return {
        "id": "openai:codex-sdk",
        "label": arm_id,
        "config": {
            "model": model,
            "model_reasoning_effort": reasoning_effort,
            "working_dir": f"./fixtures/{arm_id}",
            "skip_git_repo_check": False,
            "sandbox_mode": sandbox_mode,
            "approval_policy": "never",
            "network_access_enabled": False,
            "web_search_enabled": False,
            "web_search_mode": "disabled",
            "inherit_process_env": False,
            "enable_streaming": True,
            "cli_config": {
                "features": {
                    "apps": False,
                    "plugins": False,
                    "multi_agent": False,
                },
                "apps": {"_default": {"enabled": False}},
            },
            "cli_env": {
                "CODEX_HOME": f"{isolated_home}/.codex",
                "HOME": isolated_home,
                "USERPROFILE": isolated_home,
            },
        },
    }


def prepare_comparison(
    repo_root: Path,
    spec_path: Path,
    output_dir: Path,
    selected_case_ids: set[str] | None = None,
) -> Path:
    repo_root = repo_root.resolve()
    spec_path = spec_path.resolve()
    output_dir = output_dir.resolve()
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    if not isinstance(spec, dict):
        raise ValueError("comparison spec must be an object")
    validate_spec(spec)
    cases_path = resolve_inside(repo_root, spec_path.parent, spec["cases"], "cases")
    cases = load_cases(cases_path, selected_case_ids)
    if output_dir.exists():
        raise FileExistsError(f"refusing to overwrite evaluation run: {output_dir}")

    output_dir.parent.mkdir(parents=True, exist_ok=True)
    staging = output_dir.parent / f".{output_dir.name}.tmp-{uuid.uuid4().hex[:8]}"
    prepared = staging / "prepared"
    arm_evidence: list[dict[str, object]] = []
    try:
        prepared.mkdir(parents=True)
        providers: list[dict[str, object]] = []
        for arm in spec["arms"]:
            arm_id = arm["id"]
            fixture = prepared / "fixtures" / arm_id
            fixture.mkdir(parents=True)
            skill = arm.get("skill")
            evidence: dict[str, object] = {
                "id": arm_id,
                "skill": None,
                "install_mode": "none",
                "invocation": "none",
            }
            if skill is not None:
                if not isinstance(skill.get("id"), str) or not ID_PATTERN.fullmatch(skill["id"]):
                    raise ValueError(f"arm {arm_id} has an invalid skill id")
                if not isinstance(skill.get("source"), str):
                    raise ValueError(f"arm {arm_id} must name a skill source")
                source = resolve_inside(
                    repo_root, spec_path.parent, skill["source"], f"arm {arm_id} skill source"
                )
                package_files(source)
                install_mode = skill.get("install_mode", "project")
                snapshot = prepared / "skills" / arm_id / skill["id"]
                copy_package(source, snapshot)
                if install_mode in {"project", "both"}:
                    project_destination = (
                        fixture / ".agents" / "skills" / skill["id"]
                    )
                    copy_package(source, project_destination)
                evidence["skill"] = skill["id"]
                evidence["install_mode"] = install_mode
                evidence["invocation"] = skill.get("invocation", "implicit")
                evidence["skill_source"] = source.relative_to(repo_root).as_posix()
                evidence["skill_package_sha256"] = package_sha256(source)
                evidence["files"] = package_manifest(source)
            arm_evidence.append(evidence)
            providers.append(
                build_provider(
                    arm_id,
                    spec["model"],
                    spec["reasoning_effort"],
                    spec.get("sandbox_mode", "read-only"),
                )
            )

        common_prompt = spec["common_prompt"].strip()
        implicit_skill_ids = sorted(
            {
                arm["skill"]["id"]
                for arm in spec["arms"]
                if arm.get("skill") is not None
                and arm["skill"].get("invocation", "implicit") == "implicit"
            }
        )
        promptfoo_tests = []
        for case in cases:
            base_prompt = case["prompt"].strip()
            if common_prompt:
                base_prompt = common_prompt + "\n\n" + base_prompt
            for arm in spec["arms"]:
                skill = arm.get("skill")
                invocation = (
                    skill.get("invocation", "implicit") if skill is not None else "none"
                )
                rendered_prompt = base_prompt
                if invocation == "explicit":
                    rendered_prompt = (
                        f"请显式运行 ${skill['id']} 后完成下方任务。"
                        "只返回任务要求的结果，不说明 Skill 加载过程。\n\n"
                        + base_prompt
                    )
                promptfoo_test = {
                    "description": (
                        f"{case['id']} [{arm['id']}]: {case.get('purpose', '')}"
                    ).rstrip(),
                    "providers": [arm["id"]],
                    "vars": {"prompt": rendered_prompt},
                    "metadata": {
                        "case_id": case["id"],
                        "arm_id": arm["id"],
                        "invocation": invocation,
                        "purpose": case.get("purpose"),
                        "hard_criteria": case["hard_criteria"],
                    },
                }
                assertions = []
                if isinstance(case.get("expected_output"), str):
                    assertions.append(
                        {"type": "equals", "value": case["expected_output"]}
                    )
                if invocation == "implicit":
                    assertions.append({"type": "skill-used", "value": skill["id"]})
                elif skill is None:
                    assertions.extend(
                        {"type": "not-skill-used", "value": skill_id}
                        for skill_id in implicit_skill_ids
                    )
                if assertions:
                    promptfoo_test["assert"] = assertions
                promptfoo_tests.append(promptfoo_test)

        config = {
            "$schema": "https://promptfoo.dev/config-schema.json",
            "description": f"Native Codex skill comparison: {spec['id']}",
            "tags": {"comparison": spec["id"], "runtime": "codex-sdk"},
            "prompts": ["{{prompt}}"],
            "providers": providers,
            "tests": "file://tests.json",
            "sharing": False,
        }
        config_path = prepared / "promptfooconfig.json"
        tests_path = prepared / "tests.json"
        write_json(config_path, config)
        write_json(tests_path, promptfoo_tests)
        frozen = {
            "schema_version": SCHEMA_VERSION,
            "adapter": "promptfoo-native-codex-skill-comparison",
            "promptfoo_version": PROMPTFOO_VERSION,
            "prepared_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "comparison_id": spec["id"],
            "comparison_kind": spec.get("comparison_kind", "quality"),
            "spec_path": spec_path.relative_to(repo_root).as_posix(),
            "spec_sha256": sha256_file(spec_path),
            "cases_path": cases_path.relative_to(repo_root).as_posix(),
            "cases_sha256": sha256_file(cases_path),
            "selected_case_ids": [case["id"] for case in cases],
            "model": spec["model"],
            "reasoning_effort": spec["reasoning_effort"],
            "repetitions": spec["repetitions"],
            "arms": arm_evidence,
            "prepared_config_sha256": sha256_file(config_path),
            "prepared_tests_sha256": sha256_file(tests_path),
            "constraints": {
                "native_skill_discovery": True,
                "sandbox_mode": spec.get("sandbox_mode", "read-only"),
                "network_access": False,
                "web_search": "disabled",
                "isolated_git_root_per_arm": True,
                "isolated_user_home_per_arm": True,
                "host_apps_plugins": False,
                "evaluation_rubric_visible_to_agent": False,
                "implicit_skill_trace_assertions": bool(implicit_skill_ids),
            },
        }
        write_json(staging / "frozen.json", frozen)
        replace_directory(staging, output_dir)
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    print(f"[DONE] prepared Promptfoo comparison at {output_dir}")
    return output_dir


def default_output_dir(comparison_id: str) -> Path:
    timestamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return ROOT / "evaluations" / "runs" / f"{comparison_id}-promptfoo-{timestamp}-{uuid.uuid4().hex[:6]}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--case", action="append", dest="case_ids")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    spec_path = args.spec.resolve()
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    output = args.output or default_output_dir(spec["id"])
    prepare_comparison(ROOT, spec_path, output, set(args.case_ids) if args.case_ids else None)


if __name__ == "__main__":
    main()
