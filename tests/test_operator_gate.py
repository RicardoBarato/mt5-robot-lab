import tempfile
import unittest
from pathlib import Path

from app.core.mt5_runner import run_mt5_smoke
from app.core.operator_gate import (
    APPROVAL_PHRASE_EN,
    APPROVAL_PHRASE_PT,
    approve_operator_gate,
    create_operator_approval_request,
    default_operator_gate,
    is_real_mt5_execution_allowed,
    load_operator_gate_manifest,
    reject_operator_gate,
    save_operator_gate_manifest,
    write_operator_gate_preview,
)


READY_DIAGNOSTICS = {
    "mt5_installed": True,
    "terminal_found": True,
    "metaeditor_found": True,
}


class OperatorGateTests(unittest.TestCase):
    def ready_request(self, **overrides):
        config = {
            "real_execution_requested": True,
            "smoke_only": True,
            "max_backtests": 1,
            "tournament_100_run": False,
            "credentials_stored": False,
        }
        config.update(overrides)
        return create_operator_approval_request(config, READY_DIAGNOSTICS)

    def test_default_gate_blocks(self) -> None:
        gate = default_operator_gate()
        self.assertFalse(is_real_mt5_execution_allowed(gate))
        self.assertFalse(gate["mt5_real_run"])
        self.assertFalse(gate["backtest_real_run"])

    def test_wrong_phrase_blocks(self) -> None:
        gate = approve_operator_gate(self.ready_request(), "wrong phrase")
        self.assertFalse(gate["approval_phrase_matched"])
        self.assertFalse(gate["execution_allowed"])

    def test_english_phrase_approves_only_when_ready(self) -> None:
        gate = approve_operator_gate(self.ready_request(), APPROVAL_PHRASE_EN)
        self.assertTrue(gate["approval_phrase_matched"])
        self.assertTrue(gate["execution_allowed"])

    def test_portuguese_phrase_approves_only_when_ready(self) -> None:
        gate = approve_operator_gate(self.ready_request(), APPROVAL_PHRASE_PT)
        self.assertTrue(gate["approval_phrase_matched"])
        self.assertTrue(gate["execution_allowed"])

    def test_technical_conditions_block_even_with_phrase(self) -> None:
        not_ready = create_operator_approval_request(
            {"real_execution_requested": True, "max_backtests": 1},
            {"mt5_installed": False, "terminal_found": False, "metaeditor_found": False},
        )
        gate = approve_operator_gate(not_ready, APPROVAL_PHRASE_EN)
        self.assertFalse(gate["execution_allowed"])

    def test_max_backtests_gt_one_blocks(self) -> None:
        gate = approve_operator_gate(self.ready_request(max_backtests=2), APPROVAL_PHRASE_EN)
        self.assertFalse(gate["execution_allowed"])

    def test_tournament_100_blocks(self) -> None:
        gate = approve_operator_gate(self.ready_request(tournament_100_run=True), APPROVAL_PHRASE_EN)
        self.assertFalse(gate["execution_allowed"])

    def test_credentials_stored_blocks(self) -> None:
        gate = approve_operator_gate(self.ready_request(credentials_stored=True), APPROVAL_PHRASE_EN)
        self.assertFalse(gate["execution_allowed"])
        self.assertFalse(gate["no_credentials_stored"])

    def test_reject_operator_gate_blocks(self) -> None:
        gate = reject_operator_gate(self.ready_request(), "manual rejection")
        self.assertEqual(gate["status"], "operator_gate_rejected")
        self.assertFalse(gate["execution_allowed"])

    def test_save_and_load_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "operator_gate.json"
            saved = save_operator_gate_manifest(default_operator_gate(), path)
            loaded = load_operator_gate_manifest(path)
        self.assertEqual(saved["status"], loaded["status"])
        self.assertFalse(loaded["execution_allowed"])

    def test_preview_outputs_are_safe(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            result = write_operator_gate_preview(Path(tmpdir))
            json_path = Path(result["files"]["json"])
            md_path = Path(result["files"]["markdown"])
            text = (json_path.read_text(encoding="utf-8") + md_path.read_text(encoding="utf-8")).lower()
        self.assertTrue(json_path.name.endswith(".json"))
        self.assertTrue(md_path.name.endswith(".md"))
        self.assertFalse(result["execution_allowed"])
        self.assertFalse(result["mt5_real_run"])
        self.assertFalse(result["backtest_real_run"])
        for term in ["password", "token", "secret", "account_number", "broker_password", "real account"]:
            self.assertNotIn(term, text)

    def test_runner_blocks_real_execution_without_gate(self) -> None:
        result = run_mt5_smoke(allow_real_execution=True)
        payload = result.public_payload()
        self.assertEqual(payload["status"], "blocked_by_operator_gate")
        self.assertFalse(payload["mt5_real_run"])
        self.assertFalse(payload["backtest_real_run"])
        self.assertFalse(payload["strategy_tester_executed"])


if __name__ == "__main__":
    unittest.main()
