#!/usr/bin/env python3
"""
Package one review cycle into a bundle the Review Panel web dashboard can import.

Reads the files the review-panel skill writes into a cycle folder
(reviewer_A.md ... reviewer_E.md, panel.json, and optionally synthesis.md and
response.md) and writes one JSON file: the reviewers' comments parsed into
structured items, the panel data, and the two documents as Markdown.

Usage:
    python3 export_bundle.py _workspace/review/cycle1 -o bundle.json

Requires only Python 3.8+ stdlib.
"""

import argparse
import json
import re
import sys
from pathlib import Path

REVIEWER_IDS = ["A", "B", "C", "D", "E"]
SECTION_RE = re.compile(r"^## (.+?)\s*$", re.M)
ITEM_RE = re.compile(r"^\d+\.\s+\*\*\[(\w+)\]\s*(.+?)\*\*\s*[—-]\s*(.*)$")
RESPONSE_RE = re.compile(r"\*\*Comment ([A-E])(\d+)\..*?\*\*\s*_\(종합 (I\d+)\)_")


def sections(md):
    """Split a review file into {heading: body}."""
    parts = SECTION_RE.split(md)
    return {parts[i].strip(): parts[i + 1].strip() for i in range(1, len(parts) - 1, 2)}


def parse_items(body):
    items = []
    for line in body.splitlines():
        m = ITEM_RE.match(line.strip())
        if m:
            items.append({"category": m.group(1), "title": m.group(2).strip(), "problem": m.group(3).strip()})
        elif items and line.strip() and not re.match(r"^\d+\.", line.strip()):
            items[-1]["problem"] += "\n" + line.strip()
    return items


def parse_audit(body):
    audit = []
    for line in body.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 3 and cells[0].isdigit():
            audit.append({"item": int(cells[0]), "result": "fail" if cells[2].lower().startswith("fail") else "pass",
                          "note": cells[3] if len(cells) > 3 else ""})
    return audit


def parse_score(body):
    first = body.strip().splitlines()[0] if body.strip() else ""
    for v in ["Major Revision", "Minor Revision", "Accept", "Reject"]:
        if first.startswith(v):
            return v, first[len(v):].lstrip(" —-:").strip()
    return first, ""


def parse_review(path):
    sec = sections(path.read_text(encoding="utf-8"))
    score, reason = parse_score(sec.get("Score", ""))
    suggestions = [l.lstrip("-* ").strip() for l in sec.get("Specific Suggestions", "").splitlines() if l.strip()]
    return {
        "overall": sec.get("Overall Assessment", ""),
        "audit": parse_audit(sec.get("Structural Audit", "")),
        "major": parse_items(sec.get("Major Issues", "")),
        "minor": parse_items(sec.get("Minor Issues", "")),
        "suggestions": suggestions,
        "score": score,
        "score_reason": reason,
    }


def main():
    ap = argparse.ArgumentParser(description="Package a review cycle folder for the dashboard")
    ap.add_argument("cycle_dir")
    ap.add_argument("-o", "--output", default="bundle.json")
    args = ap.parse_args()
    d = Path(args.cycle_dir)
    panel_path = d / "panel.json"
    if not panel_path.exists():
        sys.exit(f"ERROR: {panel_path} not found")
    panel = json.loads(panel_path.read_text(encoding="utf-8"))

    reviewers = {}
    for rid in REVIEWER_IDS:
        p = d / f"reviewer_{rid}.md"
        persona = next((r.get("persona") for r in panel.get("reviewers", []) if r.get("id") == rid), "")
        if p.exists():
            reviewers[rid] = {"status": "done", "persona": persona, "review": parse_review(p)}
        else:
            reviewers[rid] = {"status": "missing", "persona": persona}

    # Link each reviewer's major comments to the synthesis issue that answers it,
    # using the "Comment A3 ... (종합 I4)" headings the response draft carries.
    refs = {}
    response_md = (d / "response.md").read_text(encoding="utf-8") if (d / "response.md").exists() else ""
    for rid, n, iid in RESPONSE_RE.findall(response_md):
        refs.setdefault(iid, []).append(f"{rid}{n}")
    # The synthesis report's action tables carry each issue's concrete fix (last column).
    synthesis_md = (d / "synthesis.md").read_text(encoding="utf-8") if (d / "synthesis.md").exists() else ""
    actions = {}
    for line in synthesis_md.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 5 and re.fullmatch(r"I\d+", cells[0]):
            actions[cells[0]] = cells[-1]
    summary = ""
    m = re.search(r"\*\*편집위원장 판정:[^\n]*", synthesis_md)
    if m:
        summary = re.sub(r"\*\*", "", m.group(0)).split(":", 1)[1].strip()
    issues = []
    for i in panel.get("issues", []):
        i = dict(i)
        i["refs"] = refs.get(i["id"], [])
        i.setdefault("action", actions.get(i["id"], ""))
        issues.append(i)

    record = {
        "id": "imp_" + re.sub(r"\W+", "", d.name) + "_" + str(panel.get("date", "")).replace("-", ""),
        "createdAt": panel.get("date"),
        "title": panel.get("manuscript", "원고"),
        "journal": panel.get("venue", ""),
        "field": "",
        "notes": "",
        "cycle": panel.get("cycle", 1),
        "parentId": None,
        "status": "done",
        "source": "local-skill",
        "reviewers": reviewers,
        "synthesis": {
            "verdict": "Major Revision" if any(r.get("score") == "Major Revision" for r in panel.get("reviewers", [])) else "",
            "summary": summary,
            "issues": issues,
            "claims": panel.get("claims", []),
            "preliminary": panel.get("preliminary", False),
        },
        "docs": {
            "synthesis_md": synthesis_md,
            "response_md": response_md,
        },
    }
    out = Path(args.output)
    out.write_text(json.dumps({"format": "review-panel-bundle@1", "record": record}, ensure_ascii=False), encoding="utf-8")
    counts = {rid: len(r.get("review", {}).get("major", [])) for rid, r in reviewers.items()}
    print(f"Bundle written: {out}  (major comments per reviewer: {counts}, issues: {len(issues)})")


if __name__ == "__main__":
    main()
