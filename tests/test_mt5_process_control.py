import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.core.mt5_process_control import (
    MT5ProcessInfo,
    close_mt5_after_run,
    default_mt5_close_policy,
    make_mt5_close_summary,
)
from app.core.mt5_runner import MT5SmokeConfig, run_mt5_smoke
from app.core.operator_gate import APPROVAL_PHRASE_EN, approve_operator_gate, create_operator_approval_request


class FakePopen:
    pid = 12345
    returncode = 0

    def __init__(self, *args, **kwargs) -> None:
        self.args = args
        self.kwargs = kwargs

    def communicate(self, timeout=None):
        return "", ""


class MT5ProcessControlTests(unittest.TestCase):
    def test_default_policy_is_close_after_real_run(self) -> None:
        policy = default_mt5_close_policy()
        self.assertEqual(policy.mt5_close_policy, "always_after_real_run")
        self.assertFalse(policy.close_external_processes)

    def test_external_terminal_is_not_closed_and_requires_manual_close(self) -> None:
        process = MT5ProcessInfo(pid=100, owned_by_app=False, already_running=True)
        result = close_mt5_after_run(process)
        self.assertFalse(result.mt5_close_attempted)
        self.assertFalse(result.mt5_closed_after_run)
        self.assertTrue(result.mt5_external_process_detected)
        self.assertTrue(result.manual_close_required)

    def test_owned_process_without_pid_records_manual_close_required(self) -> None:
        process = MT5ProcessInfo(pid=None, owned_by_app=True, already_running=False)
        result = close_mt5_after_run(process)
        self.assertTrue(result.mt5_close_attempted)
        self.assertFalse(result.mt5_closed_after_run)
        self.assertTrue(result.manual_close_required)
        self.assertEqual(result.mt5_close_method, "owned_process_no_pid")

    def test_owned_process_already_closed_is_recorded(self) -> None:
        process = MT5ProcessInfo(pid=123, owned_by_app=True, already_running=False)
        with patch("app.core.mt5_process_control.verify_mt5_closed", return_value=True):
            result = close_mt5_after_run(process)
        self.assertTrue(result.mt5_close_attempted)
        self.assertTrue(result.mt5_closed_after_run)
        self.assertEqual(result.mt5_close_method, "owned_process_already_closed")
        self.assertFalse(result.manual_close_required)

    def test_summary_fills_required_fields(self) -> None:
        summary = make_mt5_close_summary(None)
        expected = {
            "mt5_close_policy",
            "mt5_close_attempted",
            "mt5_closed_after_run",
            "mt5_close_method",
            "mt5_close_error",
            "mt5_process_owned_by_app",
            "mt5_external_process_detected",
            "manual_close_required",
        }
        self.assertTrue(expected.issubset(summary))

    def test_runner_records_close_fields_for_app_owned_real_smoke(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            terminal = root / "terminal64.exe"
            config = root / "smoke.ini"
            terminal.write_text("", encoding="utf-8")
            config.write_text("[Tester]\n", encoding="utf-8")
            gate_request = create_operator_approval_request(
                {
                    "real_execution_requested": True,
                    "smoke_only": True,
                    "max_backtests": 1,
                    "tournament_100_run": False,
                    "credentials_stored": False,
                },
                {
                    "mt5_installed": True,
                    "terminal_found": True,
                    "metaeditor_found": True,
                },
            )
            gate = approve_operator_gate(gate_request, APPROVAL_PHRASE_EN)
            with (
                patch("app.core.mt5_runner.subprocess.Popen", FakePopen),
                patch("app.core.mt5_process_control.verify_mt5_closed", return_value=True),
                patch("app.core.mt5_runner.find_mt5_processes", return_value=[]),
            ):
                result = run_mt5_smoke(
                    MT5SmokeConfig(timeout_seconds=1),
                    allow_real_execution=True,
                    operator_gate=gate,
                    terminal_path=str(terminal),
                    tester_config_path=str(config),
                    tester_config_allowed_roots=[root],
                    private_artifact_dir=root / "private",
                )

        payload = result.public_payload()
        self.assertTrue(payload["mt5_close_attempted"])
        self.assertTrue(payload["mt5_closed_after_run"])
        self.assertEqual(payload["mt5_close_policy"], "always_after_real_run")
        self.assertTrue(payload["mt5_process_owned_by_app"])
        self.assertFalse(payload["manual_close_required"])


if __name__ == "__main__":
    unittest.main()
