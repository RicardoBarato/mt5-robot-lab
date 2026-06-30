import tempfile
import unittest
from pathlib import Path

from app.core.mt5_runner import MT5SmokeConfig, MT5SmokeExecutionError, run_mt5_smoke
from app.core.operator_gate import APPROVAL_PHRASE_EN, approve_operator_gate, create_operator_approval_request


def _approved_gate() -> dict[str, object]:
    request = create_operator_approval_request(
        {
            "real_execution_requested": True,
            "smoke_only": True,
            "max_backtests": 1,
            "tournament_100_run": False,
            "credentials_stored": False,
        },
        {
            "mt5_installed": True,
            "terminal_found": True,
            "metaeditor_found": True,
        },
    )
    return approve_operator_gate(request, APPROVAL_PHRASE_EN)


class MT5RunnerTerminalContractTests(unittest.TestCase):
    def test_runner_blocks_failed_terminal_contract_before_process_start(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            tester_config = root / "config.ini"
            tester_config.write_text("[Tester]\n", encoding="utf-8")
            with self.assertRaises(MT5SmokeExecutionError) as caught:
                run_mt5_smoke(
                    MT5SmokeConfig(),
                    allow_real_execution=True,
                    operator_gate=_approved_gate(),
                    terminal_path="terminal64.exe",
                    tester_config_path=str(tester_config),
                    tester_config_allowed_roots=[root],
                    terminal_contract_audit={
                        "ready_for_real_retry": False,
                        "blocking_issues": ["compiled_ex5_not_verified_in_terminal_datadir"],
                    },
                )

        self.assertFalse(caught.exception.attempted_process)
        self.assertFalse(caught.exception.strategy_tester_requested)
        self.assertEqual(caught.exception.failure_stage, "terminal_contract_audit_failed_before_strategy_tester")


if __name__ == "__main__":
    unittest.main()
