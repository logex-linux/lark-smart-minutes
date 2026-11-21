#!/usr/bin/env python3
"""Fetch all DOCX results from search_all.json as markdown."""
import os
import json
import subprocess

BASE = os.path.dirname(os.path.abspath(__file__))


def fetch(token):
    cmd = [
        "lark-cli", "docs", "+fetch", "--as", "user",
        "--doc", token, "--doc-format", "markdown",
    ]
    p = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return json.loads(p.stdout)
    except json.JSONDecodeError:
        return {"ok": False, "raw": p.stdout[:300], "stderr": p.stderr[:300]}


def main():
    d = json.load(open(f"{BASE}/data/search_all.json"))
    results = d["results"]
    ok, fail = 0, 0
    for r in results:
        m = r.get("result_meta", {})
        if m.get("doc_types") != "DOCX":
            print(f"skip non-docx: {m.get('token')} ({m.get('doc_types')})")
            continue
        t = m["token"]
        res = fetch(t)
        is_ok = res.get("ok")
        content = (res.get("data") or {}).get("document", {}).get("content", "")
        with open(f"{BASE}/data/notes/{t}.json", "w") as f:
            json.dump(res, f, ensure_ascii=False)
        with open(f"{BASE}/data/notes/{t}.md", "w") as f:
            f.write(content)
        if is_ok:
            ok += 1
        else:
            fail += 1
        print(f"{t}: ok={is_ok} chars={len(content)}")
    print(f"DONE ok={ok} fail={fail}")


if __name__ == "__main__":
    main()
