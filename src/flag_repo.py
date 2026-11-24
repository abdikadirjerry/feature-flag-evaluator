import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from src.models import EvaluationResult, FeatureFlag

DEFAULT_FLAGS = [
    (
        "checkout-v2-edge",
        "Zero-latency edge checkout pipeline with instant Apple Pay",
        1,
        50,
        "pro,enterprise",
        "salt_chk_01",
    ),
    (
        "ai-query-copilot",
        "Natural-language SQL assistant inside analytics workbench",
        1,
        25,
        "enterprise",
        "salt_ai_09",
    ),
    (
        "realtime-webhook-stream",
        "Server-Sent Events live webhook delivery inspector",
        1,
        100,
        "free,pro,enterprise",
        "salt_wh_04",
    ),
    (
        "legacy-xml-exporter",
        "Deprecated SOAP/XML batch report generator",
        0,
        0,
        "enterprise",
        "salt_xml_02",
    ),
]


class FeatureFlagRepository:
    def __init__(self, db_path: str = "data/feature_flags.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()
        self._seed_flags()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS feature_flags (
                    flag_key TEXT PRIMARY KEY,
                    description TEXT NOT NULL,
                    enabled INTEGER NOT NULL DEFAULT 1,
                    rollout_pct INTEGER NOT NULL DEFAULT 100,
                    allowed_plans TEXT NOT NULL,
                    salt TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS evaluation_audit (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    evaluated_at TEXT NOT NULL,
                    flag_key TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    plan TEXT NOT NULL,
                    variant TEXT NOT NULL,
                    served INTEGER NOT NULL,
                    bucket INTEGER NOT NULL,
                    reason TEXT NOT NULL
                )
                """
            )

    def _seed_flags(self) -> None:
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        with self._connect() as conn:
            count = conn.execute("SELECT COUNT(*) FROM feature_flags").fetchone()[0]
            if count == 0:
                conn.executemany(
                    """
                    INSERT INTO feature_flags
                    (flag_key, description, enabled, rollout_pct, allowed_plans, salt, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    [(*row, ts) for row in DEFAULT_FLAGS],
                )

    def list_flags(self) -> list[FeatureFlag]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM feature_flags ORDER BY flag_key ASC").fetchall()
            return [
                FeatureFlag(
                    flag_key=str(r["flag_key"]),
                    description=str(r["description"]),
                    enabled=bool(r["enabled"]),
                    rollout_pct=int(r["rollout_pct"]),
                    allowed_plans=tuple(p.strip() for p in str(r["allowed_plans"]).split(",") if p.strip()),
                    salt=str(r["salt"]),
                    updated_at=str(r["updated_at"]),
                )
                for r in rows
            ]

    def get_flag(self, flag_key: str) -> FeatureFlag | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM feature_flags WHERE flag_key = ?", (flag_key,)).fetchone()
            if not row:
                return None
            return FeatureFlag(
                flag_key=str(row["flag_key"]),
                description=str(row["description"]),
                enabled=bool(row["enabled"]),
                rollout_pct=int(row["rollout_pct"]),
                allowed_plans=tuple(p.strip() for p in str(row["allowed_plans"]).split(",") if p.strip()),
                salt=str(row["salt"]),
                updated_at=str(row["updated_at"]),
            )

    def upsert_flag(
        self,
        flag_key: str,
        description: str,
        enabled: bool,
        rollout_pct: int,
        allowed_plans: list[str],
        salt: str = "salt_v1",
    ) -> None:
        clean_key = flag_key.strip().lower().replace(" ", "-")[:48] or "new-experiment-flag"
        clean_desc = description.strip()[:160] or "Feature flag rollout rule"
        clean_pct = max(0, min(100, rollout_pct))
        plans_csv = ",".join(p.strip().lower() for p in allowed_plans if p.strip()) or "free,pro,enterprise"
        clean_salt = salt.strip()[:32] or "salt_v1"
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO feature_flags (flag_key, description, enabled, rollout_pct, allowed_plans, salt, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(flag_key) DO UPDATE SET
                    description = excluded.description,
                    enabled = excluded.enabled,
                    rollout_pct = excluded.rollout_pct,
                    allowed_plans = excluded.allowed_plans,
                    salt = excluded.salt,
                    updated_at = excluded.updated_at
                """,
                (clean_key, clean_desc, 1 if enabled else 0, clean_pct, plans_csv, clean_salt, ts),
            )

    def toggle_kill_switch(self, flag_key: str) -> None:
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE feature_flags
                SET enabled = CASE WHEN enabled = 1 THEN 0 ELSE 1 END,
                    updated_at = ?
                WHERE flag_key = ?
                """,
                (ts, flag_key),
            )

    def log_evaluation(self, result: EvaluationResult) -> None:
        ts = datetime.now(timezone.utc).strftime("%H:%M:%S UTC")
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO evaluation_audit
                (evaluated_at, flag_key, user_id, plan, variant, served, bucket, reason)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    ts,
                    result.flag_key,
                    result.user_id,
                    result.plan,
                    result.variant,
                    1 if result.served else 0,
                    result.bucket,
                    result.reason,
                ),
            )

    def recent_evaluations(self, limit: int = 25) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM evaluation_audit ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [dict(r) for r in rows]

    def dashboard_metrics(self) -> dict:
        flags = self.list_flags()
        evals = self.recent_evaluations(limit=200)
        served_count = sum(1 for e in evals if int(e["served"]) == 1)
        return {
            "total_flags": len(flags),
            "active_flags": sum(1 for f in flags if f.enabled),
            "killed_flags": sum(1 for f in flags if not f.enabled),
            "evaluations_logged": len(evals),
            "treatment_served": served_count,
        }
