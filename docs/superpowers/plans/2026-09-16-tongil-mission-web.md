# 통일탐방 미니 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 바닐라 HTML/CSS/JS + Vercel Python `api/`로 탐방 AI 추천(Kakao Local 포함)과 팩트체크를 배포 가능한 미션 제출용 사이트로 만든다.

**Architecture:** 원페이지(`index.html`)가 섹션 앵커 네비로 이동한다. 프론트는 `fetch('/api/...')`만 하고, 키는 서버 env만 사용한다. `api/fact_check.py`는 Cody chat/completions만 호출한다. `api/trip_recommend.py`는 Cody JSON → Kakao Local → Cody Markdown 파이프라인을 수행한다. 공유 헬퍼는 `api/_llm.py`, `api/_kakao.py`(언더스코어 = 라우트 아님).

**Tech Stack:** HTML/CSS/JS (프레임워크 금지), Vercel Serverless Python (`BaseHTTPRequestHandler`), Cody OpenAI-compatible LLM, Kakao Local Keyword API, pytest, `urllib` (추가 HTTP 라이브러리 최소화)

## Global Constraints

- 프론트: 순수 HTML/CSS/JavaScript only (React/Vue/Next 금지)
- 백엔드: `api/` Python Vercel Serverless만
- LLM env: `LLM_BASE_URL`, `LLM_MODEL`, `LLM_API_KEY` (실값 커밋 금지)
- Kakao env: `KAKAO_REST_API_KEY` (실값 커밋 금지)
- 프로젝트 루트: `/Users/chris/Desktop/Develop/vibecoding/tongil-mission-web`
- 설계 스펙: `docs/superpowers/specs/2026-09-16-tongil-mission-web-design.md`
- koreaboard 코드를 통째로 복사하지 말고 축소 이식; 문구·구성은 미션용으로 새로 쓸 것

---

## File map

| Path | Responsibility |
|------|----------------|
| `index.html` | 4섹션 마크업 + 폼 |
| `css/styles.css` | 레이아웃·반응형 |
| `js/nav.js` | 모바일 메뉴·앵커 |
| `js/trip.js` | 탐방 폼 → API → 결과/에러 |
| `js/factcheck.js` | 팩트체크 폼 → API → 결과/에러 |
| `api/_llm.py` | Cody chat/completions 헬퍼 |
| `api/_kakao.py` | Kakao keyword search |
| `api/fact_check.py` | `POST /api/fact_check` |
| `api/trip_recommend.py` | `POST /api/trip_recommend` |
| `requirements.txt` | 런타임 deps (비어 있어도 파일 존재; 테스트용 pytest는 dev) |
| `vercel.json` | Python 버전 등 |
| `.env.example` | 키 이름만 |
| `.gitignore` | `.env`, `.venv`, `__pycache__` |
| `docs/service-plan.md` | 제출용 기획서 |
| `README.md` | 소개·스택·실행·배포·env·URL |
| `tests/test_llm_parse.py` | JSON 파싱·검증 |
| `tests/test_kakao.py` | Kakao 매핑(목) |
| `tests/test_validate.py` | 입력 검증 |

---

### Task 1: Repo scaffold + static shell

**Files:**
- Create: `.gitignore`, `.env.example`, `vercel.json`, `requirements.txt`, `index.html`, `css/styles.css`, `js/nav.js`
- Test: open `index.html` in browser (manual) — no pytest yet

**Interfaces:**
- Produces: sections with ids `intro`, `trip`, `factcheck`, `faq`; nav links `#intro` `#trip` `#factcheck` `#faq`

- [ ] **Step 1: Init git (if needed) and write `.gitignore`**

```gitignore
.env
.env.local
.venv/
__pycache__/
*.pyc
.DS_Store
.vercel/
```

- [ ] **Step 2: Write `.env.example` (names only)**

```bash
LLM_BASE_URL=https://copa.codyssey.kr/v1
LLM_MODEL=gpt-5.4-mini
LLM_API_KEY=
KAKAO_REST_API_KEY=
```

- [ ] **Step 3: Write `vercel.json` and `requirements.txt`**

