import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from app.core.compiled_ex5_readiness import DEFAULT_READINESS_MARKER
from app.core.compiled_ex5_terminal_bootstrap import (
    HOLD_AMBIGUOUS_STATUS,
    HOLD_SOURCE_STATUS,
    METHOD_ALREADY_PRESENT,
    METHOD_COMPILED,
    PASS_STATUS,
    build_compiled_ex5_terminal_bootstrap,
    generate_compiled_ex5_terminal_bootstrap,
)


def _make_root() -> tuple[tempfile.TemporaryDirectory[str], Path, Path]:
    temp = tempfile.TemporaryDirectory()
    root = Path(temp.name)
    data_dir = root / "terminal_data"
    (data_dir / "MQL5" / "Experts" / "Examples").mkdir(parents=True)
    (data_dir / "MQL5" / "Profiles" / "Tester").mkdir(parents=True)
    (root / "config").mkdir()
    (root / "config" / "mt5.local.json").write_text(
        json.dumps({"terminal_data_dir": str(data_dir)}),
        encoding="utf-8",
    )
    return temp, root, data_dir


class CompiledEX5TerminalBootstrapTests(unittest.TestCase):
    def test_existing_ex5_in_terminal_datadir_returns_pass(self) -> None:
        temp, root, data_dir = _make_root()
        with temp:
            ex5 = data_dir / "MQL5" / "Experts" / "Examples" / "MACD Sample.ex5"
            ex5.write_bytes(b"compiled")

            result = build_compiled_ex5_terminal_bootstrap(root)
            marker_exists = (root / DEFAULT_READINESS_MARKER).exists()

        self.assertEqual(result["status"], PASS_STATUS)
        self.assertEqual(result["bootstrap_method"], METHOD_ALREADY_PRESENT)
        self.assertFalse(result["metaeditor_real_run"])
        self.assertFalse(result["mt5_terminal_run"])
        self.assertTrue(result["compiled_ex5_marker_created"])
        self.assertTrue(result["compiled_ex5_verified_in_terminal_datadir"])
        self.assertTrue(marker_exists)

    def test_missing_source_and_ex5_returns_hold(self) -> None:
        temp, root, _data_dir = _make_root()
        with temp:
            result = generate_compiled_ex5_terminal_bootstrap(root)
            public_text = (
                (root / "reports" / "public" / "compiled_ex5_terminal_bootstrap_summary.json").read_text(
                    encoding="utf-8"
                )
                + (root / "reports" / "public" / "compiled_ex5_terminal_bootstrap_summary.md").read_text(
                    encoding="utf-8"
                )
            )

        self.assertEqual(result["summary"]["status"], HOLD_SOURCE_STATUS)
        self.assertEqual(result["summary"]["bootstrap_method"], "hold_missing_source_or_ex5")
        self.assertIn("mql5_source_or_ex5_not_found", result["summary"]["blocking_issues"])
        self.assertFalse(result["summary"]["compiled_ex5_found_after"])
        self.assertNotIn(str(root), public_text)

    def test_ambiguous_source_returns_hold(self) -> None:
        temp, root, data_dir = _make_root()
        with temp:
            target_mq5 = data_dir / "MQL5" / "Experts" / "Examples" / "MACD Sample.mq5"
            target_mq5.write_text("// source in datadir", encoding="utf-8")
            repo_source = root / "app" / "assets" / "mql5" / "Examples" / "MACD Sample.mq5"
            repo_source.parent.mkdir(parents=True)
            repo_source.write_text("// repo source", encoding="utf-8")

            result = build_compiled_ex5_terminal_bootstrap(root)

        self.assertEqual(result["status"], HOLD_AMBIGUOUS_STATUS)
        self.assertIn("expert_source_ambiguous", result["blocking_issues"])
        self.assertFalse(result["mt5_terminal_run"])

    def test_safe_repo_source_can_compile_with_mocked_metaeditor(self) -> None:
        temp, root, data_dir = _make_root()
        with temp:
            metaeditor = root / "metaeditor64.exe"
            metaeditor.write_text("", encoding="utf-8")
            (root / "config" / "mt5.local.json").write_text(
                json.dumps({"terminal_data_dir": str(data_dir), "metaeditor_path": str(metaeditor)}),
                encoding="utf-8",
            )
            source = root / "app" / "assets" / "mql5" / "Examples" / "MACD Sample.mq5"
            source.parent.mkdir(parents=True)
            source.write_text("// safe repo source", encoding="utf-8")
            target_ex5 = data_dir / "MQL5" / "Experts" / "Examples" / "MACD Sample.ex5"

            def runner(command, *, cwd, timeout, capture_output, text, check):
                self.assertIn("metaeditor64.exe", command[0])
                self.assertFalse(any("terminal64.exe" in part for part in command))
                target_ex5.write_bytes(b"compiled")
                return subprocess.CompletedProcess(command, 0, "", "")

            result = build_compiled_ex5_terminal_bootstrap(root, compile_runner=runner)
            marker = json.loads((root / DEFAULT_READINESS_MARKER).read_text(encoding="utf-8"))

        self.assertEqual(result["status"], PASS_STATUS)
        self.assertEqual(result["bootstrap_method"], METHOD_COMPILED)
        self.assertTrue(result["metaeditor_real_run"])
        self.assertFalse(result["mt5_terminal_run"])
        self.assertTrue(result["compiled_ex5_created_or_copied"])
        self.assertTrue(result["compiled_ex5_found_after"])
        self.assertEqual(marker["bootstrap_method"], METHOD_COMPILED)


if __name__ == "__main__":
    unittest.main()
