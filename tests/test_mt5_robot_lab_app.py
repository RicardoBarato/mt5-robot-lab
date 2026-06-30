import unittest

from app.mt5_robot_lab_app import build_parser


class MT5RobotLabAppTests(unittest.TestCase):
    def test_runtime_dry_run_flag_is_available(self) -> None:
        args = build_parser().parse_args(["--real-mt5-runtime-dry-run"])

        self.assertTrue(args.real_mt5_runtime_dry_run)


if __name__ == "__main__":
    unittest.main()