`vercel.json`:
```json
{
  "functions": {
    "api/**/*.py": {
      "runtime": "python3.12"
    }
  }
}
```

`requirements.txt`:
```text
# Vercel Python API uses stdlib only for HTTP.
# Dev tests: pip install pytest
```

- [ ] **Step 4: Create `index.html` shell**

Include: header nav, `#intro` hero, `#trip` form placeholders (`date`, `origin`, `schedule`, `audience`), `#factcheck` form (`question` + example buttons), `#faq` 3 Qs, script tags for `js/nav.js` (trip/factcheck scripts in later tasks).

- [ ] **Step 5: Create `css/styles.css`**

Mobile-first: max-width content, stack forms, nav collapse under ~640px. Avoid purple-gradient AI cliché; use clear CSS variables (e.g. deep green/ink for 통일교육 톤).

- [ ] **Step 6: Create `js/nav.js`**

Toggle `.nav-open` on hamburger; close on link click.

- [ ] **Step 7: Manual check**

Run: `python3 -m http.server 8765` from project root → open `http://127.0.0.1:8765`  
Expected: 4 sections, menu jumps work on narrow viewport.

- [ ] **Step 8: Commit**

```bash
git add .gitignore .env.example vercel.json requirements.txt index.html css/styles.css js/nav.js
git commit -m "chore: scaffold vanilla shell and vercel config"
```

---

### Task 2: Shared LLM helper + validation tests

**Files:**
- Create: `api/_llm.py`, `tests/test_validate.py`, `tests/conftest.py` (optional empty)
- Test: `tests/test_validate.py`, later import `_llm` parse helpers

**Interfaces:**
- Produces:
  - `chat_completion(system: str, user: str, *, timeout: float = 45.0) -> str`
  - `read_llm_config() -> dict` with keys `base_url`, `model`, `api_key`
  - raises `LlmError` with `.status` optional int on HTTP failure
- Consumes: env `LLM_BASE_URL`, `LLM_MODEL`, `LLM_API_KEY`

- [ ] **Step 1: Write failing tests for required-field validation (pure functions in test target module)**

Create `api/_validate.py`:

```python
def require_nonempty(fields: dict[str, str]) -> str | None:
    """Return first missing field message or None."""
    for key, value in fields.items():
        if not (value or "").strip():
            return "필수값을 입력하세요"
    return None
```

`tests/test_validate.py`:
```python
from api._validate import require_nonempty

def test_require_nonempty_ok():
    assert require_nonempty({"q": "hello"}) is None

def test_require_nonempty_blank():
    assert require_nonempty({"q": "  "}) == "필수값을 입력하세요"
```

Note: for imports, set `PYTHONPATH=.` or put packages so `api` is importable. Prefer running:

`cd tongil-mission-web && PYTHONPATH=. pytest tests/test_validate.py -v`

- [ ] **Step 2: Run tests — expect FAIL (module missing)**

Expected: `ModuleNotFoundError` or import error for `api._validate`

- [ ] **Step 3: Implement `api/_validate.py` and `api/_llm.py`**

`api/_llm.py` sketch:
```python
import json
import os
import urllib.error
import urllib.request

class LlmError(Exception):
    def __init__(self, message: str, status: int | None = None):
        super().__init__(message)
        self.status = status

def read_llm_config():
    return {
        "base_url": (os.environ.get("LLM_BASE_URL") or "").rstrip("/"),
        "model": os.environ.get("LLM_MODEL") or "",
        "api_key": os.environ.get("LLM_API_KEY") or "",
    }

def chat_completion(system: str, user: str, *, timeout: float = 45.0) -> str:
    cfg = read_llm_config()
    if not cfg["base_url"] or not cfg["model"]:
        raise LlmError("LLM이 설정되지 않았습니다", status=503)
    payload = json.dumps({
        "model": cfg["model"],
        "temperature": 0.3,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }).encode("utf-8")
    req = urllib.request.Request(
        f"{cfg['base_url']}/chat/completions",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {cfg['api_key'] or 'not-needed'}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as res:
            data = json.loads(res.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise LlmError(f"LLM HTTP {e.code}", status=e.code) from e
    except urllib.error.URLError as e:
        raise LlmError(f"LLM 네트워크 오류: {e}", status=None) from e
    content = (data.get("choices") or [{}])[0].get("message", {}).get("content") or ""
    if not content.strip():
        raise LlmError("LLM 응답이 비어 있습니다")
    return content.strip()
```

