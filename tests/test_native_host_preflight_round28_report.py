"""Integrity checks for the Round 28 native host sandbox report."""

import hashlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = (
    ROOT / "evaluations" / "reports" / "native-host-sandbox-preflight-round-28.json"
)
IGNORED_RUN = (
    ROOT
    / "evaluations"
    / "runs"
    / "native-host-sandbox-preflight-20260913-v3"
)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class NativeHostPreflightRound28ReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))

    def test_report_preserves_zero_model_scope_and_skill_boundaries(self):
        self.assertFalse(self.report["scope"]["quality_scored"])
        self.assertEqual(self.report["scope"]["model_calls"], 0)
        self.assertEqual(self.report["scope"]["business_trajectories"], 0)
        decision = self.report["decision"]
        self.assertEqual(decision["status"], "host-sandbox-unhealthy")
        self.assertFalse(decision["implicit_business_comparison_authorized"])
        self.assertFalse(decision["model_run_started"])
        for field in (
            "quality_claim_changed",
            "skill_changed",
            "version_changed",
            "catalog_changed",
            "evidence_changed",
        ):
            self.assertFalse(decision[field])

    def test_canary_and_doctor_agree_on_provisioning_failure(self):
        canary = self.report["host"]["canary"]
        doctor = self.report["host"]["doctor_sandbox"]
        self.assertFalse(canary["passed"])
        self.assertEqual(canary["status"], "sandbox-provisioning-failed")
        self.assertEqual(canary["error_code"], "helper_unknown_error")
        self.assertEqual(doctor["status"], "fail")
        self.assertEqual(doctor["error_code"], canary["error_code"])
        self.assertEqual(doctor["sandbox_provisioning"], "failed")
        self.assertFalse(
            self.report["decision"]["endpoint_protection_confirmed_as_root_cause"]
        )

    def test_source_and_prior_report_hashes_match(self):
        protocol = self.report["protocol"]
        self.assertEqual(sha256_file(ROOT / protocol["path"]), protocol["sha256"])
        for item in self.report["implementation"].values():
            if isinstance(item, dict) and "path" in item:
                self.assertEqual(sha256_file(ROOT / item["path"]), item["sha256"])
        prior = self.report["round_27_correlation"]
        self.assertEqual(
            sha256_file(ROOT / prior["report_path"]), prior["report_sha256"]
        )
        review = self.report["review_chain"]["final_independent_review"]
        self.assertEqual(sha256_file(ROOT / review["path"]), review["sha256"])
        self.assertEqual(review["open_p0_p3_findings"], 0)

    def test_evidence_projection_hash_is_reproducible(self):
        projection = {
            "host": self.report["host"],
            "hypotheses": self.report["hypotheses"],
            "decision": self.report["decision"],
        }
        encoded = json.dumps(
            projection,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        self.assertEqual(
            hashlib.sha256(encoded).hexdigest(),
            self.report["evidence_projection"]["sha256"],
        )

    def test_public_report_contains_no_absolute_user_or_workspace_path(self):
        rendered = REPORT_PATH.read_text(encoding="utf-8")
        self.assertNotIn("C:\\\\Users\\\\", rendered)
        self.assertNotIn("D:\\\\Code\\\\", rendered)
        self.assertNotIn("15005", rendered)

    def test_ignored_run_matches_public_projection_when_present(self):
        if not IGNORED_RUN.is_dir():
            self.skipTest("ignored Round 28 host run is not available")
        canary_path = IGNORED_RUN / "host-sandbox-preflight.json"
        doctor_path = IGNORED_RUN / "doctor-sandbox-projection.json"
        run_meta_path = IGNORED_RUN / "run-meta.json"
        self.assertEqual(
            json.loads(canary_path.read_text(encoding="utf-8")),
            self.report["host"]["canary"],
        )
        self.assertEqual(
            json.loads(doctor_path.read_text(encoding="utf-8")),
            self.report["host"]["doctor_sandbox"],
        )
        artifacts = self.report["ignored_run"]
        self.assertEqual(sha256_file(canary_path), artifacts["host_sandbox_preflight_sha256"])
        self.assertEqual(
            sha256_file(doctor_path), artifacts["doctor_sandbox_projection_sha256"]
        )
        self.assertEqual(sha256_file(run_meta_path), artifacts["run_meta_sha256"])
        run_meta = json.loads(run_meta_path.read_text(encoding="utf-8"))
        self.assertEqual(run_meta["model_calls"], 0)
        self.assertEqual(run_meta["retries"], 0)


if __name__ == "__main__":
    unittest.main()
