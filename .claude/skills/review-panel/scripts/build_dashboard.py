#!/usr/bin/env python3
"""
Review panel dashboard builder.

Reads a panel.json written by the review-panel orchestrator (schema in
references/panel-schema.md) and writes one self-contained HTML file: no
external scripts, fonts, or network access, so it opens in any browser.

Usage:
    python3 build_dashboard.py panel.json -o dashboard.html
    python3 build_dashboard.py cycle2/panel.json --history cycle1/panel.json -o dashboard.html

Requires only Python 3.8+ stdlib.
"""

import argparse
import json
import sys
from html import escape
from pathlib import Path

VERDICTS = ["Accept", "Minor Revision", "Major Revision", "Reject"]
# Verdicts are a state, so they wear the reserved status palette, always
# paired with an icon and a text label.
VERDICT_STYLE = {
    "Accept": ("good", "✓", "게재 가능"),
    "Minor Revision": ("warning", "!", "소폭 수정"),
    "Major Revision": ("serious", "‼", "대폭 수정"),
    "Reject": ("critical", "✕", "게재 불가"),
}
CATEGORIES = [
    ("structure", "구조"),
    ("correctness", "정확성·통계"),
    ("comparison", "비교·일반화"),
    ("clarity", "명료성"),
    ("cosmetic", "형식"),
]
TRIAGE = {"consensus": "합의", "majority": "다수", "individual": "개별"}
DECISION = {"accept": "반영", "partial": "부분 반영", "reject": "기각", "pending": "보류"}
RESOLUTION = {
    "resolved_by_evidence": ("good", "근거로 해소"),
    "claim_narrowed": ("good", "주장 범위 축소"),
    "limitation_disclosed": ("good", "한계로 명시"),
    "research_redirected": ("warning", "추가 조사 필요"),
    "claim_withdrawn": ("warning", "주장 철회"),
    "unresolved": ("critical", "미해결"),
}
AUDIT_ITEMS = ["결과-설정", "주장-근거", "내용 위치", "중복·모순", "표·그림", "초록-서론-결론"]
REVIEWER_IDS = ["A", "B", "C", "D", "E"]

