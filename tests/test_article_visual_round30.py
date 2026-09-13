"""Integrity checks for the Round 30 discriminative visual-planning report."""

import copy
import hashlib
import json
from pathlib import Path, PureWindowsPath
import runpy
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
COMPARISON = ROOT / "evaluations/comparisons/article-visual-plan-discriminative-23"
REPORT_PATH = ROOT / "evaluations/reports/article-visual-plan-discriminative-round-30-diagnostic.json"
RUN = ROOT / "evaluations/runs/article-visual-plan-discriminative-23-formal-20260913-v1"
PREFLIGHT_RUN = ROOT / "evaluations/runs/article-visual-plan-discriminative-23-preflight-20260913-v1"
ACTIVE = ROOT / "evaluations/cases/article-visual-plan.json"
SKILL = ROOT / "skills/creation/article-visual-plan"
COMMIT = "6b7a2e417500561a5ecdd0b168332f4142584617"
UPSTREAM = ROOT / "evaluations/fixtures/upstreams/baoyu-skills" / COMMIT
FREEZE_COMMIT = "b5b45539fe9b7adddf2ca2199ab6c6011cf8461d"
EXPECTED_PROJECTION = "e300418ed60d2a3d39baed4679dfeeef26dbcc3bdcbbd027489ae99e6202f152"
VALIDATOR = runpy.run_path(str(ROOT / "scripts/validate_collection.py"))
ORDER = {"baseline": 0, "ours": 1, "upstream": 2}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def object_sha(value: object) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


