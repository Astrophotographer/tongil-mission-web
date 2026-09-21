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


def map_document(doc: dict) -> dict[str, Any]:
    place: dict[str, Any] = {
        "name": _as_str(doc.get("place_name")),
        "address": _as_str(doc.get("road_address_name") or doc.get("address_name")),
        "category": _as_str(doc.get("category_name")),
    }
    try:
        lng = float(doc.get("x"))
        lat = float(doc.get("y"))
        if lng == lng and lat == lat:  # not NaN
            place["lng"] = lng
            place["lat"] = lat
    except (TypeError, ValueError):
        pass
    return place


def search_kakao(query: str, size: int = 5) -> tuple[list[dict], str | None]:
    key = (os.environ.get("KAKAO_REST_API_KEY") or "").strip()
    if not key:
        return [], "Kakao Local 키가 없습니다. KAKAO_REST_API_KEY를 설정하세요."

    q = (query or "").strip()
    if not q:
        return [], "검색어가 비어 있습니다."

    qs = urlencode({"query": q, "size": str(max(1, min(15, size)))})
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


def geocode_place(query: str) -> tuple[dict | None, str | None]:
    """Return first Kakao place with coords, or (None, error)."""
    items, err = search_kakao(query, size=1)
    if err:
        return None, err
    if not items:
        return None, "장소를 찾지 못했습니다."
    place = items[0]
    if "lat" not in place or "lng" not in place:
        return None, "좌표를 찾지 못했습니다."
    return place, None


def fetch_driving_path(
    origin: dict[str, Any], destination: dict[str, Any]
) -> tuple[list[dict[str, float]], str | None]:
    """Kakao Mobility directions → list of {lat,lng}. Soft-fail friendly."""
    key = (os.environ.get("KAKAO_REST_API_KEY") or "").strip()
    if not key:
        return [], "Kakao REST 키가 없습니다."
    try:
        ox, oy = float(origin["lng"]), float(origin["lat"])
        dx, dy = float(destination["lng"]), float(destination["lat"])
    except (KeyError, TypeError, ValueError):
        return [], "경로 좌표가 올바르지 않습니다."

    qs = urlencode(
        {
            "origin": f"{ox},{oy}",
            "destination": f"{dx},{dy}",
            "priority": "RECOMMEND",
        }
    )
    req = Request(
        f"https://apis-navi.kakaomobility.com/v1/directions?{qs}",
        headers={"Authorization": f"KakaoAK {key}"},
        method="GET",
    )
    try:
        with urlopen(req, timeout=30) as res:
            data = json.loads(res.read().decode("utf-8"))
    except HTTPError as e:
        body = e.read().decode("utf-8", "replace")[:200]
        return [], f"Kakao 경로 안내 실패({e.code}): {body}"
    except URLError as e:
        return [], f"Kakao 경로 네트워크 오류: {e}"

    routes = data.get("routes") or []
    if not routes:
        return [], "경로 결과가 없습니다."
    path: list[dict[str, float]] = []
    for section in routes[0].get("sections") or []:
        for road in section.get("roads") or []:
            verts = road.get("vertexes") or []
            # [lng, lat, lng, lat, ...]
            for i in range(0, len(verts) - 1, 2):
                try:
                    path.append({"lng": float(verts[i]), "lat": float(verts[i + 1])})
                except (TypeError, ValueError, IndexError):
                    continue
    if len(path) < 2:
        return [], "경로 좌표가 부족합니다."
    # downsample for response size
    if len(path) > 200:
        step = max(1, len(path) // 200)
        path = path[::step]
        if path[-1] != {"lng": dx, "lat": dy}:
            path.append({"lng": dx, "lat": dy})
    return path, None
