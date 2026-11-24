from dataclasses import dataclass

VALID_ENVIRONMENTS = ("production", "staging", "development")
VALID_PLANS = ("free", "pro", "enterprise")


@dataclass(frozen=True)
class FeatureFlag:
    flag_key: str
    description: str
    enabled: bool
    rollout_pct: int
    allowed_plans: tuple[str, ...]
    salt: str
    updated_at: str


@dataclass(frozen=True)
class EvaluationResult:
    flag_key: str
    user_id: str
    plan: str
    variant: str
    served: bool
    bucket: int
    reason: str
