import json
import tempfile
import unittest
from pathlib import Path

from app.core.champion_dna import sample_champion_dna
from app.core.submission_package import (
    REQUIRED_FILES,
    create_submission_package,
    hash_file,
    hash_json,
    load_submission_manifest,
    make_public_submission_summary,
    scan_submission_for_private_artifacts,
    validate_submission_package,
)


class SubmissionPackageTests(unittest.TestCase):
    def _create_package(self, root: Path) -> dict:
        return create_submission_package(
            sample_champion_dna(),
            {"status": "sample_not_real_backtest", "candidate_count": 1},
            {
                "lab_id": "ea-xau",
                "lab_name": "XAU Robot Lab",
                "requested_symbol": "XAUUSD",
                "broker_symbol": "XAUUSD",
                "timeframe": "M5",
                "timeframe_minutes": 5,
                "initial_balance_usd": 10000,
            },
            root / "submission_package_sample",
        )

    def test_create_submission_package_outputs_required_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            result = self._create_package(Path(tmpdir))
            package_dir = Path(result["package_dir"])
            files = {path.name for path in package_dir.iterdir() if path.is_file()}
            self.assertEqual(REQUIRED_FILES, files)
            validation = validate_submission_package(package_dir)
        self.assertEqual(validation["validation_status"], "pass")
        self.assertFalse(result["manifest"]["mt5_real_run"])
        self.assertFalse(result["manifest"]["backtest_real_run"])
        self.assertFalse(result["manifest"]["tournament_100_run"])
        self.assertFalse(result["manifest"]["upload_ready"])

    def test_hash_file_and_hash_json_are_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "sample.json"
            path.write_text('{"a":1}\n', encoding="utf-8")
            self.assertEqual(hash_file(path), hash_file(path))
        self.assertEqual(hash_json({"b": 2, "a": 1}), hash_json({"a": 1, "b": 2}))

    def test_manifest_load_and_public_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            result = self._create_package(Path(tmpdir))
            package_dir = Path(result["package_dir"])
            manifest = load_submission_manifest(package_dir / "submission_manifest.json")
            summary = make_public_submission_summary(manifest)
        self.assertEqual(manifest["validation_status"], "sample_not_real_backtest")
        self.assertIn("Submission Package v1", summary)
        self.assertIn("Upload ready: false", summary)

    def test_private_artifact_scan_detects_forbidden_content(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            package_dir = Path(tmpdir)
            (package_dir / "bad.set").write_text("not allowed", encoding="utf-8")
            findings = scan_submission_for_private_artifacts(package_dir)
        self.assertTrue(findings)

    def test_package_sample_contains_no_forbidden_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            result = self._create_package(Path(tmpdir))
            package_dir = Path(result["package_dir"])
            findings = scan_submission_for_private_artifacts(package_dir)
            validation = json.loads((package_dir / "validation_report.json").read_text(encoding="utf-8"))
        self.assertEqual(findings, [])
        self.assertEqual(validation["validation_status"], "pass")


if __name__ == "__main__":
    unittest.main()
