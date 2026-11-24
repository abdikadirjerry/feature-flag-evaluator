def render_flag_shell(active_tab: str, metrics: dict, content_html: str) -> str:
    tabs = [
        ("registry", "Flag Registry & Kill Switches"),
        ("sandbox", "Cohort Evaluation Sandbox"),
        ("sdk", "SDK Bootstrap JSON"),
    ]
    nav_html = "".join(
        f'<a href="/?tab={slug}" class="{"active" if slug == active_tab else ""}">{label}</a>'
        for slug, label in tabs
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>FlagPulse // Feature Flag &amp; Canary Rollout Engine</title>
  <link rel="stylesheet" href="/static/flags.css" />
</head>
<body>
  <header class="topbar">
    <div class="brand">FLAG<span>PULSE</span> // DETERMINISTIC ROLLOUT &amp; CANARY ENGINE</div>
    <nav class="nav-pills">{nav_html}</nav>
  </header>

  <main class="container">
    <section class="kpi-grid">
      <div class="card">
        <div class="kpi-label">Configured Flags</div>
        <div class="kpi-value indigo">{metrics['total_flags']}</div>
      </div>
      <div class="card">
        <div class="kpi-label">Active Rollouts</div>
        <div class="kpi-value teal">{metrics['active_flags']}</div>
      </div>
      <div class="card">
        <div class="kpi-label">Kill-Switch Halted</div>
        <div class="kpi-value rose">{metrics['killed_flags']}</div>
      </div>
      <div class="card">
        <div class="kpi-label">Treatment Cohort Hits</div>
        <div class="kpi-value amber">{metrics['treatment_served']} / {metrics['evaluations_logged']}</div>
      </div>
    </section>

    {content_html}
  </main>
</body>
</html>"""
