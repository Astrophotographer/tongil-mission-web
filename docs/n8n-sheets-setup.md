# n8n → Google 스프레드시트 연동

탐방/팩트체크/문의가 성공하면 사이트가 `POST /api/save_result`를 호출하고,  
서버가 **n8n Webhook**으로 JSON을 보냅니다. n8n이 **Google Sheets에 한 줄 append**합니다.

```text
브라우저 → /api/save_result → WEBHOOK_URL(n8n) → Google Sheets
```

## 1. 스프레드시트 준비

Google Sheets 새 문서 만들고, 시트 이름을 `기록`으로 둡니다.  
1행(헤더)에 아래 열을 만듭니다.

| recorded_at_kr | kind_label | kind | input | summary | source |
|----------------|------------|------|-------|---------|--------|

스프레드시트 URL의 `/d/`와 `/edit` 사이 문자열이 **시트 ID**입니다.  
이 프로젝트 기본 시트 ID(문서에 연결용): `1rDj4q5y8z5rS1UO6TH7huiSfVWcW-JTFMmA3fC82D9Q`  
(`docs/n8n-tongil-to-sheets.json` Document ID에 반영됨)

## 2. n8n 워크플로

1. n8n에서 **Import from File**  
   → 이 저장소의 [`n8n-tongil-to-sheets.json`](./n8n-tongil-to-sheets.json)
2. **Google Sheets** 노드
   - Google 계정 credential 연결
   - Document ID를 본인 시트 ID로 교체
   - Sheet 이름: `기록`
3. **Webhook** 노드 활성화(Active)
4. Production URL(또는 Test URL)을 복사  
   예: `https://YOUR_N8N/webhook/tongil-mission-save`

## 3. Vercel 환경 변수

| 이름 | 값 |
|------|-----|
| `WEBHOOK_URL` | 위에서 복사한 n8n Webhook URL |

Production / Preview / Development 모두에 넣고 **재배포**합니다.

```bash
# 예 (값은 채팅에 붙이지 말고 로컬에서)
printf '%s\n' 'https://YOUR_N8N/webhook/tongil-mission-save' | npx vercel env add WEBHOOK_URL production --sensitive
npx vercel deploy --prod
```

## 4. 전송 JSON 예시

```json
{
  "recorded_at": "2026-09-21T16:46:00+09:00",
  "recorded_at_kr": "2026-09-21 16:46:00",
  "kind": "trip",
  "kind_label": "탐방추천",
  "input": "2026-09-25 서울역 → 파주 …",
  "summary": "추천: 임진각 …",
  "source": "tongil-mission-web"
}
```

## 5. 확인

1. 사이트에서 팩트체크 또는 문의 1회 실행  
2. n8n Executions에 성공 로그  
3. 시트 `기록`에 행 추가  

`WEBHOOK_URL`이 없으면 로컬 기록만 되고 웹훅은 `skipped`입니다.
