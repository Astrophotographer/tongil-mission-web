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
| `KAKAO_REST_API_KEY` | Kakao Local 키워드 장소 검색 (탐방 파이프라인) |

템플릿: [`.env.example`](.env.example)

## Vercel 배포

1. GitHub 저장소를 Vercel에 Import
2. Framework Preset: **Other** (정적 루트 + `api/` Serverless)
3. **Environment Variables**에 위 4개 변수 추가 (Production / Preview)
4. Deploy
5. 배포 후 탐방·팩트체크 각 1회 이상 동작 확인 (Kakao·LLM 네트워크 허용 여부 포함)

`vercel.json`에서 `api/**/*.py`에 Python 3.12 런타임을 지정합니다.

## 배포

- **GitHub:** https://github.com/Astrophotographer/tongil-mission-web
- **Vercel URL:** (배포 후 기입 — `vercel login` 후 연동 필요)

**(배포 후 기입)**

## 프로젝트 구조

```text
tongil-mission-web/
├── index.html          # 원페이지 (소개·탐방·팩트체크·FAQ)
├── css/
│   └── styles.css
├── js/
│   ├── nav.js
│   ├── trip.js         # POST /api/trip_recommend
│   └── factcheck.js    # POST /api/fact_check
├── api/
│   ├── trip_recommend.py
│   ├── fact_check.py
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
| POST | `/api/trip_recommend` | 탐방 추천 (LLM → Kakao → LLM) |
| POST | `/api/fact_check` | 팩트체크 |

## 라이선스 / 미션

통일교육 미션 제출용 저장소입니다. API 키는 환경 변수로만 관리합니다.
