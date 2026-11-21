# 读取智能纪要内容

目标：读取一篇或一批智能纪要的正文与关联产物。身份：全部命令 `--as user`。

## 取得文档 token

两种情况：

1. **已有 note_id**（来自 `vc +detail`、`minutes +detail` 或 unified 纪要正文的 `<vc-transcribe-tab vc-node-id>`）：

```bash
lark-cli note +detail --note-id <note_id> --as user
```

保留 `note_display_type`、`note_doc_token`、`verbatim_doc_token`。只有 Doc token 或 Docx URL 时不要猜 note_id，直接按 Doc 读取正文。

2. **只有 doc token / URL**（枚举产物）：直接 `docs +fetch`，不需要 `note +detail`。

## 读取纪要正文

```bash
lark-cli docs +fetch --doc <note_doc_token> --doc-format markdown --as user
```

返回 Markdown 的结构见 [note-doc-anatomy.md](../references/note-doc-anatomy.md)。按用户目标取用：

- 只要总结/待办/决策/金句 → 提取对应 `#` 章节。
- 需要参会人 → 头部 blockquote 的 `<cite type="user">` 列表。
- 只要名称或 URL → `drive metas batch_query`，不要读正文。

## 封面画板

正文第一个 `<whiteboard token="...">` 是纪要封面。用户需要封面图时：

```bash
lark-cli docs +media-download --type whiteboard --token <whiteboard_token> --output ./notes/<note_id>/cover --as user
```

没有 `<whiteboard>` 时跳过，不算失败；只下载第一个（封面），不要自动下载正文中的其他画板。

## 逐字稿

入口由 `note_display_type` 决定，不要只看 `verbatim_doc_token` 是否为空：

### normal（且有 verbatim_doc_token）

逐字稿是独立 Docx（标题「文字记录：…」）：

```bash
lark-cli docs +fetch --doc <verbatim_doc_token> --doc-format markdown --as user
```

行格式为 `@<说话人> HH:MM:SS` 或 `说话人 N HH:MM:SS`，下一行是发言内容；头部含指向主纪要的反链。

### unified

正文本身是 `<vc-tabs><vc-summary-tab>…</vc-summary-tab><vc-transcribe-tab vc-node-id="…"></vc-transcribe-tab></vc-tabs>`；逐字稿只能：

```bash
lark-cli note +transcript --note-id <note_id> --as user --output ./notes/<note_id>/unified_transcript.md
```

- 仅支持 `--as user`；`--transcript-format plain_text` 输出 `.txt`；默认路径 `./notes/{note_id}/unified_transcript.md`。
- CLI 自动翻页拼接；目标文件已存在时只有用户明确要求才加 `--overwrite`。
- 输出行格式 `@<说话人>  MM:SS`。

### unknown

停止并说明无法确定逐字稿入口，不要反复重试或猜成 unified。

## 智能章节深链

`# 智能章节` 的每条章节形如：

```markdown
[00:00](https://<tenant>/minutes/<minute_token>?t=0)  **章节标题**

> 本章节…
```

- 时间戳链接指向关联妙记的对应时间点（毫秒），可交给用户直接跳转。
- 提取 `minute_token` 后可作为 `vc +detail` / minutes 域命令的关联标识，但不要把 `minute_token` 传给 note 命令。

## 会中共享文档

`# 相关链接` 中的 `<cite doc-id file-type title>` 与 wiki 链接是会中共享文档：

- 只要名称/URL：`drive metas batch_query`（每批最多 10 个 token）。
- 要正文：逐个 `docs +fetch --doc <doc_token>`。
- 多个共享文档时先返回标题和 URL 让用户选择；某个无权限时保留 token 并逐项报告。

## 已知限制

- 「会议最佳表现成员」章节实体在 ISV 只读块内，`docs +fetch` 只返回空占位，读不到成员名单——向用户说明，建议在客户端查看。
- `<readonly-block type="isv">` 是 AI 生成区域的占位标记，无内容，解析时跳过。
- 跨租户副本可能只有一篇有权限；无权限时报告错误码（3380004/3380002）并继续处理其余文档。失败时 CLI 退出码为 1、错误 JSON 在 stderr，批量读取脚本需同时捕获两个输出流。
