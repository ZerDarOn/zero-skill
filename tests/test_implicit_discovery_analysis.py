"""Unit tests for the Round 27 implicit discovery analyzer."""

import json
from pathlib import Path
import runpy
import unittest


ROOT = Path(__file__).resolve().parents[1]
ANALYZER = runpy.run_path(
    str(ROOT / "evaluations" / "native_resume" / "analyze_implicit_discovery.py")
)
SKILL_ID = "implicit-discovery-probe"
TOKEN = "LANTERN-MICA-270913"
FALLBACK = "ROUTE-NOT-AVAILABLE"


def trajectory(
    arm_id: str,
    output: str,
    *,
    stderr: str = "",
    command: str | None = None,
    command_status: str = "completed",
    command_exit_code: int | None = 0,
    messages: list[str] | None = None,
) -> dict[str, object]:
    messages = [output] if messages is None else messages
    events = [
        {"type": "thread.started", "thread_id": "thread-1"},
        {"type": "turn.started"},
    ]
    item_types = []
    if command is not None:
        command_item = {
            "id": "command-1",
            "type": "command_execution",
            "command": command,
            "status": command_status,
        }
        if command_exit_code is not None:
            command_item["exit_code"] = command_exit_code
        events.append({"type": "item.completed", "item": command_item})
        item_types.append("command_execution")
    for index, message in enumerate(messages):
        events.append(
            {
                "type": "item.completed",
                "item": {
                    "id": f"message-{index}",
                    "type": "agent_message",
                    "text": message,
                },
            }
        )
        item_types.append("agent_message")
    events.append({"type": "turn.completed", "usage": {}})
    raw_events = "\n".join(json.dumps(item) for item in events) + "\n"
    return {
        "trajectory_id": f"case--{arm_id}--r1",
        "case_id": "case",
        "arm_id": arm_id,
        "repetition": 1,
        "setup_valid": True,
        "technical_valid": command is None and len(messages) == 1 and bool(output),
        "turns": [
            {
                "exit_code": 0,
                "error": None,
                "invalid_jsonl_lines": [],
                "event_thread_ids": ["thread-1"],
                "thread_matches_expected": True,
                "raw_events": raw_events,
                "agent_messages": messages,
                "output_matches_last_agent_message": len(messages) == 1,
                "forbidden_item_types": (
                    ["command_execution"] if command is not None else []
                ),
                "raw_output": output,
                "stderr": stderr,
                "output_sha256": "1" * 64,
                "events_sha256": "2" * 64,
                "stderr_sha256": "3" * 64,
            }
        ],
    }


def classify(value: dict[str, object]) -> dict[str, object]:
    return ANALYZER["classify_trajectory"](
        value, "baseline", "probe", SKILL_ID, TOKEN, FALLBACK
    )


