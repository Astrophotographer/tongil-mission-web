# 통일탐방 미니

통일교육용 **탐방 일정 AI 추천**과 **팩트체크**를 한 페이지에서 제공하는 미션 제출용 웹 서비스입니다.

## 소개

- **탐방 AI 추천:** 탐방일·출발지·일정·대상을 입력하면 LLM이 탐방지·학습목표·현장미션과 수업안을 제안합니다. Kakao Local API로 주변 맛집·장소를 보조 검색합니다.
- **팩트체크:** 통일 관련 주장·질문에 대해 짧은 판정과 근거 요약을 받을 수 있습니다.
- 상세 기획은 [`docs/service-plan.md`](docs/service-plan.md)를 참고하세요.

## 기술 스택

| 영역 | 기술 |
|------|------|
| 프론트 | HTML5, CSS3, 바닐라 JavaScript |
| API | Vercel Python Serverless (`python3.12`) |
| AI | OpenAI 호환 Chat Completions (`LLM_*` 환경 변수) |
| 장소 검색 | Kakao Local (`KAKAO_REST_API_KEY`) |
| 배포 | [Vercel](https://vercel.com) |

## 로컬 실행

### 정적 파일만 (UI 확인)

프로젝트 루트에서:

```bash
python -m http.server 8080
```

브라우저에서 `http://localhost:8080` 을 엽니다.

> **참고:** `python -m http.server`만으로는 `/api/trip_recommend`, `/api/fact_check`가 동작하지 않습니다. AI·Kakao 연동 테스트는 **Vercel 배포 URL** 또는 로컬에서 **`vercel dev`**(환경 변수 설정 후)를 사용하세요.

### API 포함 로컬 개발 (권장)

1. [Vercel CLI](https://vercel.com/docs/cli) 설치
2. `.env.example`을 참고해 `.env`(또는 `.env.local`)에 변수 **이름**에 맞게 값 설정 (git에 커밋하지 않음)
3. `vercel dev` 실행 후 표시되는 URL로 접속

## 환경 변수

Vercel 프로젝트 설정 또는 로컬 `.env`에만 값을 넣습니다. README·코드·스크린샷에 **실제 키 값을 넣지 마세요.**

| 변수명 | 용도 |
|--------|------|
| `LLM_BASE_URL` | OpenAI 호환 API 베이스 URL |
| `LLM_MODEL` | 사용할 모델 ID |
| `LLM_API_KEY` | LLM API 키 (서버 전용) |
| `KAKAO_REST_API_KEY` | Kakao Local 장소 검색·경로(내비) |
| `KAKAO_JS_KEY` | Kakao Maps JavaScript 키 (지도 표시, 도메인 등록 필요) |
| `WEBHOOK_URL` | (선택) AI·문의 결과를 받을 Zapier/Make/n8n 웹훅 |

템플릿: [`.env.example`](.env.example)

## 보너스 기능

- **기록·연동:** 탐방·팩트체크·문의 결과를 브라우저에 저장하고, `WEBHOOK_URL`이 있으면 `/api/save_result`가 외부로 전달합니다.
- **다크 모드:** 헤더 「다크/라이트」 토글
- **마이크로 인터랙션:** 버튼·결과·섹션 등장 모션 (`prefers-reduced-motion` 시 축소)
- **방문자 분석:** Vercel Web Analytics + 로컬 방문 횟수

## Vercel 배포

1. GitHub 저장소를 Vercel에 Import
2. Framework Preset: **Other** (정적 루트 + `api/` Serverless)
3. **Environment Variables**에 위 4개 변수 추가 (Production / Preview)
4. Deploy
5. 배포 후 탐방·팩트체크 각 1회 이상 동작 확인 (Kakao·LLM 네트워크 허용 여부 포함)

`vercel.json`에서 `api/**/*.py`에 Python 3.12 런타임을 지정합니다.

## 배포

- **GitHub:** https://github.com/Astrophotographer/tongil-mission-web
- **Vercel URL:** https://tongil-mission-web-skcksdnr2-6055s-projects.vercel.app

## 제출 증빙

| 파일 | 내용 |
|------|------|
| [`images/desktop-home.png`](images/desktop-home.png) | 데스크톱 홈 |
| [`images/mobile-home.png`](images/mobile-home.png) | 모바일 홈 |
| [`images/ai-factcheck.png`](images/ai-factcheck.png) | AI 팩트체크 동작 |
| [`docs/evidence.md`](docs/evidence.md) | AI 코딩 도구 사용 과정 요약 |

## 프로젝트 구조

```text
tongil-mission-web/
├── index.html          # 원페이지 (소개·탐방·팩트체크·FAQ)
├── css/
│   └── styles.css
├── js/
│   ├── nav.js
│   ├── theme.js
│   ├── history.js
│   ├── ux.js
│   ├── trip.js         # POST /api/trip_recommend
│   └── factcheck.js    # POST /api/fact_check
├── api/
│   ├── trip_recommend.py
│   ├── fact_check.py
│   ├── save_result.py  # 기록·웹훅
│   ├── _llm.py
│   ├── _kakao.py
│   ├── _validate.py
│   └── _trip_parse.py
├── images/             # 제출용 스크린샷 등
├── docs/
│   └── service-plan.md
├── tests/
├── requirements.txt
├── vercel.json
├── .env.example
└── README.md
```

## API 엔드포인트

| 메서드 | 경로 | 설명 |
|--------|------|------|
| POST | `/api/trip_recommend` | 탐방 추천 (LLM → Kakao → 경로 → LLM) |
| POST | `/api/fact_check` | 팩트체크 |
| POST | `/api/save_result` | AI·문의 기록 + 선택적 웹훅 |
| GET | `/api/public_config` | 프론트용 `kakaoJsKey` |

## 라이선스 / 미션

통일교육 미션 제출용 저장소입니다. API 키는 환경 변수로만 관리합니다.
