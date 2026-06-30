import unittest

from app.mt5_robot_lab_app import build_parser


class MT5RobotLabAppTests(unittest.TestCase):
    def test_runtime_dry_run_flag_is_available(self) -> None:
        args = build_parser().parse_args(["--real-mt5-runtime-dry-run"])

        self.assertTrue(args.real_mt5_runtime_dry_run)

    def test_compiled_ex5_bootstrap_flag_is_available(self) -> None:
        args = build_parser().parse_args(["--compiled-ex5-readiness-bootstrap"])

        self.assertTrue(args.compiled_ex5_readiness_bootstrap)

    def test_compiled_ex5_terminal_bootstrap_flag_is_available(self) -> None:
        args = build_parser().parse_args(["--compiled-ex5-terminal-bootstrap"])

        self.assertTrue(args.compiled_ex5_terminal_bootstrap)


if __name__ == "__main__":
    unittest.main()
