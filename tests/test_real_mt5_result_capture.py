import json
import tempfile
import unittest
from pathlib import Path

from app.core.real_mt5_result_capture import create_capture_context, discover_capture_artifacts, write_capture_manifest


class RealMT5ResultCaptureTests(unittest.TestCase):
    def test_capture_contract_creates_private_local_manifest_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            context = create_capture_context(root, run_id="unit_run_001")
            public_root = root / "reports" / "public"
            manifest = json.loads(context.manifest_path.read_text(encoding="utf-8"))

        self.assertEqual(context.run_id, "unit_run_001")
        self.assertEqual(context.manifest_path.name, "run_manifest.local.json")
        self.assertIn("reports", context.manifest_path.parts)
        self.assertIn("private", context.manifest_path.parts)
        self.assertFalse(public_root.exists())
        self.assertEqual(manifest["capture_status"], "initialized")
        self.assertEqual(manifest["parse_status"], "not_parsed")

    def test_capture_manifest_discovers_only_local_run_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            context = create_capture_context(root, run_id="unit_run_002")
            (context.run_dir / "strategy_tester_report.html").write_text("synthetic", encoding="utf-8")
            (context.run_dir / "stdout.txt").write_text("", encoding="utf-8")
            (context.run_dir / "ignored.bin").write_text("", encoding="utf-8")
            artifacts = discover_capture_artifacts(context.run_dir)
            manifest = write_capture_manifest(
                context,
                return_code=0,
                capture_status="report_found",
                parse_status="parsed",
            )

        self.assertEqual(artifacts["observed_report_files"], ["strategy_tester_report.html"])
        self.assertEqual(artifacts["observed_log_files"], ["stdout.txt"])
        self.assertEqual(manifest.return_code, 0)
        self.assertEqual(manifest.capture_status, "report_found")
        self.assertEqual(manifest.parse_status, "parsed")

    def test_run_id_must_not_escape_private_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            with self.assertRaises(ValueError):
                create_capture_context(Path(tmpdir), run_id="../bad")


if __name__ == "__main__":
    unittest.main()
