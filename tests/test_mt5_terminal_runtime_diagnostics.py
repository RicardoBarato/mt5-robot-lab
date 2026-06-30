import json
import tempfile
import unittest
from pathlib import Path

from app.core.mt5_terminal_runtime_diagnostics import (
    classify_terminal_exit_code,
    generate_terminal_runtime_diagnostics,
    validate_expert_mapping_for_strategy_tester,
    validate_strategy_tester_config_shape,
    validate_terminal_data_dir_consistency,
    validate_tester_ini_for_mt5_runtime,
)


GOOD_INI = """[Tester]
Expert=Examples\\MACD Sample
Symbol=XAUUSD
Period=M5
Model=0
Optimization=0
Report=reports\\private\\real_mt5_smoke\\run\\strategy_tester_report
ReplaceReport=1
ShutdownTerminal=1
"""


class TerminalRuntimeDiagnosticsTests(unittest.TestCase):
    def test_detects_missing_expert(self) -> None:
        result = validate_tester_ini_for_mt5_runtime(GOOD_INI.replace("Expert=Examples\\MACD Sample\n", ""))

        self.assertFalse(result["expert_present"])
        self.assertFalse(result["expert_format_valid"])

    def test_detects_invalid_expert_format(self) -> None:
        result = validate_tester_ini_for_mt5_runtime(GOOD_INI.replace("Examples\\MACD Sample", "C:\\bad\\EA.ex5"))

        self.assertTrue(result["expert_present"])
        self.assertFalse(result["expert_format_valid"])

    def test_detects_missing_report_replace_and_shutdown(self) -> None:
        bad_ini = "\n".join(
            line
            for line in GOOD_INI.splitlines()
            if not line.startswith(("Report=", "ReplaceReport=", "ShutdownTerminal="))
        )
        result = validate_tester_ini_for_mt5_runtime(bad_ini)

        self.assertFalse(result["report_configured"])
        self.assertFalse(result["report_path_private"])
        self.assertFalse(result["replace_report_enabled"])
        self.assertFalse(result["shutdown_terminal_enabled"])

    def test_detects_config_path_not_private(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            public_config = root / "reports" / "public" / "smoke.ini"
            public_config.parent.mkdir(parents=True)
            public_config.write_text(GOOD_INI, encoding="utf-8")

            result = validate_strategy_tester_config_shape(
                GOOD_INI,
                config_path=public_config,
                project_root=root,
                terminal_launch_args=["terminal64.exe", f"/config:{public_config}"],
            )

        self.assertFalse(result["config_path_private"])
        self.assertTrue(result["config_path_accessible"])
        self.assertTrue(result["terminal_launched_with_config"])

    def test_detects_ex5_project_marker_not_terminal_data_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            marker = root / "runs" / "preflight_readiness" / "mvp_014f" / "compiled" / "MACD Sample.ex5"
            marker.parent.mkdir(parents=True)
            marker.write_text("marker", encoding="utf-8")

            mapping = validate_expert_mapping_for_strategy_tester(
                "Examples\\MACD Sample",
                str(marker),
                project_root=root,
            )
            data_dir = validate_terminal_data_dir_consistency({}, str(marker), project_root=root)

        self.assertTrue(mapping["expert_name_matches_compiled_marker"])
        self.assertTrue(mapping["compiled_ex5_marker_is_project_local"])
        self.assertFalse(data_dir["terminal_data_dir_recorded"])
        self.assertFalse(data_dir["data_dir_consistent"])

    def test_unknown_exit_code_classification(self) -> None:
        self.assertEqual(classify_terminal_exit_code(3294954941), "unknown_terminal_exit")

    def test_generate_outputs_are_sanitized_without_opening_mt5(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            marker = root / "runs" / "preflight_readiness" / "mvp_014f" / "compiled" / "MACD Sample.ex5"
            marker.parent.mkdir(parents=True)
            marker.write_text("marker", encoding="utf-8")
            run = root / "reports" / "private" / "real_mt5_smoke" / "run_001"
            run.mkdir(parents=True)
            (run / "mvp_013c_smoke.ini").write_text(GOOD_INI, encoding="utf-8")
            (run / "run_summary_sanitized.json").write_text(
                json.dumps(
                    {
                        "failure_stage": "strategy_tester_failed_before_ea",
                        "exit_code_recorded": 3294954941,
                    }
                ),
                encoding="utf-8",
            )
            (run / "execution_manifest.json").write_text(
                json.dumps(
                    {
                        "command_sanitized": [
                            "<WINDOWS_PATH_REDACTED>\\terminal64.exe",
                            "/config:<WINDOWS_PATH_REDACTED>\\mvp_013c_smoke.ini",
                        ],
                        "returncode": 3294954941,
                    }
                ),
                encoding="utf-8",
            )
            (run / "environment_sanitized.json").write_text(
                json.dumps({"terminal_found": True, "metaeditor_found": True}),
                encoding="utf-8",
            )

            result = generate_terminal_runtime_diagnostics(root)
            public_json = Path(result["files"]["json"])
            public_json_text = public_json.read_text(encoding="utf-8")
            payload = json.loads(public_json_text)

        self.assertEqual(result["status"], "PASS_MVP_014J_RUNTIME_TERMINAL_GAP_DIAGNOSED")
        self.assertFalse(payload["ready_for_real_retry"])
        self.assertFalse(payload["mt5_real_run_new"])
        self.assertIn("compiled_ex5_in_different_data_dir", payload["likely_causes"])
        self.assertNotIn(str(root), public_json_text)
        self.assertNotIn(".ex5", public_json_text.lower())


if __name__ == "__main__":
    unittest.main()
