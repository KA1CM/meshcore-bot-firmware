"""Local-only dashboard preview. Sample readings; never contacts radios or cloud services."""
import json
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "vendor/MeshCore/examples/companion_radio/RepeaterMonitorPage.html"
repeaters = json.loads((ROOT / "colorado/repeater-monitor-initial.json").read_text())["repeaters"]


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def reply(self, body, content_type="application/json", status=200):
        data = body.encode()
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == "/":
            page = PAGE.read_text(encoding="utf-8").replace("Morning battery check", "Dashboard preview · sample data")
            self.reply(page, "text/html; charset=utf-8")
        elif self.path == "/api/list":
            self.reply(json.dumps({"version": 1, "repeaters": repeaters}))
        elif self.path == "/api/state":
            now = int(time.time())
            # Preview fixtures deliberately include a missing response.
            items = []
            for i, entry in enumerate(repeaters):
                readings = [{"day": (now - 5 * 3600) // 86400 - age,
                             "timestamp": now - age * 86400,
                             "result": 2, "status": "ok", "millivolts": 3900 + age * 20}
                            for age in range(6, -1, -1)]
                if i == 1:
                    readings[-1].update(result=3, status="no_response", millivolts=None)
                items.append(dict(entry, displayName=f"Sample repeater {i + 1}", readings=readings))
            self.reply(json.dumps({"version": 1, "repeaters": items, "now": now, "timeReady": True,
                                  "storageOK": True, "running": False, "active": -1, "error": "",
                                  "node": "PREVIEW — SAMPLE DATA", "ip": "127.0.0.1", "manualReady": True,
                                  "today": (now - 5 * 3600) // 86400,
                                  "nextSunrise": now + 86400, "sunrise": now}))
        else:
            self.reply("Not found", "text/plain", 404)

    def do_POST(self):
        global repeaters
        length = int(self.headers.get("Content-Length", 0))
        if length > 8192 or self.headers.get("X-Mesh-Monitor") != "1":
            self.reply("Invalid request", "text/plain", 400)
            return
        data = json.loads(self.rfile.read(length))
        if self.path == "/api/list":
            repeaters = data["repeaters"]
        self.reply('{"ok":true}')


if __name__ == "__main__":
    print("Dashboard preview on http://127.0.0.1:8765 — sample data only", flush=True)
    HTTPServer(("127.0.0.1", 8765), Handler).serve_forever()