Also add empty `api/__init__.py` if needed for imports.

- [ ] **Step 4: Run tests — expect PASS**

`PYTHONPATH=. pytest tests/test_validate.py -v`

- [ ] **Step 5: Commit**

```bash
git add api/_validate.py api/_llm.py api/__init__.py tests/test_validate.py
git commit -m "feat: add LLM helper and input validation"
```

---

### Task 3: Kakao Local helper + tests

**Files:**
- Create: `api/_kakao.py`, `tests/test_kakao.py`
- Test: `tests/test_kakao.py`

**Interfaces:**
- Produces: `search_kakao(query: str, size: int = 5) -> tuple[list[dict], str | None]`
  - each dict: `{"name": str, "address": str, "category": str}`
  - on failure: `([], "주변 장소 정보를 불러오지 못했습니다")` or more specific message that API layer maps to that user string
- Consumes: `KAKAO_REST_API_KEY`
- Endpoint: `GET https://dapi.kakao.com/v2/local/search/keyword.json`

- [ ] **Step 1: Write failing test with mocked urlopen**

```python
import json
from unittest.mock import patch, MagicMock
from api._kakao import search_kakao, map_document

def test_map_document():
    item = map_document({
        "place_name": "임진각",
        "road_address_name": "경기 파주시",
        "category_name": "여행 > 관광",
    })
    assert item["name"] == "임진각"
    assert "파주" in item["address"]

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
```

- [ ] **Step 2: Run — expect FAIL**

- [ ] **Step 3: Implement `api/_kakao.py`**

Mirror koreaboard `KakaoLocalPlaceSearch` logic with stdlib `urllib`; export `map_document` and `search_kakao`. Authorization header: `KakaoAK {key}`.

- [ ] **Step 4: Run — expect PASS**

`PYTHONPATH=. pytest tests/test_kakao.py -v`

- [ ] **Step 5: Commit**

```bash
git add api/_kakao.py tests/test_kakao.py
git commit -m "feat: add Kakao Local keyword search helper"
```

---

### Task 4: Fact-check API endpoint

**Files:**
- Create: `api/fact_check.py`, `tests/test_fact_check_handler.py` (optional light unit on body parse)
- Modify: none
- Test: unit test for request JSON validation; manual curl with env if keys available

**Interfaces:**
- Produces HTTP: `POST /api/fact_check`
  - body: `{"question": string}`
  - success: `{"ok": true, "result": {"answer": string}}`
  - error: `{"ok": false, "error": string}` with HTTP 400/502/503
- Consumes: `require_nonempty`, `chat_completion`

**System prompt (fixed in code):** 통일교육 팩트체크 도우미. 질문에 대해 짧은 판정(확실/부분/불확실) + 2~4문장 근거. 추측이면 불확실이라고 명시. 마크다운 최소화.

- [ ] **Step 1: Write test for empty question helper path**

```python
from api._validate import require_nonempty

def test_fact_check_empty_question():
    assert require_nonempty({"question": ""}) == "필수값을 입력하세요"
```

(Already covered — add only if missing.)

- [ ] **Step 2: Implement `api/fact_check.py` Vercel handler**

```python
from http.server import BaseHTTPRequestHandler
import json
from api._validate import require_nonempty
from api._llm import chat_completion, LlmError

SYSTEM = """당신은 통일교육용 팩트체크 도우미입니다.
질문에 대해 (1) 판정: 확실/부분적/불확실 중 하나 (2) 근거 2~4문장으로 답하세요.
확인 불가하면 불확실이라고 쓰고 왜인지 밝히세요. 과도한 단정 금지."""

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
        question = (body.get("question") or "").strip()
        missing = require_nonempty({"question": question})
        if missing:
            return self._json(400, {"ok": False, "error": missing})
        try:
            answer = chat_completion(SYSTEM, f"질문: {question}")
        except LlmError as e:
            status = 503 if e.status in (None, 401, 403) else 502
            return self._json(status, {"ok": False, "error": "잠시 후 다시 시도하세요"})
        return self._json(200, {"ok": True, "result": {"answer": answer}})

    def _json(self, status, obj):
        data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, format, *args):
        return
```

