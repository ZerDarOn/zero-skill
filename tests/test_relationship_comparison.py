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


if __name__ == "__main__":
    unittest.main()
