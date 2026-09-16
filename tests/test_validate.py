from api._validate import require_nonempty

def test_require_nonempty_ok():
    assert require_nonempty({"q": "hello"}) is None

def test_require_nonempty_blank():
    assert require_nonempty({"q": "  "}) == "필수값을 입력하세요"
