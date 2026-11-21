#!/usr/bin/env python3
"""Collect all meetings via vc +search (participant=me), then vc +detail for note_id/minute_token."""
import json
import os
import subprocess

BASE = os.path.dirname(os.path.abspath(__file__))


def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return json.loads(p.stdout)
    except json.JSONDecodeError:
        return {"ok": False, "raw": p.stdout[:400], "stderr": p.stderr[:400]}


def me_open_id():
    """Current user's open_id from `lark-cli whoami` (no hard-coded identity)."""
    d = run(["lark-cli", "whoami"])
    me = ((d.get("onBehalfOf") or {}).get("openId"))
    if not me:
        raise SystemExit("cannot resolve current user open_id from `lark-cli whoami`; run `lark-cli auth login` first")
    return me


def search_all(me):
    ids, token, page = [], None, 0
    while True:
        page += 1
        cmd = ["lark-cli", "vc", "+search", "--as", "user",
               "--participant-ids", me, "--start", "2024-01-01",
               "--page-size", "30", "--format", "json"]
        if token:
            cmd += ["--page-token", token]
        d = run(cmd)
        data = d.get("data") or {}
        items = data.get("items", [])
        ids.extend(i["id"] for i in items)
        print(f"search page {page}: +{len(items)} (total {len(ids)})")
        if not data.get("has_more"):
            break
        token = data.get("page_token")
        if not token or page > 30:
            break
    return ids


def main():
    meeting_ids = search_all(me_open_id())
    with open(f"{BASE}/data/meeting_ids.json", "w") as f:
        json.dump(meeting_ids, f)
    details = []
    for i in range(0, len(meeting_ids), 20):
        batch = meeting_ids[i:i + 20]
        d = run(["lark-cli", "vc", "+detail", "--as", "user",
                 "--meeting-ids", ",".join(batch), "--format", "json"])
        for m in (d.get("data") or {}).get("meetings", []):
            details.append(m)
    with open(f"{BASE}/data/meeting_details.json", "w") as f:
        json.dump(details, f, ensure_ascii=False, indent=1)
    with_note = [m for m in details if m.get("note_id")]
    with_min = [m for m in details if m.get("minute_token")]
    print(f"meetings={len(details)} with_note={len(with_note)} with_minute={len(with_min)}")
    for m in details:
        print(f"  {m['meeting_id']} note={m.get('note_id','-'):>20} min={m.get('minute_token','-'):26s} {m.get('topic','')[:30]}")


if __name__ == "__main__":
    main()