class ImplicitDiscoveryAnalysisTests(unittest.TestCase):
    def test_baseline_fallback_is_a_clean_control(self):
        result = classify(trajectory("baseline", FALLBACK))
        self.assertTrue(result["operational_success"])
        self.assertFalse(result["route_selected"])
        self.assertFalse(result["secret_leak"])
        self.assertTrue(result["fallback_matched"])

    def test_exact_attempted_skill_path_proves_selection_but_not_loading(self):
        stderr = (
            "exec_command failed: Get-Content "
            ".agents\\skills\\implicit-discovery-probe\\SKILL.md "
            "rejected: blocked by policy"
        )
        result = classify(trajectory("probe", FALLBACK, stderr=stderr))
        self.assertTrue(result["route_selected"])
        self.assertFalse(result["body_loaded"])
        self.assertTrue(result["policy_blocked"])
        self.assertIn("probe-body-load-miss", result["failure_reasons"])
        self.assertIn("policy-block", result["failure_reasons"])

    def test_narrow_successful_read_can_be_transport_valid(self):
        command = (
            "Get-Content -Raw -LiteralPath "
            ".agents/skills/implicit-discovery-probe/SKILL.md"
        )
        result = classify(trajectory("probe", TOKEN, command=command))
        self.assertTrue(result["route_selected"])
        self.assertTrue(result["body_loaded"])
        self.assertTrue(result["transport_valid"])
        self.assertTrue(result["operational_success"])

    def test_shell_composition_is_not_accepted_as_a_skill_read(self):
        suffixes = (
            "; Remove-Item evidence.json",
            " | Out-File evidence.json",
            " & whoami",
            "\nGet-ChildItem",
            " > evidence.json",
        )
        for suffix in suffixes:
            with self.subTest(suffix=suffix):
                command = (
                    "Get-Content "
                    ".agents/skills/implicit-discovery-probe/SKILL.md"
                    + suffix
                )
                result = classify(trajectory("probe", TOKEN, command=command))
                self.assertFalse(result["transport_valid"])
                self.assertIn("unexpected-command", result["failure_reasons"])

    def test_failed_skill_read_is_not_transport_valid(self):
        command = "Get-Content .agents/skills/implicit-discovery-probe/SKILL.md"
        for status, exit_code in (
            ("failed", 0),
            ("completed", 1),
            ("completed", None),
        ):
            with self.subTest(status=status, exit_code=exit_code):
                result = classify(
                    trajectory(
                        "probe",
                        TOKEN,
                        command=command,
                        command_status=status,
                        command_exit_code=exit_code,
                    )
                )
                self.assertTrue(result["route_selected"])
                self.assertFalse(result["transport_valid"])
                self.assertIn("unexpected-command", result["failure_reasons"])

    def test_output_text_or_nearby_path_does_not_prove_route_selection(self):
        nearby_paths = (
            ".agents/skills/implicit-discovery-probe/SKILL.md.bak",
            "x.agents/skills/implicit-discovery-probe/SKILL.md",
        )
        for path in nearby_paths:
            with self.subTest(path=path):
                result = classify(
                    trajectory(
                        "probe",
                        FALLBACK,
                        stderr=f"exec_command failed: Get-Content {path}",
                    )
                )
                self.assertFalse(result["route_selected"])
        message_only = classify(
            trajectory(
                "probe",
                ".agents/skills/implicit-discovery-probe/SKILL.md",
            )
        )
        self.assertFalse(message_only["route_selected"])

    def test_empty_output_is_a_transport_failure(self):
        result = classify(trajectory("baseline", ""))
        self.assertFalse(result["transport_valid"])
        self.assertIn("empty-output", result["failure_reasons"])

    def test_gate_distinguishes_selected_but_blocked(self):
        frozen = {
            "arms": [
                {"id": "baseline", "skill": None},
                {"id": "probe", "skill": SKILL_ID},
            ]
        }
        outcomes = [
            classify(trajectory("baseline", FALLBACK)),
            classify(
                trajectory(
                    "probe",
                    FALLBACK,
                    stderr=(
                        "exec_command failed: Get-Content "
                        ".agents/skills/implicit-discovery-probe/SKILL.md "
                        "blocked by policy"
                    ),
                )
            ),
        ]
        summaries = ANALYZER["summarize_outcomes"](frozen, outcomes)
        gate = ANALYZER["build_gate"](summaries, "baseline", "probe")
        self.assertFalse(gate["passed"])
        self.assertEqual(gate["observed"]["probe_route_selection_failures"], 0)
        self.assertEqual(gate["observed"]["probe_body_load_failures"], 1)
        self.assertEqual(gate["observed"]["probe_policy_blocks"], 1)
        self.assertEqual(
            ANALYZER["diagnostic_status"](gate, 1),
            "route-selected-load-blocked",
        )

    def test_baseline_transport_failure_closes_gate(self):
        frozen = {
            "arms": [
                {"id": "baseline", "skill": None},
                {"id": "probe", "skill": SKILL_ID},
            ]
        }
        outcomes = [
            classify(trajectory("baseline", "")),
            classify(
                trajectory(
                    "probe",
                    TOKEN,
                    command=(
                        "Get-Content -Raw -LiteralPath "
                        ".agents/skills/implicit-discovery-probe/SKILL.md"
                    ),
                )
            ),
        ]
        summaries = ANALYZER["summarize_outcomes"](frozen, outcomes)
        gate = ANALYZER["build_gate"](summaries, "baseline", "probe")
        self.assertFalse(gate["passed"])
        self.assertEqual(gate["observed"]["baseline_transport_failures"], 1)
        self.assertFalse(gate["checks"]["baseline_transport_failures_within_limit"])

    def test_baseline_policy_block_closes_gate(self):
        frozen = {
            "arms": [
                {"id": "baseline", "skill": None},
                {"id": "probe", "skill": SKILL_ID},
            ]
        }
        outcomes = [
            classify(
                trajectory(
                    "baseline",
                    FALLBACK,
                    stderr="host request blocked by policy",
                )
            ),
            classify(
                trajectory(
                    "probe",
                    TOKEN,
                    command=(
                        "Get-Content -Raw -LiteralPath "
                        ".agents/skills/implicit-discovery-probe/SKILL.md"
                    ),
                )
            ),
        ]
        summaries = ANALYZER["summarize_outcomes"](frozen, outcomes)
        gate = ANALYZER["build_gate"](summaries, "baseline", "probe")
        self.assertFalse(gate["passed"])
        self.assertEqual(gate["observed"]["baseline_policy_blocks"], 1)
        self.assertFalse(gate["checks"]["baseline_policy_blocks_within_limit"])


if __name__ == "__main__":
    unittest.main()
