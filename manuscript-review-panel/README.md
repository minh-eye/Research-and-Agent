# 원고 심사 패널 (독립 실행판)

claude.ai 아티팩트로 만들었던 "원고 심사 패널"을 **Chrome·Microsoft Edge에서 주소로 바로 여는** 단일 HTML 파일로 옮긴 버전입니다. 서버도 설치도 필요 없습니다.

## 여는 방법

1. `index.html`을 PC에 내려받습니다 (예: `C:\Users\<이름>\Documents\review-panel\index.html`).
2. Chrome 또는 Edge 주소창에 파일 경로를 입력합니다.
   - Windows: `file:///C:/Users/<이름>/Documents/review-panel/index.html`
   - 또는 파일을 브라우저 창으로 끌어다 놓거나 더블클릭해도 됩니다.
3. 첫 화면 **새 심사 → 0 · Claude API 연결**에 Anthropic API 키(`sk-ant-...`)를 넣습니다. 키는 [Anthropic Console](https://console.anthropic.com/settings/keys)에서 발급합니다.
4. 원고를 올리고 **심사 시작**을 누릅니다.

정적 웹 호스팅(GitHub Pages, Vercel, 사내 웹서버 등)에 이 파일 하나만 올려도 그 주소로 똑같이 동작합니다.

## claude.ai 버전과 달라진 점

| 항목 | claude.ai 아티팩트 | 독립 실행판 |
|---|---|---|
| Claude 호출 | 로그인한 claude.ai 계정 사용량 | 입력한 **Anthropic API 키**로 `api.anthropic.com` 직접 호출 (API 요금 과금) |
| 모델 | 자동 | 화면에서 선택 (기본 Claude Opus 5.5, 심사·종합은 effort `high`, 답변서는 `medium`) |
| 심사 기록 | claude.ai 계정 저장소 | 이 브라우저의 IndexedDB (다른 PC·브라우저와 공유되지 않음) |
| 내려받기 | claude.ai 저장 창 | 브라우저 기본 다운로드 |

거절(refusal)이 나면 API가 다른 모델로 자동 재시도하도록 `fallbacks: "default"`를 켜 두었습니다.

## 비용과 보안

- 한 번 심사하면 요청이 최대 7건(심사위원 5 + 편집위원장 종합 1 + 답변서 1) 나갑니다. 원고 길이에 따라 비용이 달라집니다.
- "키 기억하기"를 켜면 키가 이 브라우저의 localStorage에 평문으로 남습니다. 공용 PC에서는 끄세요. 끄면 탭을 닫을 때 키가 지워집니다.
- 원고와 키는 `api.anthropic.com`으로만 전송됩니다. 원고 본문은 기록에 저장하지 않습니다.
- .docx/.pdf를 읽는 라이브러리(mammoth, pdf.js)는 jsDelivr CDN에서 불러오므로 인터넷 연결이 필요합니다.

## 회사망에서 안 될 때

"api.anthropic.com에 연결하지 못했습니다"가 뜨면 방화벽이나 프록시가 브라우저에서 Anthropic API로 직접 나가는 요청을 막고 있는 경우가 많습니다. 이때는 `../project-review-app`처럼 서버 프록시를 두는 방식을 써야 합니다.
