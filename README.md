# FlagPulse — Zero-Dependency Feature Flag, Canary Rollout & Cohort Engine (`python-feature-flag-evaluator`)

A deterministic feature-flagging and percentage rollout control plane built purely with Python's standard library (`http.server`, `sqlite3`, `hashlib`, `json`).

## Features
- **Deterministic SHA-256 Cohort Hashing (`src/rollout_engine.py`):** Assigns every `(flag_key, salt, user_id)` tuple to a consistent `0..99` bucket so canary percentage increases never reshuffle previously admitted users.
- **Instant Kill Switches & Plan Targeting (`src/flag_repo.py`):** Toggle emergency kill switches, adjust rollout percentages, and restrict flags to specific subscription tiers (`free`, `pro`, `enterprise`).
- **Cohort Sandbox & Edge SDK JSON (`GET /api/flags`):** Evaluate single users or 20-user cohorts in real time and export a clean SDK bootstrap JSON manifest.

## Running Locally
```bash
python3 app.py
```
Open `http://127.0.0.1:8105` in your browser, or run the unit tests:
```bash
python3 -m unittest discover -s tests -v
```
