# 智能纪要（Note）调研报告

> 数据来源：一次 lark-cli 帐号级采集（用户身份，可见内部租户文档与跨租户副本）。
> 采集方式与结论均已脱敏：不含人名、会议标题、文档 token 与租户域名；统计数字为真实采集结果。
> 采集脚本为同仓库 `*.py`，原始数据未入库。

## 1. 枚举结果：帐号可搜索到的智能纪要

### 1.1 主路径：docs +search

```
lark-cli docs +search --as user --query "智能纪要" --page-size 20   # 翻页取全部
```

- 共 **56 条** DOCX/BITABLE 结果（3 页翻完，`has_more=false`）：
  - **44 篇** 智能纪要（标题 `智能纪要：…`）
  - **4 篇** 文字记录（标题 `文字记录：…`，即 normal 纪要的独立逐字稿 Doc）
  - **8 条误命中**（正文/标题含"智能纪要"字样但非纪要）：多为个人工作记录表、内容消费记录、课程回放索引、活动总结、产品分析等普通文档与多维表格
- 命中原因：每篇纪要正文固定含免责声明「智能纪要由 AI 生成，可能不准确，请谨慎甄别后使用」。
- 按标题去重（去重键 = 去掉结尾日期后缀的标题 + 会议日期）后为 **42 个不同会议**：2 场会议同时存在内部租户 + 跨租户两份副本，标题相同、owner 不同、URL 域名不同。注意同系列不同日期的例会（如某每日站会 9/17 与 9/25）去掉日期后同名，必须带日期去重。
- 8 篇跨租户纪要（`is_cross_tenant=true`）与内部副本并存。
- 纪要创建时间跨度约 2026-03 下旬 → 2026-09 底；owner 分散在十余位不同同事名下（搜索可见全租户范围内有权限的纪要，不限本人）。

### 1.2 辅助路径

| 路径 | 命令 | 结果 |
|---|---|---|
| 会议维度 | `vc +search --participant-ids <open_id>` → `vc +detail --meeting-ids …` | 23 场会议，仅 **2 场**返回 `note_id`（本人拥有/可见的纪要）；13 场有 `minute_token` |
| 妙记维度 | `minutes +search` → `minutes +detail` | `+search` 返回空；`+detail` 缺 scope `minutes:minutes.basic:read`（未授权） |
| 图谱维度 | 纪要正文「相关会议纪要」callout 引用 | 111 条 `cite doc-id` 引用，其中 **89 个文档不在搜索结果内** |

### 1.3 图谱扩展（BFS，上限 220 篇）

- 第 1 轮 106 篇 → 第 2 轮 108 篇 → 第 3 轮 137 篇（触顶）。
- 新增：44 篇中文智能纪要、4 篇英文智能纪要（标题 `AI notes: … on <Mon D, YYYY>`）、49 篇被引用的其他文档。
- **123 篇抓取失败，全部是权限错误**（code 3380004 无查看权限 / 3380002 不存在或已删）——系列链接会指向无权限纪要，属预期情况，需逐篇报告而非整批失败。
- 系列图谱持续增长（106→167→146），说明循环会/站会的纪要互相引用成网，关键词搜索只能看到其中一层。

## 2. 智能纪要是怎么组织的

### 2.1 文档类型与标识关系（已用 CLI 交叉验证）

```
会议 meeting_id ──vc +detail──► note_id + minute_token
note_id ──note +detail──► note_display_type + note_doc_token + verbatim_doc_token
note_doc_token ──docs +fetch──► 纪要正文（Markdown）
verbatim_doc_token ──docs +fetch──► 逐字稿正文（仅 normal 类型）
note_id ──note +transcript──► unified 类型逐字稿文件
```

- `note_display_type`：`normal`（正文+独立逐字稿 Doc，样例 2 篇）与 `unified`（正文内嵌 `vc-tabs`，逐字稿经 `note +transcript`，样例 1 篇）。
- 同一场外部会议在两个租户各生成一份纪要副本（不同 note_doc_token），内容同源。

### 2.2 normal 类型纪要文档解剖（44 篇样本统计）

固定骨架，自上而下：

