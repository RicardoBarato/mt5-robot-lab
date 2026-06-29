import tempfile
import unittest
from pathlib import Path

from tools.publication_guard import scan


class PublicationGuardGlobalTests(unittest.TestCase):
    def test_scans_public_json_for_sensitive_terms(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            public = root / "reports" / "public"
            public.mkdir(parents=True)
            (public / "leak.json").write_text('{"token": "abc"}\n', encoding="utf-8")
            findings = scan(root)
        self.assertTrue(any("sensitive_term:token" in item["reason"] for item in findings))

    def test_scans_public_text_for_private_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            public = root / "reports" / "public"
            public.mkdir(parents=True)
            (public / "path.md").write_text("Local report: C:/Users/Ricardo/AppData/Local/file.json\n", encoding="utf-8")
            findings = scan(root)
        self.assertTrue(any(item["reason"].startswith("private_path") for item in findings))

    def test_ignores_private_reports_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            private = root / "reports" / "private"
            private.mkdir(parents=True)
            (private / "local_mt5_environment_status.local.json").write_text(
                '{"token": "local-only"}\n',
                encoding="utf-8",
            )
            findings = scan(root)
        self.assertEqual(findings, [])

    def test_reports_public_still_scanned(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            public = root / "reports" / "public"
            public.mkdir(parents=True)
            (public / "local_mt5_environment_status.json").write_text(
                '{"token": "public-leak"}\n',
                encoding="utf-8",
            )
            findings = scan(root)
        self.assertTrue(any("sensitive_term:token" in item["reason"] for item in findings))

    def test_allows_policy_wording_for_sensitive_terms(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            docs = root / "docs"
            docs.mkdir()
            (docs / "POLICY.md").write_text("The app does not store password, token or secret values.\n", encoding="utf-8")
            findings = scan(root)
        self.assertEqual(findings, [])


if __name__ == "__main__":
    unittest.main()
