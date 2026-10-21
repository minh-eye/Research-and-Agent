---
name: citation-verify
description: "BibTeX 참고문헌이 실제로 존재하는지 DOI·Crossref·Semantic Scholar로 대조하고, 본문 인용(\\cite)과 .bib 항목의 누락·미사용을 교차 점검하며, LLM이 지어낸 참고문헌 패턴(존재하지 않는 DOI, 미래 연도, 일반적 제목 등)을 찾아낸다. '참고문헌 검증', '인용 확인', '레퍼런스 진짜야?', 'bib 파일 점검', '가짜 인용 찾아줘', '투고 전 참고문헌 체크' 요청 시 반드시 이 스킬을 사용할 것. 원고 내용 심사는 review-panel 스킬을 쓴다."
---

# Citation Verify — 참고문헌 실재 검증

`.bib` 파일의 각 항목을 권위 있는 서지 데이터베이스와 대조해 실재 여부를 확인한다. LLM이 생성한 참고문헌은 상당 비율이 존재하지 않거나 서지사항이 틀리므로, AI 도움을 받아 쓴 원고는 투고 전에 반드시 한 번 돌린다.

출처: rev2agent `scripts/verify_citations_bibtex.py` (MIT, © 2026 Haebom Lee, https://github.com/dalbom/rev2agent). 원본 그대로 `scripts/`에 두었고 라이선스는 `scripts/LICENSE.rev2agent`.

## 절차

1. **입력 확인.** `.bib` 파일 경로와 원고 위치를 확인한다.
   - LaTeX 원고: `.tex` 파일이 있는 폴더를 `--tex-dir`로 넘긴다. 본문 `\cite` 키와 `.bib` 항목을 교차 점검한다
   - Word·한글 원고: 스크립트는 `.tex`만 읽는다. 빈 폴더를 `--tex-dir`로 넘기면 서지 검증만 수행되고 모든 항목이 "Orphan(미사용)"으로 표시되는데, 이는 정상이므로 무시하라고 사용자에게 알린다
   - `.bib`가 없고 참고문헌 목록만 있으면(Zotero·EndNote 내보내기 전) BibTeX로 내보내 달라고 요청한다. 직접 BibTeX를 만들어야 한다면 원문 목록에서 그대로 옮기고, 기억으로 빈 필드를 채우지 않는다

2. **실행.**
   ```bash
   python3 .claude/skills/citation-verify/scripts/verify_citations_bibtex.py \
     --bib {bib 경로} --tex-dir {tex 폴더} \
     --output _workspace/citations/report.txt \
     --cache _workspace/citations/cache.json
   ```
   - `--strict`: 의심·미검증 항목이 하나라도 있으면 실패 처리(투고 직전 권장)
   - `--mailto`: Crossref polite pool용 연락처. 사용자가 원할 때만 넣는다
   - `--no-s2`: Semantic Scholar 조회를 끈다(속도 제한에 걸릴 때)
   - 종료 코드: 0 통과, 1 실패, 2 통과했으나 의심 항목 있음

3. **결과 해석.** 보고서에서 다음을 사용자에게 요약한다:
   - **Suspicious(의심):** 지어낸 참고문헌일 가능성이 높다. 원문을 직접 찾아 확인하거나 삭제해야 한다
   - **Unverified(미검증):** 데이터베이스에서 찾지 못했다. 국내 학술지(KCI), 학위논문, 보고서, 표준 문서(ASHRAE, ISO, KS)는 Crossref에 없는 경우가 많으므로 가짜라는 뜻은 아니다. 출처 기관 사이트에서 직접 확인하라고 안내한다
   - **Missing from .bib:** 본문에서 인용했지만 `.bib`에 없는 키
   - **Orphan:** `.bib`에 있지만 본문에서 인용하지 않은 항목

4. **수정.** 서지사항을 고치는 것은 데이터베이스에서 확인된 값으로만 한다. 확인되지 않은 항목을 그럴듯하게 고쳐 넣지 않는다.

## 네트워크를 쓸 수 없을 때

스크립트는 `doi.org`, `api.crossref.org`, `api.semanticscholar.org`에 접속한다. 클라우드 세션의 네트워크 정책이 이 호스트들을 막으면 모든 항목이 "network error"로 Unverified가 된다. 이 경우:

- 결과를 "검증 실패"가 아니라 "검증 불가"로 보고하고, 막힌 호스트 이름을 사용자에게 알린다
- 대안으로 연결된 참고문헌 조회 도구(예: research-desk `verify_bibtex`)가 있으면 그것으로 대조한다
- 로컬 PC(Windows)에서는 `python scripts\verify_citations_bibtex.py ...`로 그대로 실행된다. 표준 라이브러리만 쓰므로 설치할 패키지가 없다

## 에러 핸들링

| 상황 | 대응 |
|------|------|
| `.bib` 파싱 오류 | 오류 줄 번호를 보고하고 해당 항목 형식 수정 제안 |
| 네트워크 오류 | 위 "네트워크를 쓸 수 없을 때" 절차 |
| 속도 제한(429) | `--cache`로 재실행하면 이미 확인한 항목은 건너뛴다 |

## 테스트 시나리오

**정상 흐름:** "paper/refs.bib 투고 전에 검증해줘" + `paper/*.tex` → 스크립트 실행 → Suspicious 0, Unverified 2(KCI 논문) → KCI 항목은 직접 확인 안내

**에러 흐름:** 네트워크 정책이 Crossref를 차단 → 전 항목 network error → "검증 불가"로 보고, 막힌 호스트 안내, 대안 도구 사용
