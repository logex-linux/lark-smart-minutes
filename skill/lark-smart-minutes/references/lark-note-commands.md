# note +detail / note +transcript

Note 域只有这两个命令；契约与 [lark-meeting 的 note +detail](../../lark-meeting/references/lark-note-detail.md) 一致，此处只列本技能常用要点。

## note +detail

```bash
lark-cli note +detail --note-id <note_id> --as user
```

返回 `data.note`：

| 字段 | 含义 |
|---|---|
| `note_id` | Note 标识 |
| `note_display_type` | `normal` / `unified` / `unknown`，决定逐字稿入口 |
| `note_doc_token` | 纪要正文 Docx token |
| `verbatim_doc_token` | normal 类型的独立逐字稿 Doc token；unified 时为空 |

- 支持 `--as user` / `--as bot`；本技能统一 `--as user`。
- `note_id` 来源：`vc +detail`、`minutes +detail`、unified 纪要正文 `<vc-transcribe-tab vc-node-id>`。不要从 Doc token、URL、标题反推。

## note +transcript

```bash
lark-cli note +transcript --note-id <note_id> --as user --output ./notes/<note_id>/unified_transcript.md
```

- 仅 `note_display_type=unified` 时使用；仅支持 `--as user`。
- 自动翻页拼接完整内容；默认输出 `./notes/{note_id}/unified_transcript.md`，`--transcript-format plain_text` 输出 `.txt`。
- 目标文件已存在时失败，仅用户明确要求才加 `--overwrite`。
- normal 类型的逐字稿不要用它：读 `verbatim_doc_token` 对应 Docx。

## 相关场景

- [读取智能纪要内容](../scenes/read-note-content.md)