CSS = """
:root {
  color-scheme: light;
  --page: #f9f9f7; --surface-1: #fcfcfb; --border: rgba(11,11,11,0.10);
  --text-primary: #0b0b0b; --text-secondary: #52514e; --text-muted: #898781;
  --grid: #e1e0d9; --baseline: #c3c2b7;
  --series-1: #2a78d6; --series-2: #eb6834;
  --good: #0ca30c; --warning: #fab219; --serious: #ec835a; --critical: #d03b3b;
  --cell-on: #2a78d6; --cell-off: #f0efec;
}
@media (prefers-color-scheme: dark) {
  :root:where(:not([data-theme="light"])) {
    color-scheme: dark;
    --page: #0d0d0d; --surface-1: #1a1a19; --border: rgba(255,255,255,0.10);
    --text-primary: #f0efec; --text-secondary: #c3c2b7; --text-muted: #898781;
    --grid: #2c2c2a; --baseline: #383835;
    --series-1: #3987e5; --series-2: #d95926;
    --cell-on: #3987e5; --cell-off: #2c2c2a;
  }
}
:root[data-theme="dark"] {
  color-scheme: dark;
  --page: #0d0d0d; --surface-1: #1a1a19; --border: rgba(255,255,255,0.10);
  --text-primary: #f0efec; --text-secondary: #c3c2b7; --text-muted: #898781;
  --grid: #2c2c2a; --baseline: #383835;
  --series-1: #3987e5; --series-2: #d95926;
  --cell-on: #3987e5; --cell-off: #2c2c2a;
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--page); color: var(--text-primary);
  font: 14px/1.5 system-ui, -apple-system, "Segoe UI", "Apple SD Gothic Neo", "Malgun Gothic", sans-serif; }
main { max-width: 1120px; margin: 0 auto; padding: 24px 16px 48px; }
header h1 { font-size: 20px; margin: 0 0 4px; }
header p { margin: 0; color: var(--text-secondary); }
.flag { display: inline-block; margin-left: 8px; padding: 1px 8px; border-radius: 999px;
  border: 1px solid var(--warning); color: var(--text-primary); font-size: 12px; }
section { margin-top: 28px; }
h2 { font-size: 15px; margin: 0 0 12px; }
.card { background: var(--surface-1); border: 1px solid var(--border); border-radius: 10px; padding: 16px; }
.tiles { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; }
.tile .label { color: var(--text-secondary); font-size: 12px; }
.tile .value { font-size: 28px; font-weight: 600; margin-top: 2px; }
.tile .sub { color: var(--text-muted); font-size: 12px; }
.reviewers { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px; }
.rev h3 { font-size: 14px; margin: 0; }
.rev .persona { color: var(--text-secondary); font-size: 12px; }
.rev p { margin: 10px 0; color: var(--text-secondary); font-size: 13px; }
.badge { display: inline-flex; align-items: center; gap: 6px; margin-top: 8px; font-size: 13px; font-weight: 600; }
.badge i { font-style: normal; display: inline-grid; place-items: center; width: 18px; height: 18px;
  border-radius: 50%; color: #0b0b0b; font-size: 11px; }
.s-good i { background: var(--good); } .s-warning i { background: var(--warning); }
.s-serious i { background: var(--serious); } .s-critical i { background: var(--critical); color: #fff; }
.s-missing i { background: var(--grid); color: var(--text-secondary); }
.audit { display: flex; flex-wrap: wrap; gap: 4px; margin-top: 8px; }
.audit span { font-size: 11px; padding: 1px 6px; border-radius: 4px; border: 1px solid var(--border); color: var(--text-secondary); }
.audit span.fail { border-color: var(--critical); color: var(--text-primary); }
.legend { display: flex; gap: 16px; font-size: 12px; color: var(--text-secondary); margin-bottom: 8px; }
.legend b { display: inline-block; width: 10px; height: 10px; border-radius: 2px; margin-right: 6px; vertical-align: -1px; }
.bars { display: grid; grid-template-columns: 96px 1fr 56px; gap: 8px 12px; align-items: center; }
.bars .name { color: var(--text-secondary); font-size: 13px; }
.bars .track { display: flex; gap: 2px; height: 14px; border-left: 1px solid var(--baseline); }
.bars .seg { height: 100%; }
.bars .seg:last-child { border-radius: 0 4px 4px 0; }
.bars .n { color: var(--text-secondary); font-size: 12px; font-variant-numeric: tabular-nums; }
.table-wrap { overflow-x: auto; }
table { border-collapse: collapse; width: 100%; font-size: 13px; }
th, td { text-align: left; padding: 8px 10px; border-bottom: 1px solid var(--grid); vertical-align: top; }
th { color: var(--text-secondary); font-weight: 600; font-size: 12px; white-space: nowrap; }
td.c { text-align: center; padding: 6px 4px; }
.dot { display: inline-block; width: 16px; height: 16px; border-radius: 4px; background: var(--cell-off); }
.dot.on { background: var(--cell-on); }
.muted { color: var(--text-muted); }
.pill { white-space: nowrap; }
.tip { position: fixed; pointer-events: none; z-index: 10; background: var(--surface-1); color: var(--text-primary);
  border: 1px solid var(--border); border-radius: 6px; padding: 6px 8px; font-size: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.15); display: none; max-width: 260px; }
footer { margin-top: 32px; color: var(--text-muted); font-size: 12px; }
"""

TIP_JS = """
(function () {
  var tip = document.getElementById('tip');
  document.addEventListener('mousemove', function (e) {
    var t = e.target.closest('[data-tip]');
    if (!t) { tip.style.display = 'none'; return; }
    tip.textContent = t.getAttribute('data-tip');
    tip.style.display = 'block';
    var x = Math.min(e.clientX + 12, window.innerWidth - tip.offsetWidth - 8);
    tip.style.left = x + 'px';
    tip.style.top = (e.clientY + 14) + 'px';
  });
})();
"""


def e(value):
    return escape(str(value if value is not None else ""))


def verdict_badge(reviewer):
    if reviewer.get("status") == "missing":
        return '<span class="badge s-missing"><i>–</i>누락</span>'
    score = reviewer.get("score")
    if score not in VERDICT_STYLE:
        return f'<span class="badge s-missing"><i>?</i>{e(score or "판정 없음")}</span>'
    status, icon, ko = VERDICT_STYLE[score]
    return f'<span class="badge s-{status}" title="{e(ko)}"><i>{icon}</i>{e(score)}</span>'


def status_badge(status, label):
    icon = {"good": "✓", "warning": "!", "critical": "✕"}[status]
    return f'<span class="badge s-{status} pill" style="margin:0"><i>{icon}</i>{e(label)}</span>'


