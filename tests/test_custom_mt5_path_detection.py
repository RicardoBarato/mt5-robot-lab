import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from app.core.mt5_detection import detect_mt5, load_local_mt5_config, write_local_mt5_environment_status


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class CustomMT5PathDetectionTests(unittest.TestCase):
    def _fake_mt5_root(self) -> tempfile.TemporaryDirectory:
        runs_root = PROJECT_ROOT / "runs"
        runs_root.mkdir(exist_ok=True)
        return tempfile.TemporaryDirectory(dir=runs_root)

    def test_accepts_custom_terminal_and_metaeditor_paths(self) -> None:
        with self._fake_mt5_root() as tmpdir:
            root = Path(tmpdir) / "E_drive_MT5"
            root.mkdir()
            terminal = root / "terminal64.exe"
            metaeditor = root / "metaeditor64.exe"
            terminal.write_text("", encoding="utf-8")
            metaeditor.write_text("", encoding="utf-8")
            result = detect_mt5([], terminal_path=str(terminal), metaeditor_path=str(metaeditor))
        self.assertTrue(result.terminal_found)
        self.assertTrue(result.metaeditor_found)
        self.assertEqual(result.status, "ready")
        self.assertTrue(result.custom_terminal_path_configured)
        self.assertTrue(result.custom_metaeditor_path_configured)

    def test_rejects_wrong_terminal_and_metaeditor_basenames(self) -> None:
        with self._fake_mt5_root() as tmpdir:
            root = Path(tmpdir)
            wrong_terminal = root / "not_terminal.exe"
            wrong_metaeditor = root / "metaeditor.exe"
            wrong_terminal.write_text("", encoding="utf-8")
            wrong_metaeditor.write_text("", encoding="utf-8")
            result = detect_mt5([], terminal_path=str(wrong_terminal), metaeditor_path=str(wrong_metaeditor))
        self.assertFalse(result.terminal_found)
        self.assertFalse(result.metaeditor_found)
        self.assertTrue(any("terminal64.exe" in item for item in result.custom_path_errors))
        self.assertTrue(any("metaeditor64.exe" in item for item in result.custom_path_errors))

    def test_reads_local_config_without_requiring_real_config_file(self) -> None:
        with self._fake_mt5_root() as tmpdir:
            root = Path(tmpdir)
            terminal = root / "terminal64.exe"
            metaeditor = root / "metaeditor64.exe"
            terminal.write_text("", encoding="utf-8")
            metaeditor.write_text("", encoding="utf-8")
            config_path = root / "mt5.local.json"
            config_path.write_text(
                json.dumps({"terminal_path": str(terminal), "metaeditor_path": str(metaeditor)}),
                encoding="utf-8",
            )
            config = load_local_mt5_config(config_path)
            result = detect_mt5([], config_path=config_path)
        self.assertEqual(config["terminal_path"], str(terminal))
        self.assertTrue(result.local_config_loaded)
        self.assertTrue(result.terminal_found)
        self.assertTrue(result.metaeditor_found)

    def test_local_config_is_ignored_but_example_is_versionable(self) -> None:
        ignored = subprocess.run(
            ["git", "check-ignore", "config/mt5.local.json", "config/custom.local.json"],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        example = subprocess.run(
            ["git", "check-ignore", "-q", "config/mt5.local.example.json"],
            cwd=PROJECT_ROOT,
            check=False,
        )
        self.assertIn("config/mt5.local.json", ignored.stdout)
        self.assertIn("config/custom.local.json", ignored.stdout)
        self.assertNotEqual(example.returncode, 0)

    def test_example_config_is_public_safe(self) -> None:
        payload = json.loads((PROJECT_ROOT / "config" / "mt5.local.example.json").read_text(encoding="utf-8"))
        self.assertEqual(Path(payload["terminal_path"]).name, "terminal64.exe")
        self.assertEqual(Path(payload["metaeditor_path"]).name, "metaeditor64.exe")
        lowered = json.dumps(payload).lower()
        for forbidden in ["password", "token", "secret", "account_number", "broker_password"]:
            self.assertNotIn(forbidden, lowered)

    def test_outputs_sanitize_custom_paths_and_do_not_execute(self) -> None:
        with self._fake_mt5_root() as tmpdir:
            root = Path(tmpdir)
            terminal = root / "terminal64.exe"
            metaeditor = root / "metaeditor64.exe"
            terminal.write_text("", encoding="utf-8")
            metaeditor.write_text("", encoding="utf-8")
            output = root / "reports" / "public"
            result = write_local_mt5_environment_status(
                output,
                [],
                terminal_path=str(terminal),
                metaeditor_path=str(metaeditor),
            )
            json_path = Path(result["files"]["json"])
            report_path = Path(result["files"]["custom_path_report"])
            status = json.loads(json_path.read_text(encoding="utf-8"))
            combined = json_path.read_text(encoding="utf-8") + report_path.read_text(encoding="utf-8")
            raw_root = str(root)
        self.assertTrue(status["paths_sanitized"])
        self.assertTrue(status["operator_gate_required"])
        self.assertFalse(status["mt5_real_run"])
        self.assertFalse(status["backtest_real_run"])
        self.assertFalse(status["strategy_tester_run"])
        self.assertFalse(status["ea_executed"])
        self.assertFalse(status["credentials_stored"])
        self.assertNotIn(raw_root, combined)
        self.assertIn("terminal64.exe", combined)
        self.assertIn("metaeditor64.exe", combined)


if __name__ == "__main__":
    unittest.main()
