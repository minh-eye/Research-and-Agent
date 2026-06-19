# 스킬 테스트 & 반복 개선 가이드

하네스에서 생성한 스킬의 품질을 검증하고 개선하는 체계적 방법론.

## 목차
1. [테스트 철학](#1-테스트-철학)
2. [테스트 프롬프트 작성](#2-테스트-프롬프트-작성)
3. [With-skill vs Baseline 비교](#3-with-skill-vs-baseline-비교)
4. [Assertion 기반 평가](#4-assertion-기반-평가)
5. [전문 평가 에이전트](#5-전문-평가-에이전트)
6. [반복 개선 프로세스](#6-반복-개선-프로세스)
7. [Description 트리거 검증](#7-description-트리거-검증)
8. [테스트 결과 해석](#8-테스트-결과-해석)

---

## 1. 테스트 철학

**스킬이 없을 때 대비 무엇이 나아지는가?** 이것이 핵심 질문이다.

테스트는 두 가지를 측정한다:
1. **절대 품질**: 산출물이 요구사항을 충족하는가?
2. **상대적 가치**: 스킬 있는 실행이 없는 실행보다 나은가?

상대적 가치가 낮으면 스킬이 불필요하거나 description 트리거가 작동하지 않는 것이다.

---

## 2. 테스트 프롬프트 작성

실제 사용자가 입력할 만한 구체적이고 자연스러운 문장으로 작성한다.

### 좋은 테스트 프롬프트

```
"다운로드 폴더에 있는 'Q4_매출_최종_v2.xlsx'에서
C열(매출)과 D열(비용)을 사용해서 이익률(%) 열을 추가해줘"
```

**특징:**
- 실제 파일명 포함 (맥락 제공)
- 열 이름 명시 (구체적)
- 원하는 결과 명확 (이익률 % 열 추가)

### 나쁜 테스트 프롬프트

```
"엑셀 파일 처리해줘"
```

**문제점:**
- 파일 불명
- 작업 불명
- 기대 결과 없음

### 테스트 프롬프트 작성 체크리스트

- [ ] 실제 파일명/경로 포함 (가상이라도)
- [ ] 구체적 작업 명시
- [ ] 기대 결과 형식 포함
- [ ] 캐주얼한 표현도 포함 (트리거 다양성)
- [ ] 엣지 케이스 1개 이상 (빈 파일, 비정상 입력 등)

---

## 3. With-skill vs Baseline 비교

스킬의 부가가치를 측정하기 위해 동시에 두 개의 서브에이전트를 실행한다.

```
Agent({
  subagent_type: "general-purpose",
  model: "opus",
  run_in_background: true,
  prompt: """
  [WITH SKILL]
  다음 스킬을 읽고 작업을 수행하라:
  {skill_content}
  
  작업: {test_prompt}
  결과를 _workspace/with_skill_result.md에 저장하라.
  """
})

Agent({
  subagent_type: "general-purpose",
  model: "opus",
  run_in_background: true,
  prompt: """
  [BASELINE - 스킬 없음]
  작업: {test_prompt}
  결과를 _workspace/baseline_result.md에 저장하라.
  """
})
```

**타이밍 데이터 수집:** 서브에이전트 완료 알림에서 즉시 저장한다. 이 데이터는 알림 시점에만 접근 가능하고 이후 복구 불가.

```json
// _workspace/timing.json
{
  "with_skill": { "total_tokens": 12400, "duration_ms": 8200 },
  "baseline": { "total_tokens": 15600, "duration_ms": 11300 }
}
```

---

## 4. Assertion 기반 평가

객관적으로 검증 가능한 항목만 assertion으로 정의한다.

### 좋은 Assertion

```json
{
  "assertions": [
    "이익률(%) 열이 생성되었다",
    "이익률 계산식이 (매출-비용)/매출*100 을 따른다",
    "원본 C열, D열 데이터가 보존되었다",
    "결과 파일이 xlsx 형식으로 저장되었다"
  ]
}
```

**특징:** 파일 존재, 수식 정확성, 데이터 보존 — 모두 자동 검증 가능.

### 피해야 할 Assertion

```json
{
  "assertions": [
    "보고서가 잘 작성되었다",  // 주관적
    "사용자가 만족한다"        // 측정 불가
  ]
}
```

### grading.json 형식

```json
{
  "expectations": [
    {
      "text": "이익률(%) 열이 생성되었다",
      "passed": true,
      "evidence": "결과 파일의 E열 헤더가 '이익률(%)'로 확인됨"
    },
    {
      "text": "원본 데이터가 보존되었다",
      "passed": true,
      "evidence": "C열, D열 값이 원본과 동일함"
    }
  ],
  "summary": {
    "passed": 2,
    "failed": 0,
    "total": 2,
    "pass_rate": 1.0
  }
}
```

**필드명 주의:** `text`, `passed`, `evidence` 정확히 사용. `name`/`met`/`details` 변형 금지.

---

## 5. 전문 평가 에이전트

평가 품질을 높이는 전문 에이전트 3종.

### Grader — Assertion 채점 에이전트

```markdown
역할: with_skill_result.md와 baseline_result.md를 각각 assertion 목록으로 채점한다.
출력: _workspace/grading_with.json, _workspace/grading_baseline.json
형식: grading.json 스키마 준수
```

### Comparator — 블라인드 비교 에이전트

```markdown
역할: 두 결과물을 레이블 없이 비교하여 어느 쪽이 나은지 판단한다.
입력: Result A (with_skill), Result B (baseline) — 레이블 숨김
출력: { "winner": "A|B|tie", "reasoning": "..." }
목적: 편향 없는 품질 비교
```

### Analyzer — 통계 분석 에이전트

```markdown
역할: grading 결과와 timing 데이터를 분석하여 개선 우선순위를 도출한다.
출력: _workspace/analysis_report.md
포함 내용:
  - pass_rate 비교 (with vs baseline)
  - 토큰 효율성 (with가 baseline보다 토큰을 얼마나 절약했는가)
  - 반복 실패 패턴
  - 개선 권고사항 (우선순위 순)
```

---

## 6. 반복 개선 프로세스

테스트 결과에서 문제가 발견되면 피드백을 일반화하여 스킬을 수정한다.

### 개선 사이클

```
테스트 실행 → 결과 분석 → 피드백 일반화 → 스킬 수정 → 재테스트
```

### 피드백 일반화 원칙

**오버피팅 수정 (나쁜 예):**
```
"Q4 매출 열이 있으면 숫자로 변환하라"
```

**일반화 수정 (좋은 예):**
```
"열 이름에 수치를 암시하는 키워드(매출, 금액, 수량, 비용 등)가 있으면
숫자 타입으로 변환한다. 변환 실패 시 원본 값을 유지한다."
```

### 개선 기준

| 지표 | 목표 | 행동 |
|------|------|------|
| pass_rate (with skill) | ≥ 0.8 | 미달 시 실패 assertion 집중 개선 |
| pass_rate 향상 (vs baseline) | +0.2 이상 | 미달 시 description 재작성 또는 스킬 내용 강화 |
| 토큰 효율 | with ≤ baseline | 초과 시 스킬 내용 간소화 |

### 종료 조건

- 사용자가 만족하거나
- 의미 있는 개선이 더 이상 없을 때 (3회 연속 pass_rate 변화 < 0.05)

---

## 7. Description 트리거 검증

각 스킬의 description이 올바르게 트리거되는지 검증한다.

### Should-trigger 쿼리 (8~10개)

다양한 표현으로 스킬이 트리거되어야 하는 쿼리:

```
# 엑셀 스킬 예시
1. "Q4 매출 엑셀 파일에서 이익률 계산해줘" (명시적)
2. "downloads 폴더의 xlsx 열어서 D열 합계 구해줘" (캐주얼)
3. "이 스프레드시트 데이터 정제 필요해" (암시적)
4. "CSV를 엑셀로 변환하고 서식 적용해줘" (변환)
5. "피벗 테이블 만들어줘" (고급 기능)
```

### Should-NOT-trigger 쿼리 (8~10개)

키워드가 유사하지만 이 스킬이 아닌 near-miss 쿼리:

```
# 엑셀 스킬 near-miss 예시
1. "이 엑셀 파일의 차트를 PNG로 추출해줘" → 이미지 변환 스킬
2. "엑셀 VBA 매크로 디버깅해줘" → 코드 디버깅 스킬
3. "엑셀 파일을 이메일로 보내줘" → 이메일 스킬
4. "스프레드시트 데이터로 웹 대시보드 만들어줘" → 웹 개발 스킬
```

**near-miss 작성 핵심:** "피보나치 함수 작성" 같이 명백히 무관한 쿼리는 테스트 가치 없다. **경계가 모호한 쿼리**가 좋은 테스트 케이스다.

### 트리거 충돌 감지

기존 스킬과의 트리거 충돌도 이 단계에서 확인한다:
- A 스킬의 should-trigger가 B 스킬을 트리거하는 경우 → B 스킬 description에 경계 조건 추가

---

## 8. 테스트 결과 해석

| 결과 패턴 | 원인 | 조치 |
|---------|------|------|
| with_skill pass_rate 낮음 | 스킬 내용 부족 or 잘못된 지시 | 실패 assertion 분석, 스킬 내용 보강 |
| with vs baseline 차이 없음 | description 트리거 실패 or 스킬이 실제 도움 안 됨 | description 재작성 또는 스킬 방향성 재검토 |
| with_skill 토큰 많음 | 스킬 내용이 너무 길거나 불필요한 단계 있음 | 스킬 내용 린화, references/로 분리 |
| 특정 assertion만 반복 실패 | 해당 기능에 대한 스킬 지시 불명확 | 해당 섹션만 집중 보완 |
| 모든 assertion 통과 | 스킬 완성도 높음 | 트리거 검증으로 이동 |
