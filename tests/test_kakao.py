import json
from unittest.mock import patch, MagicMock
from api._kakao import search_kakao, map_document

def test_map_document():
    item = map_document({
        "place_name": "임진각",
        "road_address_name": "경기 파주시",
        "category_name": "여행 > 관광",
        "x": "126.74",
        "y": "37.88",
    })
    assert item["name"] == "임진각"
    assert "파주" in item["address"]
    assert item["lng"] == 126.74
    assert item["lat"] == 37.88

def test_search_kakao_maps_documents(monkeypatch):
    monkeypatch.setenv("KAKAO_REST_API_KEY", "test-key")
    body = json.dumps({
        "documents": [
            {"place_name": "A", "road_address_name": "addr", "category_name": "cat"}
        ]
    }).encode()
    mock_res = MagicMock()
    mock_res.read.return_value = body
    mock_res.__enter__.return_value = mock_res
    mock_res.__exit__.return_value = False
    with patch("api._kakao.urlopen", return_value=mock_res):
        places, err = search_kakao("파주 임진각", size=3)
    assert err is None
    assert places[0]["name"] == "A"

def test_search_kakao_missing_key(monkeypatch):
    monkeypatch.delenv("KAKAO_REST_API_KEY", raising=False)
    places, err = search_kakao("x")
    assert places == []
    assert err is not None
