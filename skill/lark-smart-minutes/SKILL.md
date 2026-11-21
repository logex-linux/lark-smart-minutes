---
name: lark-smart-minutes
version: 1.0.0
description: "飞书智能纪要（Note / AI notes）：按关键词枚举当前帐号全部可搜索的智能纪要与逐字稿，读取总结/待办/关键决策/金句/章节等结构化内容，提取待办与决策，遍历循环会系列纪要并按标题去重跨租户副本。当用户提到智能纪要、会议纪要、AI notes、note_id、智能章节，或要求查找/汇总/提取某个帐号下的会议纪要时使用。已知 note_id 的单篇查询与妙记（minutes）管理走 lark-meeting；预约会议走 lark-calendar。"
metadata:
  requires:
    bins: ["lark-cli"]
  cliHelp: "lark-cli docs +search --help;lark-cli note --help;lark-cli vc +detail --help"
---

# lark-smart-minutes

智能纪要（开启 AI 总结后由「智能纪要助手」生成的 Note）的帐号级检索、结构化阅读与内容提取。本技能负责发现路径、文档组织模型的运用和跨命令编排；单篇纪要的原子命令契约与 lark-meeting 共享，遇到认证、身份或 scope 问题读取 [`lark-shared`](../lark-shared/SKILL.md) 修复后重试。

与 [`lark-meeting`](../lark-meeting/SKILL.md) 的分工：lark-meeting 面向会议（meeting_id）与妙记（minute_token）域，从会议/妙记定位关联 Note；本技能面向 Note 域本身——帐号有哪些智能纪要、每篇的组织结构、如何批量读取和提取。用户只给出会议主题、日期范围或"所有纪要"这类检索意图时走本技能；用户给出 meeting_id / minute_token 时走 lark-meeting。

## 身份约定

- 本技能所有命令显式使用 `--as user`：智能纪要是用户级文档，机器人身份只能看到应用有权限的纪要，枚举结果不完整。
- `note +transcript` 仅支持 `--as user`。
- 无需预读 lark-shared 或预跑 `auth status --verify`；遇到未认证、token 或 scope 错误时再读取修复。

## 领域模型

```text
[发现路径]

docs +search "智能纪要" ──► 纪要 Docx（note_doc_token）────────┐
vc +search → vc +detail ──► note_id + minute_token ────────────┤
minutes +search → minutes +detail ──► note_id ────────────────┤（需 minutes:minutes.basic:read）
纪要正文「相关会议纪要」callout ──► 同系列兄弟纪要 doc-id ─────┘（图谱扩展）

[Note 智能纪要]（note_id）
├── note +detail ──► note_display_type + note_doc_token + verbatim_doc_token
├── note_doc_token ──► docs +fetch ──► 纪要正文（标题/参会人/总结/待办/…）
├── normal 类型：verbatim_doc_token ──► docs +fetch ──► 逐字稿 Docx（「文字记录：…」）
├── unified 类型：note +transcript ──► 逐字稿文件（正文内为 vc-tabs + vc-transcribe-tab）
├── 关联妙记 minute_token（正文「相关链接」/minutes/<token> 链接）
└── 同系列纪要（正文「相关会议纪要」callout 引用）
```

| 对象 | 标识 | 说明 |
|---|---|---|
| Note 智能纪要 | `note_id` | 逻辑产物，`note +detail` 的输入；从 `vc +detail` 或 unified 纪要正文 `<vc-transcribe-tab vc-node-id>` 取得 |
| 纪要正文 Doc | `note_doc_token` | docs +fetch 读取；标题以 `智能纪要：` 或 `AI notes:` 开头 |
| 逐字稿 Doc | `verbatim_doc_token` | 仅 normal 类型；标题以 `文字记录：` 开头，头部含纪要反链 |
| 妙记 | `minute_token` | 录制链路产物，与 Note 相互独立；minutes 域命令缺 scope 时引导授权 |
| Doc token | doc token | 内容载体，不能当作 note_id 传入 note 命令 |

## 智能纪要的组织模型（研究结论，44 篇样本）

每篇纪要 Doc 结构高度稳定，按此模型解析，不要臆测章节名：

1. **标题**：`智能纪要：<会议主题> <YYYY年M月D日>`；循环会常用 `智能纪要：MM-DD | 【循环会】<主题>`；英文会话生成 `AI notes: <主题> on <Mon D, YYYY>`。
2. **头部 blockquote**：会议主题 / 会议时间（含星期与 GMT+08）/ 参会人（`<cite type="user">` 逐个引用）。
3. **免责声明**：`智能会议纪要由 AI 生成，可能不准确，请谨慎甄别后使用`。
4. **`# 总结`**（100%）：`<whiteboard token>` 封面画板 + 总起段 + 层级 bullet，内嵌 `<grid>/<column>` 双栏和图片。
5. **`# 待办`**（95%）：`- [ ] <事项>：<描述>（来自<提出人>）` + 负责人 cite。
6. **`# 相关链接`**（95%）：会中共享文档、妙记链接、文字记录链接。
7. 可选章节（按频率）：`# 会议中的金句时刻`/`# 金句时刻`（52%）、`# 会议最佳表现成员`（41%）、`# 相关会议纪要`（27%）、`# 关键决策`（18%）、`# 智能章节`（14%）。
8. AI 生成区域以 `<readonly-block type="isv">` 占位收尾；「会议最佳表现成员」的实体内容位于 ISV 只读块内，`docs +fetch` 只能得到空占位，拿不到具体成员名单——向用户说明该限制，不要反复重试。

