import hashlib
import json
from pathlib import Path
import runpy
import tempfile
import unittest


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "evaluations"
    / "promptfoo"
    / "summarize_skill_comparison.py"
)
SCORE_MODULE_PATH = MODULE_PATH.with_name("score_blind_review.py")


class PromptfooSkillSummaryTests(unittest.TestCase):
    def setUp(self):
        self.module = runpy.run_path(str(MODULE_PATH))
        self.score_module = runpy.run_path(str(SCORE_MODULE_PATH))
        self.tempdir = tempfile.TemporaryDirectory()
        self.run_dir = Path(self.tempdir.name)

    def tearDown(self):
        self.tempdir.cleanup()

    def write_run(self, kind, arms, rows, repetitions=1, run_repeat=None):
        frozen = {
            "comparison_id": "synthetic-comparison",
            "comparison_kind": kind,
            "selected_case_ids": ["C01"],
            "repetitions": repetitions,
            "arms": arms,
        }
        frozen_path = self.run_dir / "frozen.json"
        frozen_path.write_text(json.dumps(frozen), encoding="utf-8")
        results = {"version": 3, "results": {"results": rows}}
        results_path = self.run_dir / "results.json"
        results_path.write_text(json.dumps(results), encoding="utf-8")
        digest = hashlib.sha256(results_path.read_bytes()).hexdigest()
        (self.run_dir / "run-meta.json").write_text(
            json.dumps(
                {
                    "status": "completed-with-failures",
                    "repeat": repetitions if run_repeat is None else run_repeat,
                    "frozen_sha256": hashlib.sha256(
                        frozen_path.read_bytes()
                    ).hexdigest(),
                    "results_sha256": digest,
                }
            ),
            encoding="utf-8",
        )

    @staticmethod
    def row(
        arm_id,
        output,
        expected=None,
        item_types=None,
        invocation=None,
        skill_calls=None,
        attempted_skill_calls=None,
    ):
        assertions = [] if expected is None else [{"type": "equals", "value": expected}]
        raw = {
            "items": [
                {"type": item_type} for item_type in (item_types or ["agent_message"])
            ]
        }
        return {
            "provider": {"id": "openai:codex-sdk", "label": arm_id},
            "metadata": {
                "case_id": "C01",
                "arm_id": arm_id,
                "invocation": invocation
                or ("none" if arm_id == "baseline" else "explicit"),
                "purpose": "synthetic quality check",
                "hard_criteria": ["Preserve the date", "Do not invent facts"],
            },
            "vars": {"prompt": "Rewrite the synthetic note."},
            "testCase": {"assert": assertions},
            "response": {
                "output": output,
                "raw": json.dumps(raw),
                "metadata": {
                    "skillCalls": skill_calls or [],
                    "attemptedSkillCalls": attempted_skill_calls or [],
                },
            },
            "success": output == expected if expected is not None else True,
            "error": (
                "synthetic assertion mismatch"
                if expected is not None and output != expected
                else None
            ),
            "cost": 0.01,
            "latencyMs": 100,
            "tokenUsage": {"total": 20, "prompt": 15, "completion": 5},
        }

    def test_discovery_gate_requires_skill_hit_and_baseline_miss(self):
        arms = [
            {"id": "baseline", "skill": None, "install_mode": "none", "invocation": "none"},
            {
                "id": "project-skill",
                "skill": "discovery-token",
                "install_mode": "project",
                "invocation": "explicit",
                "skill_package_sha256": "abc",
            },
        ]
        expected = "CERULEAN-FALCON-SKILL"
        self.write_run(
            "discovery",
            arms,
            [
                self.row("baseline", "unknown", expected),
                self.row("project-skill", expected, expected),
            ],
        )

        summary = self.module["summarize_comparison"](self.run_dir)

        self.assertEqual(summary["status"], "passed")
        self.assertTrue(summary["infrastructure_valid"])
        baseline = next(arm for arm in summary["arms"] if arm["id"] == "baseline")
        self.assertEqual(baseline["provider_errors"], 0)
        self.assertFalse((self.run_dir / "blind-review.json").exists())

    def test_implicit_discovery_gate_requires_confirmed_skill_read(self):
        arms = [
            {"id": "baseline", "skill": None, "install_mode": "none", "invocation": "none"},
            {
                "id": "project-skill",
                "skill": "discovery-token",
                "install_mode": "project",
                "invocation": "implicit",
            },
        ]
        expected = "CERULEAN-FALCON-SKILL"
        self.write_run(
            "discovery",
            arms,
            [
                self.row("baseline", "unknown", expected),
                self.row(
                    "project-skill",
                    expected,
                    expected,
                    invocation="implicit",
                ),
            ],
        )

        summary = self.module["summarize_comparison"](self.run_dir)

        self.assertEqual(summary["status"], "failed")
        skill_check = summary["discovery_gate"]["checks"][1]
        self.assertTrue(skill_check["skill_trace_expected"])
        self.assertFalse(skill_check["skill_trace_matched"])
        skill_arm = next(
            arm for arm in summary["arms"] if arm["id"] == "project-skill"
        )
        self.assertEqual(skill_arm["rows_with_expected_skill_call"], 0)

    def test_implicit_discovery_gate_accepts_confirmed_skill_read(self):
        arms = [
            {"id": "baseline", "skill": None, "install_mode": "none", "invocation": "none"},
            {
                "id": "project-skill",
                "skill": "discovery-token",
                "install_mode": "project",
                "invocation": "implicit",
            },
        ]
        expected = "CERULEAN-FALCON-SKILL"
        self.write_run(
            "discovery",
            arms,
            [
                self.row("baseline", "unknown", expected),
                self.row(
                    "project-skill",
                    expected,
                    expected,
                    invocation="implicit",
                    skill_calls=[{"name": "discovery-token", "source": "heuristic"}],
                ),
            ],
        )

        summary = self.module["summarize_comparison"](self.run_dir)

        self.assertEqual(summary["status"], "passed")
        skill_check = summary["discovery_gate"]["checks"][1]
        self.assertTrue(skill_check["skill_trace_matched"])

    def test_discovery_gate_rejects_false_positive_baseline(self):
        arms = [
            {"id": "baseline", "skill": None, "install_mode": "none", "invocation": "none"},
            {
                "id": "project-skill",
                "skill": "discovery-token",
                "install_mode": "project",
                "invocation": "explicit",
            },
        ]
        expected = "CERULEAN-FALCON-SKILL"
        self.write_run(
            "discovery",
            arms,
            [
                self.row("baseline", expected, expected),
                self.row("project-skill", expected, expected),
            ],
        )

        summary = self.module["summarize_comparison"](self.run_dir)

        self.assertEqual(summary["status"], "failed")
        baseline_check = summary["discovery_gate"]["checks"][0]
        self.assertEqual(baseline_check["expected_behavior"], "miss-hidden-token")
        self.assertFalse(baseline_check["passed"])

    def test_implicit_quality_summary_stops_at_missing_skill_trace(self):
        arms = [
            {
                "id": "baseline",
                "skill": None,
                "install_mode": "none",
                "invocation": "none",
            },
            {
                "id": "ours",
                "skill": "ours",
                "install_mode": "project",
                "invocation": "implicit",
            },
        ]
        self.write_run(
            "quality",
            arms,
            [
                self.row("baseline", "plain"),
                self.row("ours", "good by chance", invocation="implicit"),
            ],
        )

        summary = self.module["summarize_comparison"](self.run_dir)

        self.assertEqual(summary["status"], "routing-failed")
        self.assertEqual(summary["routing_gate"]["status"], "failed")
        ours_check = next(
            check
            for check in summary["routing_gate"]["checks"]
            if check["arm_id"] == "ours"
        )
        self.assertFalse(ours_check["passed"])
        self.assertTrue((self.run_dir / "blind-review.json").is_file())

    def test_implicit_quality_summary_accepts_confirmed_skill_trace(self):
        arms = [
            {
                "id": "baseline",
                "skill": None,
                "install_mode": "none",
                "invocation": "none",
            },
            {
                "id": "ours",
                "skill": "ours",
                "install_mode": "project",
                "invocation": "implicit",
            },
        ]
        self.write_run(
            "quality",
            arms,
            [
                self.row("baseline", "plain"),
                self.row(
                    "ours",
                    "skill output",
                    invocation="implicit",
                    skill_calls=[{"name": "ours", "source": "heuristic"}],
                ),
            ],
        )

        summary = self.module["summarize_comparison"](self.run_dir)

        self.assertEqual(summary["status"], "awaiting-human-review")
        self.assertEqual(summary["routing_gate"]["status"], "passed")
    def test_malformed_provider_raw_response_marks_run_invalid(self):
        arms = [
            {"id": "baseline", "skill": None, "install_mode": "none", "invocation": "none"},
            {"id": "ours", "skill": "ours", "install_mode": "project", "invocation": "explicit"},
        ]
        baseline = self.row("baseline", "plain")
        ours = self.row("ours", "plain")
        ours["response"]["raw"] = "not-json"
        self.write_run("quality", arms, [baseline, ours])

        summary = self.module["summarize_comparison"](self.run_dir)

        self.assertFalse(summary["infrastructure_valid"])
        ours_summary = next(arm for arm in summary["arms"] if arm["id"] == "ours")
        self.assertEqual(ours_summary["provider_errors"], 1)

    def test_quality_summary_creates_blind_packet_and_separate_key(self):
        arms = [
            {"id": "baseline", "skill": None, "install_mode": "none", "invocation": "none"},
            {
                "id": "ours",
                "skill": "prose-polish",
                "install_mode": "project",
                "invocation": "explicit",
                "skill_package_sha256": "ours-hash",
            },
            {
                "id": "upstream",
                "skill": "humanizer",
                "install_mode": "project",
                "invocation": "explicit",
                "skill_package_sha256": "upstream-hash",
            },
        ]
        self.write_run(
            "quality",
            arms,
            [
                self.row("baseline", "output one"),
                self.row("ours", "output two"),
                self.row("upstream", "output three"),
            ],
            repetitions=3,
            run_repeat=1,
        )

        summary = self.module["summarize_comparison"](self.run_dir)
        packet_text = (self.run_dir / "blind-review.json").read_text(encoding="utf-8")
        summary_text = (self.run_dir / "summary.json").read_text(encoding="utf-8")
        key = json.loads(
            (self.run_dir / "blind-review-key.json").read_text(encoding="utf-8")
        )
        form = json.loads(
            (self.run_dir / "blind-review-form.json").read_text(encoding="utf-8")
        )

        self.assertEqual(summary["status"], "awaiting-human-review")
        self.assertEqual(summary["planned_repetitions"], 3)
        self.assertEqual(summary["executed_repetitions"], 1)
        self.assertNotIn("prose-polish", packet_text)
        self.assertNotIn("humanizer", packet_text)
        self.assertNotIn("randomization_salt", packet_text)
        self.assertNotIn("randomization_salt", summary_text)
        self.assertIn("randomization_salt", key)
        self.assertEqual(len(key["items"][0]["candidates"]), 3)
        self.assertEqual(
            sorted(form["reviews"][0]["criteria_pass"]), ["A", "B", "C"]
        )

        repeated = self.module["summarize_comparison"](self.run_dir)
        self.assertEqual(repeated, summary)

    def test_host_mcp_call_marks_quality_run_invalid(self):
        arms = [
            {"id": "baseline", "skill": None, "install_mode": "none", "invocation": "none"},
            {"id": "ours", "skill": "ours", "install_mode": "project", "invocation": "explicit"},
        ]
        self.write_run(
            "quality",
            arms,
            [
                self.row("baseline", "plain"),
                self.row("ours", "searched", item_types=["mcp_tool_call", "agent_message"]),
            ],
        )

        summary = self.module["summarize_comparison"](self.run_dir)

        self.assertFalse(summary["infrastructure_valid"])
        self.assertEqual(summary["status"], "infrastructure-invalid")
        ours = next(arm for arm in summary["arms"] if arm["id"] == "ours")
        self.assertEqual(ours["forbidden_tool_rows"], 1)

    def test_tampered_results_are_rejected(self):
        arms = [
            {"id": "baseline", "skill": None, "install_mode": "none", "invocation": "none"},
            {"id": "ours", "skill": "ours", "install_mode": "project", "invocation": "explicit"},
        ]
        self.write_run(
            "quality",
            arms,
            [self.row("baseline", "one"), self.row("ours", "two")],
        )
        with (self.run_dir / "results.json").open("a", encoding="utf-8") as stream:
            stream.write(" ")

        with self.assertRaisesRegex(ValueError, "results hash"):
            self.module["summarize_comparison"](self.run_dir)

    def test_tampered_frozen_evidence_is_rejected(self):
        arms = [
            {"id": "baseline", "skill": None, "install_mode": "none", "invocation": "none"},
            {"id": "ours", "skill": "ours", "install_mode": "project", "invocation": "explicit"},
        ]
        self.write_run(
            "quality",
            arms,
            [self.row("baseline", "one"), self.row("ours", "two")],
        )
        with (self.run_dir / "frozen.json").open("a", encoding="utf-8") as stream:
            stream.write(" ")

        with self.assertRaisesRegex(ValueError, "frozen evidence hash"):
            self.module["summarize_comparison"](self.run_dir)

    def prepare_completed_quality_review(self):
        arms = [
            {"id": "baseline", "skill": None, "install_mode": "none", "invocation": "none"},
            {"id": "ours", "skill": "ours", "install_mode": "project", "invocation": "explicit"},
        ]
        self.write_run(
            "quality",
            arms,
            [self.row("baseline", "one"), self.row("ours", "two")],
        )
        self.module["summarize_comparison"](self.run_dir)
        form_path = self.run_dir / "completed-review.json"
        form = json.loads(
            (self.run_dir / "blind-review-form.json").read_text(encoding="utf-8")
        )
        form["reviewer"] = {"kind": "synthetic-test-reviewer"}
        for candidate_id in form["reviews"][0]["criteria_pass"]:
            form["reviews"][0]["criteria_pass"][candidate_id] = [True, False]
        form["reviews"][0]["preferred_candidate"] = "A"
        form_path.write_text(json.dumps(form), encoding="utf-8")
        return form_path

    def test_scores_completed_blind_review_after_reveal(self):
        form_path = self.prepare_completed_quality_review()

        result = self.score_module["score_review"](self.run_dir, form_path)

        self.assertEqual(result["status"], "reviewed")
        self.assertEqual(len(result["arms"]), 2)
        self.assertTrue(
            all(arm["criterion_pass_rate"] == 0.5 for arm in result["arms"])
        )
        self.assertEqual(sum(arm["preferred_count"] for arm in result["arms"]), 1)

    def test_rejects_unfinished_blind_review(self):
        form_path = self.prepare_completed_quality_review()
        form = json.loads(form_path.read_text(encoding="utf-8"))
        first_candidate = next(iter(form["reviews"][0]["criteria_pass"]))
        form["reviews"][0]["criteria_pass"][first_candidate][0] = None
        form_path.write_text(json.dumps(form), encoding="utf-8")

        with self.assertRaisesRegex(ValueError, "must be booleans"):
            self.score_module["score_review"](self.run_dir, form_path)

    def test_rejects_review_output_outside_run_directory(self):
        form_path = self.prepare_completed_quality_review()
        outside = self.run_dir.parent / "outside-review-result.json"

        with self.assertRaisesRegex(ValueError, "inside the run directory"):
            self.score_module["score_review"](self.run_dir, form_path, outside)

    def test_rejects_blind_artifact_path_escape(self):
        form_path = self.prepare_completed_quality_review()
        summary_path = self.run_dir / "summary.json"
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        summary["blind_review"]["packet"] = "../blind-review.json"
        summary_path.write_text(json.dumps(summary), encoding="utf-8")

        with self.assertRaisesRegex(ValueError, "packet filename"):
            self.score_module["score_review"](self.run_dir, form_path)

    def test_rejects_empty_reviewer_kind_and_non_string_notes(self):
        form_path = self.prepare_completed_quality_review()
        form = json.loads(form_path.read_text(encoding="utf-8"))
        form["reviewer"]["kind"] = " "
        form_path.write_text(json.dumps(form), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "reviewer.kind"):
            self.score_module["score_review"](self.run_dir, form_path)

        form["reviewer"]["kind"] = "synthetic-test-reviewer"
        form["reviews"][0]["notes"] = ["not", "text"]
        form_path.write_text(json.dumps(form), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "notes must be a string"):
            self.score_module["score_review"](self.run_dir, form_path)


if __name__ == "__main__":
    unittest.main()
