# Research-and-Agent

## 하네스: 에이전트 팀 & 스킬 자동 생성 시스템

**목표:** 도메인 설명 한 문장을 에이전트 팀과 스킬 세트로 자동 변환한다.

**트리거:** "하네스 구성해줘", "에이전트 팀 설계해줘", "스킬 만들어줘", "하네스 점검", "하네스 감사" 등 하네스 관련 요청 시 `harness` 스킬을 사용하라. 단순 질문은 직접 응답 가능.

## 하네스: 원고 심사 패널 (건축환경·사회과학 방법론)

**목표:** 투고 전 원고를 5명의 독립 AI 심사위원이 평가하고 편집위원장이 종합해, 조치 계획·답변서·대시보드를 만든다. 연구 도중 결정은 major revision 패널로 토론한다.

**트리거:** 원고 리뷰·심사·재심사, "major revision", 리뷰 대시보드 요청 시 `review-panel` 스킬을 사용하라. 참고문헌 실재 검증은 `citation-verify` 스킬을 사용하라. 단순 질문은 직접 응답 가능.

## 프로젝트 구조

```
.claude/
├── skills/
│   └── harness/          ← 하네스 메타 스킬
│       ├── SKILL.md
│       └── references/   ← 패턴, 템플릿, 가이드
├── agents/               ← 하네스가 생성한 에이전트 정의 파일
└── settings.json         ← (필요 시 생성)
_workspace/               ← 에이전트 팀 중간 산출물 저장소
```

## Windows 환경 참고사항

- 경로 구분자: Claude Code는 Windows에서 `/`와 `\` 모두 지원
- 전역 스킬 설치 경로: `%APPDATA%\Claude\skills\harness\`
- PowerShell에서 명령 실행 시 `\` 사용 권장

## 변경 이력

| 날짜 | 변경 내용 | 대상 | 사유 |
|------|---------|------|------|
| 2026-06-19 | 초기 구성 | 전체 | revfactory/harness v1.2.0 기반 설치 |
| 2026-10-21 | 원고 심사 패널 추가 (리뷰어 에이전트 5종, review-panel, citation-verify, 대시보드 스크립트) | `.claude/agents/review-*`, `.claude/skills/review-panel`, `.claude/skills/citation-verify` | dalbom/rev2agent(MIT)의 리뷰 패널·인용 검증을 건축환경 연구용으로 이식 |
