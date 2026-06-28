import tempfile
import unittest
from pathlib import Path

from app.core.mt5_detection import detect_mt5, find_metaeditor, find_terminal, generate_diagnostics, scan_symbols


class MT5DetectionTests(unittest.TestCase):
    def test_detects_terminal_and_metaeditor_in_temp_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "MetaTrader 5"
            root.mkdir()
            (root / "terminal64.exe").write_text("", encoding="utf-8")
            (root / "metaeditor64.exe").write_text("", encoding="utf-8")
            result = detect_mt5([root])
        self.assertTrue(result.mt5_installed)
        self.assertTrue(result.terminal_found)
        self.assertTrue(result.metaeditor_found)
        self.assertEqual(result.status, "ready")

    def test_find_helpers_return_public_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "terminal64.exe").write_text("", encoding="utf-8")
            (root / "metaeditor64.exe").write_text("", encoding="utf-8")
            terminal = find_terminal([root])
            metaeditor = find_metaeditor([root])
        self.assertTrue(terminal.endswith("terminal64.exe"))
        self.assertTrue(metaeditor.endswith("metaeditor64.exe"))

    def test_scan_symbols_safe_mode(self) -> None:
        symbols = scan_symbols()
        self.assertEqual(symbols["symbol_scan_mode"], "safe_mock_common_mappings")
        self.assertFalse(symbols["mt5_connected"])
        self.assertIn("XAUUSD", symbols["symbols"])
        self.assertIn("USTEC", symbols["symbols"])
        self.assertIn("EURUSD", symbols["symbols"])

    def test_generate_diagnostics_writes_reports(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "reports"
            result = generate_diagnostics(output, roots=[Path(tmpdir) / "missing"])
            files = result["files"]
            for path in files.values():
                self.assertTrue(Path(path).exists())
        self.assertEqual(result["status"], "OK")
        self.assertFalse(result["diagnostics"]["backtest_real_run"])
        self.assertFalse(result["diagnostics"]["strategy_tester_run"])
        self.assertFalse(result["diagnostics"]["credentials_stored"])


if __name__ == "__main__":
    unittest.main()
