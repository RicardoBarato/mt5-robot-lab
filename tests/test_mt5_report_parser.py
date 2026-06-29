import tempfile
import unittest
from pathlib import Path

from app.core.mt5_report_parser import parse_mt5_report


FIXTURE_ROOT = Path(__file__).resolve().parent / "fixtures" / "mt5_reports"


class MT5ReportParserTests(unittest.TestCase):
    def test_parse_synthetic_html_report(self) -> None:
        result = parse_mt5_report(FIXTURE_ROOT / "synthetic_strategy_tester_report.html", allowed_root=FIXTURE_ROOT)
        self.assertTrue(result.parseable)
        self.assertEqual(result.source_format, "html")
        self.assertEqual(result.result_status, "completed")
        self.assertEqual(result.total_trades, 12)
        self.assertEqual(result.net_profit, 123.45)
        self.assertEqual(result.gross_profit, 400.0)
        self.assertEqual(result.gross_loss, -276.55)
        self.assertEqual(result.max_drawdown, 3.21)
        self.assertEqual(result.initial_deposit, 10000.0)
        self.assertEqual(result.symbol, "XAUUSD")
        self.assertEqual(result.timeframe, "M5")

    def test_parse_synthetic_xml_report(self) -> None:
        result = parse_mt5_report(FIXTURE_ROOT / "synthetic_strategy_tester_report.xml", allowed_root=FIXTURE_ROOT)
        self.assertTrue(result.parseable)
        self.assertEqual(result.source_format, "xml")
        self.assertEqual(result.total_trades, 12)
        self.assertEqual(result.net_profit, 123.45)

    def test_reject_unknown_format(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            path = root / "report.bin"
            path.write_text("not a report", encoding="utf-8")
            result = parse_mt5_report(path, allowed_root=root)
        self.assertFalse(result.parseable)
        self.assertEqual(result.result_status, "unsupported_format_or_missing_fields")

    def test_missing_metrics_are_none_not_invented(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            path = root / "minimal.html"
            path.write_text("<p>Status: completed</p><p>Symbol: XAUUSD</p>", encoding="utf-8")
            result = parse_mt5_report(path, allowed_root=root)
        self.assertTrue(result.parseable)
        self.assertEqual(result.result_status, "completed")
        self.assertEqual(result.symbol, "XAUUSD")
        self.assertIsNone(result.total_trades)
        self.assertIsNone(result.net_profit)
        self.assertIsNone(result.max_drawdown)

    def test_reject_path_outside_allowed_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_a, tempfile.TemporaryDirectory() as tmp_b:
            outside = Path(tmp_a) / "report.html"
            outside.write_text("<p>Status: completed</p>", encoding="utf-8")
            result = parse_mt5_report(outside, allowed_root=Path(tmp_b))
        self.assertFalse(result.parseable)
        self.assertEqual(result.result_status, "path_outside_allowed_root")
        self.assertIn("outside_allowed_root", result.warnings)


if __name__ == "__main__":
    unittest.main()
