import json
import tempfile
import unittest
from pathlib import Path
from src.cohort_simulator import export_sdk_bootstrap_json, simulate_cohort_sample
from src.flag_repo import FeatureFlagRepository


class TestCohortAndSdk(unittest.TestCase):
    def test_batch_cohort_simulation_and_sdk_payload(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = FeatureFlagRepository(str(Path(tmpdir) / "sdk.db"))
            flag = repo.get_flag("checkout-v2-edge")
            results = simulate_cohort_sample(repo, flag, plan="pro", sample_size=25)
            self.assertEqual(len(results), 25)

            sdk_raw = export_sdk_bootstrap_json(repo.list_flags(), repo.dashboard_metrics())
            parsed = json.loads(sdk_raw)
            self.assertIn("checkout-v2-edge", parsed["flags"])
            self.assertEqual(parsed["metrics"]["evaluations_logged"], 25)


if __name__ == "__main__":
    unittest.main()
