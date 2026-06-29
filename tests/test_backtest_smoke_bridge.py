import tempfile
import unittest
from pathlib import Path

from app.core.backtest_parser import empty_smoke_metrics, parse_backtest_report_text
from app.core.candidate_runner import run_xauusd_base_seed_smoke
from app.core.mt5_runner import MT5SmokeConfig, build_strategy_tester_command, run_mt5_smoke


class BacktestSmokeBridgeTests(unittest.TestCase):
    def test_parser_extracts_standard_metrics(self) -> None:
        report = """
        Total Net Profit: 1 234.50
        Equity Drawdown Maximal: 12.75
        Total Trades: 42
        Win Rate: 38.10
        Profit Factor: 1.42
        """
        metrics = parse_backtest_report_text(report)
        self.assertEqual(metrics.profit, 1234.50)
        self.assertEqual(metrics.drawdown, 12.75)
        self.assertEqual(metrics.trades, 42)
        self.assertEqual(metrics.winrate, 38.10)
        self.assertEqual(metrics.profit_factor, 1.42)

    def test_empty_smoke_metrics_are_numeric(self) -> None:
        metrics = empty_smoke_metrics()
        self.assertEqual(metrics.profit, 0.0)
        self.assertEqual(metrics.drawdown, 0.0)
        self.assertEqual(metrics.trades, 0)
        self.assertEqual(metrics.winrate, 0.0)
        self.assertEqual(metrics.profit_factor, 0.0)

    def test_runner_blocks_loop_execution(self) -> None:
        with self.assertRaises(ValueError):
            run_mt5_smoke(MT5SmokeConfig(max_backtests=2))

    def test_runner_dry_smoke_does_not_execute_mt5(self) -> None:
        result = run_mt5_smoke()
        self.assertEqual(result.status, "smoke_run")
        self.assertFalse(result.mt5_real_execution)
        self.assertFalse(result.strategy_tester_executed)
        self.assertFalse(result.loop_execution)
        self.assertEqual(result.symbol, "XAUUSD")
        self.assertEqual(result.timeframe, "M5")

    def test_runner_blocks_real_execution_without_operator_gate(self) -> None:
        result = run_mt5_smoke(allow_real_execution=True)
        payload = result.public_payload()
        self.assertEqual(result.status, "blocked_by_operator_gate")
        self.assertFalse(payload["mt5_real_run"])
        self.assertFalse(payload["backtest_real_run"])
        self.assertEqual(payload["reason"], "Real MT5 smoke execution requires explicit operator approval.")

    def test_strategy_tester_command_shape(self) -> None:
        runs_root = Path.cwd() / "runs"
        runs_root.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=runs_root) as tmpdir:
            root = Path(tmpdir)
            terminal = root / "terminal64.exe"
            config = root / "smoke.ini"
            terminal.write_text("", encoding="utf-8")
            config.write_text("[Tester]\n", encoding="utf-8")
            command = build_strategy_tester_command(str(terminal), str(config))
        self.assertEqual(Path(command[0]).name, "terminal64.exe")
        self.assertTrue(command[1].startswith("/config:"))

    def test_candidate_runner_writes_public_smoke_result(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir)
            payload = run_xauusd_base_seed_smoke(output)
            result_path = output / "backtest_smoke_result.json"
            self.assertTrue(result_path.exists())
        self.assertEqual(payload["symbol"], "XAUUSD")
        self.assertEqual(payload["timeframe"], "M5")
        self.assertEqual(payload["profit"], 0)
        self.assertEqual(payload["drawdown"], 0)
        self.assertEqual(payload["trades"], 0)
        self.assertEqual(payload["status"], "smoke_run")
        self.assertFalse(payload["mt5_real_execution"])


if __name__ == "__main__":
    unittest.main()
