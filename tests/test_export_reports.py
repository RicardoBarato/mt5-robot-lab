import tempfile
import unittest
from pathlib import Path

from app.core.export_reports import export_sample_summary


class ExportReportTests(unittest.TestCase):
    def test_csv_and_markdown_exported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            outputs = export_sample_summary(Path(tmp))
            self.assertTrue(outputs["csv"].exists())
            self.assertTrue(outputs["md"].exists())
            self.assertIn("xlsx", outputs)


if __name__ == "__main__":
    unittest.main()
