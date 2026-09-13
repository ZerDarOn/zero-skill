"""Regression tests for the native Codex host sandbox preflight."""

import hashlib
import json
from pathlib import Path
import runpy
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
PREFLIGHT = runpy.run_path(
    str(ROOT / "evaluations" / "native_resume" / "preflight_host_sandbox.py")
)
WRAPPER = runpy.run_path(
    str(
        ROOT
        / "evaluations"
        / "native_resume"
        / "run_native_resume_with_host_preflight.py"
    )
)


class NativeHostPreflightTests(unittest.TestCase):
    def test_command_uses_restricted_builtin_profile_and_synthetic_probe(self):
        command = PREFLIGHT["build_windows_canary_command"](
            "codex-test", Path("D:/synthetic-workspace")
        )

        self.assertEqual(command[0:2], ["codex-test", "sandbox"])
        self.assertIn(":read-only", command)
        self.assertIn("Get-Location", " ".join(command))
        self.assertNotIn(":danger-full-access", command)
        self.assertNotIn("--dangerously-bypass-approvals-and-sandbox", command)

    def test_exact_canary_success_is_ready(self):
        result = PREFLIGHT["classify_windows_canary"](
            0,
            (PREFLIGHT["CANARY_TOKEN"] + "\r\n").encode("utf-8"),
            b"",
            None,
        )

        self.assertTrue(result["passed"])
        self.assertEqual(result["status"], "ready")
        self.assertIsNone(result["error_code"])

    def test_failure_stderr_wins_over_zero_exit_and_exact_token(self):
        result = PREFLIGHT["classify_windows_canary"](
            0,
            (PREFLIGHT["CANARY_TOKEN"] + "\n").encode("utf-8"),
            b"windows sandbox failed: helper_unknown_error: apply deny-read ACLs\n",
            None,
        )

        self.assertFalse(result["passed"])
        self.assertEqual(result["status"], "sandbox-provisioning-failed")

    def test_zero_exit_with_wrong_output_is_not_accepted(self):
        result = PREFLIGHT["classify_windows_canary"](
            0,
            b"plausible but wrong\n",
            b"",
            None,
        )

        self.assertFalse(result["passed"])
        self.assertEqual(result["status"], "canary-output-mismatch")

    def test_acl_helper_failure_is_classified_without_losing_error_code(self):
        stderr = (
            "windows sandbox failed: helper_unknown_error: apply deny-read ACLs\r\n"
        ).encode("utf-8")
        result = PREFLIGHT["classify_windows_canary"](1, b"", stderr, None)

        self.assertFalse(result["passed"])
        self.assertEqual(result["status"], "sandbox-provisioning-failed")
        self.assertEqual(result["error_code"], "helper_unknown_error")
        self.assertEqual(result["error_detail"], "apply deny-read ACLs")

    def test_policy_block_is_distinct_from_sandbox_provisioning_failure(self):
        result = PREFLIGHT["classify_windows_canary"](
            1,
            b"",
            b"CreateProcess rejected: blocked by policy\n",
            None,
        )

        self.assertFalse(result["passed"])
        self.assertEqual(result["status"], "command-policy-blocked")

    def test_public_projection_redacts_paths_and_preserves_raw_hashes(self):
        workspace = Path(r"D:\Code\ai\skill")
        user_home = Path(r"C:\Users\synthetic-user")
        stdout = b""
        stderr = (
            "cannot read D:\\Code\\ai\\skill from "
            "C:\\Users\\synthetic-user\\.codex\n"
        ).encode("utf-8")
        record = PREFLIGHT["build_public_record"](
            ["codex-test", "sandbox", "--cd", str(workspace)],
            workspace,
            user_home,
            1,
            stdout,
            stderr,
            None,
            25,
            "codex-test 0.0.0",
        )
        rendered = str(record)

        self.assertNotIn(str(workspace), rendered)
        self.assertNotIn(str(user_home), rendered)
        self.assertIn("<WORKSPACE>", rendered)
        self.assertIn("<USER_HOME>", rendered)
        self.assertEqual(record["raw_stderr_sha256"], hashlib.sha256(stderr).hexdigest())
        self.assertFalse(record["passed"])

    def test_public_projection_redacts_classification_and_version_values(self):
        workspace = Path(r"D:\synthetic-workspace")
        user_home = Path(r"C:\Users\synthetic-user")
        stderr = (
            "windows sandbox failed: helper_unknown_error: failed under "
            "C:\\Users\\synthetic-user\\.codex\n"
        ).encode("utf-8")
        record = PREFLIGHT["build_public_record"](
            ["codex-test", "sandbox", "--cd", str(workspace)],
            workspace,
            user_home,
            1,
            b"",
            stderr,
            None,
            10,
            r"codex at C:\Users\synthetic-user\bin",
        )
        rendered = json.dumps(record)

        self.assertNotIn("synthetic-user", rendered)
        self.assertIn("<USER_HOME>", record["error_detail"])
        self.assertIn("<USER_HOME>", record["codex_version"])

    def test_doctor_projection_keeps_only_sandbox_diagnostic_fields(self):
        raw = json.dumps(
            {
                "schemaVersion": 1,
                "overallStatus": "fail",
                "checks": {
                    "sandbox.helpers": {
                        "status": "fail",
                        "summary": "sandbox provisioning failed",
                        "details": {
                            "error code": "helper_unknown_error",
                            "sandbox backend": "elevated",
                            "sandbox provisioning": "failed",
                            "private path": r"C:\Users\synthetic-user\secret",
                        },
                        "remediation": "repair the approved distribution",
                    },
                    "auth.credentials": {"stored ChatGPT tokens": "true"},
                },
            }
        ).encode("utf-8")
        projection = PREFLIGHT["project_doctor_sandbox"](
            0,
            raw,
            b"",
            Path(r"D:\synthetic-workspace"),
            Path(r"C:\Users\synthetic-user"),
        )
        rendered = json.dumps(projection)

        self.assertEqual(projection["status"], "fail")
        self.assertEqual(projection["error_code"], "helper_unknown_error")
        self.assertEqual(projection["sandbox_backend"], "elevated")
        self.assertNotIn("private path", rendered)
        self.assertNotIn("auth.credentials", rendered)
        self.assertNotIn("synthetic-user", rendered)

    def test_doctor_projection_redacts_paths_in_allowed_values(self):
        workspace = Path(r"D:\synthetic-workspace")
        user_home = Path(r"C:\Users\synthetic-user")
        raw = json.dumps(
            {
                "checks": {
                    "sandbox.helpers": {
                        "status": "fail",
                        "summary": f"failed under {workspace}",
                        "details": {
                            "error code": "helper_unknown_error",
                            "sandbox backend": f"helper at {user_home}\\bin",
                        },
                        "remediation": f"repair {user_home}\\.codex",
                    }
                }
            }
        ).encode("utf-8")
        projection = PREFLIGHT["project_doctor_sandbox"](
            0, raw, b"", workspace, user_home
        )
        rendered = json.dumps(projection)

        self.assertNotIn("synthetic-workspace", rendered)
        self.assertNotIn("synthetic-user", rendered)
        self.assertIn("<WORKSPACE>", projection["summary"])
        self.assertIn("<USER_HOME>", projection["remediation"])

    def test_doctor_projection_rejects_missing_sandbox_check(self):
        raw = json.dumps({"checks": {}}).encode("utf-8")
        projection = PREFLIGHT["project_doctor_sandbox"](0, raw, b"")

        self.assertEqual(projection["status"], "invalid-doctor-output")
        self.assertFalse(projection["diagnostic_available"])

    def test_version_probe_timeout_does_not_abort_the_canary(self):
        def timeout(*_args, **_kwargs):
            raise subprocess.TimeoutExpired(["codex-test", "--version"], 1)

        version, error = PREFLIGHT["probe_codex_version"](
            "codex-test",
            Path("D:/synthetic-workspace"),
            {},
            1,
            0,
            timeout,
        )

        self.assertEqual(version, "unavailable")
        self.assertEqual(error, "timeout after 1 seconds")

    def test_failed_wrapper_preflight_stops_before_native_runner(self):
        runs_root = ROOT / "evaluations" / "runs"
        with tempfile.TemporaryDirectory(dir=runs_root) as temporary:
            run_dir = Path(temporary) / "run"
            run_dir.mkdir()
            (run_dir / "frozen.json").write_text(
                json.dumps({"comparison_id": "synthetic-preflight"}) + "\n",
                encoding="utf-8",
            )
            globals_ = WRAPPER["run_native_resume_with_host_preflight"].__globals__
            originals = {
                name: globals_[name]
                for name in (
                    "require_host_preflight_flag",
                    "run_host_sandbox_preflight",
                    "run_native_resume",
                )
            }
            native_called = []
            globals_["require_host_preflight_flag"] = lambda _run: {
                "comparison_id": "synthetic-preflight"
            }
            globals_["run_host_sandbox_preflight"] = lambda _codex, _root: {
                "schema_version": 1,
                "platform": "windows",
                "passed": False,
                "status": "sandbox-provisioning-failed",
            }
            globals_["run_native_resume"] = lambda *_args, **_kwargs: native_called.append(
                True
            )
            try:
                with self.assertRaisesRegex(RuntimeError, "before model execution"):
                    WRAPPER["run_native_resume_with_host_preflight"](
                        run_dir, codex_path="codex-test"
                    )
            finally:
                globals_.update(originals)

            self.assertEqual(native_called, [])
            self.assertFalse((run_dir / "run-meta.json").exists())
            self.assertFalse((run_dir / "native-results.json").exists())
            preflight = json.loads(
                (run_dir / "host-sandbox-preflight.json").read_text(encoding="utf-8")
            )
            stop = json.loads(
                (run_dir / "host-preflight-stop.json").read_text(encoding="utf-8")
            )
            self.assertFalse(preflight["passed"])
            self.assertEqual(stop["model_calls"], 0)
            self.assertEqual(stop["result_trajectories"], 0)
            self.assertEqual(stop["result_turns"], 0)


if __name__ == "__main__":
    unittest.main()
