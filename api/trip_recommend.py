from http.server import BaseHTTPRequestHandler
import json

try:
    from _llm import chat_completion, LlmError
    from _kakao import search_kakao, geocode_place, fetch_driving_path
    from _validate import require_nonempty
    from _trip_parse import parse_primary_json, strip_code_fence
except ImportError:
    from api._llm import chat_completion, LlmError
    from api._kakao import search_kakao, geocode_place, fetch_driving_path
    from api._validate import require_nonempty
    from api._trip_parse import parse_primary_json, strip_code_fence

PRIMARY_SYSTEM = """당신은 통일교육 탐방 코스 추천기입니다.
오직 JSON 객체만 출력하세요. 마크다운·설명 금지.
스키마: {"recommended_site":"string","nearby_area":"string","reason":"string","learning_goals":["string"],"field_missions":["string"]}
recommended_site는 탐방 장소, nearby_area는 카카오 검색용 지역명입니다.
사용자의 도착지(도착 도시/권역) 일대에서 탐방지를 고르세요."""

PRIMARY_RETRY_SYSTEM = """JSON만 출력. 다른 텍스트 금지.
필수 키: recommended_site, nearby_area, reason, learning_goals(배열), field_missions(배열).
도착지 일대 탐방지를 추천하세요."""

REPORT_SYSTEM = """통일교육용 탐방 보고서를 한국어 마크다운으로 작성하세요.
주어진 JSON(primary, places, origin, destination)만 근거로 쓰세요. 없는 사실 만들지 마세요.
구성: 제목, 출발→도착 요약, 추천 이유, 학습 목표, 현장 미션, 주변 장소(있으면)."""


def _user_prompt(date: str, origin: str, destination: str, schedule: str, audience: str) -> str:
    return (
        f"날짜: {date}\n출발지: {origin}\n도착지: {destination}\n"
        f"일정: {schedule}\n대상: {audience}\n"
        "도착지 일대에서 통일교육 탐방지를 JSON으로 추천하세요."
    )


def _point(label: str, place: dict | None) -> dict | None:
    if not place or "lat" not in place or "lng" not in place:
        return None
    return {
        "label": label,
        "name": place.get("name") or label,
        "address": place.get("address") or "",
        "lat": place["lat"],
        "lng": place["lng"],
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

        date = (body.get("date") or "").strip()
        origin = (body.get("origin") or "").strip()
        destination = (body.get("destination") or "").strip()
        schedule = (body.get("schedule") or "").strip()
        audience = (body.get("audience") or "").strip()
        missing = require_nonempty(
            {
                "date": date,
                "origin": origin,
                "destination": destination,
                "schedule": schedule,
                "audience": audience,
            }
        )
        if missing:
            return self._json(400, {"ok": False, "error": missing})

        user = _user_prompt(date, origin, destination, schedule, audience)
        try:
            primary = self._primary_json(user)
        except LlmError as e:
            status = 503 if e.status in (None, 401, 403, 503) else 502
            return self._json(status, {"ok": False, "error": "잠시 후 다시 시도하세요"})
        except (ValueError, json.JSONDecodeError, TypeError, KeyError):
            return self._json(502, {"ok": False, "error": "잠시 후 다시 시도하세요"})

        warnings: list[str] = []
        places, kakao_err = search_kakao(primary["nearby_area"], size=5)
        if kakao_err:
            warnings.append("주변 장소 정보를 불러오지 못했습니다")
            places = []

        origin_place, origin_err = geocode_place(origin)
        dest_place, dest_err = geocode_place(destination)
        site_query = primary.get("recommended_site") or primary.get("nearby_area") or destination
        site_place, site_err = geocode_place(site_query)

        route_origin = _point("출발", origin_place)
        route_dest = _point("도착", dest_place) or _point("탐방지", site_place)
        route_site = _point("탐방지", site_place)

        if not route_origin or not route_dest:
            warnings.append("지도 경로를 위한 출발/도착 좌표를 찾지 못했습니다")
            if origin_err or dest_err or site_err:
                pass

        path: list[dict] = []
        if route_origin and route_dest:
            path, path_err = fetch_driving_path(route_origin, route_dest)
            if path_err or not path:
                # straight fallback
                path = [
                    {"lat": route_origin["lat"], "lng": route_origin["lng"]},
                    {"lat": route_dest["lat"], "lng": route_dest["lng"]},
                ]
                if path_err:
                    warnings.append("자동차 경로를 불러오지 못해 직선 경로로 표시합니다")

        try:
            report_markdown = chat_completion(
                REPORT_SYSTEM,
                json.dumps(
                    {
                        "primary": primary,
                        "places": places,
                        "origin": origin,
                        "destination": destination,
                    },
                    ensure_ascii=False,
                ),
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
                    "route": {
                        "origin": route_origin,
                        "destination": route_dest,
                        "site": route_site,
                        "path": path,
                    },
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
