import tempfile
import unittest
from pathlib import Path

from app.core.real_mt5_preflight import (
    RealMT5PreflightConfig,
    build_real_mt5_preflight_check,
    classify_failure_stage,
    generate_real_mt5_preflight_readiness,
)
from app.core.strategy_tester_report_config import build_strategy_tester_report_contract, build_tester_ini_report_lines


def _tester_ini(contract: dict[str, object]) -> str:
    return "\n".join(
        [
            "[Tester]",
            "Expert=MT5RobotLab\\SmokeHarness_Public",
            "Symbol=XAUUSD",
            "Period=M5",
            "Model=0",
            "Optimization=0",
            "Deposit=10000",
            "Currency=USD",
            *build_tester_ini_report_lines(contract),
            "",
        ]
    )


class RealMT5PreflightTests(unittest.TestCase):
    def test_preflight_blocks_missing_compiled_ex5(self) -> None:
        contract = build_strategy_tester_report_contract("unit_preflight_001")
        summary = build_real_mt5_preflight_check(
            RealMT5PreflightConfig(
                terminal_found=True,
                metaeditor_found=True,
                operator_gate_approved=True,
            ),
            contract,
            {"candidate_id": "unit"},
            tester_ini_text=_tester_ini(contract),
        )

        self.assertEqual(summary["status"], "blocked_preflight_failed")
        self.assertFalse(summary["ready_for_real_retry"])
        self.assertTrue(summary["expert_path_checked"])
        self.assertTrue(summary["compiled_ex5_checked"])
        self.assertTrue(summary["report_export_contract_checked"])
        self.assertTrue(summary["report_path_privacy_checked"])
        self.assertIn("compiled_ex5_not_configured", summary["blocking_issues"])

    def test_preflight_passes_when_all_contracts_are_explicit(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            ex5_path = Path(tmpdir) / "SmokeHarness_Public.ex5"
            ex5_path.write_text("compiled placeholder", encoding="utf-8")
            contract = build_strategy_tester_report_contract("unit_preflight_002")
            summary = build_real_mt5_preflight_check(
                RealMT5PreflightConfig(
                    terminal_found=True,
                    metaeditor_found=True,
                    expected_ex5_path=str(ex5_path),
                    operator_gate_approved=True,
                ),
                contract,
                {"candidate_id": "unit"},
                tester_ini_text=_tester_ini(contract),
            )

        self.assertEqual(summary["status"], "ready_for_one_run_retry")
        self.assertTrue(summary["ready_for_real_retry"])
        self.assertEqual(summary["blocking_issues"], [])

    def test_tester_ini_contract_requires_private_report(self) -> None:
        contract = build_strategy_tester_report_contract("unit_preflight_003")
        bad_ini = _tester_ini(contract).replace("reports\\private", "reports\\public").replace(
            "reports/private", "reports/public"
        )
        summary = build_real_mt5_preflight_check(
            RealMT5PreflightConfig(
                terminal_found=True,
                metaeditor_found=True,
                operator_gate_approved=True,
            ),
            contract,
            {"candidate_id": "unit"},
            tester_ini_text=bad_ini,
        )

        self.assertFalse(summary["ready_for_real_retry"])
        self.assertIn("tester_ini_report_path_not_private", summary["blocking_issues"])

    def test_tester_ini_contract_requires_report_line(self) -> None:
        contract = build_strategy_tester_report_contract("unit_preflight_004")
        bad_ini = "\n".join(line for line in _tester_ini(contract).splitlines() if not line.startswith("Report="))
        summary = build_real_mt5_preflight_check(
            RealMT5PreflightConfig(
                terminal_found=True,
                metaeditor_found=True,
                operator_gate_approved=True,
            ),
            contract,
            {"candidate_id": "unit"},
            tester_ini_text=bad_ini,
        )

        self.assertFalse(summary["ready_for_real_retry"])
        self.assertIn("tester_ini_contract_invalid", summary["blocking_issues"])

    def test_tester_ini_contract_requires_replace_report_and_shutdown(self) -> None:
        contract = build_strategy_tester_report_contract("unit_preflight_005")
        bad_ini = _tester_ini(contract).replace("ReplaceReport=1", "ReplaceReport=0").replace(
            "ShutdownTerminal=1", "ShutdownTerminal=0"
        )
        summary = build_real_mt5_preflight_check(
            RealMT5PreflightConfig(
                terminal_found=True,
                metaeditor_found=True,
                operator_gate_approved=True,
            ),
            contract,
            {"candidate_id": "unit"},
            tester_ini_text=bad_ini,
        )

        self.assertFalse(summary["ready_for_real_retry"])
        self.assertIn("tester_ini_contract_invalid", summary["blocking_issues"])

    def test_preflight_requires_close_after_run_policy(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            ex5_path = Path(tmpdir) / "SmokeHarness_Public.ex5"
            ex5_path.write_text("compiled placeholder", encoding="utf-8")
            contract = build_strategy_tester_report_contract("unit_preflight_006")
            summary = build_real_mt5_preflight_check(
                RealMT5PreflightConfig(
                    terminal_found=True,
                    metaeditor_found=True,
                    expected_ex5_path=str(ex5_path),
                    operator_gate_approved=True,
                    close_after_run_policy="missing",
                ),
                contract,
                {"candidate_id": "unit"},
                tester_ini_text=_tester_ini(contract),
            )

        self.assertFalse(summary["ready_for_real_retry"])
        self.assertIn("close_after_run_policy_missing", summary["blocking_issues"])

    def test_failure_stage_classifies_nonzero_no_report_before_ea(self) -> None:
        stage = classify_failure_stage(
            exit_code=3294954941,
            report_file_found=False,
            strategy_tester_requested=True,
            backtest_real_run=False,
            ea_executed=False,
        )
        self.assertEqual(stage, "strategy_tester_failed_before_ea")

    def test_generate_preflight_readiness_is_public_safe_and_non_executing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            result = generate_real_mt5_preflight_readiness(root)
            payload = result["summary"]
            public_text = (
                (root / "reports" / "public" / "real_mt5_preflight_summary.json").read_text(encoding="utf-8")
                + (root / "reports" / "public" / "real_mt5_preflight_summary.md").read_text(encoding="utf-8")
            )

        self.assertEqual(result["status"], "HOLD_MVP_014F_PREFLIGHT_BLOCKED")
        self.assertFalse(payload["ready_for_retry"])
        self.assertTrue(
            "terminal_data_dir_missing" in payload["blocking_issues"]
            or "compiled_ex5_readiness_marker_missing" in payload["blocking_issues"]
        )
        self.assertEqual(payload["terminal_contract_audit"], "FAIL")
        self.assertFalse(payload["mt5_real_run_new"])
        self.assertFalse(payload["backtest_real_run_new"])
        self.assertFalse(payload["strategy_tester_run_new"])
        self.assertFalse(payload["ea_executed_new"])
        for marker in ["C:\\Users\\", "C:/Users/", "file://", "\\\\server\\"]:
            self.assertNotIn(marker, public_text)
        self.assertNotIn(".ex5", public_text)
        self.assertIn("<COMPILED_EA_FILE>", public_text)


if __name__ == "__main__":
    unittest.main()
