"""Tests for deterministic anonymous Obsidian artifact prefill."""

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
    / "obsidian-artifact-preservation-three-arm-16"
)
MODULE = runpy.run_path(str(COMPARISON / "prefill_artifact_review.py"))


class ObsidianArtifactComparisonTests(unittest.TestCase):
    def test_exact_note_match_allows_only_missing_terminal_lf(self):
        match = MODULE["exact_note_match"]
        expected = "# Note\n\nBody\n"
        self.assertTrue(match(expected, expected))
        self.assertTrue(match(expected.removesuffix("\n"), expected))
        self.assertFalse(match(expected + "\n", expected))
        self.assertFalse(match("# Note\nBody\n", expected))
        self.assertFalse(match("# Note\r\n\r\nBody\r\n", expected))
        with self.assertRaisesRegex(ValueError, "exactly one LF"):
            match("Body", "Body")

    def test_prefill_is_anonymous_and_leaves_semantic_criteria_blank(self):
        expected = "# Note\n\nBody\n"
        cases = [
            {
                "id": "case-one",
                "expected_note": expected,
                "hard_criteria": ["exact", "meaning", "protected", "message"],
            }
        ]
        packet = {
            "schema_version": 1,
            "comparison_id": MODULE["COMPARISON_ID"],
            "items": [
                {
                    "review_id": "case-one-r1",
                    "case_id": "case-one",
                    "repetition": 1,
                    "hard_criteria": cases[0]["hard_criteria"],
                    "candidates": [
                        {
                            "candidate_id": "A",
                            "output": json.dumps(
                                {"note": expected, "message": "Changed one line."}
                            ),
                        },
                        {
                            "candidate_id": "B",
                            "output": json.dumps(
                                {"note": expected.removesuffix("\n"), "message": "Done."}
                            ),
                        },
                        {
                            "candidate_id": "C",
                            "output": "```json\n{}\n```",
                        },
                    ],
                }
            ],
        }
        form = {
            "schema_version": 1,
            "comparison_id": MODULE["COMPARISON_ID"],
            "reviews": [
                {
                    "review_id": "case-one-r1",
                    "criteria_pass": {
                        "A": [None, None, None, None],
                        "B": [None, None, None, None],
                        "C": [None, None, None, None],
                    },
                    "preferred_candidate": None,
                    "notes": "",
                }
            ],
        }
        checks, prefilled = MODULE["build_prefill"](packet, form, cases)
        scores = prefilled["reviews"][0]["criteria_pass"]
        self.assertEqual(scores["A"], [True, None, None, None])
        self.assertEqual(scores["B"], [True, None, None, None])
        self.assertEqual(scores["C"], [False, None, None, None])
        self.assertFalse(checks["arm_mapping_opened"])
        self.assertNotIn("arm_id", json.dumps(checks))
        candidates = checks["items"][0]["candidates"]
        self.assertEqual([item["artifact_exact"] for item in candidates], [True, True, False])
        self.assertEqual(candidates[2]["parse_error"], "invalid-json")
        self.assertEqual(
            candidates[0]["expected_note_sha256"],
            hashlib.sha256(expected.encode("utf-8")).hexdigest(),
        )

    def test_schema_checks_are_recorded_without_polluting_exact_note_result(self):
        parse = MODULE["parse_submission"]
        exact_with_extra = parse(
            json.dumps({"note": "Body\n", "message": "Done.", "extra": True})
        )
        self.assertTrue(exact_with_extra["parse_valid"])
        self.assertFalse(exact_with_extra["schema_valid"])
        self.assertEqual(exact_with_extra["error"], "unexpected-object-keys")
        self.assertEqual(exact_with_extra["note"], "Body\n")
        self.assertFalse(parse("[]")["schema_valid"])
        self.assertEqual(parse("[]")["error"], "root-not-object")
        self.assertEqual(parse('{"note": 7, "message": "x"}')["error"], "note-not-string")

    def test_prefill_rejects_identity_fields_in_packet_or_form(self):
        cases = [
            {
                "id": "case-one",
                "expected_note": "Body\n",
                "hard_criteria": ["exact"],
            }
        ]
        packet = {
            "comparison_id": MODULE["COMPARISON_ID"],
            "items": [
                {
                    "review_id": "case-one-r1",
                    "case_id": "case-one",
                    "repetition": 1,
                    "hard_criteria": ["exact"],
                    "candidates": [
                        {
                            "candidate_id": "A",
                            "output": '{"note":"Body\\n","message":"Done"}',
                            "arm_id": "ours",
                        }
                    ],
                }
            ],
        }
        form = {
            "comparison_id": MODULE["COMPARISON_ID"],
            "reviews": [
                {
                    "review_id": "case-one-r1",
                    "criteria_pass": {"A": [None]},
                    "preferred_candidate": None,
                    "notes": "",
                }
            ],
        }
        with self.assertRaisesRegex(ValueError, "blind packet exposes.*arm_id"):
            MODULE["build_prefill"](packet, form, cases)
        del packet["items"][0]["candidates"][0]["arm_id"]
        form["reviews"][0]["skill_package_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "blind form exposes"):
            MODULE["build_prefill"](packet, form, cases)

    def test_prepared_prompts_exclude_expected_artifacts_and_rubric(self):
        prepare = runpy.run_path(
            str(ROOT / "evaluations" / "promptfoo" / "prepare_skill_comparison.py")
        )
        cases = json.loads((COMPARISON / "cases.json").read_text(encoding="utf-8"))
        case_by_id = {case["id"]: case for case in cases}
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "prepared-run"
            prepare["prepare_comparison"](
                repo_root=ROOT,
                spec_path=COMPARISON / "promptfoo.json",
                output_dir=output,
            )
            tests = json.loads(
                (output / "prepared" / "tests.json").read_text(encoding="utf-8")
            )
            frozen = json.loads((output / "frozen.json").read_text(encoding="utf-8"))
            prepared_license = (
                output
                / "prepared"
                / "fixtures"
                / "upstream"
                / ".agents"
                / "skills"
                / "obsidian-markdown"
                / "LICENSE"
            )
            source_license = (
                ROOT
                / "evaluations"
                / "fixtures"
                / "upstreams"
                / "obsidian-skills"
                / "a1dc48e68138490d522c04cbf5822214c6eb1202"
                / "LICENSE"
            )
            self.assertEqual(prepared_license.read_bytes(), source_license.read_bytes())
            upstream_arm = next(arm for arm in frozen["arms"] if arm["id"] == "upstream")
            self.assertIn("LICENSE", {item["path"] for item in upstream_arm["files"]})
        self.assertEqual(len(tests), 18)
        self.assertEqual(
            len(frozen["selected_case_ids"])
            * len(frozen["arms"])
            * frozen["repetitions"],
            54,
        )
        for test in tests:
            source = case_by_id[test["metadata"]["case_id"]]
            self.assertEqual(set(test["vars"]), {"prompt"})
            self.assertNotIn("expected_note", test["metadata"])
            self.assertNotIn("expected_note", test["vars"]["prompt"])
            self.assertNotIn("hard_criteria", test["vars"])
            self.assertFalse(
                any(
                    criterion in test["vars"]["prompt"]
                    for criterion in source["hard_criteria"]
                )
            )

    def test_prefill_run_rejects_frozen_cases_path_outside_repository(self):
        runs_root = ROOT / "evaluations" / "runs"
        with tempfile.TemporaryDirectory(dir=runs_root) as temporary:
            run_dir = Path(temporary)
            (run_dir / "frozen.json").write_text(
                json.dumps(
                    {
                        "comparison_id": MODULE["COMPARISON_ID"],
                        "cases_path": "../outside-cases.json",
                        "cases_sha256": "0" * 64,
                    }
                ),
                encoding="utf-8",
            )
            (run_dir / "summary.json").write_text(
                json.dumps({"blind_review": {}}), encoding="utf-8"
            )
            with self.assertRaisesRegex(
                ValueError, "frozen cases path must stay inside the repository"
            ):
                MODULE["prefill_run"](run_dir)

    def test_upstream_fixture_matches_fixed_commit_provenance(self):
        fixture = (
            ROOT
            / "evaluations"
            / "fixtures"
            / "upstreams"
            / "obsidian-skills"
            / "a1dc48e68138490d522c04cbf5822214c6eb1202"
        )
        provenance = json.loads((fixture / "provenance.json").read_text(encoding="utf-8"))
        self.assertEqual(
            provenance["repository"], "https://github.com/kepano/obsidian-skills"
        )
        self.assertEqual(
            provenance["commit"], "a1dc48e68138490d522c04cbf5822214c6eb1202"
        )
        self.assertEqual(provenance["license"], "MIT")
        self.assertIn("No source bytes changed", provenance["modifications"])
        self.assertIn("copied byte-for-byte", provenance["modifications"])
        self.assertEqual(
            set(provenance["files"]),
            {
                "LICENSE",
                "skills/obsidian-markdown/SKILL.md",
                "skills/obsidian-markdown/LICENSE",
                "skills/obsidian-markdown/references/CALLOUTS.md",
                "skills/obsidian-markdown/references/EMBEDS.md",
                "skills/obsidian-markdown/references/PROPERTIES.md",
            },
        )
        for name, evidence in provenance["files"].items():
            self.assertEqual(
                hashlib.sha256((fixture / name).read_bytes()).hexdigest(),
                evidence["sha256"],
            )
        self.assertEqual(
            (fixture / "skills" / "obsidian-markdown" / "LICENSE").read_bytes(),
            (fixture / "LICENSE").read_bytes(),
        )
        self.assertIn("MIT License", (fixture / "LICENSE").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
