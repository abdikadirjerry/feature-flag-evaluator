from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from src.cohort_simulator import export_sdk_bootstrap_json, simulate_cohort_sample
from src.flag_repo import FeatureFlagRepository
from src.rollout_engine import evaluate_flag
from src.view_registry import render_registry_tab
from src.view_sandbox_sdk import render_sandbox_tab, render_sdk_tab
from src.view_shell import render_flag_shell

REPO = FeatureFlagRepository("data/feature_flags.db")
STATIC_DIR = Path(__file__).parent / "static"


class FlagPulseHandler(BaseHTTPRequestHandler):
    def _send(self, payload: bytes, content_type: str, status: int = 200) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _redirect(self, location: str) -> None:
        self.send_response(303)
        self.send_header("Location", location)
        self.end_headers()

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        if parsed.path == "/static/flags.css":
            self._send((STATIC_DIR / "flags.css").read_bytes(), "text/css; charset=utf-8")
            return

        flags = REPO.list_flags()
        metrics = REPO.dashboard_metrics()

        if parsed.path == "/api/flags":
            payload = export_sdk_bootstrap_json(flags, metrics)
            self._send(payload.encode("utf-8"), "application/json; charset=utf-8")
            return

        if parsed.path == "/":
            tab = params.get("tab", ["registry"])[0]
            if tab == "sandbox":
                body = render_sandbox_tab(flags, REPO.recent_evaluations(limit=25))
            elif tab == "sdk":
                body = render_sdk_tab(export_sdk_bootstrap_json(flags, metrics))
            else:
                tab = "registry"
                body = render_registry_tab(flags)

            page = render_flag_shell(tab, metrics, body)
            self._send(page.encode("utf-8"), "text/html; charset=utf-8")
            return

        self._send(b"404 Not Found", "text/plain; charset=utf-8", 404)

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", 0))
        form = parse_qs(self.rfile.read(length).decode("utf-8"))

        if self.path == "/flags/upsert":
            plans_raw = form.get("allowed_plans", ["pro,enterprise"])[0]
            REPO.upsert_flag(
                flag_key=form.get("flag_key", ["custom-flag"])[0],
                description=form.get("description", ["Feature rollout"])[0],
                enabled=True,
                rollout_pct=int(form.get("rollout_pct", ["50"])[0]),
                allowed_plans=plans_raw.split(","),
                salt=form.get("salt", ["salt_v1"])[0],
            )
            self._redirect("/?tab=registry")
            return

        if self.path == "/flags/toggle":
            flag_key = form.get("flag_key", [""])[0]
            if flag_key:
                REPO.toggle_kill_switch(flag_key)
            self._redirect("/?tab=registry")
            return

        if self.path == "/evaluate/single":
            flag_key = form.get("flag_key", [""])[0]
            user_id = form.get("user_id", ["usr_001"])[0]
            plan = form.get("plan", ["pro"])[0]
            flag = REPO.get_flag(flag_key)
            if flag:
                res = evaluate_flag(flag, user_id, plan)
                REPO.log_evaluation(res)
            self._redirect("/?tab=sandbox")
            return

        if self.path == "/evaluate/cohort":
            flag_key = form.get("flag_key", [""])[0]
            plan = form.get("plan", ["pro"])[0]
            flag = REPO.get_flag(flag_key)
            if flag:
                simulate_cohort_sample(REPO, flag, plan, sample_size=20)
            self._redirect("/?tab=sandbox")
            return

        self._send(b"404 Not Found", "text/plain; charset=utf-8", 404)


def main(host: str = "127.0.0.1", port: int = 8105) -> None:
    server = ThreadingHTTPServer((host, port), FlagPulseHandler)
    print(f"[*] FlagPulse Feature Flag Engine running at http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[*] Stopping FlagPulse server...")
        server.server_close()


if __name__ == "__main__":
    main()
