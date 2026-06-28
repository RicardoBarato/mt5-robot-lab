import unittest
from pathlib import Path

from app.core.app_config import load_app_config
from app.ui.screens import INTELLIGENCE_MODE_OPTIONS, SCREEN_ORDER, NavigationController, build_screen_registry


ROOT = Path(__file__).resolve().parents[1]


class DesktopNavigationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = load_app_config(ROOT / "config" / "app.default.json")
        self.screens = build_screen_registry(self.config)

    def test_screen_registry_has_11_screens(self) -> None:
        self.assertEqual(len(self.screens), 11)

    def test_ids_are_unique_and_ordered(self) -> None:
        ids = [screen.id for screen in self.screens]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(tuple(ids), SCREEN_ORDER)

    def test_default_screen_is_welcome(self) -> None:
        controller = NavigationController(self.screens)
        self.assertEqual(controller.current_screen, "welcome")
        self.assertEqual(controller.get_current_definition().title, "MT5 Robot Lab")

    def test_navigation_next_previous_and_go_to(self) -> None:
        controller = NavigationController(self.screens)
        self.assertEqual(controller.next_screen().id, "lab_selection")
        self.assertEqual(controller.previous_screen().id, "welcome")
        self.assertEqual(controller.go_to_screen("champion_dna").id, "champion_dna")
        self.assertEqual(controller.current_screen, "champion_dna")

    def test_config_defaults_are_visible(self) -> None:
        tournament = next(screen for screen in self.screens if screen.id == "tournament_setup")
        cards = dict(tournament.cards)
        self.assertEqual(cards["Backtest years"], "2")
        self.assertEqual(cards["Initial balance USD"], "10000")
        self.assertEqual(cards["Max backtests"], "100")
        self.assertEqual(cards["Champion count"], "10")

    def test_external_lab_path_is_display_only(self) -> None:
        lab_screen = next(screen for screen in self.screens if screen.id == "lab_selection")
        cards = dict(lab_screen.cards)
        self.assertEqual(cards["Path"], "E:\\ea-xau")
        self.assertEqual(cards["Write access"], "not used by this MVP")

    def test_intelligence_mode_default_is_local_auto(self) -> None:
        self.assertEqual(self.config.default_intelligence_mode, "local_auto")
        modes = {option["mode"] for option in INTELLIGENCE_MODE_OPTIONS}
        self.assertEqual(modes, {"local_auto", "codex_assisted", "seeds_only"})


if __name__ == "__main__":
    unittest.main()