| 区块 | 格式 | 出现率 |
|---|---|---|
| 标题 | `<title>智能纪要：<会议主题> <YYYY年M月D日></title>` | 44/44 |
| 头部信息 | `<blockquote>`：会议主题 / 会议时间（含星期、GMT+08 时区）/ 参会人（`<cite type="user">` 逐个列出） | 44/44 |
| 免责声明 | `> 智能会议纪要由 AI 生成，可能不准确，请谨慎甄别后使用` | 44/44 |
| `# 总结` | `<whiteboard token>` 封面画板 + 一段总起 + 层级 bullet；内嵌 `<grid>/<column>` 双栏排版与图片（`feishu.cn/file/...`） | 44/44 |
| `# 待办` | `- [ ] <事项名>：<描述>（来自<提出人>）` + 负责人 `<cite type="user">`（可多个） | 42/44 |
| `# 相关链接` | 会中共享的文档（`<cite doc-id file-type title>` 或 wiki 链接 `?from=vcFollow`）；妙记链接 `/minutes/<token>?from=ai_minutes`；文字记录 docx 链接 | 42/44 |
| `# 会议中的金句时刻` 或 `# 金句时刻` | `「引文」` 空行 `—— 点评` | 23/44 (52%) |
| `# 会议最佳表现成员` | 正文仅为 `<readonly-block type="isv">` 空占位 | 18/44 (41%) |
| `# 相关会议纪要` | `<callout emoji="📌">` 内多条 `<cite doc-id file-type="docx" title="智能纪要：<同系列历史会议>">` | 12/44 (27%) |
| `# 关键决策` | `**关键决策**`：问题 / 讨论方案（bullet）/ 决策依据；`---` 分隔后 `**其他决策**` 编号列表 | 8/44 (18%) |
| `# 智能章节` | `[MM:SS](<minutes_url>?t=<毫秒>)  **章节标题**` + `> 本章节…` 摘要，深链到妙记时间点 | 6/44 (14%) |

要点：

1. **AI 生成区域以 `<readonly-block type="isv">` 收尾标记**（总结/待办等章节末尾），它是只读块的占位符，本身无内容。
2. **「会议最佳表现成员」内容在 ISV 只读块内，`docs +fetch` 拿不到**（返回空占位），只能客户端查看——skill 必须显式说明该限制。
3. **标题变体**：`智能纪要：MM-DD | 【循环会】XXX`（日期前缀型，循环会常用）、无日期型、英文 `AI notes: <topic> on <Mon D, YYYY>`。
4. **「相关会议纪要」是系列组织的核心**：循环会（研发循环会、团队周会、每日站会、中台跟进会等）每期纪要引用同系列历史纪要，构成可遍历图谱；单篇可达 26 条引用。
5. **待办带归属**：`（来自<提出人>）` + cite 负责人，可直接汇总成全组待办清单。

### 2.3 unified 类型纪要

```
<vc-tabs>
  <vc-summary-tab> …总结/待办/关键决策/金句时刻（h1 结构同上）… </vc-summary-tab>
  <vc-transcribe-tab vc-node-id="<note_id>"></vc-transcribe-tab>
</vc-tabs>
```

- `note +detail` → `note_display_type=unified`、`verbatim_doc_token` 为空；逐字稿只能 `note +transcript --note-id`（仅 `--as user`），输出 `@<说话人>  MM:SS` 行格式，默认存 `./notes/{note_id}/unified_transcript.md`。

### 2.4 文字记录（逐字稿）文档

- 标题 `文字记录：<主题> <日期>`（注意有前导空格变体）。
- 头部：会议主题 / 会议时间 / **智能纪要反链**（指向纪要主文档）。
- 发言行两种格式：`@<说话人> HH:MM:SS` 或 `说话人 N HH:MM:SS`，下一行为发言内容。

## 3. 对 skill 设计的输入

1. **发现**：`docs +search "智能纪要"` 是唯一能枚举全帐号纪要的路径；需本地过滤标题前缀（`智能纪要：`/`AI notes:`/`文字记录：`）剔除约 8/56 的误命中；跨租户副本按「归一化标题 + 日期」去重。
2. **补全**：`vc +search → vc +detail` 拿 note_id（会议视角）；`minutes +search` 需 scope，缺权限时按提示引导授权。
3. **读取**：`note +detail` 拿 token → `docs +fetch` 读正文；封面画板 `docs +media-download --type whiteboard`；normal 逐字稿读 `verbatim_doc_token`，unified 用 `note +transcript`；「会议最佳表现成员」不可读需说明。
4. **提取**：待办/关键决策/金句时刻/智能章节均有稳定 markdown 模式，可程序化提取；智能章节的时间戳深链可跳转妙记。
5. **遍历**：「相关会议纪要」callout 的 `cite doc-id` 可 BFS 扩展系列；权限失败逐篇报告。
6. **身份**：全部命令 `--as user`；`note +transcript` 仅支持 user。
