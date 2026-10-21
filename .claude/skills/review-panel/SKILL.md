---
name: review-panel
description: "건축환경·사회과학 방법론 연구 원고를 5명의 AI 심사위원(방법론·통계, 비교·일반화, 건축환경 도메인, 회의적 독자, 글쓰기)이 독립 심사하고 편집위원장이 종합하는 리뷰 패널. 심사 결과를 HTML 대시보드로 시각화한다. 'major revision' 입력 시 연구 도중의 결정 사항에 대한 다관점 토론 패널도 실행한다. '논문 리뷰해줘', '원고 심사', '투고 전 점검', '리뷰어 관점에서 봐줘', '심사위원이라면', 'major revision', '패널 의견', '재심사', '리뷰 다시', '수정본 다시 봐줘', '리뷰 대시보드' 요청 시 반드시 이 스킬을 사용할 것. 참고문헌 실재 여부만 확인하는 요청은 citation-verify 스킬을 쓴다."
---

# Review Panel — 원고 심사 패널 오케스트레이터

투고 전 원고를 다섯 관점의 독립 심사위원이 평가하고, 오케스트레이터(당신)가 편집위원장으로서 종합·조치 계획·답변서를 만든다. 결과는 대시보드로 시각화한다.

출처: rev2agent `prompts/08_manuscript_review.md`, `prompts/agent_workflow.md` (MIT, © 2026 Haebom Lee, https://github.com/dalbom/rev2agent)를 이 하네스 형식과 건축환경 연구에 맞게 재구성.

## 실행 모드

**서브 에이전트 (팬아웃/팬인).** 하네스 기본값은 에이전트 팀이지만, 이 패널은 리뷰어 간 독립성이 품질의 핵심이다. 리뷰어가 서로의 의견을 보면 먼저 나온 지적에 끌려가는 앵커링이 생기므로, 리뷰어끼리 통신하지 않는 서브 에이전트로 병렬 호출하고 종합은 편집위원장이 한다.

## 패널 구성

| ID | 에이전트 정의 | 페르소나 | 초점 |
|----|------------|---------|------|
| A | `.claude/agents/review-methodologist.md` | 방법론·통계 | 측정·설문·FGI 설계, 통계 타당성, 재현성 |
| B | `.claude/agents/review-comparison-critic.md` | 비교·일반화 | 기준 사례 공정성, 기후·계절·건물·재실자 일반화, 과잉 주장 |
| C | `.claude/agents/review-domain-expert.md` | 건축환경 도메인 | 온열·공기질·빛·음, 시뮬레이션 검증, 선행 연구 위치 |
| D | `.claude/agents/review-skeptic.md` | 회의적 독자 | 논리 비약, 대안 설명, 신규성, 윤리 |
| E | `.claude/agents/review-writing.md` | 글쓰기·표현 | 구조, 일관성, 그림·표, 용어 |

## 모드 분기

- 사용자가 **"major revision"** 또는 연구 도중 결정에 대한 패널 토론을 요청 → `references/major-revision.md`를 읽고 그 절차를 따른다. 아래 원고 심사 절차는 건너뛴다
- 원고 심사 요청 → 아래 Phase 0부터

## Phase 0: 컨텍스트 확인

1. 원고 파일 위치, 대상 저널, 원고 언어를 확인한다. 사용자가 말하지 않았으면 한 번 묻는다. 대상 저널을 모르면 "건축환경 분야 SCIE 저널"로 가정하고 그 가정을 알린다
2. `_workspace/review/` 상태로 사이클 번호를 정한다:
   - 없음 → `cycle1`, 초기 실행
   - 있음 + 같은 원고의 수정본 → 다음 번호로 재심사. 이전 `synthesis.md`는 편집위원장만 참조한다
   - 있음 + 다른 원고 → 기존 폴더를 `_workspace/review_prev_{YYYYMMDD}/`로 옮기고 `cycle1`부터
   - 사용자가 특정 리뷰어만 다시 요청 → 해당 리뷰어만 같은 사이클에서 재호출(부분 재실행)
3. 사이클이 5회를 넘으면 진행하지 않고, 남은 쟁점을 사용자에게 넘긴다. 같은 지적이 반복되면 패널이 아니라 사람이 판단할 문제다

## Phase 1: 독립 심사 (Pass 1)

**실행 모드:** 서브 에이전트, 5명 병렬

각 리뷰어를 `Agent` 도구로 호출한다: `subagent_type: "general-purpose"`, `model: "opus"`, `run_in_background: true`. 프롬프트에는 다음만 넣는다:

- 리뷰어 정의 파일 경로 (먼저 읽으라고 지시)
- 공통 지침 `.claude/skills/review-panel/references/reviewer-common.md` 경로
- 원고 파일 목록, 참고문헌 파일, 맥락 파일 목록
- 대상 저널
- 출력 경로 `_workspace/review/cycle{N}/reviewer_{ID}.md`
- "이전 사이클 리뷰, synthesis.md, response.md, panel.json은 읽지 말 것"

이전 리뷰 내용, 편집위원장의 의견, 다른 리뷰어의 결과는 프롬프트에 넣지 않는다.

리뷰어가 실패하면 1회 재호출한다. 재실패하면 그 리뷰어 없이 진행하고 종합 문서와 대시보드에 누락을 표시한다. 성공한 리뷰어가 3명 미만이면 패널 결과를 "예비"로 표시한다.

## Phase 2: 섹션별 심층 점검 (Pass 2)

**실행 모드:** 편집위원장 직접

다섯 리뷰를 읽은 뒤, 원고를 섹션별로 직접 점검한다. 질문 목록은 `references/section-audit.md`. Pass 2에서 찾은 문제는 `Pass 2` 태그를 붙여 합의 지적과 같은 우선순위로 다룬다.

## Phase 3: 종합

**실행 모드:** 편집위원장 직접

1. **분류(triage).** 같은 문제를 가리키는 지적을 하나로 묶고 분류한다:
   - consensus: 3명 이상 지적, 또는 Pass 2 발견 → 반드시 반영
   - majority: 2명 지적 → 반영 권장
   - individual: 1명 지적 → 타당성으로 판단. 표결 수가 적다고 결정적 반증을 무시하지 않는다
2. **우선순위.** structure·correctness → comparison → clarity → cosmetic
3. **조치 결정.** 지적마다 accept(반영) / partial(부분 반영, 사유) / reject(기각, 사유)
4. **주장 도전 원장.** 원고의 핵심 주장마다, 그 주장을 흔드는 결과·반례·대안 설명·미해결 지적을 모으고 다음 중 하나로 결론짓는다:
   - `resolved_by_evidence` 근거로 해소 / `claim_narrowed` 주장 범위 축소 / `limitation_disclosed` 한계로 명시 / `research_redirected` 추가 조사·재구성 필요 / `claim_withdrawn` 주장 철회 / `unresolved` 미해결
   핵심 주장에 `unresolved`가 남아 있으면 원고를 "투고 준비 완료"로 판정하지 않는다
5. **산출물 작성:**
   - `_workspace/review/cycle{N}/synthesis.md` — 분류된 지적 목록, 조치 계획, 주장 도전 원장
   - `_workspace/review/cycle{N}/response.md` — 리뷰어별 Major Issue에 대한 답변서 초안(실제 수정 답변서 형식)
   - `_workspace/review/cycle{N}/panel.json` — 대시보드 데이터. 스키마는 `references/panel-schema.md`

## Phase 4: 대시보드

```bash
python3 .claude/skills/review-panel/scripts/build_dashboard.py _workspace/review/cycle{N}/panel.json -o _workspace/review/cycle{N}/dashboard.html
```

이전 사이클이 있으면 `--history _workspace/review/cycle1/panel.json ...`을 더해 사이클별 판정 추이를 함께 그린다. 스크립트는 외부 라이브러리 없이 단일 HTML 파일을 만들므로 브라우저로 바로 열 수 있다. 생성 후 사용자에게 파일을 보낸다.

이어서 웹 대시보드(아래 "웹 대시보드")에서 열 수 있도록 결과 파일을 만든다:

```bash
python3 .claude/skills/review-panel/scripts/export_bundle.py _workspace/review/cycle{N} -o _workspace/review/cycle{N}/bundle.json
```

## 웹 대시보드

`app/review-desk.html`은 claude.ai Artifact로 게시된 웹 앱이다(https://claude.ai/artifact/2CEjH1ZmMEcmVeJaW5xbQZ, 소유자 전용). 이 스킬과 같은 패널(A~E + 편집위원장)을 브라우저에서 실행한다.

- 원고(.docx/.pdf/.md/.txt) 업로드, 목표 학술지·논문 유형·연구 분야·리뷰 언어 선택, 재심사 대상 지정
- 심사위원 호출은 페이지의 `sample` capability로, 보는 사람의 Claude 계정 사용량으로 실행된다. 호출마다 기억이 없으므로 리뷰어 독립성이 구조적으로 보장된다
- 결과는 보는 사람 전용 저장소(`db`의 `data/users/<id>/`)에 저장되고, 원고 본문은 저장하지 않는다
- 종합 보고서·답변서 초안·리뷰 원문(.md)과 전체 결과(.json)를 내려받는다
- 로컬 스킬로 만든 `bundle.json`을 "기록 → 결과 파일 불러오기"로 가져올 수 있다

앱의 페르소나·프롬프트를 바꿀 때는 `.claude/agents/review-*.md`와 함께 고쳐 둘을 맞춘다. 수정 후 같은 파일 경로로 다시 게시하면 URL이 유지된다.

## Phase 5: 보고와 수정

1. 사용자에게 요약한다: 리뷰어별 판정, consensus 지적 목록, 미해결 핵심 주장, 대시보드 경로
2. 원고 수정은 사용자가 승인한 항목만 한다. 연구 질문, 분석 계획, 결과 해석 자체를 바꾸는 수정은 사용자 결정 사항으로 남긴다. 새 조사나 분석이 필요하면 그 필요를 보고하고 직접 수행하지 않는다
3. 수정 후 재심사를 원하면 Phase 0부터 다음 사이클로 진행한다
4. 실행 후 피드백(리뷰어가 놓친 관점, 불필요한 지적 유형)을 물어보고, 반복되는 피드백은 해당 리뷰어 정의 파일에 반영한다

## 에러 핸들링

| 상황 | 대응 |
|------|------|
| 리뷰어 호출 실패 | 1회 재시도, 재실패 시 누락 표시 후 진행 |
| 원고 형식을 읽을 수 없음(.hwp 등) | 사용자에게 PDF·DOCX·텍스트 변환 요청 |
| 리뷰 형식이 공통 지침과 다름 | 편집위원장이 내용을 읽어 수동으로 panel.json에 반영 |
| 대시보드 스크립트 오류 | 오류 메시지를 보고하고 synthesis.md만 전달 |

## 테스트 시나리오

**정상 흐름:** "이 원고 Building and Environment 투고 전에 리뷰해줘" + `paper/` 폴더 → cycle1 생성 → 리뷰어 5명 병렬 → Pass 2 → synthesis.md, response.md, panel.json → dashboard.html 전달

**재심사 흐름:** cycle1이 있는 상태에서 "수정본 다시 봐줘" → cycle2 생성 → 리뷰어 프롬프트에 cycle1 내용 없음 확인 → 편집위원장이 cycle1 지적 해소 여부를 synthesis.md에 대조 → `--history`로 추이 포함 대시보드

**에러 흐름:** Reviewer C 호출이 두 번 실패 → 4명으로 진행 → panel.json의 C 항목 `status: "missing"` → 대시보드에 누락 표시, 보고에 명시

**major revision 흐름:** "major revision — 설문 결과랑 실측 결과가 반대로 나왔는데 어떻게 해석하지?" → `references/major-revision.md` 절차 → A·C·D 독립 의견 → synthesis.md 권고안
