# 智能纪要文档解剖（note-doc-anatomy）

`docs +fetch --doc-format markdown` 返回的智能纪要正文结构。基于 44 篇真实纪要的统计；章节以实际返回为准。

## 标题规范

| 模式 | 示例（已脱敏） | 说明 |
|---|---|---|
| `智能纪要：<主题> <YYYY年M月D日>` | `智能纪要：某项目落地对齐会 2026年9月18日` | 标准型（43/44） |
| `智能纪要：MM-DD \| 【循环会】<主题>` | `智能纪要：09-18 \| 【循环会】某项目（2917） 2026年9月18日` | 循环会，标题前缀带期号日期 |
| `智能纪要：<主题>`（无日期） | `智能纪要：某对外沟通会` | 偶发 |
| `AI notes: <topic> on <Mon D, YYYY>` | `AI notes: 11-14 \| 某项目 Daily on Nov 14, 2026` | 英文会话 |

## 固定骨架

```markdown
<title>智能纪要：<主题> <日期></title>

<blockquote><p>会议主题：…</p><p>会议时间：2026年9月18日（周五） 10:32 - 10:49 （GMT+08）</p><p>参会人：<cite type="user" user-id="ou_…" user-name="…"></cite>…</p></blockquote>

> 智能会议纪要由 AI 生成，可能不准确，请谨慎甄别后使用

# 总结

<whiteboard token="…"></whiteboard>

<总起段>

- **<主题一>**
  - **<子项>**：<结论>…
  <grid><column width-ratio="0.55">…</column><column width-ratio="0.45">![图注](https://feishu.cn/file/…)</column></grid>

<readonly-block type="isv"></readonly-block>

# 待办

- [ ] <事项名>：<描述>（来自<提出人>） <cite type="user" user-id="…" user-name="<负责人>"></cite>

<readonly-block type="isv"></readonly-block>

# 相关链接

- 会中共享的文档：<cite doc-id="…" file-type="docx" title="…" type="doc"></cite> 或 [标题](https://<tenant>/wiki/<token>?from=vcFollow)
- 妙记：[标题](https://<tenant>/minutes/<minute_token>?from=ai_minutes)
- 文字记录
  - [标题](https://<tenant>/docx/<verbatim_doc_token>)
```

## 章节频率（44 篇样本）

| 章节 | 出现率 | 内容形态 |
|---|---|---|
| `# 总结` | 100% | 封面画板 + 总起 + 层级 bullet；`<grid>/<column>` 双栏、图片 `feishu.cn/file/...` |
| `# 待办` | 95% | `- [ ]` 复选框 + 负责人 cite + 「（来自X）」提出人 |
| `# 相关链接` | 95% | 共享文档 cite/wiki 链接、妙记链接、文字记录链接 |
| `# 会议中的金句时刻` / `# 金句时刻` | 52% | `「引文」` + `—— 点评` |
| `# 会议最佳表现成员` | 41% | 实体在 ISV 只读块内，fetch 只得空占位 |
| `# 相关会议纪要` | 27% | `<callout emoji="📌">` 内同系列纪要 cite 列表 |
| `# 关键决策` | 18% | 问题/讨论方案/决策依据 + `---` 后「其他决策」编号列表 |
| `# 智能章节` | 14% | `[MM:SS](minutes_url?t=ms)` + `**标题**` + `> 本章节…` |

## 关键决策章节样例

```markdown
# 关键决策

- **关键决策**：<一句话结论>

  - **问题**：…
  - **讨论方案**：
    - <说话人/角色> 提出 …
  - **决策依据**：…

---

- **其他决策**：
  1. …
```

## unified 类型差异

整篇是 tab 容器，章节在 `vc-summary-tab` 内：

```markdown
<vc-tabs><vc-summary-tab><h1>总结</h1>…<h1>待办</h1>…</vc-summary-tab><vc-transcribe-tab vc-node-id="<note_id>"></vc-transcribe-tab></vc-tabs>
```

- `note +detail` 返回 `note_display_type=unified`、`verbatim_doc_token` 为空。
- 逐字稿用 `note +transcript`，输出 `@<说话人>  MM:SS` 行。
- `<vc-transcribe-tab vc-node-id>` 是该 note 的权威 note_id 来源之一。

## 文字记录（逐字稿）文档

```markdown
# 文字记录：<主题> <日期>

> 会议主题：…
> 会议时间：…
> 智能纪要：[<主题> <日期>](https://<tenant>/docx/<note_doc_token>)

@<说话人> 00:04:35
<发言内容>
```

- 说话人行两种格式：`@<姓名> HH:MM:SS` 与 `说话人 N HH:MM:SS`。
- 标题可能带前导空格（`文字记录： 阶跃星辰…`），归一化时 trim。

## 解析注意

- `<readonly-block type="isv">` 是 AI 生成区域占位符，无内容；「会议最佳表现成员」实体在其中，fetch 不可得。
- 图片是 `https://feishu.cn/file/<token>` 外链；正文中的 cite 分三类：`type="user"`（参会人/负责人）、`type="doc"`（共享文档/相关纪要）、`doc-id + file-type="docx"`（文档 token）。
- 时间均为 GMT+08；章节时间戳深链的 `?t=` 单位是毫秒。
