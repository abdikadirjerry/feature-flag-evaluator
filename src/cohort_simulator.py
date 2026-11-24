import json
from src.flag_repo import FeatureFlagRepository
from src.models import EvaluationResult, FeatureFlag
from src.rollout_engine import evaluate_flag


def simulate_cohort_sample(
    repo: FeatureFlagRepository,
    flag: FeatureFlag,
    plan: str,
    sample_size: int = 20,
) -> list[EvaluationResult]:
    safe_size = max(1, min(100, sample_size))
    results: list[EvaluationResult] = []
    for idx in range(1, safe_size + 1):
        user_id = f"usr_{plan}_{idx:03d}"
        res = evaluate_flag(flag, user_id, plan)
        repo.log_evaluation(res)
        results.append(res)
    return results


def export_sdk_bootstrap_json(flags: list[FeatureFlag], metrics: dict) -> str:
    payload = {
        "sdk_schema_version": "2026.11",
        "metrics": metrics,
        "flags": {
            f.flag_key: {
                "enabled": f.enabled,
                "rollout_pct": f.rollout_pct,
                "allowed_plans": list(f.allowed_plans),
                "salt": f.salt,
                "updated_at": f.updated_at,
            }
            for f in flags
        },
    }
    return json.dumps(payload, indent=2)
