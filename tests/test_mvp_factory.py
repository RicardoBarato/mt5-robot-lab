import subprocess
import sys
import unittest
from pathlib import Path

from factory.mvp_factory import VALID_STATUSES, load_queue, next_mvp, render_prompt, validate_queue


ROOT = Path(__file__).resolve().parents[1]


class MvpFactoryTests(unittest.TestCase):
    def test_queue_loads_and_has_11_mvps(self) -> None:
        queue = load_queue()
        validate_queue(queue)
        self.assertEqual(len(queue), 11)

    def test_ids_are_unique(self) -> None:
        queue = load_queue()
        ids = [item["id"] for item in queue]
        self.assertEqual(len(ids), len(set(ids)))

    def test_statuses_are_valid(self) -> None:
        queue = load_queue()
        for item in queue:
            self.assertIn(item["status"], VALID_STATUSES)

    def test_forbidden_scope_contains_project_boundaries(self) -> None:
        queue = load_queue()
        for item in queue:
            forbidden = " ".join(item["forbidden_scope"])
            self.assertIn("ea-xau", forbidden)
            self.assertIn("PayoffGrid", forbidden)
            self.assertIn("ONPN11", forbidden)

    def test_next_mvp_returns_next_available_mvp(self) -> None:
        queue = load_queue()
        item = next_mvp(queue)
        self.assertIsNone(item)

    def test_generate_prompt_renders_mvp_001(self) -> None:
        queue = load_queue()
        prompt = render_prompt(queue[0])
        self.assertIn("MVP-001", prompt)
        self.assertIn("Desktop Navigation v2", prompt)
        self.assertIn("Do not touch ea-xau", prompt)

    def test_cli_next_works(self) -> None:
        result = subprocess.run(
            [sys.executable, "factory\\mvp_factory.py", "--next"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertIn("NO_NEXT_MVP", result.stdout)

    def test_cli_generate_prompt_works(self) -> None:
        result = subprocess.run(
            [sys.executable, "factory\\mvp_factory.py", "--generate-prompt", "MVP-001"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertIn("Desktop Navigation v2", result.stdout)


if __name__ == "__main__":
    unittest.main()
