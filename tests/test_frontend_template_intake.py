import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ADAPTER = ROOT / "frontend" / "mt5-robot-lab-premium.html"


class FrontendTemplateIntakeTests(unittest.TestCase):
    def test_premium_adapter_contains_required_product_terms(self) -> None:
        text = ADAPTER.read_text(encoding="utf-8")
        self.assertIn("MT5 Robot Lab", text)
        self.assertIn("Evolutionary Backtest Lab", text)
        self.assertIn("10 Recommended", text)
        self.assertIn("50 Deep", text)
        self.assertIn("100 Advanced", text)
        self.assertIn("Custom &gt;= 10", text)
        self.assertIn("Unified ranking", text)
        self.assertIn("Search budget transparency", text)
        self.assertIn("max_concurrent_mt5", text)
        self.assertIn("Close MT5 after each run", text)
        self.assertIn("Operator Gate V2", text)
        self.assertIn("Terminal Contract Audit", text)
        self.assertIn("Preflight", text)
        self.assertIn("Runtime Dry Run", text)
        self.assertIn("Safe Smoke EA", text)
        self.assertIn("Report Capture", text)

    def test_premium_adapter_has_no_private_or_local_references(self) -> None:
        text = ADAPTER.read_text(encoding="utf-8")
        lower = text.lower()
        self.assertNotIn("reports/private", lower)
        self.assertNotIn("password", lower)
        self.assertNotIn("token", lower)
        self.assertNotIn("secret", lower)
        self.assertNotIn("file://", lower)
        self.assertIsNone(re.search(r"(?i)[a-z]:[\\/]", text))


if __name__ == "__main__":
    unittest.main()
