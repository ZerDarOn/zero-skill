"""Test safe, deterministic local skill exports with synthetic repositories."""

import json
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import export_skills
from export_skills import ExportBatchError, ExportError, export_selected, list_exportable
from validate_collection import package_fingerprint


class ExportSkillsTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.skill_dir = self.root / "skills/people/sample-skill"
        (self.skill_dir / "references").mkdir(parents=True)
        (self.skill_dir / "SKILL.md").write_text(
            '---\nname: sample-skill\ndescription: "合成技能。"\n---\n\n[示例](references/example.md)\n',
            encoding="utf-8",
        )
        (self.skill_dir / "references/example.md").write_text("合成引用。\n", encoding="utf-8")
        self.record = {
            "id": "sample-skill", "category": "people", "form": "analysis",
            "version": "0.1.0", "path": "skills/people/sample-skill/SKILL.md",
            "status": "experimental", "tags": [], "upstream_ids": ["source-a"],
            "evaluation": None, "evidence": None,
        }
        self.write_collection([self.record])

    def write_collection(self, skills):
        path = self.root / "catalog/collection.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"schema_version": 1, "skills": skills}), encoding="utf-8")

    def test_list_reads_catalog_without_writing(self):
        self.assertEqual(list_exportable(self.root), [("sample-skill", "0.1.0", "experimental")])
        self.assertFalse((self.root / "dist").exists())

    def test_unknown_and_ineligible_skills_are_rejected(self):
        with self.assertRaisesRegex(ExportError, "unknown"):
            export_selected(self.root, ["missing"], self.root / "dist")
        for status in ("draft", "archived"):
            self.record["status"] = status
            self.write_collection([self.record])
            with self.assertRaisesRegex(ExportError, "not exportable"):
                export_selected(self.root, ["sample-skill"], self.root / "dist")
        self.assertFalse((self.root / "dist").exists())

    def test_traversal_and_unexpected_files_are_rejected(self):
        escaped = dict(self.record, path="../outside/SKILL.md")
        self.write_collection([escaped])
        with self.assertRaisesRegex(ExportError, "path"):
            export_selected(self.root, ["sample-skill"], self.root / "dist")
        self.write_collection([self.record])
        (self.skill_dir / ".env").write_text("TOKEN=synthetic", encoding="utf-8")
        with self.assertRaisesRegex(ExportError, "unexpected"):
            export_selected(self.root, ["sample-skill"], self.root / "dist")

    def test_symlink_is_rejected_when_supported(self):
        target = self.root / "outside.txt"
        target.write_text("outside", encoding="utf-8")
        link = self.skill_dir / "references/link.md"
        try:
            link.symlink_to(target)
        except (OSError, NotImplementedError) as error:
            self.skipTest(f"symlink unavailable: {error}")
        with self.assertRaisesRegex(ExportError, "link|reparse"):
            export_selected(self.root, ["sample-skill"], self.root / "dist")

    def test_export_contains_exact_package_and_external_manifest(self):
        output = export_selected(self.root, ["sample-skill"], self.root / "dist")[0]
        with zipfile.ZipFile(output) as archive:
            self.assertEqual(
                archive.namelist(),
                ["bundle-manifest.json", "sample-skill/SKILL.md", "sample-skill/references/example.md"],
            )
            manifest = json.loads(archive.read("bundle-manifest.json"))
            self.assertEqual(manifest["package_sha256"], package_fingerprint(self.skill_dir))
            self.assertEqual(manifest["status"], "experimental")
            self.assertEqual(manifest["upstream_ids"], ["source-a"])
            self.assertEqual(
                archive.read("sample-skill/references/example.md"),
                (self.skill_dir / "references/example.md").read_bytes(),
            )
            self.assertNotIn("bundle-manifest.json", manifest["files"])

    def test_collision_and_batch_preflight_preserve_existing_outputs(self):
        with self.assertRaisesRegex(ExportError, "duplicate"):
            export_selected(self.root, ["sample-skill", "sample-skill"], self.root / "duplicate")
        self.assertFalse((self.root / "duplicate").exists())

        second = dict(self.record, id="second-skill", path="skills/people/second-skill/SKILL.md")
        second_dir = self.root / "skills/people/second-skill"
        second_dir.mkdir(parents=True)
        (second_dir / "SKILL.md").write_text("---\nname: second-skill\ndescription: \"合成。\"\n---\n\n内容。\n", encoding="utf-8")
        self.write_collection([self.record, second])
        dist = self.root / "dist"
        dist.mkdir()
        collision = dist / "second-skill-0.1.0.zip"
        collision.write_bytes(b"keep")
        with self.assertRaisesRegex(ExportError, "exists"):
            export_selected(self.root, ["sample-skill", "second-skill"], dist)
        self.assertEqual(collision.read_bytes(), b"keep")
        self.assertFalse((dist / "sample-skill-0.1.0.zip").exists())

    def test_same_input_produces_identical_zip_bytes(self):
        first = export_selected(self.root, ["sample-skill"], self.root / "one")[0]
        second = export_selected(self.root, ["sample-skill"], self.root / "two")[0]
        self.assertEqual(first.read_bytes(), second.read_bytes())

    @unittest.skipUnless(os.name == "nt", "Windows junction test")
    def test_output_and_source_junctions_are_rejected(self):
        outside = self.root / "outside-output"
        outside.mkdir()
        junction = self.root / "dist"
        result = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(junction), str(outside)],
            capture_output=True,
        )
        if result.returncode:
            self.skipTest("junction creation unavailable")
        with self.assertRaisesRegex(ExportError, "reparse|link|output"):
            export_selected(self.root, ["sample-skill"], junction)
        self.assertEqual(list(outside.iterdir()), [])

        junction.rmdir()
        external_skills = self.root / "outside-skills"
        shutil.move(str(self.root / "skills/people"), external_skills)
        result = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(self.root / "skills/people"), str(external_skills)],
            capture_output=True,
        )
        if result.returncode:
            self.skipTest("source junction creation unavailable")
        with self.assertRaisesRegex(ExportError, "reparse|link"):
            export_selected(self.root, ["sample-skill"], self.root / "safe-output")

    def test_source_mutation_after_manifest_does_not_split_archive_snapshot(self):
        original = export_skills._build_manifest

        def mutate_after_manifest(record, package, snapshot):
            manifest = original(record, package, snapshot)
            (package / "references/example.md").write_text("changed later", encoding="utf-8")
            return manifest

        with mock.patch.object(export_skills, "_build_manifest", side_effect=mutate_after_manifest):
            output = export_selected(self.root, ["sample-skill"], self.root / "dist")[0]
        with zipfile.ZipFile(output) as archive:
            manifest = json.loads(archive.read("bundle-manifest.json"))
            frozen = archive.read("sample-skill/references/example.md")
            self.assertEqual(hashlib.sha256(frozen).hexdigest(), manifest["files"]["references/example.md"])

    def test_runtime_batch_failure_reports_prior_success(self):
        second = dict(self.record, id="second-skill", path="skills/people/second-skill/SKILL.md")
        second_dir = self.root / "skills/people/second-skill"
        second_dir.mkdir(parents=True)
        (second_dir / "SKILL.md").write_text("---\nname: second-skill\ndescription: \"合成。\"\n---\n\n内容。\n", encoding="utf-8")
        self.write_collection([self.record, second])
        real_link = os.link
        calls = 0

        def fail_second(source, destination):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError("synthetic publish failure")
            return real_link(source, destination)

        with mock.patch.object(export_skills.os, "link", side_effect=fail_second):
            with self.assertRaises(ExportBatchError) as caught:
                export_selected(self.root, ["sample-skill", "second-skill"], self.root / "dist")
        self.assertEqual([path.name for path in caught.exception.outputs], ["sample-skill-0.1.0.zip"])
        self.assertTrue((self.root / "dist/sample-skill-0.1.0.zip").is_file())
        self.assertFalse((self.root / "dist/second-skill-0.1.0.zip").exists())


if __name__ == "__main__":
    unittest.main()
