import unittest
from pathlib import Path

from app.core.app_config import load_app_config, validate_app_config
from app.core.intelligence_modes import validate_intelligence_modes


ROOT = Path(__file__).resolve().parents[1]


class ConfigTests(unittest.TestCase):
    def test_default_config_valid(self) -> None:
        config = load_app_config(ROOT / "config" / "app.default.json")
        validate_app_config(config)
        validate_intelligence_modes(config.supported_intelligence_modes, config.default_intelligence_mode)
        self.assertEqual(config.product_name, "MT5 Robot Lab")
        self.assertFalse(config.mt5_installer_bundled)
        self.assertFalse(config.codex_required)
        self.assertFalse(config.cli_required_for_end_user)


if __name__ == "__main__":
    unittest.main()
