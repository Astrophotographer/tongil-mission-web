import json
import os
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


def _as_str(value: Any, default: str = "") -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (int, float)):
        return str(value)
    return default


def map_document(doc: dict) -> dict[str, str]:
    return {
        "name": _as_str(doc.get("place_name")),
        "address": _as_str(doc.get("road_address_name") or doc.get("address_name")),
        "category": _as_str(doc.get("category_name")),
    }


def search_kakao(query: str, size: int = 5) -> tuple[list[dict], str | None]:
    key = (os.environ.get("KAKAO_REST_API_KEY") or "").strip()
    if not key:
        return [], "Kakao Local 키가 없습니다. KAKAO_REST_API_KEY를 설정하세요."

    qs = urlencode({"query": query, "size": str(max(1, min(15, size)))})
    req = Request(
        f"https://dapi.kakao.com/v2/local/search/keyword.json?{qs}",
        headers={"Authorization": f"KakaoAK {key}"},
        method="GET",
    )
    try:
        with urlopen(req, timeout=30) as res:
            data = json.loads(res.read().decode("utf-8"))
    except HTTPError as e:
        body = e.read().decode("utf-8", "replace")[:200]
        if e.code in (401, 403):
            return [], f"Kakao Local 인증 실패({e.code}): {body}"
        if e.code == 429:
            return [], "Kakao Local 쿼터 초과(429)."
        return [], f"Kakao Local HTTP {e.code}: {body}"
    except URLError as e:
        return [], f"Kakao Local 네트워크 오류: {e}"

    items: list[dict] = []
    for doc in data.get("documents") or []:
        place = map_document(doc)
        if place["name"]:
            items.append(place)
    return items, None
