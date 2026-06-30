import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.core.mt5_datadir_resolver import resolve_terminal_datadir


def _make_datadir(root: Path) -> Path:
    data_dir = root / "terminal_data"
    (data_dir / "MQL5" / "Experts").mkdir(parents=True)
    return data_dir


class MT5DataDirResolverTests(unittest.TestCase):
    def test_resolves_datadir_from_local_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            data_dir = _make_datadir(root)
            config_dir = root / "config"
            config_dir.mkdir()
            (config_dir / "mt5.local.json").write_text(
                json.dumps({"terminal_data_dir": str(data_dir)}),
                encoding="utf-8",
            )
            result = resolve_terminal_datadir(root)

        self.assertTrue(result["terminal_data_dir_found"])
        self.assertEqual(result["datadir_source"], "config_mt5_local_json")
        self.assertTrue(result["mql5_dir_found"])
        self.assertTrue(result["experts_dir_found"])

    def test_resolves_datadir_from_origin_txt_matching_terminal_install(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            install_dir = root / "install"
            install_dir.mkdir()
            terminal = install_dir / "terminal64.exe"
            terminal.write_text("fake exe", encoding="utf-8")
            data_dir = root / "roaming" / "MetaQuotes" / "Terminal" / "abc123"
            (data_dir / "MQL5" / "Experts").mkdir(parents=True)
            (data_dir / "origin.txt").write_text(str(install_dir), encoding="utf-8")
            config_dir = root / "config"
            config_dir.mkdir()
            (config_dir / "mt5.local.json").write_text(
                json.dumps({"terminal_path": str(terminal)}),
                encoding="utf-8",
            )
            with patch.dict(os.environ, {"APPDATA": str(root / "roaming")}):
                result = resolve_terminal_datadir(root)

        self.assertTrue(result["terminal_data_dir_found"])
        self.assertEqual(result["datadir_source"], "appdata_origin_txt")
        self.assertTrue(result["origin_txt_found"])
        self.assertTrue(result["origin_txt_matched_terminal"])

    def test_blocks_when_datadir_absent(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            with patch.dict(os.environ, {"APPDATA": str(root / "empty_roaming")}):
                result = resolve_terminal_datadir(root)

        self.assertFalse(result["terminal_data_dir_found"])
        self.assertEqual(result["datadir_source"], "not_found")
        self.assertIn("terminal_data_dir_missing", result["blocking_issues"])


if __name__ == "__main__":
    unittest.main()
