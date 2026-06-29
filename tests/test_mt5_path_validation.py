import tempfile
import unittest
from pathlib import Path

from app.core.mt5_detection import validate_mt5_executable_path, validate_tester_config_path
from app.core.mt5_runner import build_strategy_tester_command, run_mt5_smoke


class MT5PathValidationTests(unittest.TestCase):
    def test_executable_name_and_extension_are_required(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            terminal = root / "terminal64.exe"
            terminal.write_text("", encoding="utf-8")
            wrong_name = root / "terminal.exe"
            wrong_name.write_text("", encoding="utf-8")
            wrong_extension = root / "terminal64.txt"
            wrong_extension.write_text("", encoding="utf-8")

            self.assertEqual(validate_mt5_executable_path(terminal, "terminal64.exe"), terminal)
            with self.assertRaises(ValueError):
                validate_mt5_executable_path(wrong_name, "terminal64.exe")
            with self.assertRaises(ValueError):
                validate_mt5_executable_path(wrong_extension, "terminal64.exe")

    def test_tester_config_must_be_local_config_or_ignored_run_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            config = root / "smoke.ini"
            config.write_text("[Tester]\n", encoding="utf-8")
            forbidden = root / "real.set"
            forbidden.write_text("", encoding="utf-8")

            self.assertEqual(validate_tester_config_path(config, allowed_roots=[root]), config)
            with self.assertRaises(ValueError):
                validate_tester_config_path(forbidden, allowed_roots=[root])

    def test_build_strategy_tester_command_validates_paths(self) -> None:
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

    def test_operator_gate_blocks_before_path_validation(self) -> None:
        result = run_mt5_smoke(
            allow_real_execution=True,
            terminal_path=r"C:\Users\Ricardo\AppData\Local\terminal64.exe",
            tester_config_path=r"C:\Users\Ricardo\AppData\Local\smoke.ini",
        )
        payload = result.public_payload()
        self.assertEqual(payload["status"], "blocked_by_operator_gate")
        self.assertTrue(
            payload["terminal_path"].startswith("<LOCAL_APPDATA>")
            or payload["terminal_path"].startswith("<USER_HOME>")
        )


if __name__ == "__main__":
    unittest.main()
