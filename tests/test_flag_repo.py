import tempfile
import unittest
from pathlib import Path
from src.flag_repo import FeatureFlagRepository


class TestFeatureFlagRepo(unittest.TestCase):
    def test_upsert_and_toggle_kill_switch(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = FeatureFlagRepository(str(Path(tmpdir) / "flags.db"))
            repo.upsert_flag("search-v4", "Fast search", True, 40, ["pro"], "salt_4")

            flag = repo.get_flag("search-v4")
            self.assertIsNotNone(flag)
            self.assertTrue(flag.enabled)
            self.assertEqual(flag.rollout_pct, 40)

            repo.toggle_kill_switch("search-v4")
            toggled = repo.get_flag("search-v4")
            self.assertFalse(toggled.enabled)


if __name__ == "__main__":
    unittest.main()
