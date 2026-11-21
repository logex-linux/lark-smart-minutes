#!/usr/bin/env python3
"""Fetch a batch of note docs as markdown and save raw JSON per token."""
import os
import json
import subprocess
import sys

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
        return {"ok": False, "raw": p.stdout[:500], "stderr": p.stderr[:500]}


def main():
    tokens = sys.argv[1:]
    for t in tokens:
        d = fetch(t)
        ok = d.get("ok")
        content = (d.get("data") or {}).get("document", {}).get("content", "")
        with open(f"{BASE}/data/notes/{t}.json", "w") as f:
            json.dump(d, f, ensure_ascii=False)
        with open(f"{BASE}/data/notes/{t}.md", "w") as f:
            f.write(content)
        print(f"{t}: ok={ok} chars={len(content)}")


if __name__ == "__main__":
    main()
