import tempfile
import unittest
from pathlib import Path

from app.core.submission_package import scan_submission_for_private_artifacts


class SubmissionPrivatePathScanTests(unittest.TestCase):
    def test_detects_private_windows_and_file_uri_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "summary.json").write_text(
                '{"report": "file:///C:/Users/Ricardo/AppData/Local/report.json"}\n',
                encoding="utf-8",
            )
            findings = scan_submission_for_private_artifacts(root)
        self.assertTrue(any(item["reason"] == "private_local_path" for item in findings))

    def test_detects_forbidden_artifact_extensions(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "candidate.ex5").write_text("", encoding="utf-8")
            findings = scan_submission_for_private_artifacts(root)
        self.assertTrue(any(item["reason"] == "forbidden_file_pattern" for item in findings))


if __name__ == "__main__":
    unittest.main()
