import json
import tempfile
import unittest
from pathlib import Path

from app.core.compiled_ex5_readiness import (
    validate_compiled_ex5_readiness,
    validate_expert_relative_path,
    write_compiled_ex5_readiness_marker,
)


class CompiledEX5ReadinessTests(unittest.TestCase):
    def test_ex5_in_terminal_datadir_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data_dir = root / "terminal_data"
            ex5 = data_dir / "MQL5" / "Experts" / "RBRiskEngine" / "RBRiskEngine_Public.ex5"
            ex5.parent.mkdir(parents=True)
            ex5.write_text("compiled fake", encoding="utf-8")
            write_compiled_ex5_readiness_marker(
                root,
                terminal_data_dir=data_dir,
                expert_relative_path="RBRiskEngine\\RBRiskEngine_Public",
            )
            result = validate_compiled_ex5_readiness(
                root,
                environment={"terminal_data_dir": str(data_dir)},
                expert_relative_path="RBRiskEngine\\RBRiskEngine_Public",
            )

        self.assertTrue(result["compiled_ex5_verified_in_terminal_datadir"])
        self.assertTrue(result["terminal_data_dir_consistent"])
        self.assertTrue(result["expert_mapping_valid_for_strategy_tester"])
        self.assertEqual(result["blocking_issues"], [])

    def test_ex5_in_different_datadir_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            marker_data_dir = root / "terminal_data_a"
            runtime_data_dir = root / "terminal_data_b"
            ex5 = marker_data_dir / "MQL5" / "Experts" / "RBRiskEngine" / "RBRiskEngine_Public.ex5"
            ex5.parent.mkdir(parents=True)
            ex5.write_text("compiled fake", encoding="utf-8")
            write_compiled_ex5_readiness_marker(
                root,
                terminal_data_dir=marker_data_dir,
                expert_relative_path="RBRiskEngine\\RBRiskEngine_Public",
            )
            result = validate_compiled_ex5_readiness(
                root,
                environment={"terminal_data_dir": str(runtime_data_dir)},
                expert_relative_path="RBRiskEngine\\RBRiskEngine_Public",
            )

        self.assertFalse(result["compiled_ex5_verified_in_terminal_datadir"])
        self.assertIn("terminal_data_dir_mismatch", result["blocking_issues"])

    def test_expert_mapping_rejects_empty_absolute_and_extension(self) -> None:
        self.assertIn("expert_missing", validate_expert_relative_path("")["blocking_issues"])
        self.assertIn(
            "expert_absolute_path_blocked",
            validate_expert_relative_path("C:\\MT5\\MQL5\\Experts\\EA")["blocking_issues"],
        )
        self.assertIn(
            "expert_must_not_include_extension",
            validate_expert_relative_path("RBRiskEngine\\RBRiskEngine_Public.ex5")["blocking_issues"],
        )

    def test_expert_parameters_optional_and_required(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data_dir = root / "terminal_data"
            ex5 = data_dir / "MQL5" / "Experts" / "RBRiskEngine" / "RBRiskEngine_Public.ex5"
            ex5.parent.mkdir(parents=True)
            ex5.write_text("compiled fake", encoding="utf-8")
            write_compiled_ex5_readiness_marker(
                root,
                terminal_data_dir=data_dir,
                expert_relative_path="RBRiskEngine\\RBRiskEngine_Public",
            )
            optional = validate_compiled_ex5_readiness(
                root,
                environment={"terminal_data_dir": str(data_dir)},
                expert_relative_path="RBRiskEngine\\RBRiskEngine_Public",
            )
            required = validate_compiled_ex5_readiness(
                root,
                environment={"terminal_data_dir": str(data_dir)},
                expert_relative_path="RBRiskEngine\\RBRiskEngine_Public",
                expert_parameters_required=True,
            )
            set_file = data_dir / "MQL5" / "Profiles" / "Tester" / "public_safe.set"
            set_file.parent.mkdir(parents=True)
            set_file.write_text("fake params", encoding="utf-8")
            valid = validate_compiled_ex5_readiness(
                root,
                environment={"terminal_data_dir": str(data_dir)},
                expert_relative_path="RBRiskEngine\\RBRiskEngine_Public",
                expert_parameters="public_safe.set",
                expert_parameters_required=True,
            )

        self.assertEqual(optional["expert_parameters_status"], "not_required")
        self.assertEqual(required["expert_parameters_status"], "missing_required")
        self.assertIn("expert_parameters_missing", required["blocking_issues"])
        self.assertEqual(valid["expert_parameters_status"], "valid")

    def test_marker_is_ignored_style_json_without_public_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data_dir = root / "terminal_data"
            ex5 = data_dir / "MQL5" / "Experts" / "RBRiskEngine" / "RBRiskEngine_Public.ex5"
            ex5.parent.mkdir(parents=True)
            ex5.write_text("compiled fake", encoding="utf-8")
            marker = write_compiled_ex5_readiness_marker(
                root,
                terminal_data_dir=data_dir,
                expert_relative_path="RBRiskEngine\\RBRiskEngine_Public",
            )

        self.assertTrue(marker["compiled_ex5_exists"])
        self.assertIn("marker_created_at", marker)
        json.dumps(marker)


if __name__ == "__main__":
    unittest.main()
