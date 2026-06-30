import json
import tempfile
import unittest
from pathlib import Path

from app.core.mt5_runner import MT5SmokeRunResult
from app.core.operator_gate import APPROVAL_PHRASE_PT
from app.core.compiled_ex5_readiness import write_compiled_ex5_readiness_marker
from app.core.real_mt5_preflight import ensure_ignored_preflight_ex5_marker
from app.core.real_mt5_smoke import execute_one_run_real_mt5_smoke


READY_ENVIRONMENT = {
    "mt5_detected": True,
    "terminal_found": True,
    "metaeditor_found": True,
    "ready_for_real_smoke": True,
    "terminal_path_sanitized": "<WINDOWS_PATH_REDACTED>\\terminal64.exe",
}

READY_PREFLIGHT = {
    "status": "ready_for_one_run_retry",
    "ready_for_real_retry": True,
    "failure_stage": "not_attempted",
    "exit_code_recorded": None,
    "exit_code_category": "not_recorded",
    "expert_path_checked": True,
    "compiled_ex5_checked": True,
    "report_export_contract_checked": True,
    "report_path_privacy_checked": True,
    "tester_ini_contract_checked": True,
    "terminal_launch_args_sanitized": ["<WINDOWS_PATH_REDACTED>\\terminal64.exe", "/config:<PRIVATE_TESTER_INI>"],
    "tester_ini_contract_summary": {
        "section": "Tester",
        "expert": "Examples\\MACD Sample",
        "symbol": "XAUUSD",
        "period": "M5",
        "optimization": "0",
        "report_configured": True,
        "replace_report": "1",
        "shutdown_terminal": "1",
    },
    "report_contract_summary": {
        "report_export_configured": True,
        "replace_report": True,
        "shutdown_terminal": True,
        "private_artifacts_only": True,
    },
    "blocking_issues": [],
    "warnings": [],
    "checks": [],
}


def _fake_success_runner(*args, **kwargs) -> MT5SmokeRunResult:
    return MT5SmokeRunResult(
        symbol="XAUUSD",
        timeframe="M5",
        profit=0,
        drawdown=0,
        trades=0,
        winrate=0,
        profit_factor=0,
        status="smoke_run",
        candidate_id="fake",
        initial_balance_usd=10000,
        mt5_real_execution=True,
        strategy_tester_executed=True,
        loop_execution=False,
        terminal_path="<WINDOWS_PATH_REDACTED>\\terminal64.exe",
        command=["<WINDOWS_PATH_REDACTED>\\terminal64.exe", "/config:<WINDOWS_PATH_REDACTED>\\mvp_013c_smoke.ini"],
        reason="single_strategy_tester_smoke_completed",
        mt5_close_policy="always_after_real_run",
        mt5_close_attempted=True,
        mt5_closed_after_run=True,
        mt5_close_method="owned_process_already_closed",
        mt5_close_error="",
        mt5_process_owned_by_app=True,
        mt5_external_process_detected=False,
        manual_close_required=False,
    )


def _fake_success_runner_with_report(*args, **kwargs) -> MT5SmokeRunResult:
    private_artifact_dir = kwargs["private_artifact_dir"]
    (private_artifact_dir / "strategy_tester_report.html").write_text(
        "\n".join(
            [
                "<p>Status: completed</p>",
                "<p>Symbol: XAUUSD</p>",
                "<p>Timeframe: M5</p>",
                "<p>Total Trades: 7</p>",
                "<p>Total Net Profit: 42.5</p>",
                "<p>Max Drawdown: 1.2</p>",
            ]
        ),
        encoding="utf-8",
    )
    return _fake_success_runner(*args, **kwargs)