Import path note: On Vercel, prefer relative imports if `api.` package import fails:

```python
from _validate import require_nonempty
from _llm import chat_completion, LlmError
```

Verify both local pytest (`api.` prefix) and Vercel (same-folder imports). If conflict, keep helpers as `api/_llm.py` and in handlers use:

```python
try:
    from _llm import chat_completion, LlmError
    from _validate import require_nonempty
except ImportError:
    from api._llm import chat_completion, LlmError
    from api._validate import require_nonempty
```

- [ ] **Step 3: Local smoke (optional if keys in env)**

Load `.env` manually for shell; do not commit. Curl against a tiny local wrapper only if easy — otherwise defer to Vercel preview.

- [ ] **Step 4: Commit**

```bash
git add api/fact_check.py
git commit -m "feat: add fact-check serverless endpoint"
```

---

### Task 5: Fact-check frontend

**Files:**
- Create: `js/factcheck.js`
- Modify: `index.html` (wire ids + script)

**Interfaces:**
- Consumes: `POST /api/fact_check` JSON as Task 4
- DOM ids: `fact-form`, `fact-question`, `fact-submit`, `fact-status`, `fact-result`, example buttons `[data-example]`

- [ ] **Step 1: Implement `js/factcheck.js`**

Behavior:
1. Submit preventDefault
2. If empty → set `fact-status` text “필수값을 입력하세요”, clear result
3. Else status “응답을 기다리는 중…”, disable button
4. `fetch('/api/fact-check'...)` — **path must match file**: Vercel maps `api/fact_check.py` → `/api/fact_check` (underscore). Use `/api/fact_check` consistently in JS.
5. On `!res.ok` or `ok===false` → “잠시 후 다시 시도하세요”
6. On success → show `result.answer` in `fact-result`
7. Example buttons fill textarea and optionally auto-submit

- [ ] **Step 2: Manual UI check** (empty input message without API)

- [ ] **Step 3: Commit**

```bash
git add js/factcheck.js index.html
git commit -m "feat: wire fact-check form to API"
```

---

### Task 6: Trip-recommend API (LLM + Kakao + Markdown)

**Files:**
- Create: `api/trip_recommend.py`, `tests/test_trip_parse.py`
- Test: `tests/test_trip_parse.py`

**Interfaces:**
- Produces: `POST /api/trip_recommend`
  - body: `{date, origin, schedule, audience}`
  - success: `{ok:true, result:{primary: object, places: list, report_markdown: string, warnings: string[]}}`
  - Kakao failure: still `ok:true` with `places:[]` and `warnings` including user-facing “주변 장소 정보를 불러오지 못했습니다”
- Consumes: `chat_completion`, `search_kakao`, `require_nonempty`

**Primary JSON schema (simplified vs koreaboard):**
```json
{
  "recommended_site": "string",
  "nearby_area": "string",
  "reason": "string",
  "learning_goals": ["string"],
  "field_missions": ["string"]
}
```

- [ ] **Step 1: Write failing parse tests**

