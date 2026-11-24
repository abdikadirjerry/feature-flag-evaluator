import unittest
from src.models import FeatureFlag
from src.rollout_engine import compute_user_bucket, evaluate_flag


class TestRolloutEngine(unittest.TestCase):
    def test_deterministic_bucket_consistency_and_plan_targeting(self):
        flag = FeatureFlag(
            flag_key="new-billing-ui",
            description="Test flag",
            enabled=True,
            rollout_pct=50,
            allowed_plans=("pro", "enterprise"),
            salt="salt_fixed",
            updated_at="2026-11-24",
        )

        # Same user always gets identical bucket
        b1 = compute_user_bucket(flag.flag_key, flag.salt, "user-42")
        b2 = compute_user_bucket(flag.flag_key, flag.salt, "user-42")
        self.assertEqual(b1, b2)
        self.assertTrue(0 <= b1 <= 99)

        # Free plan must be excluded regardless of bucket
        free_res = evaluate_flag(flag, "user-42", "free")
        self.assertFalse(free_res.served)
        self.assertEqual(free_res.variant, "CONTROL")

    def test_kill_switch_overrides_100_percent_rollout(self):
        killed = FeatureFlag(
            flag_key="emergency-off",
            description="Killed flag",
            enabled=False,
            rollout_pct=100,
            allowed_plans=("free", "pro", "enterprise"),
            salt="s1",
            updated_at="2026-11-24",
        )
        res = evaluate_flag(killed, "user-99", "enterprise")
        self.assertFalse(res.served)
        self.assertEqual(res.variant, "OFF")


if __name__ == "__main__":
    unittest.main()
