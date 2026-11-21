#!/usr/bin/env python3
"""BFS expansion: fetch note docs linked from 相关会议纪要 sections, up to N rounds."""
import os
import json
import re
import subprocess

BASE = os.path.dirname(os.path.abspath(__file__))
MAX_ROUNDS = 3
MAX_DOCS = 220


def fetch(token):
    cmd = ["lark-cli", "docs", "+fetch", "--as", "user",
           "--doc", token, "--doc-format", "markdown"]
    p = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return json.loads(p.stdout)
    except json.JSONDecodeError:
        return {"ok": False, "raw": p.stdout[:200]}


def title_of(txt):
    m = re.search(r"<title>(.*?)</title>", txt, re.S)
    if m:
        return re.sub(r"</?h[bp]?>", "", m.group(1)).replace("&amp;", "&").strip()
    m = re.search(r"^# (.+)$", txt, re.M)
    return m.group(1).strip() if m else None


def main():
    rows = json.load(open(f"{BASE}/data/structure.json"))
    known = {r["token"] for r in rows}
    frontier = set()
    for r in rows:
        for tok, _t in r["related_notes"]:
            if tok not in known:
                frontier.add(tok)
    print("round 0 frontier:", len(frontier))

    corpus = {}  # token -> {title, cls, related:[...]}
    total_new = 0
    for rnd in range(1, MAX_ROUNDS + 1):
        batch = [t for t in sorted(frontier) if t not in corpus and total_new < MAX_DOCS]
        if not batch:
            break
        new_frontier = set()
        for t in batch:
            if total_new >= MAX_DOCS:
                print("MAX_DOCS reached, stopping expansion")
                break
            d = fetch(t)
            content = (d.get("data") or {}).get("document", {}).get("content", "")
            if not content:
                corpus[t] = {"title": None, "cls": "fetch-failed", "related": []}
                total_new += 1
                continue
            title = title_of(content)
            cls = "note" if (title or "").startswith("智能纪要：") else \
                  "note-en" if (title or "").startswith("AI notes:") else \
                  "transcript" if (title or "").startswith("文字记录：") else "other"
            rel = re.findall(r'<cite doc-id="(\w+)"[^>]*title="([^"]+)"', content)
            corpus[t] = {"title": title, "cls": cls, "related": rel}
            total_new += 1
            for tok, _ in rel:
                if tok not in known and tok not in corpus:
                    new_frontier.add(tok)
        print(f"round {rnd}: fetched {len(batch)}, new frontier {len(new_frontier)}, corpus {len(corpus)}")
        frontier = new_frontier

    with open(f"{BASE}/data/expanded_corpus.json", "w") as f:
        json.dump(corpus, f, ensure_ascii=False, indent=1)
    from collections import Counter
    print("class distribution:", Counter(v["cls"] for v in corpus.values()))


if __name__ == "__main__":
    main()
