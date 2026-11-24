import hashlib
from src.models import EvaluationResult, FeatureFlag


def compute_user_bucket(flag_key: str, salt: str, user_id: str) -> int:
    material = f"{flag_key}:{salt}:{user_id}".encode("utf-8")
    digest = hashlib.sha256(material).hexdigest()
    return int(digest[:8], 16) % 100


def evaluate_flag(flag: FeatureFlag, user_id: str, plan: str) -> EvaluationResult:
    clean_user = user_id.strip() or "anonymous-user"
    clean_plan = plan.strip().lower() or "free"
    bucket = compute_user_bucket(flag.flag_key, flag.salt, clean_user)

    if not flag.enabled:
        return EvaluationResult(
            flag_key=flag.flag_key,
            user_id=clean_user,
            plan=clean_plan,
            variant="OFF",
            served=False,
            bucket=bucket,
            reason="Global kill switch disabled",
        )

    if flag.allowed_plans and clean_plan not in flag.allowed_plans:
        return EvaluationResult(
            flag_key=flag.flag_key,
            user_id=clean_user,
            plan=clean_plan,
            variant="CONTROL",
            served=False,
            bucket=bucket,
            reason=f"Plan '{clean_plan}' excluded by targeting rule",
        )

    if bucket < flag.rollout_pct:
        return EvaluationResult(
            flag_key=flag.flag_key,
            user_id=clean_user,
            plan=clean_plan,
            variant="TREATMENT",
            served=True,
            bucket=bucket,
            reason=f"Bucket {bucket} < {flag.rollout_pct}% rollout threshold",
        )

    return EvaluationResult(
        flag_key=flag.flag_key,
        user_id=clean_user,
        plan=clean_plan,
        variant="CONTROL",
        served=False,
        bucket=bucket,
        reason=f"Bucket {bucket} >= {flag.rollout_pct}% rollout threshold",
    )
