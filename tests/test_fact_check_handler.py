import json
from io import BytesIO
from unittest.mock import MagicMock, patch

from api.fact_check import handler


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
    h.path = "/api/fact_check"
    status_holder = {}

    def send_response(code):
        status_holder["code"] = code

    h.send_response = send_response
    h.send_header = lambda *args, **kwargs: None
    h.end_headers = lambda: None
    h.do_POST()
    return status_holder.get("code"), json.loads(out.getvalue().decode("utf-8"))


def test_fact_check_invalid_json():
    code, obj = _post(b"{not json")
    assert code == 400
    assert obj == {"ok": False, "error": "잘못된 요청입니다"}


def test_fact_check_empty_question():
    code, obj = _post(json.dumps({"question": ""}).encode("utf-8"))
    assert code == 400
    assert obj == {"ok": False, "error": "필수값을 입력하세요"}


@patch("api.fact_check.chat_completion", return_value="판정: 확실\n근거입니다.")
def test_fact_check_success(mock_chat):
    code, obj = _post(json.dumps({"question": "38선이란?"}).encode("utf-8"))
    assert code == 200
    assert obj == {"ok": True, "result": {"answer": "판정: 확실\n근거입니다."}}
    mock_chat.assert_called_once()
