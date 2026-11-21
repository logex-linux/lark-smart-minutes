# docs +search

搜索云文档（Search v2: doc_wiki/search），只读，仅支持 `--as user`。这是枚举智能纪要的主路径。

## 命令

```bash
lark-cli docs +search --as user --query "智能纪要" --page-size 20 --format json
lark-cli docs +search --as user --query "智能纪要 <主题关键词>" --page-token "<page_token>" --format json
lark-cli docs +search --as user --query "智能纪要" --filter '{"owner_ids":["ou_…"]}' --format json
```

## 参数

| 参数 | 说明 |
|---|---|
| `--query` | 关键词；命中标题或正文。智能纪要正文固定含「智能纪要由 AI 生成，可能不准确，请谨慎甄别后使用」，用「智能纪要」可枚举帐号可见的全部纪要 |
| `--page-size` | 默认 15，最大 20 |
| `--page-token` | 翻页令牌，取上一页 `data.page_token`；`data.has_more=false` 时结束 |
| `--filter` | JSON 过滤条件，CLI 将其展开为请求体的 `doc_filter` / `wiki_filter`（如 `{"owner_ids":[…]}`）。注意：实测 `owner_ids` 并未严格限制返回（结果仍含其他 owner 的文档），owner 收敛以本地按 `result_meta.owner_id` 过滤为准 |

## 返回字段（`data.results[].result_meta`）

| 字段 | 用途 |
|---|---|
| `title_highlighted` | 标题，`<h>` 标签为命中片段；解析时去标签、`&amp;` 还原 |
| `summary_highlighted` | 正文摘要高亮，可用于确认是否真为纪要 |
| `doc_types` | `DOCX` / `BITABLE` / `SHEET`；只处理 DOCX |
| `token` | 文档 token，交给 `docs +fetch` |
| `url` | 文档 URL，域名区分内部/跨租户 |
| `owner_id` / `owner_name` | 所有者 |
| `is_cross_tenant` | 是否跨租户副本 |
| `create_time_iso` / `update_time_iso` | 创建/更新时间 |

## 注意

- 搜索结果包含误命中（正文提到"智能纪要"的普通文档、多维表格）；按标题前缀 `智能纪要：` / `AI notes:` / `文字记录：` 分类剔除。
- 分页令牌是 JSON 字符串，原样传入 `--page-token`。
- 搜索覆盖帐号有权限查看的文档，不限于本人创建；跨租户副本与内部副本会同时出现。

## 相关场景

- [搜索与枚举智能纪要](../scenes/search-and-enumerate.md)
