from http.server import BaseHTTPRequestHandler
import json

try:
    from _llm import chat_completion, LlmError
    from _kakao import search_kakao
    from _validate import require_nonempty
    from _trip_parse import parse_primary_json, strip_code_fence
except ImportError:
    from api._llm import chat_completion, LlmError
    from api._kakao import search_kakao
    from api._validate import require_nonempty
    from api._trip_parse import parse_primary_json, strip_code_fence

PRIMARY_SYSTEM = """당신은 통일교육 탐방 코스 추천기입니다.
오직 JSON 객체만 출력하세요. 마크다운·설명 금지.
스키마: {"recommended_site":"string","nearby_area":"string","reason":"string","learning_goals":["string"],"field_missions":["string"]}
recommended_site는 탐방 장소, nearby_area는 카카오 검색용 지역명입니다."""

PRIMARY_RETRY_SYSTEM = """JSON만 출력. 다른 텍스트 금지.
필수 키: recommended_site, nearby_area, reason, learning_goals(배열), field_missions(배열)."""

REPORT_SYSTEM = """통일교육용 탐방 보고서를 한국어 마크다운으로 작성하세요.
주어진 JSON(primary, places)만 근거로 쓰세요. 없는 사실 만들지 마세요.
구성: 제목, 추천 이유, 학습 목표, 현장 미션, 주변 장소(있으면)."""


def _user_prompt(date: str, origin: str, schedule: str, audience: str) -> str:
    return (
        f"날짜: {date}\n출발지: {origin}\n일정: {schedule}\n대상: {audience}\n"
        "위 조건에 맞는 통일교육 탐방지를 JSON으로 추천하세요."
    )


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

        date = (body.get("date") or "").strip()
        origin = (body.get("origin") or "").strip()
        schedule = (body.get("schedule") or "").strip()
        audience = (body.get("audience") or "").strip()
        missing = require_nonempty(
            {"date": date, "origin": origin, "schedule": schedule, "audience": audience}
        )
        if missing:
            return self._json(400, {"ok": False, "error": missing})

        user = _user_prompt(date, origin, schedule, audience)
        try:
            primary = self._primary_json(user)
        except LlmError as e:
            status = 503 if e.status in (None, 401, 403, 503) else 502
            return self._json(status, {"ok": False, "error": "잠시 후 다시 시도하세요"})
        except (ValueError, json.JSONDecodeError, TypeError, KeyError):
            return self._json(502, {"ok": False, "error": "잠시 후 다시 시도하세요"})

        places, kakao_err = search_kakao(primary["nearby_area"], size=5)
        warnings: list[str] = []
        if kakao_err:
            warnings.append("주변 장소 정보를 불러오지 못했습니다")
            places = []

        try:
            report_markdown = chat_completion(
                REPORT_SYSTEM,
                json.dumps({"primary": primary, "places": places}, ensure_ascii=False),
            )
            report_markdown = strip_code_fence(report_markdown)
        except LlmError as e:
            status = 503 if e.status in (None, 401, 403, 503) else 502
            return self._json(status, {"ok": False, "error": "잠시 후 다시 시도하세요"})

        return self._json(
            200,
            {
                "ok": True,
                "result": {
                    "primary": primary,
                    "places": places,
                    "report_markdown": report_markdown,
                    "warnings": warnings,
                },
            },
        )

    def _primary_json(self, user: str) -> dict:
        try:
            return parse_primary_json(chat_completion(PRIMARY_SYSTEM, user))
        except (LlmError, ValueError, json.JSONDecodeError, TypeError, KeyError):
            return parse_primary_json(chat_completion(PRIMARY_RETRY_SYSTEM, user))

    def _json(self, status, obj):
        data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, format, *args):
        return
