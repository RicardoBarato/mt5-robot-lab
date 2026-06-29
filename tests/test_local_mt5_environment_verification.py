import json
import tempfile
import unittest
from pathlib import Path

from app.core.mt5_detection import build_local_mt5_environment_status, write_local_mt5_environment_status


class LocalMT5EnvironmentVerificationTests(unittest.TestCase):
    def test_absent_mt5_does_not_fail_system(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            status = build_local_mt5_environment_status([Path(tmpdir) / "missing"])
        self.assertFalse(status["mt5_detected"])
        self.assertFalse(status["terminal_found"])
        self.assertFalse(status["metaeditor_found"])
        self.assertEqual(status["status"], "not ready")
        self.assertFalse(status["ready_for_real_smoke"])
        self.assertTrue(status["operator_gate_required"])

    def test_detected_paths_are_sanitized(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "MetaTrader 5"
            root.mkdir()
            (root / "terminal64.exe").write_text("", encoding="utf-8")
            (root / "metaeditor64.exe").write_text("", encoding="utf-8")
            status = build_local_mt5_environment_status([root])
        self.assertTrue(status["mt5_detected"])
        self.assertTrue(status["terminal_found"])
        self.assertTrue(status["metaeditor_found"])
        self.assertTrue(status["ready_for_real_smoke"])
        self.assertTrue(status["paths_sanitized"])
        payload = json.dumps(status)
        for raw_path_marker in ["C:\\Users\\", "C:/Users/", "file://", "\\\\server\\"]:
            self.assertNotIn(raw_path_marker, payload)

    def test_outputs_contain_required_non_execution_flags(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "reports" / "public"
            result = write_local_mt5_environment_status(output, [Path(tmpdir) / "missing"])
            json_path = Path(result["files"]["json"])
            markdown_path = Path(result["files"]["markdown"])
            self.assertTrue(json_path.exists())
            self.assertTrue(markdown_path.exists())
            status = json.loads(json_path.read_text(encoding="utf-8"))
            text = json_path.read_text(encoding="utf-8") + markdown_path.read_text(encoding="utf-8")
        self.assertTrue(status["operator_gate_required"])
        self.assertFalse(status["mt5_real_run"])
        self.assertFalse(status["backtest_real_run"])
        self.assertFalse(status["strategy_tester_run"])
        self.assertFalse(status["ea_executed"])
        self.assertFalse(status["credentials_stored"])
        for raw_path_marker in ["C:\\Users\\", "C:/Users/", "file://", "\\\\server\\"]:
            self.assertNotIn(raw_path_marker, text)


if __name__ == "__main__":
    unittest.main()
