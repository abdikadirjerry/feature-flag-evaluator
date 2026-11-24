import html
from src.models import FeatureFlag, VALID_PLANS


def render_sandbox_tab(flags: list[FeatureFlag], recent_evals: list[dict]) -> str:
    flag_options = "".join(
        f'<option value="{html.escape(f.flag_key)}">{html.escape(f.flag_key)} ({f.rollout_pct}%)</option>'
        for f in flags
    )
    plan_options = "".join(f'<option value="{p}">{p}</option>' for p in VALID_PLANS)

    eval_rows = []
    for ev in recent_evals[:18]:
        served = int(ev["served"]) == 1
        pill_cls = "pill-on" if served else ("pill-off" if ev["variant"] == "OFF" else "pill-ctrl")
        eval_rows.append(
            f"""
            <tr>
              <td class="mono">{html.escape(str(ev['evaluated_at']))}</td>
              <td class="mono"><strong>{html.escape(str(ev['flag_key']))}</strong></td>
              <td class="mono">{html.escape(str(ev['user_id']))}</td>
              <td class="mono">{html.escape(str(ev['plan']))}</td>
              <td><span class="pill {pill_cls}">{html.escape(str(ev['variant']))}</span></td>
              <td class="mono">{ev['bucket']}/99</td>
              <td style="font-size:0.76rem; color:#94a3b8;">{html.escape(str(ev['reason']))}</td>
            </tr>
            """
        )

    empty_notice = (
        '<tr><td colspan="7" style="text-align:center; padding:1.5rem; color:#94a3b8;">No evaluations logged yet. Test a user or run a 20-user cohort batch!</td></tr>'
        if not eval_rows
        else "".join(eval_rows)
    )

    return f"""
    <div class="split-layout">
      <section class="card">
        <div class="card-head">
          <h2>Evaluate Single User or Cohort</h2>
        </div>

        <form class="flag-form" method="POST" action="/evaluate/single">
          <label>
            Feature Flag Key
            <select name="flag_key">{flag_options}</select>
          </label>
          <label>
            User Identifier (Deterministic Hash Input)
            <input type="text" name="user_id" value="usr_abdikadir_042" required />
          </label>
          <label>
            User Subscription Plan
            <select name="plan">{plan_options}</select>
          </label>
          <button type="submit" class="btn-teal">Evaluate Single User</button>
        </form>

        <form class="flag-form" method="POST" action="/evaluate/cohort" style="margin-top:1.25rem; padding-top:1.1rem; border-top:1px solid #24324d;">
          <label>
            Batch Simulate 20 Users on Flag
            <select name="flag_key">{flag_options}</select>
          </label>
          <label>
            Cohort Plan Tier
            <select name="plan">{plan_options}</select>
          </label>
          <button type="submit" class="btn-outline">Run 20-User Cohort Rollout</button>
        </form>
      </section>

      <section class="card">
        <div class="card-head">
          <h2>Deterministic Evaluation Audit Log</h2>
        </div>
        <div style="overflow-x:auto;">
          <table class="flag-table">
            <thead>
              <tr>
                <th>Time</th><th>Flag</th><th>User ID</th><th>Plan</th><th>Variant</th><th>Bucket</th><th>Decision Reason</th>
              </tr>
            </thead>
            <tbody>{empty_notice}</tbody>
          </table>
        </div>
      </section>
    </div>
    """


def render_sdk_tab(json_payload: str) -> str:
    return f"""
    <section class="card">
      <div class="card-head">
        <h2>Edge SDK Bootstrap Payload (/api/flags)</h2>
        <a href="/api/flags" target="_blank" class="btn-outline">Open /api/flags</a>
      </div>
      <pre class="mono" style="background:#070b14; color:#5eead4; padding:1rem; border-radius:8px; overflow-x:auto; font-size:0.8rem;">{html.escape(json_payload)}</pre>
    </section>
    """
