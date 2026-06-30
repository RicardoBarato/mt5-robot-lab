import json
import tempfile
import unittest
from pathlib import Path

from app.core.compiled_ex5_readiness import write_compiled_ex5_readiness_marker
from app.core.strategy_tester_report_config import build_strategy_tester_report_contract
from app.core.terminal_contract_audit import build_terminal_contract_audit, generate_terminal_contract_audit


READY_ENV = {
    "mt5_detected": True,
    "terminal_found": True,
    "metaeditor_found": True,
    "ready_for_real_smoke": True,
}


def _ready_root(expert: str = "RBRiskEngine\\RBRiskEngine_Public") -> tuple[tempfile.TemporaryDirectory[str], Path, Path]:
    tmp = tempfile.TemporaryDirectory()
    root = Path(tmp.name)
    data_dir = root / "terminal_data"
    parts = expert.split("\\")
    ex5 = data_dir / "MQL5" / "Experts" / Path(*parts).with_suffix(".ex5")
    ex5.parent.mkdir(parents=True)
    ex5.write_text("compiled fake", encoding="utf-8")
    write_compiled_ex5_readiness_marker(
        root,
        terminal_data_dir=data_dir,
        expert_relative_path=expert,
    )
    return tmp, root, data_dir


class TerminalContractAuditTests(unittest.TestCase):
    def test_terminal_contract_audit_passes_with_datadir_marker_and_tester_mapping(self) -> None:
        tmp, root, data_dir = _ready_root()
        self.addCleanup(tmp.cleanup)
        result = build_terminal_contract_audit(
            root,
            environment={**READY_ENV, "terminal_data_dir": str(data_dir)},
            expert="RBRiskEngine\\RBRiskEngine_Public",
        )

        self.assertEqual(result["terminal_contract_audit"], "PASS")
        self.assertTrue(result["ready_for_real_retry"])
        self.assertTrue(result["compiled_ex5_verified_in_terminal_datadir"])
        self.assertTrue(result["expert_mapping_valid_for_tester"])
        self.assertEqual(result["blocking_issues"], [])

    def test_terminal_contract_audit_blocks_public_report_path(self) -> None:
        tmp, root, data_dir = _ready_root()
        self.addCleanup(tmp.cleanup)
        report = build_strategy_tester_report_contract("unit_terminal_contract")
        report = {**report, "report_base": "reports/public/bad_report"}
        result = build_terminal_contract_audit(
            root,
            environment={**READY_ENV, "terminal_data_dir": str(data_dir)},
            expert="RBRiskEngine\\RBRiskEngine_Public",
            report_contract=report,
        )

        self.assertEqual(result["terminal_contract_audit"], "FAIL")
        self.assertIn("report_base_not_private", result["blocking_issues"])

    def test_terminal_contract_audit_blocks_bad_tester_ini_contract(self) -> None:
        tmp, root, data_dir = _ready_root("Examples\\MACD Sample")
        self.addCleanup(tmp.cleanup)
        bad_ini = "\n".join(
            [
                "[Tester]",
                "Expert=C:\\absolute\\EA.ex5",
                "Symbol=XAUUSD",
                "Period=M5",
                "Optimization=1",
                "Report=reports\\public\\bad",
                "ReplaceReport=0",
                "ShutdownTerminal=0",
            ]
        )
        result = build_terminal_contract_audit(
            root,
            environment={**READY_ENV, "terminal_data_dir": str(data_dir)},
            tester_ini_text=bad_ini,
        )

        self.assertEqual(result["terminal_contract_audit"], "FAIL")
        self.assertIn("expert_absolute_path_blocked", result["blocking_issues"])
        self.assertIn("expert_must_not_include_extension", result["blocking_issues"])
        self.assertIn("report_path_not_private", result["blocking_issues"])
        self.assertIn("replace_report_required", result["blocking_issues"])
        self.assertIn("shutdown_terminal_required", result["blocking_issues"])

    def test_terminal_contract_audit_blocks_without_datadir_marker(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = build_terminal_contract_audit(Path(tmp), environment=READY_ENV)

        self.assertEqual(result["terminal_contract_audit"], "FAIL")
        self.assertFalse(result["ready_for_real_retry"])
        self.assertIn("terminal_data_dir_missing", result["blocking_issues"])
        self.assertIn("compiled_ex5_readiness_marker_missing", result["blocking_issues"])

    def test_generate_terminal_contract_audit_writes_sanitized_public_outputs_without_execution(self) -> None:
        tmp, root, data_dir = _ready_root("Examples\\MACD Sample")
        self.addCleanup(tmp.cleanup)
        # Force the default command path to use marker metadata only; no MT5 is launched.
        result = generate_terminal_contract_audit(root)
        public_json = root / "reports" / "public" / "terminal_contract_audit_summary.json"
        public_md = root / "reports" / "public" / "terminal_contract_audit_summary.md"
        payload = json.loads(public_json.read_text(encoding="utf-8"))
        public_text = public_json.read_text(encoding="utf-8") + public_md.read_text(encoding="utf-8")

        self.assertEqual(result["status"], "PASS_MVP_014K_TERMINAL_DATADIR_EX5_VERIFICATION_COMPLETED")
        self.assertEqual(payload["terminal_contract_audit"], "PASS")
        self.assertFalse(payload["mt5_real_run_new"])
        self.assertFalse(payload["strategy_tester_run_new"])
        self.assertFalse(payload["ea_executed_new"])
        self.assertNotIn(str(root), public_text)
        self.assertNotIn(str(data_dir), public_text)
        self.assertNotIn(".ex5", public_text.lower())
        self.assertNotIn(".set", public_text.lower())


if __name__ == "__main__":
    unittest.main()