def tiles(panel):
    done = [r for r in panel.get("reviewers", []) if r.get("status") != "missing"]
    issues = panel.get("issues", [])
    claims = panel.get("claims", [])
    counts = {v: sum(1 for r in done if r.get("score") == v) for v in VERDICTS}
    worst = next((v for v in reversed(VERDICTS) if counts[v]), None)
    dist = " · ".join(f"{VERDICT_STYLE[v][2]} {counts[v]}" for v in VERDICTS if counts[v])
    consensus_open = sum(1 for i in issues if i.get("triage") == "consensus" and i.get("status") != "addressed")
    open_issues = sum(1 for i in issues if i.get("status") != "addressed")
    unresolved = sum(1 for c in claims if c.get("resolution") == "unresolved")
    worst_html = verdict_badge({"score": worst}) if worst else '<span class="muted">—</span>'
    return f"""
<div class="tiles">
  <div class="card tile"><div class="label">가장 엄격한 판정</div><div class="value" style="font-size:16px">{worst_html}</div><div class="sub">{e(dist) or "판정 없음"}</div></div>
  <div class="card tile"><div class="label">미해결 합의 지적</div><div class="value">{consensus_open}</div><div class="sub">3명 이상 또는 Pass 2 발견</div></div>
  <div class="card tile"><div class="label">미해결 지적 / 전체</div><div class="value">{open_issues} <span class="muted" style="font-size:16px">/ {len(issues)}</span></div><div class="sub">해결 {len(issues) - open_issues}건</div></div>
  <div class="card tile"><div class="label">미해결 핵심 주장</div><div class="value">{unresolved}</div><div class="sub">{"투고 전 해소 필요" if unresolved else "모든 주장에 결론 있음"}</div></div>
</div>"""


def reviewer_cards(panel):
    by_id = {r.get("id"): r for r in panel.get("reviewers", [])}
    cards = []
    for rid in REVIEWER_IDS + [r for r in by_id if r not in REVIEWER_IDS]:
        r = by_id.get(rid)
        if r is None:
            continue
        audit = r.get("audit") or {}
        audit_html = "".join(
            f'<span class="{"fail" if audit.get(str(n)) == "fail" else ""}" data-tip="구조 감사 {n}. {e(name)}: {"Fail" if audit.get(str(n)) == "fail" else ("Pass" if audit.get(str(n)) == "pass" else "미기록")}">'
            f'{"✕" if audit.get(str(n)) == "fail" else "✓"} {e(name)}</span>'
            for n, name in enumerate(AUDIT_ITEMS, 1)
        ) if audit else ""
        cards.append(f"""
<div class="card rev">
  <h3>Reviewer {e(rid)}</h3><div class="persona">{e(r.get("persona"))}</div>
  {verdict_badge(r)}
  <p>{e(r.get("summary", ""))}</p>
  <div class="audit">{audit_html}</div>
</div>""")
    return f'<div class="reviewers">{"".join(cards)}</div>'


def category_bars(panel):
    issues = panel.get("issues", [])
    rows = []
    max_n = max([sum(1 for i in issues if i.get("category") == c) for c, _ in CATEGORIES] + [1])
    for key, label in CATEGORIES:
        cat = [i for i in issues if i.get("category") == key]
        n_open = sum(1 for i in cat if i.get("status") != "addressed")
        n_done = len(cat) - n_open
        segs = ""
        if n_open:
            segs += f'<div class="seg" style="width:{n_open / max_n * 100:.1f}%;background:var(--series-1)" data-tip="{e(label)} · 미해결 {n_open}건"></div>'
        if n_done:
            segs += f'<div class="seg" style="width:{n_done / max_n * 100:.1f}%;background:var(--series-2)" data-tip="{e(label)} · 해결 {n_done}건"></div>'
        rows.append(f'<div class="name">{e(label)}</div><div class="track">{segs}</div><div class="n">{n_open} / {len(cat)}</div>')
    return f"""
<div class="card">
  <div class="legend"><span><b style="background:var(--series-1)"></b>미해결</span><span><b style="background:var(--series-2)"></b>해결</span><span class="muted">오른쪽 숫자: 미해결 / 전체</span></div>
  <div class="bars">{"".join(rows)}</div>
</div>"""


def issue_matrix(panel):
    issues = panel.get("issues", [])
    tri_rank = {"consensus": 0, "majority": 1, "individual": 2}
    cat_rank = {"structure": 0, "correctness": 0, "comparison": 1, "clarity": 2, "cosmetic": 3}
    ordered = sorted(issues, key=lambda i: (i.get("status") == "addressed", tri_rank.get(i.get("triage"), 3),
                                            cat_rank.get(i.get("category"), 4)))
    cat_label = dict(CATEGORIES)
    head = "".join(f"<th class='c'>{r}</th>" for r in REVIEWER_IDS) + "<th class='c'>P2</th>"
    body = []
    for i in ordered:
        raised = set(i.get("raised_by") or [])
        cells = "".join(
            f'<td class="c"><span class="dot{" on" if r in raised else ""}" data-tip="Reviewer {r}: {"지적함" if r in raised else "지적 안 함"}"></span></td>'
            for r in REVIEWER_IDS
        )
        cells += f'<td class="c"><span class="dot{" on" if i.get("pass2") else ""}" data-tip="Pass 2: {"발견" if i.get("pass2") else "해당 없음"}"></span></td>'
        done = i.get("status") == "addressed"
        body.append(
            f"<tr><td class='muted'>{e(i.get('id'))}</td>"
            f"<td>{e(i.get('title'))}<div class='muted' style='font-size:12px'>{e(cat_label.get(i.get('category'), i.get('category')))} · {'Major' if i.get('severity') == 'major' else 'Minor'}</div></td>"
            f"{cells}<td class='pill'>{e(TRIAGE.get(i.get('triage'), i.get('triage')))}</td>"
            f"<td class='pill'>{e(DECISION.get(i.get('decision'), i.get('decision')))}</td>"
            f"<td class='pill'>{status_badge('good', '해결') if done else '<span class=muted>미해결</span>'}</td></tr>"
        )
    if not body:
        body.append(f"<tr><td colspan='{len(REVIEWER_IDS) + 6}' class='muted'>기록된 지적 없음</td></tr>")
    return f"""
<div class="card table-wrap">
  <div class="legend"><span><b style="background:var(--cell-on)"></b>해당 리뷰어가 지적</span><span>P2 = 편집위원장 섹션별 점검(Pass 2) 발견</span></div>
  <table><thead><tr><th>ID</th><th>지적</th>{head}<th>분류</th><th>조치</th><th>상태</th></tr></thead>
  <tbody>{"".join(body)}</tbody></table>
</div>"""


