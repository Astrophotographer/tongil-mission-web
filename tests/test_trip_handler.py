import json
from io import BytesIO
from unittest.mock import MagicMock, patch

from api._llm import LlmError
from api.trip_recommend import handler

PRIMARY = {
    "recommended_site": "임진각",
    "nearby_area": "파주",
    "reason": "분단의 상징",
    "learning_goals": ["분단 이해"],
    "field_missions": ["기념관 관람"],
}


def _post(body: bytes):
    out = BytesIO()
    conn = MagicMock()
    conn.makefile.side_effect = lambda mode, bufsize: BytesIO(body) if "r" in mode else out
    h = handler(conn, ("127.0.0.1", 0), None)
    h.rfile = BytesIO(body)
    h.wfile = out
    h.headers = {"Content-Length": str(len(body))}
    h.request_version = "HTTP/1.1"
    h.command = "POST"
    h.path = "/api/trip_recommend"
    status_holder = {}

    def send_response(code):
        status_holder["code"] = code

    h.send_response = send_response
    h.send_header = lambda *args, **kwargs: None
    h.end_headers = lambda: None
    h.do_POST()
    return status_holder.get("code"), json.loads(out.getvalue().decode("utf-8"))


def _body(**overrides):
    data = {
        "date": "2026-09-20",
        "origin": "서울역",
        "schedule": "반나절",
        "audience": "중2",
    }
    data.update(overrides)
    return json.dumps(data).encode("utf-8")


def test_trip_empty_fields():
    code, obj = _post(_body(date="", origin="", schedule="", audience=""))
    assert code == 400
    assert obj == {"ok": False, "error": "필수값을 입력하세요"}


@patch("api.trip_recommend.search_kakao", return_value=([], "Kakao Local 키가 없습니다"))
@patch(
    "api.trip_recommend.chat_completion",
    side_effect=[
        json.dumps(PRIMARY, ensure_ascii=False),
        "## 탐방 보고서\n내용",
    ],
)
def test_trip_success_kakao_soft_fail(mock_chat, mock_kakao):
    code, obj = _post(_body())
    assert code == 200
    assert obj["ok"] is True
    result = obj["result"]
    assert result["primary"]["recommended_site"] == "임진각"
    assert result["places"] == []
    assert result["warnings"] == ["주변 장소 정보를 불러오지 못했습니다"]
    assert "탐방 보고서" in result["report_markdown"]
    assert mock_chat.call_count == 2
    mock_kakao.assert_called_once_with("파주", size=5)


@patch("api.trip_recommend.search_kakao", return_value=([{"name": "카페", "address": "파주", "category": "음식점"}], None))
@patch(
    "api.trip_recommend.chat_completion",
    side_effect=[
        json.dumps(PRIMARY, ensure_ascii=False),
        "## 보고서",
    ],
)
def test_trip_pipeline_success(mock_chat, mock_kakao):
    code, obj = _post(_body())
    assert code == 200
    assert obj["ok"] is True
    assert obj["result"]["places"][0]["name"] == "카페"
    assert obj["result"]["warnings"] == []
    assert mock_chat.call_count == 2


@patch("api.trip_recommend.chat_completion", side_effect=LlmError("LLM이 설정되지 않았습니다", status=503))
def test_trip_llm_missing_config_503(mock_chat):
    code, obj = _post(_body())
    assert code == 503
    assert obj == {"ok": False, "error": "잠시 후 다시 시도하세요"}
