from http.server import BaseHTTPRequestHandler
import json

try:
    from _llm import chat_completion, LlmError
    from _validate import require_nonempty
except ImportError:
    from api._llm import chat_completion, LlmError
    from api._validate import require_nonempty

SYSTEM = """당신은 통일교육용 팩트체크 도우미입니다.
질문에 대해 (1) 판정: 확실/부분적/불확실 중 하나 (2) 근거 2~4문장으로 답하세요.
확인 불가하면 불확실이라고 쓰고 왜인지 밝히세요. 과도한 단정 금지."""


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
        question = (body.get("question") or "").strip()
        missing = require_nonempty({"question": question})
        if missing:
            return self._json(400, {"ok": False, "error": missing})
        try:
            answer = chat_completion(SYSTEM, f"질문: {question}")
        except LlmError as e:
            status = 503 if e.status in (None, 401, 403) else 502
            return self._json(status, {"ok": False, "error": "잠시 후 다시 시도하세요"})
        return self._json(200, {"ok": True, "result": {"answer": answer}})

    def _json(self, status, obj):
        data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, format, *args):
        return
