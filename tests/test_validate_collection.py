"""Exercise the collection's acceptance boundaries using synthetic packages."""

import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from validate_collection import package_fingerprint, validate_collection


class CollectionValidationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.collection = {
            "schema_version": 1,
            "categories": [{"id": "people", "title": "人物", "description": "人物分析"}],
            "forms": ["analysis"],
            "skills": [],
        }
        self.write_json("catalog/collection.json", self.collection)
        self.write_json("catalog/upstreams.json", {"schema_version": 1, "upstreams": []})

    def write_text(self, path, content):
        destination = self.root / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content, encoding="utf-8")

    def write_json(self, path, value):
        self.write_text(path, json.dumps(value, ensure_ascii=False))

    def save(self):
        self.write_json("catalog/collection.json", self.collection)

    def add_skill(self):
        record = {
            "id": "person-analysis", "category": "people", "form": "analysis",
            "version": "0.1.0", "path": "skills/people/person-analysis/SKILL.md",
            "status": "draft", "tags": ["evidence"], "upstream_ids": [],
            "evaluation": None, "evidence": None,
        }
        self.collection["skills"].append(record)
        self.write_text(record["path"], '---\nname: person-analysis\ndescription: "分析给定材料中的行为证据。"\n---\n\n根据证据讨论可能解释。\n')
        self.save()
        return record

    def errors(self):
        self.save()
        return "\n".join(validate_collection(self.root))

    def add_report(self, record):
        record["evaluation"] = "evaluations/cases/person-analysis.json"
        record["evidence"] = "evaluations/reports/person-analysis.json"
        record["status"] = "verified"
        self.write_json(record["evaluation"], {
            "schema_version": 1, "skill_id": record["id"], "stage": "active",
            "cases": [{"id": "basic", "prompt": "分析", "input": {"kind": "synthetic", "text": "你好"},
                       "expected_route": record["id"], "must_include": ["证据"], "must_avoid": ["武断"]}],
        })
        report = {
            "schema_version": 1, "skill_id": record["id"], "skill_version": record["version"],
            "package_sha256": package_fingerprint((self.root / record["path"]).parent),
            "cases_sha256": hashlib.sha256((self.root / record["evaluation"]).read_bytes()).hexdigest(),
            "run_date": "2026-09-08", "host": "test-host", "model": "test-model",
            "reviewer": "synthetic-reviewer", "comparison": "baseline-and-skill",
            "results": [{"case_id": "basic", "baseline_output": "基线", "skill_output": "证据说明",
                         "passed": True, "rationale": "只用于测试证据结构。"}],
        }
        self.write_json(record["evidence"], report)
        return report

    def test_empty_collection_is_valid_foundation(self):
        self.assertEqual(self.errors(), "")

    def test_registered_draft_is_valid(self):
        self.add_skill()
        self.assertEqual(self.errors(), "")

    def test_unknown_category_is_rejected(self):
        self.add_skill()["category"] = "unknown"
        self.assertIn("category", self.errors())

    def test_unregistered_package_is_rejected(self):
        self.add_skill()
        self.collection["skills"] = []
        self.assertIn("unregistered", self.errors())

    def test_duplicate_id_is_rejected(self):
        record = self.add_skill()
        self.collection["skills"].append(dict(record))
        self.assertIn("duplicate", self.errors())

    def test_path_escape_is_rejected(self):
        self.add_skill()["path"] = "../outside/SKILL.md"
        self.assertIn("path", self.errors())

    def test_cross_package_link_is_rejected(self):
        record = self.add_skill()
        self.write_text(record["path"], (self.root / record["path"]).read_text(encoding="utf-8") + "\n[external](../../../catalog/collection.json)\n")
        self.assertIn("escapes", self.errors())

    def test_missing_reference_is_rejected(self):
        record = self.add_skill()
        self.write_text(record["path"], (self.root / record["path"]).read_text(encoding="utf-8") + "\n[missing](references/missing.md)\n")
        self.assertIn("missing", self.errors())

    def test_unknown_upstream_is_rejected(self):
        self.add_skill()["upstream_ids"] = ["unknown"]
        self.assertIn("upstream", self.errors())

    def test_unfinished_template_is_rejected(self):
        record = self.add_skill()
        self.write_text(record["path"], (self.root / record["path"]).read_text(encoding="utf-8") + "\n{{unfinished}}\n")
        self.assertIn("placeholder", self.errors())

    def test_verified_requires_evidence(self):
        self.add_skill()["status"] = "verified"
        self.assertIn("verified", self.errors())

    def test_complete_synthetic_report_is_accepted(self):
        record = self.add_skill()
        self.add_report(record)
        self.assertEqual(self.errors(), "")

    def test_changed_reference_invalidates_report(self):
        record = self.add_skill()
        self.add_report(record)
        self.write_text("skills/people/person-analysis/references/evidence.md", "new instructions")
        self.assertIn("fingerprint", self.errors())

    def test_incomplete_case_results_are_rejected(self):
        record = self.add_skill()
        report = self.add_report(record)
        report["results"] = []
        self.write_json(record["evidence"], report)
        self.assertIn("coverage", self.errors())

    def test_changed_case_requirements_invalidate_report(self):
        record = self.add_skill()
        self.add_report(record)
        case_path = self.root / record["evaluation"]
        suite = json.loads(case_path.read_text(encoding="utf-8"))
        suite["cases"][0]["must_include"] = ["different requirement"]
        self.write_json(record["evaluation"], suite)
        self.assertIn("cases fingerprint", self.errors())

    def test_malformed_json_is_reported(self):
        self.write_text("catalog/collection.json", "{broken")
        self.assertIn("JSON", "\n".join(validate_collection(self.root)))

    def test_wrong_record_type_is_reported(self):
        self.collection["skills"] = [42]
        self.assertIn("object", self.errors())


if __name__ == "__main__":
    unittest.main()
