# 통일탐방 미니 — 미션 제출용 웹서비스 설계

날짜: 2026-09-16  
상태: 승인됨 (설계)  
저장소: `tongil-mission-web` (koreaboard / tongildata와 분리)

## 1. 목표

통일교육용 **탐방 일정 AI 추천**과 **팩트체크**를 한 사이트에서 제공하고, Vercel URL로 배포해 미션 제출 패키지를 완성한다.

학습/제출 포인트:

- 바닐라 HTML/CSS/JS + Vercel Python Serverless (`api/`)
- 프론트 `fetch('/api/...')` → 서버에서 AI/Kakao 호출 → 화면 반영
- API 키는 환경 변수만 사용 (코드·README·스크린샷 미노출)

## 2. 비범위

- React / Vue / Next 등 프레임워크
- koreaboard 보드·지도 JS SDK(핀)·차트·히스토리 DB
- 노코드 자동화·다크모드 등 보너스
- 기존 koreaboard/tongildata 저장소에 섞어 배포

## 3. 서비스 개요

| 항목 | 내용 |
|------|------|
| 서비스명(가칭) | 통일탐방 미니 |
| 목적 | 탐방 수업 초안 생성 + 관련 질문 팩트체크 |
| 타겟 | 통일교육 준비 교사·강사·대학생 |

## 4. 페이지/섹션 (원페이지 + 앵커 메뉴)

1. **소개(Hero)** — 가치 한 줄 + CTA(탐방 / 팩트체크)
2. **탐방 AI 추천** — 입력 폼 + 결과
3. **팩트체크** — 질문 폼 + 예시 버튼 + 결과
4. **이용 안내/FAQ** — 실패·키·주의사항

반응형: 모바일에서도 메뉴 이동·폼·결과가 깨지지 않을 것.

## 5. AI·외부 API

### 공통 LLM (기존 koreaboard와 동일)

| 환경 변수 | 용도 |
|-----------|------|
| `LLM_BASE_URL` | OpenAI 호환 베이스 (Cody: `…/v1`) |
| `LLM_MODEL` | 예: `gpt-5.4-mini` |
| `LLM_API_KEY` | 서버 전용 |

### Kakao Local (탐방 보조)

| 환경 변수 | 용도 |
|-----------|------|
| `KAKAO_REST_API_KEY` | 키워드 장소 검색 (맛집·주변지) |

## 6. 기능 A — 탐방 AI 추천

**엔드포인트:** `POST /api/trip-recommend`

### 입력 (필수)

| 필드 | 설명 |
|------|------|
| `date` | 탐방일 `YYYY-MM-DD` |
| `origin` | 출발지 |
| `schedule` | 일정(반나절/1일 등) |
| `audience` | 대상 요약(학년·인원 등) |

### 파이프라인

```text
입력
  → 1) Cody: 탐방지·학습목표·현장미션·nearby_area JSON
  → 2) Kakao Local: nearby_area 기준 맛집·주변지
       (실패/0건 → 빈 목록, 본문 리포트는 계속)
  → 3) Cody: Markdown 탐방 수업안(장소 결과 반영)
  → JSON 응답 → 화면 카드
```

### 출력

- 추천 탐방지, 추천 이유, 학습목표, 현장미션
- 주변 맛집·장소 목록(있으면)
- Markdown 또는 구조화 텍스트 본문

### 실패 처리

| 상황 | 사용자 안내 |
|------|-------------|
| 필수값 누락 | “필수값을 입력하세요” |
| LLM 4xx/5xx·타임아웃 | “잠시 후 다시 시도하세요” |
| Kakao 실패 | “주변 장소 정보를 불러오지 못했습니다” + 탐방 본문은 표시 |
| 로딩 중 | “응답을 기다리는 중…” |

## 7. 기능 B — 팩트체크

**엔드포인트:** `POST /api/fact-check`

### 입력

- `question` (필수): 주장/질문 텍스트
- 예시 버튼 2~3개(클라이언트 프리필)

### 처리

- 동일 Cody 모델로 짧은 판정·근거 요약
- koreaboard의 보드/차트/용어사전 풀파이프라인은 이식하지 않음
- (선택) 데모성 고정 답은 없어도 됨 — LLM만으로 동작

### 출력

- 답변 텍스트 영역

### 실패 처리

| 상황 | 사용자 안내 |
|------|-------------|
| 빈 입력 | “필수값을 입력하세요” |
| API 오류·타임아웃 | “잠시 후 다시 시도하세요” |
| 로딩 중 | “응답을 기다리는 중…” |

## 8. 아키텍처·폴더 구조

```text
tongil-mission-web/
├── index.html
├── css/styles.css
├── js/
│   ├── nav.js
│   ├── trip.js
│   └── factcheck.js
├── api/
│   ├── trip_recommend.py
│   └── fact_check.py
├── images/
├── docs/
│   ├── service-plan.md
│   └── superpowers/specs/… (본 문서)
├── requirements.txt
├── vercel.json
├── .env.example
├── .gitignore
└── README.md
```

### 데이터 흐름

```text
브라우저 (바닐라 JS)
    → fetch('/api/trip-recommend' | '/api/fact-check')
Vercel Python Serverless
    → Cody chat/completions (+ Kakao Local for trip)
    → { ok, result | error }
화면 반영
```

## 9. 보안

- 키는 Vercel / 로컬 `.env`만. `.env`는 gitignore.
- `.env.example`·README에는 변수 **이름**만.
- 프론트에 키를 넣지 않는다.
- Cody·Kakao가 Vercel에서 호출 가능한지 배포 후 검증. 막히면 키/네트워크 설정 점검.

## 10. 제출 패키지

1. 배포된 Vercel URL  
2. GitHub 저장소 (위 구조)  
3. README (소개·스택·실행/배포·URL·env)  
4. 서비스 기획서 `docs/service-plan.md`  
5. 증빙: 데스크톱·모바일·AI 동작 스크린샷 + AI 코딩 도구 사용 증빙  

## 11. 성공 기준

- [ ] 메뉴로 섹션 3개 이상 이동
- [ ] 모바일·데스크톱에서 레이아웃 정상
- [ ] 탐방: 입력 → (Kakao 포함) 결과 표시
- [ ] 팩트체크: 입력 → 결과 표시
- [ ] 빈 입력 또는 API 오류 안내 중 최소 1종
- [ ] 배포 URL에서 동료 테스트 가능
- [ ] 키 미노출

## 12. 결정 이력

- 미션 제출(A) → 바닐라 + Python `api/` 필수
- 테마: 통일/탐방 + 팩트체크
- AI 기능: 탐방 + 팩트체크 (B), 동일 Cody 모델
- 접근: 미션 전용 얇은 사이트 (접근 1)
- Kakao Local: 탐방 파이프라인에 **포함** (사용자 요청으로 비범위에서 제외 해제)
