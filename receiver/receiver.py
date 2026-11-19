"""Local HTTP receiver: saves posted CI test reports to testreport.json."""
import json
import os
import sys
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer

OUT = os.environ.get("REPORT_FILE", "testreport.json")
TOKEN = os.environ.get("RECEIVER_TOKEN", "")
HISTORY = "reports_history"


class Handler(BaseHTTPRequestHandler):
    def _reply(self, code, text):
        body = text.encode()
        self.send_response(code)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        self._reply(200, "receiver running")

    def do_POST(self):
        if self.path != "/report":
            return self._reply(404, "not found")
        if TOKEN and self.headers.get("X-Receiver-Token") != TOKEN:
            return self._reply(401, "bad token")
        raw = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        try:
            report = json.loads(raw)
        except ValueError:
            return self._reply(400, "invalid JSON")
        with open(OUT, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=2)
        os.makedirs(HISTORY, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        with open(f"{HISTORY}/{stamp}_{report.get('overall_status', 'unknown')}.json", "w") as fh:
            json.dump(report, fh, indent=2)
        print(f"[{stamp}] saved {OUT}: {report.get('overall_status')} "
              f"({report.get('summary')})", flush=True)
        self._reply(200, "saved")


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    print(f"Receiver listening on http://localhost:{port}/report -> {OUT}", flush=True)
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()
