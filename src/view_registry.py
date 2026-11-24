import html
from src.models import FeatureFlag


def render_registry_tab(flags: list[FeatureFlag]) -> str:
    rows = []
    for f in flags:
        status_pill = (
            '<span class="pill pill-on">ACTIVE</span>'
            if f.enabled
            else '<span class="pill pill-off">KILLED (OFF)</span>'
        )
        plans_str = ", ".join(f.allowed_plans)
        rows.append(
            f"""
            <tr>
              <td>
                <div class="mono"><strong>{html.escape(f.flag_key)}</strong></div>
                <div style="font-size:0.76rem; color:#94a3b8;">{html.escape(f.description)}</div>
              </td>
              <td>{status_pill}</td>
              <td style="min-width:130px;">
                <div class="mono"><strong>{f.rollout_pct}%</strong> traffic</div>
                <div class="meter-track">
                  <div class="meter-fill" style="width:{f.rollout_pct}%;"></div>
                </div>
              </td>
              <td class="mono" style="font-size:0.76rem;">{html.escape(plans_str)}</td>
              <td>
                <form method="POST" action="/flags/toggle">
                  <input type="hidden" name="flag_key" value="{html.escape(f.flag_key)}" />
                  <button type="submit" class="btn-outline">
                    {'Kill Flag' if f.enabled else 'Enable Flag'}
                  </button>
                </form>
              </td>
            </tr>
            """
        )

    return f"""
    <div class="split-layout">
      <section class="card">
        <div class="card-head">
          <h2>Create or Update Feature Flag</h2>
        </div>

        <form class="flag-form" method="POST" action="/flags/upsert">
          <label>
            Flag Key (slug)
            <input type="text" name="flag_key" placeholder="vector-search-v3" required />
          </label>

          <label>
            Rollout Description
            <input type="text" name="description" placeholder="Enable HNSW vector index queries" required />
          </label>

          <label>
            Canary Rollout Percentage (0 - 100%)
            <input type="number" name="rollout_pct" min="0" max="100" value="35" required />
          </label>

          <label>
            Allowed Subscription Plans (comma-separated)
            <input type="text" name="allowed_plans" value="pro,enterprise" required />
          </label>

          <label>
            Deterministic Hash Salt
            <input type="text" name="salt" value="salt_canary_2026" required />
          </label>

          <button type="submit" class="btn-teal">Save Flag Rule</button>
        </form>
      </section>

      <section class="card">
        <div class="card-head">
          <h2>Feature Flag Registry ({len(flags)})</h2>
          <a href="/api/flags" target="_blank" class="btn-outline">Raw SDK JSON</a>
        </div>

        <div style="overflow-x:auto;">
          <table class="flag-table">
            <thead>
              <tr>
                <th>Flag &amp; Description</th><th>State</th><th>Rollout</th><th>Target Plans</th><th>Kill Switch</th>
              </tr>
            </thead>
            <tbody>{''.join(rows)}</tbody>
          </table>
        </div>
      </section>
    </div>
    """
