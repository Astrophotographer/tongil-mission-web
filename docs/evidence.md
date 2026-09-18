# 증빙 자료 — AI 코딩 도구 사용 과정

작성일: 2026-09-18  
도구: Cursor (Composer / Agent)

## 요약

본 프로젝트(통일탐방 미니)는 Cursor AI 코딩 에이전트와 대화하며 기획·구현·배포를 진행했습니다.

| 단계 | 내용 |
|------|------|
| 요구사항 검토 | 미션 스펙과 tongildata/koreaboard 스택 충돌 정리, 바닐라+Python `api/`로 결정 |
| 설계 | 탐방 AI + 팩트체크 + Kakao, 별도 레포 `tongil-mission-web` |
| 구현 | Subagent-Driven으로 Task 1~9 구현(프론트·API·테스트·문서) |
| 배포 | GitHub 연동, Vercel 배포, SSO 보호 해제, 환경 변수 설정 |
| 보너스 | 다크 모드, 기록/웹훅, 마이크로 인터랙션, 방문 측정 |
| 증빙 캡처 | 배포 URL에서 데스크톱·모바일·팩트체크 AI 결과 스크린샷 촬영 |

## 스크린샷 세트 (서비스)

| 파일 | 설명 |
|------|------|
| [`images/desktop-home.png`](../images/desktop-home.png) | 데스크톱 홈(라이트 모드·상단 메뉴) |
| [`images/mobile-home.png`](../images/mobile-home.png) | 모바일 뷰(햄버거 메뉴) |
| [`images/ai-factcheck.png`](../images/ai-factcheck.png) | AI 팩트체크 입력→결과 동작 |

## AI 코딩 과정 증빙

- Cursor 채팅에서 미션 요구사항 붙여넣기 → 가능 여부·중복 검토 → 설계 승인 → 구현 플랜 → 배포까지 연속 진행
- 커밋 이력(`git log`)에 scaffold, API, 프론트 연동, 보너스, 배포 URL 문서화가 남아 있음
- 본 문서는 제출용 **대화 과정 요약 로그**이며, 필요 시 Cursor 채팅 화면을 추가로 캡처해 제출 패키지에 첨부하면 됩니다.

## 배포 URL

https://tongil-mission-web-skcksdnr2-6055s-projects.vercel.app
