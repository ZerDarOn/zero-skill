"""Protect the relationship comparison freeze, provenance, and blind-review inputs."""

import hashlib
import json
from pathlib import Path
import runpy
import tempfile
import unittest


BASE = (
    Path(__file__).resolve().parents[1]
    / "evaluations"
    / "comparisons"
    / "relationship-three-arm-04"
)
RUNNER = runpy.run_path(str(BASE / "run_comparison.py"))
UPSTREAM = (
    Path(__file__).resolve().parents[1]
    / "evaluations"
    / "fixtures"
    / "upstreams"
    / "love-helper"
    / "1e391e26fd1c1bfee06e4daa9b439086a098a49b"
)

ROUND_14_SKILL = (
    Path(__file__).resolve().parents[1]
    / "evaluations"
    / "comparisons"
    / "relationship-boundary-regression-06"
    / "packages"
    / "relationship-review-0.1.1"
)


class RelationshipComparisonTests(unittest.TestCase):
    def test_prompt_includes_complete_package_without_frozen_rubric(self):
        package = {
            "entrypoint": "SKILL.md",
            "files": {"SKILL.md": "入口说明", "references/example.md": "引用内容"},
        }
        prompt = RUNNER["build_prompt"]("共同约定", "用户任务", package)

        self.assertIn("入口说明", prompt)
        self.assertIn("引用内容", prompt)
        self.assertTrue(prompt.endswith("<USER_TASK>\n用户任务\n</USER_TASK>"))
        for case in json.loads((BASE / "cases.json").read_text(encoding="utf-8")):
            for criterion in case["hard_criteria"]:
                self.assertNotIn(criterion, prompt)

    def test_package_digest_uses_posix_name_order_and_length_framing(self):
        files = {"z.md": "最后", "a/ref.md": "先"}
        digest = hashlib.sha256()
        for name in sorted(files):
            for data in (name.encode("utf-8"), files[name].encode("utf-8")):
                digest.update(len(data).to_bytes(8, "big"))
                digest.update(data)

        self.assertEqual(RUNNER["package_digest"](files), digest.hexdigest())
        self.assertEqual(
            RUNNER["package_digest"](files),
            RUNNER["package_digest"](dict(reversed(list(files.items())))),
        )

    def test_upstream_provenance_accepts_exact_bytes_and_rejects_mutation(self):
        provenance = json.loads(
            (UPSTREAM / "provenance.json").read_text(encoding="utf-8")
        )
        RUNNER["validate_upstream"](provenance, UPSTREAM)

        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            for name in provenance["files"]:
                destination = root / name
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes((UPSTREAM / name).read_bytes())
            target = root / "relationship-copilot" / "SKILL.md"
            target.write_bytes(target.read_bytes() + b"\nmutated")

            with self.assertRaisesRegex(ValueError, "upstream bytes changed"):
                RUNNER["validate_upstream"](provenance, root)

    def test_invalid_attempts_do_not_enter_blind_quality_results(self):
        good = {
            "exit_code": 0,
            "raw_output": "回答",
            "turn_completed": True,
            "tool_items": [],
            "error": None,
        }
        self.assertTrue(RUNNER["valid_record"](good))
        for patch in [
            {"exit_code": 1},
            {"raw_output": " "},
            {"turn_completed": False},
            {"tool_items": [{"type": "command_execution"}]},
            {"error": "timeout; no retry"},
        ]:
            self.assertFalse(RUNNER["valid_record"]({**good, **patch}))


    def test_published_report_matches_frozen_sources_and_packages(self):
        report = json.loads(
            (
                Path(__file__).resolve().parents[1]
                / "evaluations"
                / "reports"
                / "relationship-three-arm-round-14-diagnostic.json"
            ).read_text(encoding="utf-8")
        )
        source_hashes = report["comparison"]["source_hashes"]
        for name, expected in source_hashes.items():
            self.assertEqual(RUNNER["sha256_file"](BASE / name), expected)

        provenance = json.loads(
            (UPSTREAM / "provenance.json").read_text(encoding="utf-8")
        )
        self.assertEqual(report["upstream"], provenance)
        RUNNER["validate_upstream"](provenance, UPSTREAM)

        arms = {item["arm_id"]: item for item in report["arms"]}
        self.assertEqual(report["comparison"]["records"], 18)
        self.assertEqual(report["comparison"]["valid_records"], 18)
        self.assertEqual(
            {
                arm_id: (
                    item["strict_blind_review"]["criteria_passed"],
                    item["strict_blind_review"]["criteria_total"],
                    item["strict_blind_review"]["perfect_outputs"],
                    item["strict_blind_review"]["preferred_count"],
                    item["metrics"]["usage"]["total_tokens"],
                )
                for arm_id, item in arms.items()
            },
            {
                "baseline": (19, 19, 6, 0, 91807),
                "ours": (19, 19, 6, 2, 100757),
                "upstream": (16, 19, 5, 0, 174983),
            },
        )

        recomputed = {
            arm_id: {
                "outputs": 0,
                "perfect_outputs": 0,
                "criteria_passed": 0,
                "criteria_total": 0,
                "preferred_count": 0,
            }
            for arm_id in arms
        }
        for review_item in report["items"]:
            preferred = review_item["preferred_candidate"]
            for candidate in review_item["candidates"]:
                self.assertEqual(
                    hashlib.sha256(candidate["output"].encode("utf-8")).hexdigest(),
                    candidate["output_sha256"],
                )
                arm = recomputed[candidate["arm_id"]]
                arm["outputs"] += 1
                arm["perfect_outputs"] += candidate["passed"] == candidate["total"]
                arm["criteria_passed"] += sum(candidate["criteria_pass"])
                arm["criteria_total"] += len(candidate["criteria_pass"])
                arm["preferred_count"] += preferred == candidate["candidate_id"]
        for arm_id, totals in recomputed.items():
            published = arms[arm_id]["strict_blind_review"]
            self.assertEqual(
                totals,
                {key: published[key] for key in totals},
            )
        ours_folder = ROUND_14_SKILL
        validator = runpy.run_path(
            str(Path(__file__).resolve().parents[1] / "scripts" / "validate_collection.py")
        )
        self.assertEqual(
            arms["ours"]["skill_package_sha256"],
            validator["package_fingerprint"](ours_folder),
        )
        upstream_files = {
            name: (UPSTREAM / name).read_text(encoding="utf-8")
            for name in RUNNER["UPSTREAM_RUNTIME_FILES"]
        }
        self.assertEqual(
            arms["upstream"]["skill_package_sha256"],
            RUNNER["package_digest"](upstream_files),
        )


if __name__ == "__main__":
    unittest.main()