class ArticleVisualRound30Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
        cls.cases = json.loads((COMPARISON / "cases.json").read_text(encoding="utf-8"))
        cls.protocol = json.loads((COMPARISON / "promptfoo.json").read_text(encoding="utf-8"))

    def _recompute_core_failures(self, report):
        case_by = {case["id"]: case for case in self.cases}
        failures = {
            case_id: {arm: 0 for arm in ORDER} for case_id in case_by
        }
        for item in report["experiment"]["items"]:
            case = case_by[item["case_id"]]
            for candidate in item["candidates"]:
                criteria = candidate["criteria_pass"]
                core_failure = any(
                    not criteria[index] for index in case["core_criteria"]
                )
                failures[case["id"]][candidate["arm_id"]] += core_failure
        return failures

    def _assert_gate_semantics(self, report):
        gate = self.protocol["decision_gate"]
        analysis = report["analysis"]
        self.assertEqual(analysis["decision_gate"], gate)
        self.assertEqual(gate["scope"], "ours-versus-baseline")
        self.assertEqual(gate["upstream_role"], "context-only")
        self.assertEqual(gate["effect"], "open-minimal-candidate-design-only")

        failures = self._recompute_core_failures(report)
        self.assertEqual(analysis["case_core_failures"], failures)
        valid_outputs = sum(
            len(item["candidates"]) for item in report["experiment"]["items"]
        )
        self.assertEqual(analysis["valid_output_count"], valid_outputs)
        self.assertEqual(valid_outputs, gate["required_valid_outputs"])
        self.assertTrue(report["experiment"]["infrastructure_valid"])

        case_ids_by_mechanism = {}
        for case in self.cases:
            case_ids_by_mechanism.setdefault(case["mechanism"], []).append(
                case["id"]
            )
        expected_mechanisms = []
        for mechanism, case_ids in case_ids_by_mechanism.items():
            self.assertEqual(
                len(case_ids), gate["minimum_cases_in_same_mechanism"]
            )
            ours_met = all(
                failures[case_id]["ours"]
                >= gate["ours_min_core_failures_per_case"]
                for case_id in case_ids
            )
            baseline_met = all(
                failures[case_id]["baseline"]
                <= gate["baseline_max_core_failures_per_case"]
                for case_id in case_ids
            )
            expected_mechanisms.append(
                {
                    "mechanism": mechanism,
                    "case_ids": case_ids,
                    "core_failures": {
                        case_id: failures[case_id] for case_id in case_ids
                    },
                    "ours_threshold_met": ours_met,
                    "baseline_threshold_met": baseline_met,
                    "triggered": ours_met and baseline_met,
                }
            )
        self.assertEqual(analysis["mechanisms"], expected_mechanisms)
        self.assertEqual(
            report["decision"]["candidate_design_open"],
            any(item["triggered"] for item in expected_mechanisms),
        )

    def _assert_frozen_package(self, frozen_arm, package, report_arm):
        self.assertEqual(frozen_arm["skill"], report_arm["skill"])
        self.assertEqual(
            frozen_arm["skill_source"], report_arm["package_evidence_path"]
        )
        self.assertEqual(
            frozen_arm["install_mode"], report_arm["runtime"]["install_mode"]
        )
        self.assertEqual(
            frozen_arm["invocation"], report_arm["runtime"]["invocation"]
        )
        files = []
        for path in sorted(
            (item for item in package.rglob("*") if item.is_file()),
            key=lambda item: item.relative_to(package).as_posix(),
        ):
            files.append(
                {
                    "path": path.relative_to(package).as_posix(),
                    "bytes": path.stat().st_size,
                    "sha256": sha(path),
                }
            )
        self.assertEqual(frozen_arm["files"], files)
        self.assertEqual(
            frozen_arm["skill_package_sha256"],
            VALIDATOR["package_fingerprint"](package),
        )
        self.assertEqual(
            frozen_arm["skill_package_sha256"],
            report_arm["skill_package_sha256"],
        )

    def _assert_raw_run_semantics(
        self,
        report,
        frozen,
        run_meta,
        summary,
        preflight_summary,
        prepared_root=None,
    ):
        if prepared_root is None:
            prepared_root = RUN / "prepared"
        experiment = report["experiment"]
        self.assertEqual(frozen["comparison_id"], self.protocol["id"])
        self.assertEqual(frozen["comparison_kind"], "quality")
        self.assertEqual(frozen["spec_sha256"], sha(COMPARISON / "promptfoo.json"))
        self.assertEqual(frozen["cases_sha256"], sha(COMPARISON / "cases.json"))
        self.assertEqual(
            frozen["selected_case_ids"], [case["id"] for case in self.cases]
        )
        self.assertEqual(frozen["model"], self.protocol["model"])
        self.assertEqual(
            frozen["reasoning_effort"], self.protocol["reasoning_effort"]
        )
        self.assertEqual(frozen["repetitions"], self.protocol["repetitions"])
        self.assertEqual(
            frozen["prepared_config_sha256"],
            experiment["prepared_hashes"]["config"],
        )
        self.assertEqual(
            frozen["prepared_tests_sha256"],
            experiment["prepared_hashes"]["tests"],
        )
        self.assertEqual(
            sha(prepared_root / "promptfooconfig.json"),
            frozen["prepared_config_sha256"],
        )
        self.assertEqual(
            sha(prepared_root / "tests.json"),
            frozen["prepared_tests_sha256"],
        )
        self.assertEqual(
            frozen["constraints"],
            {
                "native_skill_discovery": True,
                "sandbox_mode": self.protocol["sandbox_mode"],
                "network_access": False,
                "web_search": "disabled",
                "isolated_git_root_per_arm": True,
                "isolated_user_home_per_arm": True,
                "host_apps_plugins": False,
                "evaluation_rubric_visible_to_agent": False,
                "implicit_skill_trace_assertions": False,
            },
        )

        frozen_arms = {item["id"]: item for item in frozen["arms"]}
        report_arms = {item["arm_id"]: item for item in experiment["arms"]}
        self.assertEqual(
            frozen_arms["baseline"],
            {
                "id": "baseline",
                "skill": None,
                "install_mode": "none",
                "invocation": "none",
            },
        )
        self._assert_frozen_package(
            frozen_arms["ours"], SKILL, report_arms["ours"]
        )
        self._assert_frozen_package(
            frozen_arms["upstream"],
            UPSTREAM / "skills/baoyu-article-illustrator",
            report_arms["upstream"],
        )
        for package in (
            prepared_root / "skills/ours/article-visual-plan",
            prepared_root / "fixtures/ours/.agents/skills/article-visual-plan",
        ):
            self._assert_frozen_package(
                frozen_arms["ours"], package, report_arms["ours"]
            )
        for package in (
            prepared_root / "skills/upstream/baoyu-article-illustrator",
            prepared_root
            / "fixtures/upstream/.agents/skills/baoyu-article-illustrator",
        ):
            self._assert_frozen_package(
                frozen_arms["upstream"], package, report_arms["upstream"]
            )

        self.assertEqual(run_meta["comparison_id"], self.protocol["id"])
        self.assertEqual(run_meta["frozen_sha256"], sha(RUN / "frozen.json"))
        self.assertEqual(run_meta["repeat"], 3)
        self.assertEqual(len(run_meta["commands"]), 2)
        validate_command, eval_command = run_meta["commands"]
        self.assertEqual(validate_command[:3], eval_command[:3])
        self.assertEqual(
            validate_command[3:],
            ["validate", "config", "-c", "promptfooconfig.json"],
        )
        self.assertEqual(
            eval_command[3:],
            [
                "eval",
                "-c",
                "promptfooconfig.json",
                "--repeat",
                "3",
                "--no-cache",
                "-o",
                "results.json",
                "-o",
                "results.html",
            ],
        )
        self.assertEqual(
            sum(command.count("eval") for command in run_meta["commands"]), 1
        )
        self.assertEqual(run_meta["validation_exit_code"], 0)
        self.assertEqual(run_meta["exit_code"], 0)
        self.assertEqual(run_meta["status"], "completed")
        self.assertEqual(
            (
                run_meta["expected_rows"],
                run_meta["result_rows"],
                run_meta["passed_rows"],
                run_meta["failed_rows"],
            ),
            (54, 54, 54, 0),
        )
        self.assertEqual(
            run_meta["results_sha256"], experiment["artifact_hashes"]["results.json"]
        )

        self.assertEqual(summary["comparison_id"], self.protocol["id"])
        self.assertEqual(summary["comparison_kind"], "quality")
        self.assertTrue(summary["infrastructure_valid"])
        self.assertEqual(summary["planned_repetitions"], 3)
        self.assertEqual(summary["executed_repetitions"], 3)
        self.assertEqual(summary["results_sha256"], run_meta["results_sha256"])
        self.assertEqual({item["id"] for item in summary["arms"]}, set(ORDER))
        self.assertEqual(sum(item["rows"] for item in summary["arms"]), 54)
        for arm in summary["arms"]:
            self.assertEqual(arm["rows"], 18)
            self.assertEqual(arm["promptfoo_passed_rows"], 18)
            self.assertEqual(arm["provider_errors"], 0)
            self.assertEqual(arm["forbidden_tool_rows"], 0)

        preflight = experiment["preflight"]
        self.assertEqual(preflight["summary_sha256"], sha(PREFLIGHT_RUN / "summary.json"))
        self.assertEqual(preflight["outputs"], 3)
        self.assertTrue(preflight["infrastructure_valid"])
        self.assertFalse(preflight["scored"])
        self.assertEqual(preflight_summary["comparison_id"], self.protocol["id"])
        self.assertEqual(preflight_summary["comparison_kind"], "quality")
        self.assertTrue(preflight_summary["infrastructure_valid"])
        self.assertEqual(preflight_summary["executed_repetitions"], 1)
        self.assertEqual({item["id"] for item in preflight_summary["arms"]}, set(ORDER))
        self.assertEqual(sum(item["rows"] for item in preflight_summary["arms"]), 3)
        for arm in preflight_summary["arms"]:
            self.assertEqual(arm["rows"], 1)
            self.assertEqual(arm["promptfoo_passed_rows"], 1)
            self.assertEqual(arm["provider_errors"], 0)
            self.assertEqual(arm["forbidden_tool_rows"], 0)

    def test_sources_projection_and_freeze_commit_are_bound(self):
        report = self.report
        self.assertEqual(report["report_id"], "article-visual-plan-discriminative-round-30-diagnostic")
        experiment = report["experiment"]
        self.assertEqual(experiment["freeze_commit"], FREEZE_COMMIT)
        sources = {
            "promptfoo.json": COMPARISON / "promptfoo.json",
            "cases.json": COMPARISON / "cases.json",
            "active-cases.json": ACTIVE,
            "SKILL.md": SKILL / "SKILL.md",
            "upstream-provenance.json": UPSTREAM / "provenance.json",
        }
        for name, path in sources.items():
            self.assertEqual(experiment["source_hashes"][name], sha(path))
        for name, expected in experiment["review_hashes"].items():
            self.assertEqual(expected, sha(COMPARISON / name))
        projection = {key: report[key] for key in ("scope", "experiment", "analysis", "decision", "limitations")}
        self.assertEqual(object_sha(projection), report["evidence_projection_sha256"])
        self.assertEqual(report["evidence_projection_sha256"], EXPECTED_PROJECTION)

        if (ROOT / ".git").exists():
            subprocess.run(["git", "merge-base", "--is-ancestor", FREEZE_COMMIT, "HEAD"], cwd=ROOT, check=True)
            for name, path in sources.items():
                if name == "active-cases.json":
                    continue
                relative = path.relative_to(ROOT).as_posix()
                content = subprocess.run(["git", "show", f"{FREEZE_COMMIT}:{relative}"], cwd=ROOT, check=True, capture_output=True).stdout
                self.assertEqual(hashlib.sha256(content).hexdigest(), experiment["source_hashes"][name])

    def test_scores_core_failures_gate_and_efficiency_recompute(self):
        case_by = {case["id"]: case for case in self.cases}
        aggregates = {arm: [0, 0, 0, 0] for arm in ORDER}
        failures = {case_id: {arm: 0 for arm in ORDER} for case_id in case_by}
        for item in self.report["experiment"]["items"]:
            case = case_by[item["case_id"]]
            for candidate in item["candidates"]:
                arm = candidate["arm_id"]
                criteria = candidate["criteria_pass"]
                self.assertEqual(candidate["output_sha256"], hashlib.sha256(candidate["output"].encode()).hexdigest())
                self.assertEqual(candidate["passed"], sum(criteria))
                core = any(not criteria[index] for index in case["core_criteria"])
                self.assertEqual(candidate["core_failure"], core)
                failures[case["id"]][arm] += core
                aggregates[arm][0] += 1
                aggregates[arm][1] += candidate["passed"] == 4
                aggregates[arm][2] += candidate["passed"]
                aggregates[arm][3] += candidate["preferred"]
        self.assertEqual(aggregates, {arm: [18, 16, 70, 0] for arm in ORDER})
        self.assertEqual(self.report["analysis"]["case_core_failures"], failures)
        expected_failures = {case_id: {arm: 0 for arm in ORDER} for case_id in case_by}
        expected_failures["unequal-cohort-observed-rates"]["ours"] = 1
        self.assertEqual(failures, expected_failures)
        self._assert_gate_semantics(self.report)

        runtime = {arm["arm_id"]: arm["runtime"] for arm in self.report["experiment"]["arms"]}
        def pct(left, right, field):
            a = runtime[left][field]["total"] if field == "tokens_total" else runtime[left][field]
            b = runtime[right][field]["total"] if field == "tokens_total" else runtime[right][field]
            return round((a / b - 1) * 100, 1)
        comparisons = (("ours_vs_baseline_percent", "ours", "baseline"), ("upstream_vs_baseline_percent", "upstream", "baseline"), ("ours_vs_upstream_percent", "ours", "upstream"))
        for name, left, right in comparisons:
            expected = {field: pct(left, right, field) for field in ("tokens_total", "cost_total", "latency_ms_median")}
            self.assertEqual(self.report["analysis"]["efficiency"][name], expected)

    def test_active_cases_and_skill_state_match_decision(self):
        active = json.loads(ACTIVE.read_text(encoding="utf-8"))
        by_id = {case["id"]: case for case in active["cases"]}
        self.assertEqual(len(by_id), 16)
        for case in self.cases:
            self.assertEqual(by_id[case["id"]]["prompt"], case["prompt"])
            self.assertEqual(by_id[case["id"]]["must_include"], case["hard_criteria"])
        catalog = json.loads((ROOT / "catalog/collection.json").read_text(encoding="utf-8"))
        entry = next(item for item in catalog["skills"] if item["id"] == "article-visual-plan")
        self.assertEqual((entry["version"], entry["status"], entry["evidence"]), ("0.1.0", "experimental", None))
        total = sum(len(json.loads((ROOT / item["evaluation"]).read_text(encoding="utf-8"))["cases"]) for item in catalog["skills"])
        self.assertEqual(total, 160)
        decision = self.report["decision"]
        self.assertEqual(decision["active_cases_sha256"], sha(ACTIVE))
        self.assertEqual(decision["skill_package_sha256"], VALIDATOR["package_fingerprint"](SKILL))
        self.assertFalse(any(decision[field] for field in ("skill_changed", "version_changed", "verification_status_changed")))

    def test_raw_run_semantically_reprojects_when_present(self):
        if not RUN.is_dir():
            self.skipTest("ignored Round 30 run is unavailable")
        self.assertTrue(PREFLIGHT_RUN.is_dir())
        experiment = self.report["experiment"]
        for name, expected in experiment["artifact_hashes"].items():
            self.assertEqual(sha(RUN / name), expected)
        frozen = json.loads((RUN / "frozen.json").read_text(encoding="utf-8"))
        run_meta = json.loads((RUN / "run-meta.json").read_text(encoding="utf-8"))
        summary = json.loads((RUN / "summary.json").read_text(encoding="utf-8"))
        preflight_summary = json.loads(
            (PREFLIGHT_RUN / "summary.json").read_text(encoding="utf-8")
        )
        self._assert_raw_run_semantics(
            self.report, frozen, run_meta, summary, preflight_summary
        )
        packet = json.loads((RUN / "blind-review.json").read_text(encoding="utf-8"))
        key = json.loads((RUN / "blind-review-key.json").read_text(encoding="utf-8"))
        completed = json.loads((RUN / "blind-review-completed-independent.json").read_text(encoding="utf-8"))
        scored = json.loads((RUN / "review-result-blind-review-completed-independent.json").read_text(encoding="utf-8"))
        for public in experiment["arms"]:
            arm = public["arm_id"]
            self.assertEqual(public["runtime"], next(item for item in summary["arms"] if item["id"] == arm))
            self.assertEqual(public["blind_review"], next(item for item in scored["arms"] if item["arm_id"] == arm))
        packet_by = {item["review_id"]: item for item in packet["items"]}; key_by = {item["review_id"]: item for item in key["items"]}; completed_by = {item["review_id"]: item for item in completed["reviews"]}; scored_by = {item["review_id"]: item for item in scored["items"]}; case_by = {case["id"]: case for case in self.cases}
        rebuilt = []
        for review_id in sorted(packet_by):
            source = packet_by[review_id]; case = case_by[source["case_id"]]; identities = {item["candidate_id"]: item for item in key_by[review_id]["candidates"]}; scores = {item["candidate_id"]: item for item in scored_by[review_id]["candidates"]}; review = completed_by[review_id]; candidates = []
            for item in source["candidates"]:
                cid = item["candidate_id"]; identity = identities[cid]; criteria = review["criteria_pass"][cid]; score = scores[cid]
                candidates.append({"arm_id": identity["arm_id"], "skill": identity["skill"], "output": item["output"], "output_sha256": hashlib.sha256(item["output"].encode()).hexdigest(), "criteria_pass": criteria, "passed": score["passed"], "total": score["total"], "core_failure": any(not criteria[index] for index in case["core_criteria"]), "preferred": review["preferred_candidate"] == cid})
            rebuilt.append({"review_id": review_id, "case_id": source["case_id"], "mechanism": case["mechanism"], "repetition": source["repetition"], "candidates": sorted(candidates, key=lambda item: ORDER[item["arm_id"]])})
        self.assertEqual(experiment["items"], rebuilt)
        reviewer = copy.deepcopy(completed["reviewer"])
        reviewer["allowed_files"] = [PureWindowsPath(path).name for path in reviewer["allowed_files"]]
        self.assertEqual(experiment["blind_reviewer"], reviewer)

    def test_coordinated_report_changes_fail_the_fixed_anchor(self):
        for path, value in ((["decision", "candidate_design_open"], True), (["experiment", "freeze_commit"], "0" * 40), (["experiment", "blind_reviewer", "independent_human"], True)):
            mutated = copy.deepcopy(self.report); target = mutated
            for key in path[:-1]: target = target[key]
            target[path[-1]] = value
            projection = {key: mutated[key] for key in ("scope", "experiment", "analysis", "decision", "limitations")}
            mutated["evidence_projection_sha256"] = object_sha(projection)
            self.assertNotEqual(mutated["evidence_projection_sha256"], EXPECTED_PROJECTION)

    def test_coordinated_gate_changes_fail_semantic_recomputation(self):
        mutated = copy.deepcopy(self.report)
        mutated["analysis"]["decision_gate"][
            "ours_min_core_failures_per_case"
        ] = 0
        for mechanism in mutated["analysis"]["mechanisms"]:
            mechanism["ours_threshold_met"] = True
            mechanism["triggered"] = True
        mutated["decision"]["candidate_design_open"] = True
        projection = {
            key: mutated[key]
            for key in ("scope", "experiment", "analysis", "decision", "limitations")
        }
        mutated["evidence_projection_sha256"] = object_sha(projection)
        with self.assertRaises(AssertionError):
            self._assert_gate_semantics(mutated)

    def test_coordinated_raw_validity_changes_fail_semantic_checks(self):
        if not RUN.is_dir() or not PREFLIGHT_RUN.is_dir():
            self.skipTest("ignored Round 30 runs are unavailable")
        frozen = json.loads((RUN / "frozen.json").read_text(encoding="utf-8"))
        run_meta = json.loads((RUN / "run-meta.json").read_text(encoding="utf-8"))
        summary = json.loads((RUN / "summary.json").read_text(encoding="utf-8"))
        preflight_summary = json.loads(
            (PREFLIGHT_RUN / "summary.json").read_text(encoding="utf-8")
        )
        mutations = []

        invalid_summary = copy.deepcopy(summary)
        invalid_summary["infrastructure_valid"] = False
        mutations.append(
            (self.report, frozen, run_meta, invalid_summary, preflight_summary)
        )

        incomplete_meta = copy.deepcopy(run_meta)
        incomplete_meta["result_rows"] = 53
        incomplete_meta["failed_rows"] = 1
        mutations.append(
            (self.report, frozen, incomplete_meta, summary, preflight_summary)
        )

        repeated_eval = copy.deepcopy(run_meta)
        repeated_eval["commands"][0] = copy.deepcopy(repeated_eval["commands"][1])
        mutations.append(
            (self.report, frozen, repeated_eval, summary, preflight_summary)
        )

        wrong_package = copy.deepcopy(frozen)
        wrong_package["arms"][1]["skill_package_sha256"] = "0" * 64
        mutated_report = copy.deepcopy(self.report)
        mutated_report["experiment"]["arms"][1]["skill_package_sha256"] = "0" * 64
        mutations.append(
            (mutated_report, wrong_package, run_meta, summary, preflight_summary)
        )

        for mutation in mutations:
            report, frozen_value, meta_value, summary_value, preflight_value = mutation
            with self.subTest():
                with self.assertRaises(AssertionError):
                    self._assert_raw_run_semantics(
                        report,
                        frozen_value,
                        meta_value,
                        summary_value,
                        preflight_value,
                    )

        with tempfile.TemporaryDirectory() as temporary:
            prepared_copy = Path(temporary) / "prepared"
            shutil.copytree(RUN / "prepared", prepared_copy)
            tests_path = prepared_copy / "tests.json"
            original_tests = tests_path.read_bytes()
            tests_path.write_bytes(original_tests + b"\n")
            with self.assertRaises(AssertionError):
                self._assert_raw_run_semantics(
                    self.report,
                    frozen,
                    run_meta,
                    summary,
                    preflight_summary,
                    prepared_copy,
                )
            tests_path.write_bytes(original_tests)

            prepared_skill = (
                prepared_copy
                / "fixtures/ours/.agents/skills/article-visual-plan/SKILL.md"
            )
            prepared_skill.write_bytes(prepared_skill.read_bytes() + b"\n")
            with self.assertRaises(AssertionError):
                self._assert_raw_run_semantics(
                    self.report,
                    frozen,
                    run_meta,
                    summary,
                    preflight_summary,
                    prepared_copy,
                )


if __name__ == "__main__":
    unittest.main()
