# 搜索与枚举智能纪要

目标：列出当前用户帐号下所有可搜索到的智能纪要（及逐字稿），输出去重后的清单。身份：全部命令 `--as user`。

## 主路径：docs +search

```bash
lark-cli docs +search --as user --query "智能纪要" --page-size 20 --format json
```

- `page-size` 最大 20；`has_more=true` 时用返回的 `page_token` 继续，直到 `has_more=false`。
- 每篇纪要正文固定含「智能纪要由 AI 生成，可能不准确，请谨慎甄别后使用」，因此该关键词可命中帐号可见的全部纪要；`title_highlighted` 以 `<h>` 标签标注命中片段。
- 需要按主题收敛时把 `--query` 换成「智能纪要 <主题关键词>」；按 owner 收敛用本地过滤 `result_meta.owner_id`（`--filter` 的 `owner_ids` 不严格限制返回，见 [lark-docs-search](../references/lark-docs-search.md)）。

## 分类与剔除

对每条结果按 `result_meta.doc_types` 和标题分类：

| 标题模式 | 分类 | 处理 |
|---|---|---|
| `智能纪要：…` | 纪要 | 纳入清单 |
| `AI notes: …` | 英文纪要 | 纳入清单 |
| `文字记录：…` | 逐字稿 Doc | 单独列出，标注其所属会议；头部含纪要反链 |
| 其他（BITABLE、普通 DOCX） | 误命中 | 剔除并说明条数（实测约 8/56） |

取标题时去掉 `title_highlighted` 的 `<h>` 等标签；`&amp;` 还原为 `&`。

## 去重：跨租户副本

同一场外部会议会在内部租户与跨租户各生成一份纪要（`is_cross_tenant=true`，URL 域名为对方租户）：

- 去重键 = **归一化标题（去掉结尾的 `YYYY年M月D日`）+ 会议日期**：同键多篇即同一会议的副本。
- 不能只用归一化标题：同系列不同日期的例会（如「某每日站会」9/17 与 9/25）归一化后同名，但是不同会议。
- 两份都纳入原始结果，汇总时只保留一篇：优先内部租户副本，其次选择 `docs +fetch` 有权限的一篇；在输出中注明存在副本及各自 owner/域名。
- 逐字稿同样可能双副本，随主纪要一并去重。

## 补全路径

### 会议维度（用户给出会议主题/时间，或需要 note_id 时）

```bash
lark-cli vc +search --as user --participant-ids <open_id> --start 2024-01-01 --page-size 30 --format json
lark-cli vc +detail --as user --meeting-ids <meeting_id1,meeting_id2> --format json
```

- `vc +search` 只返回用户参会的会议；`vc +detail` 对每场会议返回 `note_id` 与 `minute_token`（可能为空）。
- `participant-ids` / `organizer-ids` 传 open_id，不支持 `me`；当前用户 open_id 从 `lark-cli whoami` 取。
- 实测：用户参会的 23 场会议中只有本人拥有/可见的纪要才返回 `note_id`；不要因为返回空推断纪要不存在。

### 妙记维度

```bash
lark-cli minutes +search --as user --query "<关键词>" --format json
```

- `minutes +search` 可用；`minutes +detail` 需要 scope `minutes:minutes.basic:read`，缺失时按 CLI 提示引导用户授权（`lark-cli auth login --scope "minutes:minutes.basic:read" --no-wait`，把 verification_url 原样交给用户），不要静默跳过。

## 图谱扩展（可选，用户要求"全部/系列"时）

纪要正文「相关会议纪要」callout 引用同系列历史纪要，其中大部分不在关键词搜索结果内（实测 111 条引用、89 条不在结果集）。按 [traverse-series.md](traverse-series.md) 做有界 BFS。

## 输出清单格式

每篇纪要输出：标题、owner、创建时间、内部/跨租户、doc token、URL（来自 `result_meta.url`）。末尾附统计：纪要数、逐字稿数、剔除的误命中数、去重合并的副本数、无权限文档数。
