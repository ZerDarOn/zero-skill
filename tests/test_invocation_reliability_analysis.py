"""Regression tests for explicit Skill invocation reliability analysis."""

import json
from pathlib import Path
import runpy
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
ANALYZER = runpy.run_path(
    str(
        ROOT
        / "evaluations"
        / "native_resume"
        / "analyze_invocation_reliability.py"
    )
)


def events(messages: list[str]) -> str:
    values = [{"type": "thread.started", "thread_id": "thread-1"}]
    values.extend(
        {
            "type": "item.completed",
            "item": {"type": "agent_message", "text": message},
        }
        for message in messages
    )
    values.append({"type": "turn.completed", "usage": {}})
    return "".join(json.dumps(value) + "\n" for value in values)


def trajectory(arm_id: str, output: str, messages: list[str] | None = None) -> dict:
    messages = messages or [output]
    valid = len(messages) == 1
    return {
        "trajectory_id": f"case--{arm_id}--r1",
        "case_id": "case",
        "arm_id": arm_id,
        "repetition": 1,
        "setup_valid": True,
        "technical_valid": valid,
        "turns": [
            {
                "exit_code": 0,
                "error": None,
                "invalid_jsonl_lines": [],
                "event_thread_ids": ["thread-1"],
                "thread_matches_expected": True,
                "raw_events": events(messages),
                "agent_messages": messages,
                "output_matches_last_agent_message": valid,
                "forbidden_item_types": [],
                "stderr": "",
                "technical_valid": valid,
                "raw_output": output,
                "output_sha256": "output-hash",
                "events_sha256": "events-hash",
                "stderr_sha256": "stderr-hash",
            }
        ],
    }


class InvocationReliabilityAnalysisTests(unittest.TestCase):
    def test_canary_skill_requires_the_frozen_output(self):
        passed = ANALYZER["classify_trajectory"](
            trajectory("probe", "FROZEN-TOKEN"),
            "canary",
            "baseline",
            "probe",
            "FROZEN-TOKEN",
        )
        missed = ANALYZER["classify_trajectory"](
            trajectory("probe", "guessed"),
            "canary",
            "baseline",
            "probe",
            "FROZEN-TOKEN",
        )

        self.assertTrue(passed["operational_success"])
        self.assertFalse(missed["operational_success"])
        self.assertIn("canary-output-miss", missed["failure_reasons"])

    def test_baseline_returning_the_secret_is_rejected(self):
        result = ANALYZER["classify_trajectory"](
            trajectory("baseline", "答案是 FROZEN-TOKEN。"),
            "canary",
            "baseline",
            "probe",
            "FROZEN-TOKEN",
        )

        self.assertFalse(result["operational_success"])
        self.assertIn("canary-secret-leak", result["failure_reasons"])

    def test_multiple_messages_and_policy_block_remain_incidents(self):
        item = trajectory("ours", "answer", ["loading", "answer"])
        item["turns"][0]["stderr"] = "command rejected: blocked by policy"
        result = ANALYZER["classify_trajectory"](
            item, "business", "baseline", "ours", None
        )

        self.assertFalse(result["operational_success"])
        self.assertIn("agent-message-count-failure", result["failure_reasons"])
        self.assertIn("output-binding-failure", result["failure_reasons"])
        self.assertIn("policy-block", result["failure_reasons"])
        self.assertIn("technical-invalid", result["failure_reasons"])

    def test_single_message_skill_process_disclosure_is_an_incident(self):
        result = ANALYZER["classify_trajectory"](
            trajectory("ours", "我会先加载 Skill 再回答。"),
            "business",
            "baseline",
            "ours",
            None,
        )

        self.assertFalse(result["operational_success"])
        self.assertIn("skill-process-disclosure", result["failure_reasons"])

        ordinary = ANALYZER["classify_trajectory"](
            trajectory("ours", "A skillful answer."),
            "business",
            "baseline",
            "ours",
            None,
        )
        self.assertTrue(ordinary["operational_success"])

    def test_zero_tolerance_gate_opens_infrastructure_investigation(self):
        cohorts = [
            {
                "role": "canary",
                "baseline_arm": "baseline",
                "skill_arm": "probe",
                "arms": [
                    {
                        "arm_id": "baseline",
                        "attempts": 2,
                        "technical_valid": 2,
                        "operational_failures": 0,
                        "failure_reason_counts": {},
                    },
                    {
                        "arm_id": "probe",
                        "attempts": 2,
                        "technical_valid": 2,
                        "operational_failures": 1,
                        "failure_reason_counts": {"canary-output-miss": 1},
                    },
                ],
            },
            {
                "role": "business",
                "baseline_arm": "baseline",
                "skill_arm": "ours",
                "arms": [
                    {
                        "arm_id": "baseline",
                        "attempts": 2,
                        "technical_valid": 2,
                        "operational_failures": 0,
                        "failure_reason_counts": {},
                    },
                    {
                        "arm_id": "ours",
                        "attempts": 2,
                        "technical_valid": 2,
                        "operational_failures": 0,
                        "failure_reason_counts": {},
                    },
                ],
            },
        ]

        gate = ANALYZER["build_gate"](cohorts)

        self.assertFalse(gate["passed"])
        self.assertEqual(gate["observed"]["canary_skill_failures"], 1)

    def test_analysis_output_must_stay_inside_a_run(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            run = base / "run"
            run.mkdir()
            inside = ANALYZER["require_output_inside_runs"](
                run / "analysis.json", [run]
            )
            self.assertEqual(inside, (run / "analysis.json").resolve())
            with self.assertRaisesRegex(ValueError, "validated run directory"):
                ANALYZER["require_output_inside_runs"](
                    base / "outside.json", [run]
                )


if __name__ == "__main__":
    unittest.main()
