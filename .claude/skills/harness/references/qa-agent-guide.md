# QA 에이전트 가이드

빌드 하네스에 QA 에이전트를 포함할 때 참조한다. 통합 정합성 검증 방법론, 경계면 버그 패턴, QA 에이전트 정의 템플릿을 포함한다.

## 목차
1. [QA의 핵심 문제: 경계면 버그](#1-qa의-핵심-문제-경계면-버그)
2. [주요 검증 영역](#2-주요-검증-영역)
3. [점진적 QA 전략](#3-점진적-qa-전략)
4. [QA 에이전트 정의 템플릿](#4-qa-에이전트-정의-템플릿)
5. [실전 버그 패턴 7가지](#5-실전-버그-패턴-7가지)
6. [QA 체크리스트](#6-qa-체크리스트)

---

## 1. QA의 핵심 문제: 경계면 버그

정적 코드 리뷰와 TypeScript 컴파일은 통합 실패를 자주 놓친다.

**대표 예시:**
```typescript
// 컴파일 성공하지만 런타임 실패
const data = await fetchJson<SlideProject[]>('/api/projects');
// API가 실제로 { projects: [...] }를 반환하는 경우
```

TypeScript generics는 컴파일 타임에 타입을 확인하지만, 런타임 API 응답의 실제 shape은 검사하지 않는다. 각 컴포넌트가 독립적으로 완벽해도 **연결 지점(경계면)**에서 실패한다.

**QA 에이전트의 역할:** "존재 확인"이 아니라 **"경계면 교차 비교"** — API 응답과 프론트 훅을 동시에 읽고 shape을 비교한다.

---

## 2. 주요 검증 영역

### 2-1. API 응답 ↔ 프론트엔드 훅 정합성

```
검증 대상:
  - NextResponse.json()이 반환하는 실제 shape
  - vs. 해당 API를 소비하는 훅의 타입 파라미터

찾아야 할 버그:
  - 래핑 불일치: API는 { data: [...] } 반환, 훅은 [...] 기대
  - 필드명 불일치: API는 user_id, 훅은 userId
  - 중첩 구조 차이: API는 { meta: { total } }, 훅은 { total }
```

### 2-2. 파일 경로 ↔ 라우트 링크 정합성

```
검증 대상:
  - src/app/ 디렉토리의 실제 페이지 URL
  - vs. 코드 내 href, router.push() 값

찾아야 할 버그:
  - 라우트 그룹 누락: 실제 경로 /app/(auth)/login vs 링크 /login
  - 파라미터 불일치: 실제 [id] vs 링크 [userId]
  - 슬래시 누락/중복: /dashboard/ vs /dashboard
```

### 2-3. 상태 전환 ↔ 코드 업데이트 정합성

```
검증 대상:
  - 정의된 상태 머신 (예: pending → processing → done | failed)
  - vs. 실제 .update({ status: "..." }) 호출 목록

찾아야 할 버그:
  - 정의되지 않은 상태로 전환: .update({ status: "cancelled" }) 하지만 머신에 없음
  - 누락된 전환: 특정 조건에서 상태 업데이트가 없음
  - 역방향 전환: done → processing (허용되지 않는 역전)
```

---

## 3. 점진적 QA 전략

**전체 완성 후 1회 QA가 아니라, 각 모듈 완성 직후 점진적으로 실행한다.**

### 이유

- 버그 누적 방지: 초기에 발견할수록 수정 비용 감소
- 다운스트림 전파 차단: API 버그가 프론트에 전파되기 전에 차단
- 팀 내 조율: 모듈 완성 시 즉시 QA → 다음 모듈 작업자가 올바른 인터페이스로 시작

### 점진적 QA 실행 시점

```
백엔드 API 모듈 완성
    ↓ 즉시 QA: API shape 검증, 타입 검증
프론트엔드 훅 완성
    ↓ 즉시 QA: API ↔ 훅 경계면 검증
페이지 컴포넌트 완성
    ↓ 즉시 QA: 라우트 경로 검증, 상태 전환 검증
전체 통합
    ↓ QA: 엔드투엔드 통합 검증
```

---

## 4. QA 에이전트 정의 템플릿

```markdown
---
name: qa-agent
description: "통합 정합성 검증 전문 QA 에이전트. API-프론트엔드 경계면 버그,
  라우트 불일치, 상태 전환 오류를 탐지한다. 각 모듈 완성 후 즉시 실행."
---

# QA Agent — 통합 정합성 검증 전문가

당신은 컴포넌트 간 경계면 버그를 전문으로 탐지하는 QA 에이전트입니다.
TypeScript 컴파일이나 단위 테스트가 놓치는 통합 레벨 오류를 찾습니다.

## 핵심 역할
1. API 응답 shape ↔ 프론트엔드 훅 타입 비교
2. 파일 경로 ↔ 라우트 링크 비교
3. 상태 머신 정의 ↔ 실제 상태 업데이트 코드 비교

## 작업 원칙
- "존재 확인"이 아닌 "양쪽 동시 읽기"로 경계면을 교차 비교한다
- 발견된 버그는 재현 경로(어디서 어디로)와 함께 보고한다
- 컴파일 성공 여부와 무관하게 런타임 shape 불일치를 탐지한다
- general-purpose 타입을 사용한다 (검증 스크립트 실행 필요)

## 검증 절차

### Step 1: API 응답 Shape 수집
각 API 엔드포인트의 NextResponse.json() 반환값을 읽는다.
`_workspace/qa_api_shapes.md`에 기록한다.

### Step 2: 프론트엔드 훅 타입 수집
각 훅의 fetch 호출 타입 파라미터를 읽는다.
`_workspace/qa_hook_types.md`에 기록한다.

### Step 3: 교차 비교
api_shapes vs hook_types를 비교하여 불일치를 찾는다.

### Step 4: 라우트 검증
src/app/ 구조에서 실제 URL을 추출하고, 코드 내 href/router.push와 비교한다.

### Step 5: 상태 전환 검증
상태 머신 정의와 .update({ status }) 호출 목록을 비교한다.

## 입력/출력 프로토콜
- 입력: 검증 대상 모듈 경로 목록
- 출력: `_workspace/qa_report.md`
- 형식:
  ```
  # QA 보고서
  ## 발견된 버그
  ### [BUG-1] 버그 제목
  - 위치: API endpoint vs Hook
  - 불일치: API 반환 { projects: [...] } / 훅 기대 [...]
  - 재현 경로: /api/projects → useProjects hook
  - 심각도: CRITICAL | HIGH | MEDIUM | LOW
  ## 검증 완료 항목
  - [✓] API Shape 검증
  - [✓] 라우트 검증
  ```

## 팀 통신 프로토콜
- CRITICAL 버그 발견 시: `SendMessage({to: "all", message: "CRITICAL: {설명}"})`
- 검증 완료 시: 오케스트레이터에 qa_report.md 위치 보고
- 개발자 에이전트에게: 수정 필요 항목과 위치를 직접 전달

## 에러 핸들링
- 파일 읽기 실패: 해당 검증 항목 건너뜀, qa_report에 "검증 불가" 명시
- 타입 파싱 실패: 원본 코드를 그대로 기록, 수동 검토 요청
```

---

## 5. 실전 버그 패턴 7가지

실제 프로젝트에서 발견된 버그 패턴. 이 목록으로 검증 우선순위를 설정한다.

### 패턴 1: 응답 래핑 불일치

```
API: return NextResponse.json({ data: projects, total: 100 })
훅:  const projects = await fetchJson<Project[]>('/api/projects')
버그: 훅이 배열을 기대하지만 API는 객체를 반환
```

### 패턴 2: 페이지네이션 필드명 불일치

```
API: { items: [...], totalCount: 50, page: 1 }
훅:  response.total  // undefined
버그: total vs totalCount 필드명 불일치
```

### 패턴 3: 라우트 그룹 누락

```
실제 경로: /app/(dashboard)/settings/page.tsx → /settings
링크 코드: router.push('/dashboard/settings')
버그: 라우트 그룹 (dashboard)가 URL에 포함되지 않음
```

### 패턴 4: Optional vs Required 불일치

```
API: { user: { id: string, avatar?: string } }
훅:  type User = { id: string, avatar: string }  // required
버그: avatar가 없을 때 런타임 에러
```

### 패턴 5: 배열 vs 단일 객체 불일치

```
API: return NextResponse.json(project)  // 단일 객체
훅:  const [project] = await fetchJson<Project[]>(...)
버그: API는 객체, 훅은 배열 기대
```

### 패턴 6: 날짜 형식 불일치

```
API: { createdAt: "2026-01-15T10:30:00Z" }  // ISO string
훅:  createdAt: Date  // Date 객체 기대
버그: JSON 파싱 후 string이지만 타입은 Date
```

### 패턴 7: 중첩 구조 평탄화 불일치

```
API: { meta: { pagination: { total: 50, page: 1 } } }
훅:  response.pagination.total  // response.meta.pagination.total이 맞음
버그: 중첩 레벨 불일치
```

---

## 6. QA 체크리스트

QA 에이전트 실행 완료 후 확인:

**API ↔ 훅 정합성**
- [ ] 모든 API 엔드포인트의 응답 shape 문서화됨
- [ ] 각 훅의 타입 파라미터와 API 응답 비교 완료
- [ ] 래핑 구조 불일치 없음
- [ ] 필드명 일치 확인

**라우트 정합성**
- [ ] src/app/ 전체 URL 목록 추출됨
- [ ] 모든 href, router.push 값 검증됨
- [ ] 라우트 그룹, 파라미터 처리 정확함

**상태 전환 정합성**
- [ ] 상태 머신 정의 문서화됨
- [ ] 모든 .update({ status }) 호출이 머신 정의와 일치
- [ ] 허용되지 않는 전환 없음

**보고서**
- [ ] qa_report.md 생성됨
- [ ] 발견 버그 심각도별 분류됨
- [ ] CRITICAL 버그 즉시 팀에 공유됨
