"""Regression tests for the native multi-turn resume evaluation adapter."""

import copy
import hashlib
import json
from pathlib import Path
import runpy
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
COMPARISON = (
    ROOT
    / "evaluations"
    / "comparisons"
    / "conversation-native-resume-two-arm-17"
)
RUNNER = runpy.run_path(
    str(ROOT / "evaluations" / "native_resume" / "run_native_resume.py")
)
SUMMARY = runpy.run_path(
    str(ROOT / "evaluations" / "native_resume" / "summarize_native_resume.py")
)
PREPARE = runpy.run_path(
    str(ROOT / "evaluations" / "promptfoo" / "prepare_skill_comparison.py")
)
SCORE = runpy.run_path(
    str(ROOT / "evaluations" / "promptfoo" / "score_blind_review.py")
)
ANALYZE = runpy.run_path(
    str(ROOT / "evaluations" / "native_resume" / "analyze_native_review.py")
)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def json_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def write_json(path: Path, value: object) -> None:
    path.write_bytes(json_bytes(value))


class NativeResumeComparisonTests(unittest.TestCase):
    def setUp(self):
        runs_root = ROOT / "evaluations" / "runs"
        runs_root.mkdir(parents=True, exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(dir=runs_root)
        self.run_dir = Path(self.temporary.name) / "run"
        PREPARE["prepare_comparison"](
            ROOT,
            COMPARISON / "promptfoo.json",
            self.run_dir,
        )
        self.frozen = json.loads(
            (self.run_dir / "frozen.json").read_text(encoding="utf-8")
        )
        self.cases = json.loads((COMPARISON / "cases.json").read_text(encoding="utf-8"))
        self.prompts = RUNNER["load_prepared_prompts"](self.run_dir, self.frozen)

    def tearDown(self):
        self.temporary.cleanup()

    @staticmethod
    def events(thread_id: str, output: str) -> str:
        values = [
            {"type": "thread.started", "thread_id": thread_id},
            {"type": "turn.started"},
            {"type": "item.completed", "item": {"id": "item_0", "type": "agent_message", "text": output}},
            {
                "type": "turn.completed",
                "usage": {
                    "input_tokens": 100,
                    "cached_input_tokens": 25,
                    "output_tokens": 12,
                    "reasoning_output_tokens": 2,
                },
            },
        ]
        return "".join(json.dumps(value, ensure_ascii=False) + "\n" for value in values)

    def make_turn(
        self,
        case: dict[str, object],
        arm: dict[str, object],
        thread_id: str,
        index: int,
        prior_hashes: list[str],
    ) -> dict[str, object]:
        source_message = case["turns"][index - 1]
        submitted = (
            self.prompts[(case["id"], arm["id"])]
            if index == 1
            else source_message
        )
        output = f"synthetic output {case['id']} {arm['id']} turn {index}"
        events = self.events(thread_id, output)
        output_path = Path("synthetic-final.txt")
        command = RUNNER["build_codex_command"](
            "codex-test",
            self.frozen["model"],
            self.frozen["reasoning_effort"],
            output_path,
            None if index == 1 else thread_id,
        )
        safe = RUNNER["safe_command"](command, output_path)
        usage = json.loads(events.splitlines()[-1])["usage"]
        return {
            "started_at": "2026-09-13T00:00:00+00:00",
            "finished_at": "2026-09-13T00:00:01+00:00",
            "duration_ms": 1000,
            "prompt_sha256": sha256_bytes(submitted.encode("utf-8")),
            "raw_output": output,
            "output_sha256": sha256_bytes(output.encode("utf-8")),
            "raw_events": events,
            "events_sha256": sha256_bytes(events.encode("utf-8")),
            "stderr": "",
            "stderr_sha256": sha256_bytes(b""),
            "exit_code": 0,
            "error": None,
            "invalid_jsonl_lines": [],
            "event_thread_ids": [thread_id],
            "thread_id": thread_id,
            "thread_matches_expected": True,
            "item_types": ["agent_message"],
            "forbidden_item_types": [],
            "agent_messages": [output],
            "output_matches_last_agent_message": True,
            "usage": usage,
            "technical_valid": True,
            "turn_index": index,
            "source_user_message": source_message,
            "submitted_prompt": submitted,
            "context_mode": (
                "initial-prepared-prompt"
                if index == 1
                else "native-resume-current-user-message-only"
            ),
            "expected_thread_id": None if index == 1 else thread_id,
            "prior_output_sha256": list(prior_hashes),
            "command": safe,
        }

    def make_trajectory(
        self,
        case: dict[str, object],
        arm: dict[str, object],
        repetition: int = 1,
    ) -> dict[str, object]:
        thread_id = f"thread-{case['id']}-{arm['id']}-{repetition}"
        turns = []
        prior = []
        for index in range(1, len(case["turns"]) + 1):
            turn = self.make_turn(case, arm, thread_id, index, prior)
            turns.append(turn)
            prior.append(turn["output_sha256"])
        return {
            "trajectory_id": f"{case['id']}--{arm['id']}--r{repetition}",
            "case_id": case["id"],
            "arm_id": arm["id"],
            "repetition": repetition,
            "mechanism": case["mechanism"],
            "purpose": case["purpose"],
            "hard_criteria": case["hard_criteria"],
            "source_user_turns": case["turns"],
            "source_user_turns_sha256": sha256_bytes(json_bytes(case["turns"])),
            "skill": arm.get("skill"),
            "skill_package_sha256": arm.get("skill_package_sha256"),
            "thread_id": thread_id,
            "setup_valid": True,
            "setup_error": None,
            "turns": turns,
            "technical_valid": True,
        }

    def write_valid_run(self, repetitions: int = 1) -> list[dict[str, object]]:
        trajectories = [
            self.make_trajectory(case, arm, repetition)
            for case in self.cases
            for arm in self.frozen["arms"]
            for repetition in range(1, repetitions + 1)
        ]
        results = {
            "schema_version": 1,
            "comparison_id": self.frozen["comparison_id"],
            "generated_at": "2026-09-13T00:01:00+00:00",
            "trajectories": trajectories,
        }
        results_path = self.run_dir / "native-results.json"
        write_json(results_path, results)
        turn_count = sum(len(item["turns"]) for item in trajectories)
        write_json(
            self.run_dir / "run-meta.json",
            {
                "schema_version": 1,
                "comparison_id": self.frozen["comparison_id"],
                "status": "completed",
                "frozen_sha256": sha256_bytes((self.run_dir / "frozen.json").read_bytes()),
                "repeat": repetitions,
                "session_mode": "explicit-thread-id",
                "resume_last_used": False,
                "ephemeral_used": False,
                "execution_fixture_manifests": RUNNER["verify_execution_fixtures"](
                    self.run_dir, self.frozen
                ),
                "expected_trajectories": len(trajectories),
                "expected_turns": turn_count,
                "result_trajectories": len(trajectories),
                "valid_trajectories": len(trajectories),
                "invalid_trajectories": 0,
                "result_turns": turn_count,
                "results_sha256": sha256_bytes(results_path.read_bytes()),
            },
        )
        return trajectories

    def rewrite_results(self, trajectories: list[dict[str, object]]) -> None:
        results_path = self.run_dir / "native-results.json"
        payload = json.loads(results_path.read_text(encoding="utf-8"))
        payload["trajectories"] = trajectories
        write_json(results_path, payload)
        meta_path = self.run_dir / "run-meta.json"
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        meta["results_sha256"] = sha256_bytes(results_path.read_bytes())
        write_json(meta_path, meta)

    def test_frozen_shape_has_three_paired_mechanisms_and_84_turns(self):
        mechanisms = {}
        for case in self.cases:
            mechanisms.setdefault(case["mechanism"], []).append(case["id"])
            self.assertEqual(case["prompt"], case["turns"][0])
            self.assertEqual(len(case["hard_criteria"]), 4)
            prompt_text = "\n".join(case["turns"])
            for criterion in case["hard_criteria"]:
                self.assertNotIn(criterion, prompt_text)
        self.assertEqual(
            {key: len(value) for key, value in mechanisms.items()},
            {"phase-boundary": 2, "state-isolation": 2, "evidence-boundary": 2},
        )
        self.assertEqual(sum(len(case["turns"]) for case in self.cases), 14)
        self.assertEqual(14 * 2 * 3, 84)

    def test_selected_case_prepare_is_supported_for_unscored_preflight(self):
        selected_run = Path(self.temporary.name) / "selected-run"
        case_id = "stop-roleplay-one-real-message"
        PREPARE["prepare_comparison"](
            ROOT,
            COMPARISON / "promptfoo.json",
            selected_run,
            {case_id},
        )
        frozen = json.loads((selected_run / "frozen.json").read_text(encoding="utf-8"))
        cases = RUNNER["load_trajectory_cases"](ROOT, frozen)
        self.assertEqual([case["id"] for case in cases], [case_id])
        prompts = RUNNER["load_prepared_prompts"](selected_run, frozen)
        self.assertEqual(set(prompts), {(case_id, "baseline"), (case_id, "ours")})

    def test_prepared_prompts_only_add_explicit_skill_to_ours_first_turn(self):
        for case in self.cases:
            baseline = self.prompts[(case["id"], "baseline")]
            ours = self.prompts[(case["id"], "ours")]
            self.assertNotIn("$conversation-rehearsal", baseline)
            self.assertIn("$conversation-rehearsal", ours)
            self.assertTrue(baseline.endswith(case["turns"][0]))
            self.assertTrue(ours.endswith(case["turns"][0]))
            for later in case["turns"][1:]:
                self.assertNotIn(later, baseline)
                self.assertNotIn(later, ours)

    def test_command_builder_uses_explicit_id_without_last_or_ephemeral(self):
        first = RUNNER["build_codex_command"](
            "codex-test", "gpt-5.6-sol", "medium", Path("first.txt")
        )
        resumed = RUNNER["build_codex_command"](
            "codex-test",
            "gpt-5.6-sol",
            "medium",
            Path("second.txt"),
            "thread-fixed-id",
        )
        self.assertNotIn("resume", first)
        self.assertEqual(resumed[:3], ["codex-test", "exec", "resume"])
        self.assertIn("thread-fixed-id", resumed)
        for command in (first, resumed):
            self.assertNotIn("--last", command)
            self.assertNotIn("--ephemeral", command)
            self.assertIn('sandbox_mode="read-only"', command)

    def test_rejects_injected_baseline_fixture_file(self):
        injected = self.run_dir / "prepared" / "fixtures" / "baseline" / "injected.txt"
        injected.write_text("not allowed", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "fixture files"):
            RUNNER["verify_execution_fixtures"](self.run_dir, self.frozen)

    def test_rejects_wrong_skill_bytes_in_execution_fixture(self):
        skill = (
            self.run_dir
            / "prepared"
            / "fixtures"
            / "ours"
            / ".agents"
            / "skills"
            / "conversation-rehearsal"
            / "SKILL.md"
        )
        skill.write_text(skill.read_text(encoding="utf-8") + "tampered", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "skill hash"):
            RUNNER["verify_execution_fixtures"](self.run_dir, self.frozen)

    def test_valid_run_builds_anonymous_trajectory_packet(self):
        self.write_valid_run()
        summary = SUMMARY["summarize_native_resume"](self.run_dir, ROOT)
        packet_text = (self.run_dir / "blind-review.json").read_text(encoding="utf-8")
        packet = json.loads(packet_text)
        key = json.loads((self.run_dir / "blind-review-key.json").read_text(encoding="utf-8"))
        self.assertTrue(summary["infrastructure_valid"])
        self.assertEqual(summary["status"], "awaiting-human-review")
        self.assertEqual(summary["trajectory_count"], 12)
        self.assertEqual(summary["turn_count"], 28)
        self.assertEqual(len(packet["items"]), 6)
        self.assertNotIn('"arm_id"', packet_text)
        self.assertNotIn('"skill"', packet_text)
        self.assertNotIn("randomization_salt", packet_text)
        self.assertIn("randomization_salt", key)
        first = packet["items"][0]
        case = next(case for case in self.cases if case["id"] == first["case_id"])
        self.assertEqual(
            [item["user_message"] for item in first["user_turns"]], case["turns"]
        )
        self.assertTrue(all("turns" in candidate for candidate in first["candidates"]))

    def write_all_true_review(self):
        self.write_valid_run(repetitions=3)
        SUMMARY["summarize_native_resume"](self.run_dir, ROOT)
        form_path = self.run_dir / "completed-review.json"
        form = json.loads(
            (self.run_dir / "blind-review-form.json").read_text(encoding="utf-8")
        )
        form["reviewer"] = {"kind": "synthetic-unit-test"}
        for review in form["reviews"]:
            for candidate_id in review["criteria_pass"]:
                review["criteria_pass"][candidate_id] = [True, True, True, True]
            review["preferred_candidate"] = None
            review["notes"] = "synthetic all-pass fixture"
        write_json(form_path, form)
        SCORE["score_review"](self.run_dir, form_path)
        return form_path, self.run_dir / "review-result-completed-review.json"

    def test_frozen_candidate_gate_requires_both_cases_in_a_mechanism(self):
        self.write_valid_run(repetitions=3)
        SUMMARY["summarize_native_resume"](self.run_dir, ROOT)
        form_path = self.run_dir / "completed-review.json"
        form = json.loads(
            (self.run_dir / "blind-review-form.json").read_text(encoding="utf-8")
        )
        key = json.loads(
            (self.run_dir / "blind-review-key.json").read_text(encoding="utf-8")
        )
        packet = json.loads(
            (self.run_dir / "blind-review.json").read_text(encoding="utf-8")
        )
        mapping_by_review = {
            item["review_id"]: {
                candidate["candidate_id"]: candidate["arm_id"]
                for candidate in item["candidates"]
            }
            for item in key["items"]
        }
        mechanism_by_review = {
            item["review_id"]: item["mechanism"] for item in packet["items"]
        }
        for review in form["reviews"]:
            repetition = int(review["review_id"].rsplit("-r", 1)[1])
            for candidate_id in review["criteria_pass"]:
                scores = [True, True, True, True]
                if (
                    mechanism_by_review[review["review_id"]] == "phase-boundary"
                    and mapping_by_review[review["review_id"]][candidate_id] == "ours"
                    and repetition in {1, 2}
                ):
                    scores[0] = False
                review["criteria_pass"][candidate_id] = scores
            review["preferred_candidate"] = None
            review["notes"] = "synthetic gate fixture"
        form["reviewer"] = {"kind": "synthetic-unit-test"}
        write_json(form_path, form)
        scored = SCORE["score_review"](self.run_dir, form_path)
        result_path = self.run_dir / "review-result-completed-review.json"
        self.assertEqual(scored["status"], "reviewed")
        analysis = ANALYZE["analyze_review"](
            self.run_dir, form_path, result_path, root=ROOT
        )
        self.assertEqual(
            analysis["candidate_gate"]["qualifying_mechanisms"],
            ["phase-boundary"],
        )
        self.assertTrue(analysis["candidate_gate"]["triggered"])
        self.assertTrue(analysis["decision"]["candidate_design_opened"])
        self.assertFalse(analysis["decision"]["skill_changed"])

    def test_analyzer_rejects_packet_case_swap_with_updated_summary_hash(self):
        form_path, result_path = self.write_all_true_review()
        packet_path = self.run_dir / "blind-review.json"
        packet = json.loads(packet_path.read_text(encoding="utf-8"))
        first = packet["items"][0]
        other = next(
            item for item in packet["items"] if item["case_id"] != first["case_id"]
        )
        first["user_turns"], other["user_turns"] = (
            other["user_turns"],
            first["user_turns"],
        )
        write_json(packet_path, packet)
        summary_path = self.run_dir / "summary.json"
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        summary["blind_review"]["packet_sha256"] = sha256_bytes(packet_path.read_bytes())
        write_json(summary_path, summary)
        with self.assertRaisesRegex(ValueError, "packet does not match native trajectories"):
            ANALYZE["analyze_review"](
                self.run_dir, form_path, result_path, root=ROOT
            )

    def test_analyzer_rejects_key_mapping_two_candidates_to_ours(self):
        form_path, result_path = self.write_all_true_review()
        key_path = self.run_dir / "blind-review-key.json"
        key = json.loads(key_path.read_text(encoding="utf-8"))
        first = key["items"][0]["candidates"]
        ours = next(candidate for candidate in first if candidate["arm_id"] == "ours")
        baseline = next(candidate for candidate in first if candidate["arm_id"] == "baseline")
        baseline["arm_id"] = "ours"
        baseline["skill"] = ours["skill"]
        baseline["skill_package_sha256"] = ours["skill_package_sha256"]
        write_json(key_path, key)
        summary_path = self.run_dir / "summary.json"
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        summary["blind_review"]["key_sha256"] = sha256_bytes(key_path.read_bytes())
        write_json(summary_path, summary)
        with self.assertRaisesRegex(ValueError, "key does not match native trajectories"):
            ANALYZE["analyze_review"](
                self.run_dir, form_path, result_path, root=ROOT
            )

    def test_analyzer_rejects_forged_key_trajectory_and_thread(self):
        form_path, result_path = self.write_all_true_review()
        key_path = self.run_dir / "blind-review-key.json"
        key = json.loads(key_path.read_text(encoding="utf-8"))
        mapping = key["items"][0]["candidates"][0]
        mapping["trajectory_id"] = "forged-trajectory"
        mapping["thread_id"] = "forged-thread"
        write_json(key_path, key)
        summary_path = self.run_dir / "summary.json"
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        summary["blind_review"]["key_sha256"] = sha256_bytes(key_path.read_bytes())
        write_json(summary_path, summary)
        with self.assertRaisesRegex(ValueError, "key does not match native trajectories"):
            ANALYZE["analyze_review"](
                self.run_dir, form_path, result_path, root=ROOT
            )

    def test_analyzer_rejects_duplicate_scored_review_id(self):
        form_path, result_path = self.write_all_true_review()
        scored = json.loads(result_path.read_text(encoding="utf-8"))
        scored["items"].append(copy.deepcopy(scored["items"][0]))
        write_json(result_path, scored)
        with self.assertRaisesRegex(ValueError, "duplicate review_id"):
            ANALYZE["analyze_review"](
                self.run_dir, form_path, result_path, root=ROOT
            )

    def test_rejects_changed_output_without_hash_update(self):
        trajectories = self.write_valid_run()
        trajectories[0]["turns"][0]["raw_output"] += " tampered"
        self.rewrite_results(trajectories)
        with self.assertRaisesRegex(ValueError, "output hash"):
            SUMMARY["normalize_trajectories"](self.run_dir, ROOT)

    def test_rejects_output_rewritten_with_new_hash_but_old_event(self):
        trajectories = self.write_valid_run()
        turn = trajectories[0]["turns"][0]
        turn["raw_output"] += " coordinated-change"
        turn["output_sha256"] = sha256_bytes(turn["raw_output"].encode("utf-8"))
        self.rewrite_results(trajectories)
        with self.assertRaisesRegex(ValueError, "output-to-event binding"):
            SUMMARY["normalize_trajectories"](self.run_dir, ROOT)
    def test_rejects_ideal_or_other_output_in_prior_hash_chain(self):
        trajectories = self.write_valid_run()
        target = next(item for item in trajectories if len(item["turns"]) > 1)
        target["turns"][1]["prior_output_sha256"] = ["0" * 64]
        self.rewrite_results(trajectories)
        with self.assertRaisesRegex(ValueError, "prior-output hash chain"):
            SUMMARY["normalize_trajectories"](self.run_dir, ROOT)

    def test_rejects_replayed_history_instead_of_current_resume_message(self):
        trajectories = self.write_valid_run()
        target = next(item for item in trajectories if len(item["turns"]) > 1)
        turn = target["turns"][1]
        turn["submitted_prompt"] = target["turns"][0]["raw_output"] + "\n" + turn["submitted_prompt"]
        turn["prompt_sha256"] = sha256_bytes(turn["submitted_prompt"].encode("utf-8"))
        self.rewrite_results(trajectories)
        with self.assertRaisesRegex(ValueError, "prepared/current user message"):
            SUMMARY["normalize_trajectories"](self.run_dir, ROOT)

    def test_rejects_swapped_or_missing_turn(self):
        trajectories = self.write_valid_run()
        target = next(item for item in trajectories if len(item["turns"]) == 3)
        target["turns"][0], target["turns"][1] = target["turns"][1], target["turns"][0]
        self.rewrite_results(trajectories)
        with self.assertRaisesRegex(ValueError, "missing or out of order"):
            SUMMARY["normalize_trajectories"](self.run_dir, ROOT)

    def test_rejects_cross_trajectory_thread_reuse(self):
        trajectories = self.write_valid_run()
        source_id = trajectories[0]["thread_id"]
        target = trajectories[1]
        target["thread_id"] = source_id
        for index, turn in enumerate(target["turns"], 1):
            turn["thread_id"] = source_id
            turn["event_thread_ids"] = [source_id]
            turn["expected_thread_id"] = None if index == 1 else source_id
            events = self.events(source_id, turn["raw_output"])
            turn["raw_events"] = events
            turn["events_sha256"] = sha256_bytes(events.encode("utf-8"))
            if index > 1:
                old_id = next(part for part in turn["command"] if part.startswith("thread-"))
                turn["command"][turn["command"].index(old_id)] = source_id
        self.rewrite_results(trajectories)
        with self.assertRaisesRegex(ValueError, "reused across trajectories"):
            SUMMARY["normalize_trajectories"](self.run_dir, ROOT)

    def test_rejects_fake_selector_when_real_id_is_hidden_elsewhere(self):
        trajectories = self.write_valid_run()
        target = next(item for item in trajectories if len(item["turns"]) > 1)
        command = target["turns"][1]["command"]
        expected = target["thread_id"]
        command[-2] = "fake-thread-id"
        command.insert(5, expected)
        self.rewrite_results(trajectories)
        with self.assertRaisesRegex(ValueError, "invalid explicit thread selector"):
            SUMMARY["normalize_trajectories"](self.run_dir, ROOT)

    def test_rejects_arm_package_injection_mismatch(self):
        trajectories = self.write_valid_run()
        ours = next(item for item in trajectories if item["arm_id"] == "ours")
        ours["skill_package_sha256"] = None
        self.rewrite_results(trajectories)
        with self.assertRaisesRegex(ValueError, "skill package"):
            SUMMARY["normalize_trajectories"](self.run_dir, ROOT)

    def test_blind_packet_is_write_once(self):
        self.write_valid_run()
        SUMMARY["summarize_native_resume"](self.run_dir, ROOT)
        packet_path = self.run_dir / "blind-review.json"
        packet_path.write_text("{}\n", encoding="utf-8")
        with self.assertRaisesRegex(FileExistsError, "refusing to overwrite"):
            SUMMARY["summarize_native_resume"](self.run_dir, ROOT)


if __name__ == "__main__":
    unittest.main()