class RealMT5SmokeGateTests(unittest.TestCase):
    def test_wrong_phrase_does_not_attempt_runner(self) -> None:
        calls = []

        def runner(*args, **kwargs):
            calls.append("called")
            return _fake_success_runner(*args, **kwargs)

        with tempfile.TemporaryDirectory() as tmpdir:
            result = execute_one_run_real_mt5_smoke(
                Path(tmpdir),
                approval_phrase="wrong phrase",
                runner=runner,
                environment_override=READY_ENVIRONMENT,
            )

        self.assertEqual(calls, [])
        self.assertFalse(result["summary"]["real_smoke_attempted"])
        self.assertFalse(result["summary"]["mt5_real_run"])

    def test_approved_smoke_writes_public_sanitized_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            result = execute_one_run_real_mt5_smoke(
                root,
                approval_phrase=APPROVAL_PHRASE_PT,
                runner=_fake_success_runner,
                environment_override=READY_ENVIRONMENT,
                preflight_override=READY_PREFLIGHT,
            )
            public_json = root / "reports" / "public" / "real_mt5_smoke_summary.json"
            public_md = root / "reports" / "public" / "real_mt5_smoke_summary.md"
            capture_json = root / "reports" / "public" / "real_mt5_capture_smoke_summary.json"
            private_dir = root / "reports" / "private" / "real_mt5_smoke"
            payload = json.loads(public_json.read_text(encoding="utf-8"))
            capture_payload = json.loads(capture_json.read_text(encoding="utf-8"))
            public_text = public_json.read_text(encoding="utf-8") + public_md.read_text(encoding="utf-8")
            private_dir_exists = private_dir.exists()
            local_manifests = list(private_dir.glob("*/run_manifest.local.json"))

        self.assertEqual(result["status"], "PASS_REAL_MT5_SMOKE_ONE_RUN_COMPLETED")
        self.assertTrue(payload["operator_gate_approved"])
        self.assertTrue(payload["mt5_real_run"])
        self.assertTrue(payload["backtest_real_run"])
        self.assertEqual(payload["runs_attempted"], 1)
        self.assertEqual(payload["real_smoke_runs"], 1)
        self.assertEqual(capture_payload["parse_status"], "no_report_found")
        self.assertFalse(capture_payload["report_file_found"])
        self.assertEqual(payload["mt5_close_policy"], "always_after_real_run")
        self.assertTrue(payload["mt5_close_attempted"])
        self.assertTrue(payload["mt5_closed_after_run"])
        self.assertEqual(capture_payload["mt5_close_policy"], "always_after_real_run")
        self.assertFalse(capture_payload["manual_close_required"])
        self.assertTrue(capture_payload["report_export_configured"])
        self.assertTrue(capture_payload["replace_report"])
        self.assertTrue(capture_payload["shutdown_terminal"])
        self.assertFalse(capture_payload["parser_attempted"])
        self.assertEqual(capture_payload["preflight_status"], "ready_for_one_run_retry")
        self.assertEqual(capture_payload["failure_stage"], "completed_report_pending_capture")
        self.assertTrue(payload["ready_for_real_retry"])
        self.assertNotIn("reports/public", str(capture_payload))
        self.assertTrue(private_dir_exists)
        self.assertEqual(len(local_manifests), 1)
        for marker in ["C:\\Users\\", "C:/Users/", "file://", "\\\\server\\"]:
            self.assertNotIn(marker, public_text)

    def test_approved_smoke_parses_local_report_when_present(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            result = execute_one_run_real_mt5_smoke(
                root,
                approval_phrase=APPROVAL_PHRASE_PT,
                runner=_fake_success_runner_with_report,
                environment_override=READY_ENVIRONMENT,
                preflight_override=READY_PREFLIGHT,
            )
            capture_json = root / "reports" / "public" / "real_mt5_capture_smoke_summary.json"
            capture_payload = json.loads(capture_json.read_text(encoding="utf-8"))

        self.assertEqual(result["capture_summary"]["parse_status"], "parse_success")
        self.assertTrue(capture_payload["report_file_found"])
        self.assertTrue(capture_payload["parseable"])
        self.assertTrue(capture_payload["metrics_extracted"])
        self.assertEqual(capture_payload["metrics"]["total_trades"], 7)
        self.assertEqual(capture_payload["metrics"]["net_profit"], 42.5)

    def test_approved_smoke_uses_runtime_contract_marker_handoff(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            ensure_ignored_preflight_ex5_marker(root)
            terminal_data_dir = root / "terminal_data"
            ex5 = terminal_data_dir / "MQL5" / "Experts" / "Examples" / "MACD Sample.ex5"
            ex5.parent.mkdir(parents=True)
            ex5.write_text("compiled fake", encoding="utf-8")
            write_compiled_ex5_readiness_marker(
                root,
                terminal_data_dir=terminal_data_dir,
                expert_relative_path="Examples\\MACD Sample",
            )
            result = execute_one_run_real_mt5_smoke(
                root,
                approval_phrase=APPROVAL_PHRASE_PT,
                runner=_fake_success_runner,
                environment_override={**READY_ENVIRONMENT, "terminal_data_dir": str(terminal_data_dir)},
            )

        self.assertEqual(result["status"], "PASS_REAL_MT5_SMOKE_ONE_RUN_COMPLETED")
        self.assertTrue(result["summary"]["ready_for_real_retry"])
        self.assertEqual(result["summary"]["preflight_blocking_issues"], [])

    def test_approved_smoke_blocks_without_compiled_ex5_preflight(self) -> None:
        calls = []

        def runner(*args, **kwargs):
            calls.append("called")
            return _fake_success_runner(*args, **kwargs)

        with tempfile.TemporaryDirectory() as tmpdir:
            result = execute_one_run_real_mt5_smoke(
                Path(tmpdir),
                approval_phrase=APPROVAL_PHRASE_PT,
                runner=runner,
                environment_override=READY_ENVIRONMENT,
            )

        self.assertEqual(calls, [])
        self.assertEqual(result["status"], "HOLD_REAL_MT5_PREFLIGHT_BLOCKED_NO_RETRY")
        self.assertFalse(result["summary"]["ready_for_real_retry"])
        self.assertIn("compiled_ex5_marker_missing", result["summary"]["preflight_blocking_issues"])


if __name__ == "__main__":
    unittest.main()
