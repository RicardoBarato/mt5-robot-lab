import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


POLICY_FILES = [
    "docs/LICENSING_POLICY.md",
    "docs/BRAND_AND_TRADEMARK_POLICY.md",
    "CONTRIBUTING.md",
    "CODE_OF_CONDUCT.md",
    "docs/SUBMISSION_TERMS_DRAFT.md",
    "docs/OFFICIAL_RANKING_GOVERNANCE.md",
    "docs/COMMUNITY_AND_MONETIZATION_MODEL.md",
    "README.md",
]


class PolicyDocsTests(unittest.TestCase):
    def read(self, relative_path: str) -> str:
        return (ROOT / relative_path).read_text(encoding="utf-8")

    def normalized(self, relative_path: str) -> str:
        return " ".join(self.read(relative_path).lower().split())

    def test_policy_files_exist(self) -> None:
        for relative_path in POLICY_FILES:
            self.assertTrue((ROOT / relative_path).exists(), relative_path)

    def test_docs_do_not_make_profit_or_advice_claims(self) -> None:
        forbidden = [
            "guaranteed profit",
            "profit guaranteed",
            "risk-free trading",
            "we provide financial advice",
            "this is financial advice",
        ]
        for relative_path in POLICY_FILES:
            text = self.read(relative_path).lower()
            for phrase in forbidden:
                self.assertNotIn(phrase, text, relative_path)

    def test_licensing_policy_disclaims_legal_advice(self) -> None:
        text = self.read("docs/LICENSING_POLICY.md").lower()
        self.assertIn("not legal advice", text)
        self.assertIn("not final legal advice", text)
        self.assertIn("do not restrict commercial use", text)
        self.assertIn("do not try to prohibit resale", text)

    def test_submission_terms_are_draft_only(self) -> None:
        text = self.read("docs/SUBMISSION_TERMS_DRAFT.md").lower()
        self.assertIn("draft", text)
        self.assertIn("not final legal terms", text)
        self.assertIn("future upload", text)
        self.assertIn("optional", text)

    def test_contributing_blocks_private_artifacts(self) -> None:
        text = self.read("CONTRIBUTING.md")
        for phrase in [".set", ".ex5", ".env", "private reports", "broker names or servers"]:
            self.assertIn(phrase, text)

    def test_official_ranking_separates_result_classes(self) -> None:
        text = self.read("docs/OFFICIAL_RANKING_GOVERNANCE.md").lower()
        for phrase in ["sample", "smoke", "real_backtest", "official_verified"]:
            self.assertIn(phrase, text)

    def test_readme_contains_open_software_official_ranking(self) -> None:
        text = self.normalized("README.md")
        self.assertIn("open software, official ranking", text)
        self.assertIn("official online ranking", text)
        self.assertIn("separate project-controlled services", text)


if __name__ == "__main__":
    unittest.main()
