import tempfile
import unittest
from pathlib import Path
from src.flag_repo import FeatureFlagRepository
from src.view_registry import render_registry_tab
from src.view_shell import render_flag_shell


class TestFlagPulseViews(unittest.TestCase):
    def test_renders_shell_and_escapes_descriptions(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = FeatureFlagRepository(str(Path(tmpdir) / "views.db"))
            repo.upsert_flag("xss-check", "<script>alert(1)</script>", True, 10, ["free"])
            html_out = render_flag_shell("registry", repo.dashboard_metrics(), render_registry_tab(repo.list_flags()))
            self.assertIn("FLAG<span>PULSE</span>", html_out)
            self.assertNotIn("<script>alert(1)</script>", html_out)


if __name__ == "__main__":
    unittest.main()
