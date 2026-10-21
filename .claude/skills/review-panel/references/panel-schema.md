# panel.json 스키마

편집위원장이 Phase 3에서 작성하고 `scripts/build_dashboard.py`가 읽는 대시보드 데이터. 예시 파일: `assets/panel.example.json`.

```json
{
  "manuscript": "원고 제목",
  "venue": "대상 저널",
  "cycle": 1,
  "date": "YYYY-MM-DD",
  "preliminary": false,
  "reviewers": [
    {
      "id": "A",
      "persona": "방법론·통계",
      "status": "done",
      "score": "Major Revision",
      "summary": "Overall Assessment 한두 문장",
      "audit": {"1": "pass", "2": "fail", "3": "pass", "4": "pass", "5": "pass", "6": "pass"}
    }
  ],
  "issues": [
    {
      "id": "I1",
      "title": "한 줄 제목",
      "category": "correctness",
      "severity": "major",
      "raised_by": ["A", "C"],
      "pass2": false,
      "triage": "majority",
      "decision": "accept",
      "status": "open"
    }
  ],
  "claims": [
    {
      "claim": "핵심 주장",
      "challenge": "주장을 흔드는 근거",
      "resolution": "limitation_disclosed"
    }
  ]
}
```

## 필드 값

| 필드 | 허용 값 |
|------|--------|
| `reviewers[].status` | `done`, `missing` (missing이면 score·summary·audit 생략 가능) |
| `reviewers[].score` | `Accept`, `Minor Revision`, `Major Revision`, `Reject` |
| `reviewers[].audit` 값 | `pass`, `fail` (키는 구조 감사 항목 번호 "1"~"6") |
| `issues[].category` | `structure`, `correctness`, `comparison`, `clarity`, `cosmetic` |
| `issues[].severity` | `major`, `minor` |
| `issues[].raised_by` | 리뷰어 ID 목록. Pass 2 발견만이면 빈 목록 + `pass2: true` |
| `issues[].triage` | `consensus`, `majority`, `individual` |
| `issues[].decision` | `accept`, `partial`, `reject`, `pending` |
| `issues[].status` | `open`, `addressed` |
| `claims[].resolution` | `resolved_by_evidence`, `claim_narrowed`, `limitation_disclosed`, `research_redirected`, `claim_withdrawn`, `unresolved` |

`preliminary`는 성공한 리뷰어가 3명 미만이거나 독립 서브 에이전트를 쓰지 못했을 때 `true`.
