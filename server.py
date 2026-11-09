"""Minimal AgentPhone webhook receiver for testing. Free-tier friendly."""
from __future__ import annotations

import json
import os
import sys
from collections import deque
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

MAX_EVENTS = 100
EVENTS: deque = deque(maxlen=MAX_EVENTS)
EVENTS_KEY = os.environ.get("EVENTS_KEY", "")
# Placeholder for later AgentPhone signature verification
AGENTPHONE_WEBHOOK_SECRET = os.environ.get("AGENTPHONE_WEBHOOK_SECRET", "")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class Handler(BaseHTTPRequestHandler):
    server_version = "AgentPhoneWebhook/1.0"

    def log_message(self, fmt: str, *args) -> None:
        sys.stdout.write("%s - %s\n" % (self.log_date_time_string(), fmt % args))
        sys.stdout.flush()

    def _json(self, code: int, payload: dict | list) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _text(self, code: int, text: str) -> None:
        body = text.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path in ("/", ""):
            self._text(200, "ok")
            return
        if parsed.path == "/events":
            qs = parse_qs(parsed.query)
            key = (qs.get("key") or [None])[0]
            if not EVENTS_KEY or key != EVENTS_KEY:
                self._json(401, {"ok": False, "error": "unauthorized"})
                return
            self._json(200, {"ok": True, "count": len(EVENTS), "events": list(EVENTS)})
            return
        self._json(404, {"ok": False, "error": "not found"})

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path != "/webhook":
            self._json(404, {"ok": False, "error": "not found"})
            return
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b""
        text = raw.decode("utf-8", "replace")
        try:
            body = json.loads(text) if text else None
        except Exception:
            body = text
        headers = {k: v for k, v in self.headers.items()}
        event = {
            "timestamp": utc_now(),
            "method": "POST",
            "path": self.path,
            "headers": headers,
            "body": body,
        }
        EVENTS.appendleft(event)
        print("EVENT", json.dumps(event, default=str), flush=True)
        # Always acknowledge quickly; voice handling comes later.
        self._json(200, {"ok": True})


def main() -> None:
    port = int(os.environ.get("PORT", "10000"))
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    print(f"listening on 0.0.0.0:{port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