完整格式样本、频率统计与解析规则见 [note-doc-anatomy.md](references/note-doc-anatomy.md)。

## 快速行动

### 枚举当前帐号全部智能纪要

```bash
lark-cli docs +search --as user --query "智能纪要" --page-size 20 --format json
```

按 `page_token` 翻页取全部；本地按标题前缀过滤（`智能纪要：` / `AI notes:` / `文字记录：`），剔除正文误命中的普通文档。流程与去重规则见 [search-and-enumerate.md](scenes/search-and-enumerate.md)。

### 读取一篇纪要

```bash
lark-cli note +detail --note-id <note_id> --as user          # 需要 note_id 时
lark-cli docs +fetch --doc <note_doc_token> --doc-format markdown --as user
```

逐字稿入口由 `note_display_type` 决定：normal 读 `verbatim_doc_token`，unified 用 `note +transcript`。详见 [read-note-content.md](scenes/read-note-content.md)。

## 场景手册

- [搜索与枚举智能纪要](scenes/search-and-enumerate.md)：按关键词/主题/时间枚举帐号下所有智能纪要与逐字稿，剔除误命中，跨租户副本去重，会议与妙记维度补全。
- [读取智能纪要内容](scenes/read-note-content.md)：读取纪要正文、封面画板、逐字稿、智能章节深链、会中共享文档，处理 ISV 只读块限制。
- [提取待办、决策与金句](scenes/extract-and-summarize.md)：从单篇或一批纪要程序化提取待办、关键决策、金句、章节，汇总输出。
- [遍历系列纪要](scenes/traverse-series.md)：沿「相关会议纪要」链接遍历循环会/站会系列，BFS 扩展与权限失败处理。

## 命令参考

| 命令 | 用途 | 参考方式 |
|---|---|---|
| `docs +search` | 搜索智能纪要文档（枚举主路径） | [lark-docs-search](references/lark-docs-search.md) |
| `docs +fetch` | 读取纪要/逐字稿正文 | `lark-cli docs +fetch --help` |
| `docs +media-download` | 下载纪要封面画板 | `lark-cli docs +media-download --help` |
| `note +detail` | 查 note 详情与文档 token | [lark-note-commands](references/lark-note-commands.md) |
| `note +transcript` | 获取 unified 纪要逐字稿 | [lark-note-commands](references/lark-note-commands.md) |
| `vc +search` / `vc +detail` | 会议维度补全 note_id / minute_token | `lark-cli vc +detail --help` |
| `minutes +search` | 妙记维度搜索（需 scope） | `lark-cli minutes +search --help` |
| `drive metas batch_query` | 批量查文档名称与 URL | `lark-cli drive metas batch_query --help` |

## 渐进加载规则

1. 用户目标符合「快速行动」进入条件时直接执行对应 CLI，不预读场景手册与参考。
2. 需要枚举、去重、提取、遍历或遇到字段/异常不确定时，读取与目标匹配的一个场景手册，按流程执行。
3. 仅当缺少具体参数、返回字段或约束时读取对应命令参考；场景手册已给出精确命令时不再调用 `--help`。

## 关键原则

- **标题前缀是分类依据**：`智能纪要：`/`AI notes:` 为纪要，`文字记录：` 为逐字稿；搜索命中的其他文档（BITABLE、普通 DOCX）一律剔除并说明。
- **同一会议可能有两份纪要副本**：内部租户与跨租户各一份，标题相同、域名与 owner 不同。去重键 = 归一化标题（去掉标题结尾的日期）+ 会议日期；同键多篇才是同会议副本，保留有权限读取的一篇（优先内部租户）。注意同系列不同日期的例会归一化标题相同但日期不同，不能合并。
- **note_id 只从权威来源取得**：`vc +detail`、`minutes +detail`、unified 纪要正文的 `<vc-transcribe-tab vc-node-id>`；不从 Doc token、标题或正文反推。
- **逐字稿格式不是统一契约**：normal 是 Doc 读取结果，unified 是 `@说话人 MM:SS` 行；以实际内容为准。
- **权限失败逐篇报告**：系列链接指向无权限纪要时保留该 doc-id 并单项说明，不把整批结果误报为失败。
