from http.server import BaseHTTPRequestHandler
import json
import os
import urllib.error
import urllib.request

try:
    from _validate import require_nonempty
except ImportError:
    from api._validate import require_nonempty


def _forward_webhook(payload: dict) -> str | None:
    """POST payload to WEBHOOK_URL if set. Returns error message or None."""
    url = (os.environ.get("WEBHOOK_URL") or "").strip()
    if not url:
        return None
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=12) as res:
            if res.status >= 400:
                return f"webhook HTTP {res.status}"
    except urllib.error.HTTPError as e:
        return f"webhook HTTP {e.code}"
    except urllib.error.URLError:
        return "webhook network error"
    return None


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_POST(self):
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length)
        try:
            body = json.loads(raw.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            return self._json(400, {"ok": False, "error": "잘못된 요청입니다"})

        kind = (body.get("kind") or "").strip()
        summary = (body.get("summary") or "").strip()
        missing = require_nonempty({"kind": kind, "summary": summary})
        if missing:
            return self._json(400, {"ok": False, "error": missing})

        if kind not in ("fact_check", "trip", "inquiry"):
            return self._json(400, {"ok": False, "error": "잘못된 요청입니다"})

        payload = {
            "kind": kind,
            "summary": summary[:4000],
            "input": (body.get("input") or "")[:2000],
            "source": "tongil-mission-web",
        }
        webhook_error = _forward_webhook(payload)
        return self._json(
            200,
            {
                "ok": True,
                "result": {
                    "saved": True,
                    "webhook": "sent" if (os.environ.get("WEBHOOK_URL") or "").strip() and not webhook_error else (
                        "skipped" if not (os.environ.get("WEBHOOK_URL") or "").strip() else "failed"
                    ),
                    "webhook_error": webhook_error,
                },
            },
        )

    def _json(self, status, obj):
        data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, format, *args):
        return
