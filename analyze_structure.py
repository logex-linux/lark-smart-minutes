#!/usr/bin/env python3
"""Structural analysis of all fetched note docs."""
import os
import json
import re
from collections import Counter

BASE = os.path.dirname(os.path.abspath(__file__))


def clean_title(t):
    if not t:
        return None
    return re.sub(r"</?h[bp]?>", "", t).replace("&amp;", "&")


def main():
    search = json.load(open(f"{BASE}/data/search_all.json"))
    meta_by_token = {r["result_meta"]["token"]: r["result_meta"] for r in search["results"]}

    classes = Counter()
    h1_counter = Counter()
    rows = []
    for token, m in meta_by_token.items():
        try:
            txt = open(f"{BASE}/data/notes/{token}.md").read()
        except FileNotFoundError:
            continue
        title_m = re.search(r"<title>(.*?)</title>", txt, re.S)
        h1_first = re.search(r"^# (.+)$", txt, re.M)
        title = clean_title(title_m.group(1)) if title_m else (h1_first.group(1) if h1_first else "?")
        cls = "other"
        if title.startswith("智能纪要："):
            cls = "note"
        elif title.startswith("文字记录："):
            cls = "transcript"
        elif title.startswith("AI notes:"):
            cls = "note-en"
        classes[cls] += 1
        h1s = re.findall(r"^# (.+)$", txt, re.M)
        for h in h1s:
            h1_counter[h] += 1
        rows.append({
            "token": token,
            "cls": cls,
            "title": title.strip(),
            "owner": m.get("owner_name"),
            "cross": bool(m.get("is_cross_tenant")),
            "created": m.get("create_time_iso"),
            "h1": h1s,
            "has_vc_tab": "vc-transcribe-tab" in txt,
            "has_whiteboard": "<whiteboard" in txt,
            "minutes_url": re.findall(r"https://[\w.]+/minutes/(\w+)", txt),
            "transcript_links": re.findall(r"\]\((https://[\w.]+/docx/\w+)[^)]*\)", txt),
            "related_notes": re.findall(r'<cite doc-id="(\w+)"[^>]*title="([^"]+)"', txt),
            "shared_docs": re.findall(r'<cite doc-id="(\w+)"[^>]*file-type="(\w+)"[^>]*title="([^"]+)"', txt),
        })

    with open(f"{BASE}/data/structure.json", "w") as f:
        json.dump(rows, f, ensure_ascii=False, indent=1)

    print("classes:", dict(classes))
    print("\nH1 section frequency:")
    for h, c in h1_counter.most_common():
        print(f"  {c:3d}  {h}")
    print("\nvc-transcribe-tab present:", sum(r["has_vc_tab"] for r in rows))
    print("whiteboard cover present:", sum(r["has_whiteboard"] for r in rows))
    print("minutes url present:", sum(1 for r in rows if r["minutes_url"]))
    print("related-notes present:", sum(1 for r in rows if r["related_notes"]))
    print("\nPer-doc summary:")
    for r in rows:
        print(f"{r['cls']:10s} xt={int(r['cross'])} vc={int(r['has_vc_tab'])} wb={int(r['has_whiteboard'])} "
              f"min={len(r['minutes_url'])} rel={len(r['related_notes'])} | {r['title'][:46]}")


if __name__ == "__main__":
    main()
