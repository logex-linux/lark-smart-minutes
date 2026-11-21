# lark-smart-minutes

飞书**智能纪要**（Note / AI notes）的调研成果与 Skill 设计。

## 内容

| 目录/文件 | 说明 |
|---|---|
| [`skill/lark-smart-minutes/`](skill/lark-smart-minutes/SKILL.md) | 智能纪要 Skill：帐号级检索、结构化阅读、待办/决策提取、系列纪要遍历 |
| [`RESEARCH.md`](RESEARCH.md) | 调研报告：枚举结果、文档组织结构、标识关系、对 skill 设计的输入 |
| `*.py` | 采集与分析脚本（可复跑） |

## 研究结论速览

- **枚举**：`lark-cli docs +search --query "智能纪要"` 是枚举帐号全部智能纪要的主路径（实测 56 条结果 → 44 篇纪要 + 4 篇逐字稿 + 8 条误命中，去重后 42 个会议）；会议维度 `vc +search → vc +detail` 与妙记维度可补全 note_id；纪要「相关会议纪要」引用构成搜索覆盖不到的系列图谱（111 条引用中 89 条不在搜索结果内）。
- **组织结构**：每篇纪要结构高度稳定——标题规范 → 头部 blockquote（主题/时间/参会人）→ 免责声明 → `# 总结`（封面画板 + 层级 bullet，100%）→ `# 待办`（95%）→ `# 相关链接`（95%），可选章节按频率为金句 52%、会议最佳表现成员 41%、相关会议纪要 27%、关键决策 18%、智能章节 14%。
- **关键限制**：「会议最佳表现成员」实体在 ISV 只读块内，`docs +fetch` 不可得；unified 类型逐字稿只能 `note +transcript`；权限失败退出码 1 且错误 JSON 在 stderr；跨租户副本需按「归一化标题 + 日期」去重。

## 复跑

```bash
python3 collect_search.py      # 枚举全部搜索结果
python3 fetch_all_notes.py     # 批量抓取纪要正文
python3 analyze_structure.py   # 结构统计
python3 collect_meetings.py    # 会议维度 note_id 映射（open_id 自动取自 lark-cli whoami）
python3 expand_corpus.py       # 系列图谱 BFS 扩展
python3 smoke_test.py          # skill 记录路径的端到端验证
```

脚本以自身所在目录为工作目录（`BASE = os.path.dirname(os.path.abspath(__file__))`），原始数据落在 `data/`（未入库）。

`smoke_test.py` 不含任何硬编码 ID；可选用环境变量启用对应检查：

| 环境变量 | 用途 |
|---|---|
| `SMOKE_NOTE_ID` | 一个 `unified` 类型 note_id，验证 `note +detail` |
| `SMOKE_MEETING_ID` | 一个关联 `normal` 纪要的 meeting_id，验证 `vc +detail → note +detail` |
| `SMOKE_FORBIDDEN_DOC` | 一个无权限文档 token，验证权限失败行为（错误码 3380004/3380002） |

> 原始采集数据（`data/`，含公司内部会议内容）已通过 `.gitignore` 排除，未上传；本仓库内容已脱敏（无人名、会议标题、文档 token、租户域名）。

## Skill 使用

Skill 按 lark-* 家族规范编写，放入 agent skills 目录（如 `~/.agents/skills/`）即可被加载。结构：`SKILL.md`（领域模型 + 快速行动 + 场景路由）+ `scenes/`（4 个场景手册）+ `references/`（3 个参考）。
