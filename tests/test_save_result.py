from api.save_result import _forward_webhook


def test_forward_webhook_skipped_without_url(monkeypatch):
    monkeypatch.delenv("WEBHOOK_URL", raising=False)
    assert _forward_webhook({"kind": "inquiry", "summary": "hi"}) is None
