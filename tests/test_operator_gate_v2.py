import io
import json
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from app.core.operator_gate import (
    APPROVAL_METHOD_CLI_FLAG,
    OPERATOR_GATE_VERSION_V2,
    approve_one_run_local_smoke,
    create_operator_approval_request,
    default_operator_gate,
)
from app.mt5_robot_lab_app import main


READY_DIAGNOSTICS = {
    "mt5_installed": True,
    "terminal_found": True,
    "metaeditor_found": True,
}


def ready_request(**overrides):
    config = {
        "real_execution_requested": True,
        "smoke_only": True,
        "max_backtests": 1,
        "max_runs": 1,
        "strategy_tester_runs": 1,
        "tournament_100_run": False,
        "backtest_budget_run": False,
        "optimization_requested": False,
        "loop_execution": False,
        "credentials_stored": False,
        "mt5_close_after_run_authorized": True,
    }
    config.update(overrides)
    return create_operator_approval_request(config, READY_DIAGNOSTICS)


class OperatorGateV2Tests(unittest.TestCase):
    def test_default_gate_v2_blocks_without_flag(self) -> None:
        gate = default_operator_gate()
        self.assertEqual(gate["operator_gate_version"], OPERATOR_GATE_VERSION_V2)
        self.assertEqual(gate["operator_approval_method"], "none")
        self.assertFalse(gate["operator_approval_persistent"])
        self.assertFalse(gate["one_run_local_smoke_approved"])
        self.assertFalse(gate["execution_allowed"])

    def test_cli_flag_approves_one_run_only(self) -> None:
        gate = approve_one_run_local_smoke(ready_request())
        self.assertTrue(gate["execution_allowed"])
        self.assertEqual(gate["operator_gate_version"], OPERATOR_GATE_VERSION_V2)
        self.assertEqual(gate["operator_approval_method"], APPROVAL_METHOD_CLI_FLAG)
        self.assertFalse(gate["operator_approval_persistent"])
        self.assertTrue(gate["one_run_local_smoke_approved"])
        self.assertEqual(gate["max_backtests"], 1)
        self.assertEqual(gate["max_runs"], 1)
        self.assertEqual(gate["strategy_tester_runs"], 1)

    def test_cli_flag_blocks_tournament_budget_optimization_loop_and_missing_close(self) -> None:
        blocked_configs = [
            {"max_backtests": 10},
            {"max_backtests": 50},
            {"max_backtests": 100},
            {"backtest_budget_run": True},
            {"tournament_100_run": True},
            {"optimization_requested": True},
            {"loop_execution": True},
            {"mt5_close_after_run_authorized": False},
            {"max_runs": 2},
            {"strategy_tester_runs": 2},
        ]
        for config in blocked_configs:
            with self.subTest(config=config):
                gate = approve_one_run_local_smoke(ready_request(**config))
                self.assertFalse(gate["execution_allowed"])

    def test_cli_flag_blocks_when_terminal_not_ready(self) -> None:
        request = create_operator_approval_request(
            {
                "real_execution_requested": True,
                "smoke_only": True,
                "max_backtests": 1,
                "credentials_stored": False,
                "mt5_close_after_run_authorized": True,
            },
            {"mt5_installed": False, "terminal_found": False, "metaeditor_found": False},
        )
        gate = approve_one_run_local_smoke(request)
        self.assertFalse(gate["execution_allowed"])

    def test_cli_without_approval_flag_returns_hold_without_runner(self) -> None:
        with patch("app.mt5_robot_lab_app.execute_one_run_real_mt5_smoke") as runner:
            output = io.StringIO()
            with redirect_stdout(output):
                code = main(["--run-real-mt5-smoke-once"])

        self.assertEqual(code, 2)
        runner.assert_not_called()
        payload = json.loads(output.getvalue())
        self.assertEqual(payload["status"], "HOLD_OPERATOR_APPROVAL_REQUIRED")
        self.assertEqual(payload["operator_gate_version"], OPERATOR_GATE_VERSION_V2)
        self.assertFalse(payload["operator_approval_persistent"])
        self.assertFalse(payload["mt5_real_run"])

    def test_cli_with_approval_flag_dispatches_one_run_v2(self) -> None:
        fake_result = {
            "status": "fake_no_real_run_in_unit_test",
            "summary": {
                "operator_gate_version": OPERATOR_GATE_VERSION_V2,
                "operator_approval_method": APPROVAL_METHOD_CLI_FLAG,
                "operator_approval_persistent": False,
            },
        }
        with patch("app.mt5_robot_lab_app.execute_one_run_real_mt5_smoke", return_value=fake_result) as runner:
            output = io.StringIO()
            with redirect_stdout(output):
                code = main(["--run-real-mt5-smoke-once", "--approve-one-run-local-smoke"])

        self.assertEqual(code, 0)
        runner.assert_called_once()
        self.assertTrue(runner.call_args.kwargs["approve_one_run_local_smoke_flag"])
        payload = json.loads(output.getvalue())
        self.assertEqual(payload["status"], "fake_no_real_run_in_unit_test")


if __name__ == "__main__":
    unittest.main()
