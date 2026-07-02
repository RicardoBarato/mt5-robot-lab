import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ADAPTER = ROOT / "frontend" / "mt5-robot-lab-premium.html"
CLADE_TEMPLATE = ROOT / "frontend" / "templates" / "clade" / "CLADE.dc.html"
CLADE_SUPPORT = ROOT / "frontend" / "templates" / "clade" / "support.js"


class FrontendTemplateIntakeTests(unittest.TestCase):
    def test_premium_adapter_contains_required_product_terms(self) -> None:
        text = ADAPTER.read_text(encoding="utf-8")
        self.assertIn("MT5 Robot Lab", text)
        self.assertIn("Evolutionary Backtest Lab", text)
        self.assertIn("10 / 50 / 100", text)
        self.assertIn("Custom >= 10", text)
        self.assertRegex(text, re.compile(r"unified ranking", re.IGNORECASE))
        self.assertIn("max_concurrent_mt5", text)
        self.assertIn("Close MT5 after each run", text)
        self.assertIn("Operator Gate V2", text)
        self.assertIn("Terminal Contract Audit", text)
        self.assertIn("Preflight", text)
        self.assertIn("Runtime Dry Run", text)
        self.assertIn("Safe Smoke EA", text)
        self.assertIn("Report Capture", text)
        self.assertIn('script src="templates/clade/support.js"', text)

    def test_clade_template_assets_are_preserved(self) -> None:
        self.assertTrue(CLADE_TEMPLATE.exists())
        self.assertTrue(CLADE_SUPPORT.exists())
        text = ADAPTER.read_text(encoding="utf-8")
        self.assertIn("<x-dc>", text)
        self.assertIn("<sc-for", text)

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
