import subprocess
import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _tracked_public_status() -> str:
    completed = subprocess.run(
        ["git", "status", "--short", "--", "reports/public"],
        cwd=PROJECT_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout


class NoSelfTestTrackedOutputTests(unittest.TestCase):
    def test_app_self_tests_do_not_dirty_tracked_public_reports(self) -> None:
        before = _tracked_public_status()
        for flag in ["--self-test", "--preview-real-mt5-smoke-gate"]:
            subprocess.run(
                [sys.executable, "app\\mt5_robot_lab_app.py", flag],
                cwd=PROJECT_ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
        after = _tracked_public_status()
        self.assertEqual(after, before)


if __name__ == "__main__":
    unittest.main()
