import json
import os
import tempfile
import time
import unittest
from pathlib import Path

from app.core.real_mt5_preflight import ensure_ignored_preflight_ex5_marker
from app.core.real_mt5_runtime_contract import (
    build_real_mt5_runtime_contract,
    generate_real_mt5_runtime_dry_run,
)


READY_ENVIRONMENT = {
    "mt5_detected": True,
    "terminal_found": True,
    "metaeditor_found": True,
    "ready_for_real_smoke": True,
    "terminal_path_sanitized": "<WINDOWS_PATH_REDACTED>\\terminal64.exe",
    "metaeditor_path_sanitized": "<WINDOWS_PATH_REDACTED>\\metaeditor64.exe",
}


class RealMT5RuntimeContractTests(unittest.TestCase):
    def test_preflight_marker_is_attached_to_runtime_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            ensure_ignored_preflight_ex5_marker(root)
            contract = build_real_mt5_runtime_contract(root, environment=READY_ENVIRONMENT)

        self.assertTrue(contract["ready_for_retry"])
        self.assertTrue(contract["compiled_ex5_configured"])
        self.assertTrue(contract["ex5_readiness_marker_present"])
        self.assertEqual(contract["blocking_issues"], [])
        self.assertEqual(contract["runtime_preflight"]["status"], "ready_for_one_run_retry")

    def test_runtime_contract_blocks_missing_marker(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            contract = build_real_mt5_runtime_contract(Path(tmpdir), environment=READY_ENVIRONMENT)

        self.assertFalse(contract["ready_for_retry"])
        self.assertIn("compiled_ex5_marker_missing", contract["blocking_issues"])

    def test_runtime_contract_blocks_stale_marker(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            marker = ensure_ignored_preflight_ex5_marker(root)
            old = time.time() - 3600
            os.utime(marker, (old, old))
            contract = build_real_mt5_runtime_contract(
                root,
                environment=READY_ENVIRONMENT,
                marker_max_age_seconds=1,
            )

        self.assertFalse(contract["ready_for_retry"])
        self.assertTrue(contract["ex5_readiness_marker_stale"])
        self.assertIn("compiled_ex5_marker_stale", contract["blocking_issues"])

    def test_runtime_contract_blocks_empty_expert_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            ensure_ignored_preflight_ex5_marker(root)
            contract = build_real_mt5_runtime_contract(root, environment=READY_ENVIRONMENT, expert_path="")

        self.assertFalse(contract["ready_for_retry"])
        self.assertIn("expert_path_missing", contract["blocking_issues"])

    def test_runtime_contract_blocks_non_one_backtest_scope(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            ensure_ignored_preflight_ex5_marker(root)
            contract = build_real_mt5_runtime_contract(root, environment=READY_ENVIRONMENT, max_backtests=2)

        self.assertFalse(contract["ready_for_retry"])
        self.assertIn("max_backtests_must_equal_1", contract["blocking_issues"])

    def test_runtime_contract_blocks_non_smoke_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            ensure_ignored_preflight_ex5_marker(root)
            contract = build_real_mt5_runtime_contract(root, environment=READY_ENVIRONMENT, smoke_only=False)

        self.assertFalse(contract["ready_for_retry"])
        self.assertIn("smoke_only_required", contract["blocking_issues"])

    def test_runtime_contract_blocks_missing_close_after_run_policy(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            ensure_ignored_preflight_ex5_marker(root)
            contract = build_real_mt5_runtime_contract(
                root,
                environment=READY_ENVIRONMENT,
                close_after_run_policy="",
            )

        self.assertFalse(contract["ready_for_retry"])
        self.assertIn("close_after_run_policy_missing", contract["blocking_issues"])

    def test_runtime_dry_run_writes_public_sanitized_summary_without_execution(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            ensure_ignored_preflight_ex5_marker(root)
            result = generate_real_mt5_runtime_dry_run(root, environment_override=READY_ENVIRONMENT)
            public_json = root / "reports" / "public" / "real_mt5_runtime_dry_run_summary.json"
            public_md = root / "reports" / "public" / "real_mt5_runtime_dry_run_summary.md"
            payload = json.loads(public_json.read_text(encoding="utf-8"))
            public_text = public_json.read_text(encoding="utf-8") + public_md.read_text(encoding="utf-8")

        self.assertEqual(result["status"], "PASS_MVP_014H_RUNTIME_DRY_RUN_READY")
        self.assertTrue(payload["compiled_ex5_configured"])
        self.assertTrue(payload["ready_for_real_retry"])
        self.assertFalse(payload["mt5_real_run_new"])
        self.assertFalse(payload["backtest_real_run_new"])
        self.assertFalse(payload["strategy_tester_run_new"])
        self.assertFalse(payload["ea_executed_new"])
        self.assertNotIn(".ex5", public_text)
        self.assertIn("<COMPILED_EA_FILE>", public_text)


if __name__ == "__main__":
    unittest.main()
