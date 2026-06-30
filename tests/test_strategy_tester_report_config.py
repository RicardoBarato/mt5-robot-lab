import unittest

from app.core.strategy_tester_report_config import (
    build_report_output_paths,
    build_strategy_tester_report_contract,
    build_tester_ini_report_lines,
    default_report_export_config,
    expected_report_candidates,
    make_report_export_summary,
    sanitize_report_export_summary,
    validate_report_export_config,
)


class StrategyTesterReportConfigTests(unittest.TestCase):
    def test_default_report_export_config_is_private_and_enabled(self) -> None:
        config = default_report_export_config()
        self.assertTrue(config.report_export_enabled)
        self.assertEqual(config.private_output_root, "reports/private/real_mt5_smoke")
        self.assertTrue(config.replace_report)
        self.assertTrue(config.shutdown_terminal)
        self.assertFalse(config.commit_raw_reports)

    def test_build_report_output_paths_stays_private(self) -> None:
        paths = build_report_output_paths("unit_run_001")
        self.assertIn("reports", paths.private_run_dir)
        self.assertIn("private", paths.private_run_dir)
        self.assertNotIn("reports/public", paths.report_base.replace("\\", "/"))
        self.assertTrue(paths.expected_report_html.endswith(".html"))
        self.assertTrue(paths.expected_report_xml.endswith(".xml"))
        self.assertTrue(paths.expected_report_csv.endswith(".csv"))

    def test_tester_ini_report_lines_include_required_flags(self) -> None:
        contract = build_strategy_tester_report_contract("unit_run_002")
        lines = build_tester_ini_report_lines(contract)
        self.assertTrue(lines[0].startswith("Report="))
        self.assertIn("reports", lines[0])
        self.assertIn("private", lines[0])
        self.assertIn("ReplaceReport=1", lines)
        self.assertIn("ShutdownTerminal=1", lines)

    def test_validate_report_export_config_rejects_public_raw_reports(self) -> None:
        with self.assertRaises(ValueError):
            validate_report_export_config({"private_output_root": "reports/public/raw"})
        with self.assertRaises(ValueError):
            validate_report_export_config({"commit_raw_reports": True})
        with self.assertRaises(ValueError):
            validate_report_export_config({"replace_report": False})
        with self.assertRaises(ValueError):
            validate_report_export_config({"shutdown_terminal": False})

    def test_expected_report_candidates_cover_supported_extensions(self) -> None:
        candidates = expected_report_candidates("unit_run_003")
        suffixes = {candidate.rsplit(".", 1)[-1] for candidate in candidates}
        self.assertTrue({"html", "htm", "xml", "csv", "json"}.issubset(suffixes))
        self.assertTrue(all("reports" in candidate and "private" in candidate for candidate in candidates))

    def test_sanitized_summary_does_not_publish_raw_local_paths(self) -> None:
        summary = sanitize_report_export_summary(
            {
                "report_base": r"C:\Users\Ricardo\AppData\Roaming\MetaQuotes\Terminal\report",
                "expected_report_paths": [r"C:\Users\Ricardo\AppData\Roaming\MetaQuotes\Terminal\report.html"],
            }
        )
        text = str(summary)
        self.assertNotIn("C:\\Users\\Ricardo", text)
        self.assertIn("<APPDATA>", text)

    def test_make_report_export_summary_is_public_safe(self) -> None:
        summary = make_report_export_summary()
        self.assertTrue(summary["report_export_configured"])
        self.assertTrue(summary["private_artifacts_only"])
        self.assertTrue(summary["public_summary_sanitized"])
        self.assertFalse(summary["commit_raw_reports"])
        self.assertNotIn("reports/public", str(summary))


if __name__ == "__main__":
    unittest.main()