def claim_ledger(panel):
    rows = []
    for c in panel.get("claims", []):
        status, label = RESOLUTION.get(c.get("resolution"), ("warning", c.get("resolution") or "미기록"))
        rows.append(f"<tr><td>{e(c.get('claim'))}</td><td class='muted'>{e(c.get('challenge'))}</td><td>{status_badge(status, label)}</td></tr>")
    if not rows:
        rows.append("<tr><td colspan='3' class='muted'>기록된 주장 없음</td></tr>")
    return f"""
<div class="card table-wrap">
  <table><thead><tr><th>핵심 주장</th><th>도전 근거</th><th>결론</th></tr></thead>
  <tbody>{"".join(rows)}</tbody></table>
</div>"""


def history_table(panels):
    head = "".join(f"<th>Reviewer {r}</th>" for r in REVIEWER_IDS)
    rows = []
    for p in panels:
        by_id = {r.get("id"): r for r in p.get("reviewers", [])}
        cells = "".join(f"<td>{verdict_badge(by_id[r]) if r in by_id else '<span class=muted>—</span>'}</td>" for r in REVIEWER_IDS)
        rows.append(f"<tr><td class='pill'>Cycle {e(p.get('cycle'))}<div class='muted' style='font-size:12px'>{e(p.get('date'))}</div></td>{cells}</tr>")
    return f"""
<div class="card table-wrap">
  <table><thead><tr><th>사이클</th>{head}</tr></thead><tbody>{"".join(rows)}</tbody></table>
</div>"""


def build(panel, history):
    title = panel.get("manuscript") or "원고"
    flag = '<span class="flag">예비 결과 — 독립 리뷰어 3명 미만</span>' if panel.get("preliminary") else ""
    sections = [
        f"<section><h2>요약</h2>{tiles(panel)}</section>",
        f"<section><h2>리뷰어별 판정</h2>{reviewer_cards(panel)}</section>",
        f"<section><h2>범주별 지적</h2>{category_bars(panel)}</section>",
        f"<section><h2>지적 × 리뷰어</h2>{issue_matrix(panel)}</section>",
        f"<section><h2>주장 도전 원장</h2>{claim_ledger(panel)}</section>",
    ]
    if history:
        cycles = sorted(history + [panel], key=lambda p: p.get("cycle") or 0)
        sections.append(f"<section><h2>사이클별 판정 추이</h2>{history_table(cycles)}</section>")
    return f"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Review Panel Dashboard</title><style>{CSS}</style></head>
<body><main>
<header><h1>{e(title)}</h1><p>{e(panel.get("venue") or "대상 저널 미지정")} · Cycle {e(panel.get("cycle"))} · {e(panel.get("date"))}{flag}</p></header>
{"".join(sections)}
<footer>review-panel 스킬로 생성 · 판정과 지적은 AI 심사위원의 의견이며 실제 심사 결과가 아닙니다.</footer>
</main><div class="tip" id="tip"></div><script>{TIP_JS}</script></body></html>
"""


def load(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: cannot read {path}: {exc}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Build the review panel HTML dashboard from panel.json")
    parser.add_argument("panel", help="Path to the current cycle's panel.json")
    parser.add_argument("--history", nargs="*", default=[], help="panel.json files from earlier cycles")
    parser.add_argument("-o", "--output", default="dashboard.html", help="Output HTML path")
    args = parser.parse_args()

    panel = load(args.panel)
    history = [load(p) for p in args.history]
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(build(panel, history), encoding="utf-8")
    print(f"Dashboard written: {out}")


if __name__ == "__main__":
    main()
