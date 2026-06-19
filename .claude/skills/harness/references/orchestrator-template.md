# 오케스트레이터 스킬 템플릿

하네스 오케스트레이터를 작성할 때 참조하는 3가지 템플릿. 실행 모드(에이전트 팀 / 서브 에이전트 / 하이브리드)에 따라 선택한다.

## 목차
1. [템플릿 A: 에이전트 팀 모드](#템플릿-a-에이전트-팀-모드)
2. [템플릿 B: 서브 에이전트 모드](#템플릿-b-서브-에이전트-모드)
3. [템플릿 C: 하이브리드 모드](#템플릿-c-하이브리드-모드)
4. [에러 핸들링](#에러-핸들링)
5. [공통 원칙](#공통-원칙)

---

## 템플릿 A: 에이전트 팀 모드

2명 이상의 에이전트가 실시간 협업이 필요할 때 사용하는 기본 모드.

```markdown
---
name: {domain}-orchestrator
description: "{도메인} 전체 워크플로우를 조율한다. '{도메인} 시작해줘', '{도메인} 실행해줘',
  '{도메인} 다시 실행', '{도메인} 업데이트', '이전 결과 개선' 요청 시 이 스킬을 사용한다.
  **실행 모드: 에이전트 팀**"
---

# {Domain} Orchestrator

**실행 모드:** 에이전트 팀 (기본)

## Phase 0: 컨텍스트 확인

_workspace/ 디렉토리 존재 여부를 확인하여 실행 모드를 결정한다:

- `_workspace/` 없음 → **초기 실행** (Phase 1부터)
- `_workspace/` 있음 + 부분 수정 요청 → **부분 재실행** (해당 에이전트만 재호출)
- `_workspace/` 있음 + 새 입력 → **새 실행** (기존 `_workspace/`를 `_workspace_prev/`로 이동)

## Phase 1: 입력 분석 및 준비

1. 사용자 입력 파싱
2. `_workspace/` 디렉토리 생성 (없으면)
3. 팀 구성 계획 수립

## Phase 2: 팀 구성 및 실행

**실행 모드: 에이전트 팀**

TeamCreate로 팀을 구성한다:

```
TeamCreate({
  team_name: "{domain}-team",
  members: [
    { name: "agent-a", agent_type: "agent-a", role: "역할 설명" },
    { name: "agent-b", agent_type: "agent-b", role: "역할 설명" },
    { name: "agent-c", agent_type: "agent-c", role: "역할 설명" }
  ]
})
```

작업을 TaskCreate로 등록한다:

```
TaskCreate([
  { id: "task-1", assignee: "agent-a", description: "작업1", dependencies: [] },
  { id: "task-2", assignee: "agent-b", description: "작업2", dependencies: ["task-1"] },
  { id: "task-3", assignee: "agent-c", description: "작업3", dependencies: [] }
])
```

팀원들은 SendMessage로 자체 조율한다:
- 팀원A → 팀원B: 중간 산출물 전달
- 팀원B → 팀원A: 검증 결과 피드백

## Phase 3: 결과 수집 및 종합

1. 팀원들의 산출물 수집 (`_workspace/` 파일 읽기)
2. 결과 통합
3. 최종 보고서 생성

## Phase 4: 팀 정리

팀을 해체하고 결과를 보고한다.

## 에러 핸들링

- 에이전트 실패 시: 1회 재시도 후 실패하면 해당 결과 없이 진행 (보고서에 누락 명시)
- 상충 데이터: 삭제하지 않고 출처 병기
- 타임아웃: 30초 대기 후 다음 단계 진행

## 테스트 시나리오

**정상 흐름:**
1. 입력 → Phase 0 판단 (초기 실행) → Phase 1~4 완료 → 결과 보고

**에러 흐름:**
1. 에이전트 B 실패 → 재시도 → 실패 → 나머지 에이전트 결과로 부분 보고
```

---

## 템플릿 B: 서브 에이전트 모드

팀원 간 통신이 불필요하고, 결과만 메인에 반환하면 충분한 경우.

```markdown
---
name: {domain}-orchestrator
description: "{도메인} 워크플로우를 조율한다. **실행 모드: 서브 에이전트**"
---

# {Domain} Orchestrator

**실행 모드:** 서브 에이전트

## Phase 0: 컨텍스트 확인

_workspace/ 존재 여부로 초기/부분/새 실행을 결정한다.

## Phase 1: 입력 분석

사용자 입력 파싱, `_workspace/` 준비.

## Phase 2: 병렬 실행

**실행 모드: 서브 에이전트**

Agent 도구로 서브 에이전트를 병렬 실행한다:

```
// 병렬 실행 (백그라운드)
Agent({ subagent_type: "agent-a", model: "opus", run_in_background: true,
  prompt: "작업A 수행. 결과를 _workspace/01_agent-a_output.md에 저장하라." })

Agent({ subagent_type: "agent-b", model: "opus", run_in_background: true,
  prompt: "작업B 수행. 결과를 _workspace/01_agent-b_output.md에 저장하라." })

// 완료 대기 후 결과 수집
```

## Phase 3: 결과 통합

`_workspace/` 파일들을 읽고 통합 산출물 생성.

## 에러 핸들링

- 서브 에이전트 실패 시: 1회 재시도, 재실패 시 결과 없이 진행
- 반환값 파싱 실패 시: 파일 기반 산출물로 폴백

## 테스트 시나리오

**정상 흐름:** 병렬 실행 → 결과 수집 → 통합 보고
**에러 흐름:** 서브A 실패 → 재시도 → 서브B 결과만으로 통합 보고
```

---

## 템플릿 C: 하이브리드 모드

Phase마다 실행 모드를 전환하는 패턴. 자주 쓰이는 조합:
- Phase 2: 서브 에이전트로 독립 자료 병렬 수집
- Phase 3: 팀으로 합의 기반 통합

```markdown
---
name: {domain}-orchestrator
description: "{도메인} 하이브리드 워크플로우를 조율한다. **실행 모드: 하이브리드**"
---

# {Domain} Orchestrator

**실행 모드:** 하이브리드 (Phase별 전환)

## Phase 0: 컨텍스트 확인

_workspace/ 존재 여부로 실행 모드 결정.

## Phase 1: 입력 분석

사용자 입력 파싱, `_workspace/` 준비.

## Phase 2: 독립 수집 (서브 에이전트)

**실행 모드: 서브 에이전트**

각 소스에서 독립적으로 자료를 수집한다:

```
Agent({ subagent_type: "collector-a", model: "opus", run_in_background: true,
  prompt: "소스A 수집 후 _workspace/02_collect_a.md에 저장" })
Agent({ subagent_type: "collector-b", model: "opus", run_in_background: true,
  prompt: "소스B 수집 후 _workspace/02_collect_b.md에 저장" })
```

## Phase 3: 합의 기반 통합 (에이전트 팀)

**실행 모드: 에이전트 팀**

Phase 2 산출물을 바탕으로 팀을 구성하여 합의 통합한다:

```
TeamCreate({
  team_name: "integration-team",
  members: [
    { name: "analyst", agent_type: "analyst", role: "수집 데이터 분석" },
    { name: "synthesizer", agent_type: "synthesizer", role: "최종 통합" }
  ]
})
```

팀원들이 `_workspace/02_collect_*.md`를 읽고 SendMessage로 토론·합의한다.

## Phase 4: 최종 보고

팀 해체, 통합 결과 보고.

## 에러 핸들링

- Phase 2 수집 실패: 가용한 소스만으로 Phase 3 진행, 누락 소스 명시
- Phase 3 팀 통신 중단: 마지막 공유 파일 기준으로 강제 통합

## 테스트 시나리오

**정상 흐름:** 서브 수집(병렬) → 팀 통합(협의) → 최종 보고
**에러 흐름:** 소스B 수집 실패 → 소스A만으로 Phase 3 진행 → 부분 보고
```

---

## 에러 핸들링

오케스트레이터에 포함하는 에러 처리 방침:

| 에러 유형 | 1차 대응 | 2차 대응 |
|----------|---------|---------|
| 에이전트 타임아웃 | 30초 대기 후 재시도 | 해당 결과 없이 진행, 보고서에 누락 명시 |
| 파일 읽기 실패 | 경로 재확인 후 재시도 | 해당 에이전트 건너뜀 |
| 상충 데이터 | 두 결과 모두 출처 병기 | 사용자에게 선택 요청 |
| 팀 통신 중단 | SendMessage 재시도 | 마지막 공유 파일로 강제 진행 |
| 의존 작업 실패 | 의존 에이전트 재실행 | 의존 관계 우회 경로 탐색 |

**핵심 원칙:**
- 1회 재시도 후 재실패 시 해당 결과 없이 진행 (무한 루프 방지)
- 상충 데이터는 삭제하지 않고 출처 병기 (정보 손실 방지)
- 실패 항목은 최종 보고서에 명시 (투명성 보장)

---

## 공통 원칙

모든 오케스트레이터가 따르는 공통 규칙:

1. **Phase 0 필수**: 컨텍스트 확인으로 초기/부분/새 실행을 구분한다
2. **_workspace/ 활용**: 중간 산출물은 `_workspace/`에 저장, 최종 산출물만 사용자 경로에 출력
3. **파일명 컨벤션**: `{phase:02d}_{agent}_{artifact}.{ext}` (예: `02_analyst_requirements.md`)
4. **model: "opus" 명시**: 모든 Agent 호출에 필수
5. **후속 키워드 포함**: description에 "다시 실행", "업데이트", "수정", "보완" 포함
6. **테스트 시나리오 섹션**: 정상 흐름 1개 + 에러 흐름 1개 이상
