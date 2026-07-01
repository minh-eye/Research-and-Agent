# Project Review App

`harness-review.vercel.app`을 리버스 엔지니어링해 만든, **개인용 프로젝트 리뷰 코칭 웹앱**입니다.
원본은 "스킬/에이전트 설계 자료"만 대상으로 했지만, 이 버전은 앞으로 진행하는 **어떤 프로젝트**(코드, 기획서, 보고서, 슬라이드 등)든 업로드해서 코칭 피드백을 받을 수 있도록 범위를 넓혔습니다.

## 무엇을 하는 앱인가

1. 브라우저에서 `.md/.txt/.html/.docx/.pptx/.pdf` 파일을 업로드하면, **서버로 파일을 보내지 않고** 브라우저 안에서 텍스트만 추출합니다 (mammoth/JSZip/pdf.js).
2. 추출된 텍스트를 Claude API에 보내 4개 섹션을 병렬로 분석합니다:
   - **01 요약·강점** — 무엇을 만들었는지 + 잘된 점
   - **02 성장 지점** — 약점을 "무엇을·어떻게·왜" 개선책과 함께 제시
   - **03 하네스 엔지니어링 보완** — 컨텍스트/에러처리/문서화/재현성 등 13개 축 중 해당하는 것만
   - **04 GitHub 학습 경로** — 실재하는 저장소 추천 + 다음 한 걸음 3가지
3. 점수·등급은 매기지 않고, 모든 지적은 제출물의 실제 문구를 인용해 근거를 붙입니다.
4. 비개발자도 이해하도록 각 섹션 끝에 "쉽게 말하면 / 용어 풀이 / 꿀팁" 각주가 붙습니다.

## 배포 모드 (2가지)

`index.html`의 `window.PROJECT_REVIEW_CONFIG.proxyUrl`로 전환합니다.

- **프록시 모드 (기본, `proxyUrl: "/api/messages"`)**: Claude API 키는 서버 환경변수(`ANTHROPIC_API_KEY`)에만 있고 브라우저는 절대 키를 다루지 않습니다. 대신 비밀번호 게이트(`APP_PASSWORD`)가 앱 앞단을 지킵니다. 여러 명과 링크를 공유할 때 이 모드를 씁니다.
- **직접 모드 (`proxyUrl: ""`)**: 사용자가 자신의 Claude API 키를 브라우저에 직접 입력합니다. 게이트가 없고, 서버가 필요 없어 정적 호스팅만으로 동작합니다. 혼자 로컬에서 쓸 때 편합니다.

## 로컬 실행

```bash
cd project-review-app
cp .env.example .env   # 값 채우기
export $(cat .env | xargs)   # 또는 직접 env로 실행
ANTHROPIC_API_KEY=sk-ant-... APP_PASSWORD=AISTP26 node server.js
```

`http://localhost:8787` 접속 → 비밀번호(`AISTP26`, 미변경 시) 입력 → 파일 업로드.

## Vercel 배포

1. 이 저장소를 GitHub에 push한 뒤 Vercel에서 `project-review-app` 디렉터리를 루트로 지정해 Import.
2. Vercel 프로젝트 설정 → Environment Variables에 추가:
   - `ANTHROPIC_API_KEY` — Anthropic API 키
   - `APP_PASSWORD` — 앱 비밀번호 (기본값 `AISTP26`, 원하는 값으로 교체 권장)
3. `api/messages.js`는 자동으로 Vercel Serverless Function(`/api/messages`)이 되고, `index.html`은 정적 파일로 서빙됩니다. 별도 설정 파일(`vercel.json`) 없이 동작합니다.

## 보안 메모

- `APP_PASSWORD` 기본값(`AISTP26`)은 이 저장소에 하드코딩되어 있으므로, **공개적으로 링크를 공유하기 전에 반드시 환경변수로 다른 값을 설정**하세요.
- `ANTHROPIC_API_KEY`는 절대 클라이언트 코드나 저장소에 커밋하지 마세요 (`.env`는 이미 이런 용도로 분리되어 있습니다).
- 업로드된 파일 자체는 서버로 전송되지 않습니다 — 브라우저에서 추출한 텍스트(최대 14,000자)만 Anthropic API로 전송됩니다.

## 원본과의 주요 차이점

| 항목 | 원본 (harness-review) | 이 버전 (project-review-app) |
|---|---|---|
| 대상 | 스킬/에이전트 설계 자료 | 임의의 프로젝트 산출물 |
| 03번 섹션 축 | 11개 (에이전트 중심) | 13개 (문서화·재현성 축 추가, 일반 소프트웨어/연구 프로젝트도 커버) |
| 문구 | 수업(과학기술분야 AI활용) 맥락 | 범용 개인 코칭 도구 맥락 |
| 배포 코드 | 비공개 | 이 저장소에 `api/messages.js` + `server.js`로 재구현 |
