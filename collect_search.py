#!/usr/bin/env python3
"""Collect all pages of `docs +search` for the query 智能纪要 into one JSON."""
import os
import json
import subprocess
import sys

QUERY = "智能纪要"
BASE = os.path.dirname(os.path.abspath(__file__))


def run_search(page_token=None):
    cmd = [
        "lark-cli", "docs", "+search", "--as", "user",
        "--query", QUERY, "--page-size", "20", "--format", "json",
    ]
    if page_token:
        cmd += ["--page-token", page_token]
    out = subprocess.run(cmd, capture_output=True, text=True).stdout
    return json.loads(out)


def main():
    token = None
    all_results = []
    page = 0
    while True:
        page += 1
        d = run_search(token)
        data = d["data"]
        results = data.get("results", [])
        all_results.extend(results)
        print(f"page {page}: +{len(results)} (total {len(all_results)})")
        if not data.get("has_more"):
            break
        token = data.get("page_token")
        if not token:
            break
        if page > 20:
            print("safety stop after 20 pages")
            break
    out = {"query": QUERY, "total_collected": len(all_results), "results": all_results}
    with open(f"{BASE}/data/search_all.json", "w") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("saved", len(all_results), "results")


if __name__ == "__main__":
    main()
