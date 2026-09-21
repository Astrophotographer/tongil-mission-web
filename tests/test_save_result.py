from api.save_result import _forward_webhook, build_sheet_payload


def test_forward_webhook_skipped_without_url(monkeypatch):
    monkeypatch.delenv("WEBHOOK_URL", raising=False)
    assert _forward_webhook({"kind": "inquiry", "summary": "hi"}) is None


def test_build_sheet_payload_fields():
    payload = build_sheet_payload("trip", "추천: 임진각", "서울역 → 파주")
    assert payload["kind"] == "trip"
    assert payload["kind_label"] == "탐방추천"
    assert payload["input"] == "서울역 → 파주"
    assert payload["summary"].startswith("추천")
    assert payload["source"] == "tongil-mission-web"
    assert "recorded_at_kr" in payload
    assert "recorded_at" in payload
