import tempfile
import unittest
from pathlib import Path

from app.core.champion_dna import sample_champion_dna, write_champion_artifacts


class ChampionDNATests(unittest.TestCase):
    def test_sample_artifacts_written(self) -> None:
        dna = sample_champion_dna()
        with tempfile.TemporaryDirectory() as tmp:
            written = write_champion_artifacts(dna, Path(tmp))
            self.assertTrue(written["champion_dna"].exists())
            self.assertTrue(written["metrics"].exists())
            self.assertTrue(written["parameter_diff"].exists())


if __name__ == "__main__":
    unittest.main()