```python
from api.trip_recommend import parse_primary_json, strip_code_fence

def test_strip_fence():
    raw = "```json\n{\"recommended_site\":\"임진각\"}\n```"
    assert "임진각" in strip_code_fence(raw)

def test_parse_primary_minimal():
    data = parse_primary_json('{"recommended_site":"임진각","nearby_area":"파주 임진각","reason":"r","learning_goals":["g"],"field_missions":["m"]}')
    assert data["recommended_site"] == "임진각"
```

(If parse helpers live in `_trip_parse.py` to avoid loading handler, create `api/_trip_parse.py` instead — preferred.)

- [ ] **Step 2: Run — FAIL**

- [ ] **Step 3: Implement `api/_trip_parse.py` + `api/trip_recommend.py`**

Pipeline in handler `do_POST`:
1. Validate four fields → 400 “필수값을 입력하세요”
2. `chat_completion` primary system (통일교육 탐방 JSON only)
3. Parse; on failure one retry with stricter system; still fail → 502 “잠시 후 다시 시도하세요”
4. `places, kakao_err = search_kakao(primary["nearby_area"], size=5)`
5. `warnings = []`; if kakao_err: append “주변 장소 정보를 불러오지 못했습니다”
6. Second `chat_completion` to write Markdown report using primary + places JSON
7. Return 200 with result

Keep prompts short to reduce latency/cost.

- [ ] **Step 4: pytest parse tests PASS**

- [ ] **Step 5: Commit**

```bash
git add api/_trip_parse.py api/trip_recommend.py tests/test_trip_parse.py
git commit -m "feat: add trip-recommend pipeline with Kakao"
```

---

### Task 7: Trip frontend

**Files:**
- Create: `js/trip.js`
- Modify: `index.html`

**Interfaces:**
- Consumes: `POST /api/trip_recommend`
- DOM: `trip-form`, fields, `trip-status`, `trip-result`

- [ ] **Step 1: Implement `js/trip.js`**

Same UX patterns as factcheck: empty → 필수값; loading → 기다리는 중; error → 잠시 후; success → render site, reason, goals, missions, places list, markdown as pre-wrapped text (`textContent` / simple `innerText`, not raw HTML inject).

- [ ] **Step 2: Manual empty-input check**

- [ ] **Step 3: Commit**

```bash
git add js/trip.js index.html
git commit -m "feat: wire trip-recommend form to API"
```

---

### Task 8: Docs — README + service plan + images folder

**Files:**
- Create: `README.md`, `docs/service-plan.md`, `images/.gitkeep`
- Modify: none

- [ ] **Step 1: Write `docs/service-plan.md`**

Include: purpose, target, 4 sections, AI A/B input·output·failure (Kakao warning included), test cases (normal / empty / API error).

- [ ] **Step 2: Write `README.md`**

Sections: 소개, 기술 스택, 로컬 실행(`python -m http.server` note that API needs Vercel/dev), 환경 변수 표, Vercel 배포 절차, 배포 URL placeholder `(배포 후 기입)`, 구조 트리. **No secret values.**

- [ ] **Step 3: Commit**

```bash
git add README.md docs/service-plan.md images/.gitkeep
git commit -m "docs: add README and service plan for submission"
```

---

### Task 9: GitHub + Vercel deploy + verify

**Files:**
- Modify: `README.md` (fill real Vercel URL after deploy)

- [ ] **Step 1: Create GitHub repo and push** (`gh repo create` or remote add). Ensure `.env` not included (`git status`).

- [ ] **Step 2: Import project on Vercel; set env:**
  - `LLM_BASE_URL`, `LLM_MODEL`, `LLM_API_KEY`, `KAKAO_REST_API_KEY`

- [ ] **Step 3: Deploy and test on production URL**
  - Nav + mobile layout
  - Fact-check happy path + empty
  - Trip happy path; confirm places or Kakao warning
  - If Cody blocked from Vercel: document failure and fix network/key

- [ ] **Step 4: Update README deployment URL; commit**

```bash
git add README.md
git commit -m "docs: add production Vercel URL"
git push
```

- [ ] **Step 5: Capture submission screenshots** into `images/` (desktop, mobile, AI results) — user may take these manually; agent assists with browser if available. Do not include secrets in shots.

---

## Spec coverage checklist

| Spec item | Task |
|-----------|------|
| Vanilla + 4 sections + nav | 1, 5, 7 |
| Responsive | 1 |
| Fact-check AI | 4, 5 |
| Trip AI + Kakao | 3, 6, 7 |
| Failure messages | 4–7 |
| Env keys safe | 1, 8, 9 |
| README + service plan | 8 |
| Vercel deploy | 9 |
| Separate from koreaboard | all (new repo root) |

## Placeholder / consistency self-review

- API paths unified as `/api/fact_check` and `/api/trip_recommend` (underscore filenames).
- User-facing errors exact strings from spec.
- Kakao soft-fail keeps trip `ok: true` with warning.
- No TBD left in tasks.
