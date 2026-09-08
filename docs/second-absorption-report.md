# 第二次吸收：文稿润色与 Obsidian 笔记编辑

日期：2026-09-08。起始提交：`e50464b7cf4a1905a4c518c9f2ff0049e1b53c8c`。

## 来源与取舍

`prose-polish` 参考 Humanizer 的固定提交 `9862685f575c65a8247f90369951df1b3416e3d6`，阅读范围为入口中保留原意、作者样本和完成后检查的段落，以及仓库 MIT 许可证。采用信息保真、按作者样本匹配声音和编辑后回查；没有复制长风格清单，不建立机械禁词表，也不强迫输出多稿。

`obsidian-note-edit` 参考 Obsidian Skills 的固定提交 `a1dc48e68138490d522c04cbf5822214c6eb1202`，阅读范围为 `obsidian-markdown/SKILL.md` 中属性、内部链接、嵌入和 callout 段落，以及仓库 MIT 许可证。采用最小必要语法和笔记结构；不采用插件安装、CLI／仓库操作、无条件模板或未实际执行的渲染验证。

两个包的说明与合成示例均为本仓库原创措辞，没有复制第三方文件或执行上游脚本。`catalog/upstreams.json` 中继续标记 `imported: false`。

## 实现

- `prose-polish` 0.1.0：`creation / workflow`。默认只返回最终稿，匹配用途与作者声音，同时保护数字、日期、引语、专名、否定、因果、概率、范围、代码、命令、路径和链接目标；清楚原文可以不改。
- `obsidian-note-edit` 0.1.0：`productivity / workflow`。只编辑给定或指定文本，按需使用 Obsidian 语法，区分已知目标、未验证目标和计划新建笔记，并保护属性类型、链接别名、代码块和块 ID。

两者均登记为 `experimental`，`evidence` 保持 `null`；单次合成诊断不支持提升为 `verified`。

最终包指纹：

| 技能 | 包 SHA-256 | active 用例 SHA-256 |
| --- | --- | --- |
| `prose-polish` | `814d88e2b5874df4b2cc1dd54fc380b4f1745caf1622419f1d740faf81d58b8e` | `0a58daadb6a209588ff7b0db5b3d2d9e06ad7d25aa212637e0b115da5c3acc89` |
| `obsidian-note-edit` | `552b3dfeb25608e6a19b8bc7157f849a77b4ba6cccf9b6ea9155badcf8357077` | `be3ed6a8fbf745169fa9f01b5df30ec48d3c59334f5aec2ff3b441e2def856a1` |

## 对照运行

每个技能有 4 个冻结合成用例。先在技能不存在时运行 8 个 baseline，再实现并登记技能，仅把用例 `stage` 从 `planned` 改为 `active`，随后用相同 8 个用户请求显式加载各自完整技能包。模型为 `gpt-5.6-sol`、`medium`；共 16 次有效独立生成，模型启动 16 次、启动失败 0、重试 0。每次使用全新临时目录、`--ephemeral --ignore-user-config`、只读沙箱且不调用工具。

Windows PowerShell 5 曾在模型启动前因 UTF-8 无 BOM 解码失败；改用 PowerShell 7 运行同一脚本。该预检失败没有产生模型调用，不计入 16 次运行。

| 技能 | Baseline | Skill | 严格改善 | 退化 |
| --- | --- | --- | --- | --- |
| `prose-polish` | 3/4 | 4/4 | 1 | 0 |
| `obsidian-note-edit` | 4/4 | 4/4 | 0 | 0 |

唯一严格改善出现在 `preserve-qualified-claims`：baseline 把“可能缩短约12%”写成确定陈述“缩短了约12%”；skill 保留了概率、试点范围和不普适限定。其余 7 例两组均通过，其中 5 例输出完全相同或语义等价。强 baseline 已覆盖大多数要求，因此这里只观察到一项窄范围改善，不主张稳定或聚合收益。

baseline 总观察时长 80,327 ms，输入／缓存输入／输出 token 为 121,920／81,408／517；skill 为 74,434 ms 和 128,730／81,408／485。时长是本地编排观察区间，不是服务端延迟。

完整包与用例快照、精确提示、原始输出、事件、stderr、哈希、时长、用量和逐例人工理由见[诊断证据](../evaluations/reports/second-absorption-0.1.0-diagnostic.json)。

## 本地导出

使用仓库导出器分别生成两个归档，均只含 `bundle-manifest.json`、技能入口和合成示例；manifest 的包指纹与上表一致。

| 归档 | ZIP SHA-256 |
| --- | --- |
| `dist/prose-polish-0.1.0.zip` | `fd1949a9ac5e35eac0c1549568794ee107267adc31d9f7485d40ad8e012b9252` |
| `dist/obsidian-note-edit-0.1.0.zip` | `abbc9d7a3232654c14ad77bb08a290566d257cb81ec82960ec0561ba2265be7e` |

## 限制

每例只运行一次，评分由本次执行任务中的 Codex 模型复核，没有独立人工评审或重复采样。显式注入不测试自动发现与路由；隔离 CLI 也不测试真实 Obsidian 仓库编辑、渲染、插件或文件权限。后续如要声称稳定收益，需要固定版本复测、独立评分和真实宿主验证。
