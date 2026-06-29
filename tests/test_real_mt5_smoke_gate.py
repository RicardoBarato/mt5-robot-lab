import json
import tempfile
import unittest
from pathlib import Path

from app.core.mt5_runner import MT5SmokeRunResult
from app.core.operator_gate import APPROVAL_PHRASE_PT
from app.core.real_mt5_smoke import execute_one_run_real_mt5_smoke


READY_ENVIRONMENT = {
    "mt5_detected": True,
    "terminal_found": True,
    "metaeditor_found": True,
    "ready_for_real_smoke": True,
    "terminal_path_sanitized": "<WINDOWS_PATH_REDACTED>\\terminal64.exe",
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
    )


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
            )
            public_json = root / "reports" / "public" / "real_mt5_smoke_summary.json"
            public_md = root / "reports" / "public" / "real_mt5_smoke_summary.md"
            private_dir = root / "reports" / "private" / "real_mt5_smoke"
            payload = json.loads(public_json.read_text(encoding="utf-8"))
            public_text = public_json.read_text(encoding="utf-8") + public_md.read_text(encoding="utf-8")
            private_dir_exists = private_dir.exists()
            local_manifests = list(private_dir.glob("*/run_manifest.local.json"))

        self.assertEqual(result["status"], "PASS_REAL_MT5_SMOKE_ONE_RUN_COMPLETED")
        self.assertTrue(payload["operator_gate_approved"])
        self.assertTrue(payload["mt5_real_run"])
        self.assertTrue(payload["backtest_real_run"])
        self.assertEqual(payload["runs_attempted"], 1)
        self.assertEqual(payload["real_smoke_runs"], 1)
        self.assertTrue(private_dir_exists)
        self.assertEqual(len(local_manifests), 1)
        for marker in ["C:\\Users\\", "C:/Users/", "file://", "\\\\server\\"]:
            self.assertNotIn(marker, public_text)


if __name__ == "__main__":
    unittest.main()
