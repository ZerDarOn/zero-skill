import json
from pathlib import Path
import runpy
import unittest

BASE = Path(__file__).resolve().parents[1] / "evaluations/comparisons/engineering-three-arm-01"
RUNNER = runpy.run_path(str(BASE / "run_comparison.py"))
VERIFIER = runpy.run_path(str(BASE / "verify_fixtures.py"))


class EngineeringComparisonTests(unittest.TestCase):
    def test_rejects_paths_and_invalid_source_before_application(self):
        parse = RUNNER["parse_submission"]
        self.assertEqual(
            parse('{"files":{"memo.py":"x = 1"},"done":false}', ["memo.py"])["files"]["memo.py"],
            "x = 1",
        )
        invalid = [
            '{"files":{"../memo.py":"x = 1"},"done":false}',
            '{"files":{"test_public.py":""},"done":false}',
            '{"files":{"memo.py":7},"done":false}',
            '{"files":{},"done":"true"}',
        ]
        for submission in invalid:
            with self.assertRaises(ValueError):
                parse(submission, ["memo.py"])
        with self.assertRaises(SyntaxError):
            parse('{"files":{"memo.py":"def"},"done":false}', ["memo.py"])

    def test_empty_skipped_and_failed_suites_do_not_count_as_acceptance(self):
        good = {"exit_code": 0, "error": None, "has_skips": False, "tests_run": 5}
        self.assertTrue(RUNNER["tests_pass"](good, 5))
        for change in [
            {"tests_run": 0},
            {"tests_run": 4},
            {"exit_code": 1},
            {"error": "timeout"},
            {"has_skips": True},
        ]:
            self.assertFalse(RUNNER["tests_pass"]({**good, **change}, 5))

    def test_current_fixture_verification_matches_normalized_sources(self):
        report = json.loads((BASE / "fixture-verification-current.json").read_text(encoding="utf-8"))
        self.assertEqual(report["fixture_tree_sha256"], VERIFIER["fixture_fingerprint"]())
        self.assertEqual(len(report["results"]), 8)
        self.assertTrue(
            all(item["expectation_met"] and item["tests_run"] > 0 for item in report["results"])
        )
        current_hashes = {
            path.relative_to(BASE).as_posix(): VERIFIER["sha256"](path.read_bytes())
            for path in VERIFIER["fixture_files"]()
        }
        self.assertEqual(report["source_sha256"], current_hashes)


if __name__ == "__main__":
    unittest.main()
