from http.server import BaseHTTPRequestHandler
from datetime import datetime, timezone
import json
import os
import urllib.error
import urllib.request

try:
    from _validate import require_nonempty
except ImportError:
    from api._validate import require_nonempty

KIND_LABELS = {
    "fact_check": "팩트체크(검색)",
    "trip": "탐방추천(검색)",
    "inquiry": "문의",
}


def _forward_webhook(payload: dict) -> str | None:
    """POST payload to WEBHOOK_URL (n8n 등). Returns error message or None."""
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


def build_sheet_payload(kind: str, summary: str, input_text: str) -> dict:
    """n8n → Google Sheets 행에 맞춘 평탄한 필드."""
    now = datetime.now(timezone.utc).astimezone()
    return {
        "recorded_at": now.isoformat(timespec="seconds"),
        "recorded_at_kr": now.strftime("%Y-%m-%d %H:%M:%S"),
        "kind": kind,
        "kind_label": KIND_LABELS.get(kind, kind),
        "input": input_text[:2000],
        "summary": summary[:4000],
        "source": "tongil-mission-web",
    }


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

        payload = build_sheet_payload(
            kind, summary, (body.get("input") or "").strip()
        )
        webhook_error = _forward_webhook(payload)
        has_url = bool((os.environ.get("WEBHOOK_URL") or "").strip())
        webhook_status = (
            "sent"
            if has_url and not webhook_error
            else ("skipped" if not has_url else "failed")
        )
        return self._json(
            200,
            {
                "ok": True,
                "result": {
                    "saved": True,
                    "webhook": webhook_status,
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
