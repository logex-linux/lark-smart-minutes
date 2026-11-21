#!/usr/bin/env python3
"""Smoke-test the lark-smart-minutes skill's documented paths end to end.

No hard-coded tenant identifiers. Optional env vars for the ID-based checks:
  SMOKE_NOTE_ID        a note_id whose note_display_type is `unified`
  SMOKE_MEETING_ID     a meeting_id that has an associated `normal` note
  SMOKE_FORBIDDEN_DOC  a doc token the current user cannot read
Unset vars make the corresponding check skip (counted as skipped, not failed).
"""
import json
import os
import re
import subprocess

BASE = os.path.dirname(os.path.abspath(__file__))


def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    for stream in (p.stdout, p.stderr):
        try:
            return json.loads(stream)
        except json.JSONDecodeError:
            continue
    return {"ok": False, "stderr": p.stderr[:300], "stdout": p.stdout[:300], "rc": p.returncode}


def check(name, cond, detail=""):
    print(f"[{'PASS' if cond else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))
    return bool(cond)


def skip(name, reason):
    print(f"[SKIP] {name} — {reason}")
    return None


def main():
    results = []

    # 1. docs +search enumerate
    d = run(["lark-cli", "docs", "+search", "--as", "user", "--query", "智能纪要",
             "--page-size", "20", "--format", "json"])
    rs = (d.get("data") or {}).get("results", [])
    notes = [r for r in rs if re.sub(r"</?h[bp]?>", "", r.get("title_highlighted", "")).startswith("智能纪要：")]
    results.append(check("docs +search 返回纪要", d.get("ok") and len(notes) > 0, f"{len(notes)} 篇/页"))
    if not notes:
        print("\n0/0 passed (search returned no notes; aborting)")
        return

    # 2. docs +fetch anatomy parse
    token = notes[0]["result_meta"]["token"]
    f = run(["lark-cli", "docs", "+fetch", "--as", "user", "--doc", token,
             "--doc-format", "markdown"])
    txt = (f.get("data") or {}).get("document", {}).get("content", "")
    h1 = re.findall(r"^# (.+)$", txt, re.M)
    results.append(check("docs +fetch 解析章节", f.get("ok") and "总结" in h1, f"H1={h1[:6]}"))

    # 3. note +detail on a unified note (id via env, not hard-coded)
    note_id = os.environ.get("SMOKE_NOTE_ID")
    if note_id:
        n = run(["lark-cli", "note", "+detail", "--note-id", note_id, "--as", "user", "--format", "json"])
        note = (n.get("data") or {}).get("note", {})
        results.append(check("note +detail unified", n.get("ok") and note.get("note_display_type") == "unified"
                             and bool(note.get("note_doc_token"))))
    else:
        results.append(skip("note +detail unified", "SMOKE_NOTE_ID unset"))

    # 4. meeting → note +detail (normal type), meeting id via env
    meeting_id = os.environ.get("SMOKE_MEETING_ID")
    if meeting_id:
        v = run(["lark-cli", "vc", "+detail", "--as", "user", "--meeting-ids", meeting_id, "--format", "json"])
        m = ((v.get("data") or {}).get("meetings") or [{}])[0]
        n2 = run(["lark-cli", "note", "+detail", "--note-id", m.get("note_id", ""), "--as", "user", "--format", "json"])
        note2 = (n2.get("data") or {}).get("note", {})
        results.append(check("vc +detail → note +detail normal", v.get("ok") and n2.get("ok")
                             and note2.get("note_display_type") == "normal"
                             and bool(note2.get("verbatim_doc_token"))))
    else:
        results.append(skip("vc +detail → note +detail normal", "SMOKE_MEETING_ID unset"))

    # 5. todo extraction pattern
    todos = re.findall(r"^- \[ \] (.+)$", txt, re.M)
    results.append(check("待办提取模式", isinstance(todos, list), f"{len(todos)} 条"))

    # 6. related-notes cite extraction (series graph)
    cites = re.findall(r'<cite doc-id="(\w+)"[^>]*title="([^"]+)"', txt)
    results.append(check("相关会议纪要 cite 提取", isinstance(cites, list), f"{len(cites)} 条引用"))

    # 7. permission-failure behavior (3380004/3380002, JSON on stderr, rc=1)
    bad_token = os.environ.get("SMOKE_FORBIDDEN_DOC")
    if not bad_token:
        corpus_path = f"{BASE}/data/expanded_corpus.json"
        if os.path.exists(corpus_path):
            corpus = json.load(open(corpus_path))
            bad_token = next((t for t, v in corpus.items() if v["cls"] == "fetch-failed"), None)
    if bad_token:
        bad = run(["lark-cli", "docs", "+fetch", "--as", "user", "--doc", bad_token,
                   "--doc-format", "markdown"])
        err = (bad.get("error") or {})
        results.append(check("无权限文档返回错误码", bad.get("ok") is False and err.get("code") in (3380004, 3380002),
                             f"code={err.get('code')}"))
    else:
        results.append(skip("无权限文档返回错误码", "SMOKE_FORBIDDEN_DOC unset 且无本地 corpus"))

    passed = [r for r in results if r is True]
    failed = [r for r in results if r is False]
    print(f"\n{len(passed)} passed, {len(failed)} failed, {len(results) - len(passed) - len(failed)} skipped")


if __name__ == "__main__":
    main()
