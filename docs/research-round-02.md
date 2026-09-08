# 第二轮开源技能研究

核查日期：2026-09-08。Star 来自 GitHub 公开 API，当日会继续变化。精确值、提交、最后推送时间和固定阅读链接见 [研究快照](../catalog/research-snapshot-2026-09-08.json)。本轮十个仓库均未归档；维护时间只是活跃度线索。

本轮阅读 README，并查看四个仓库中的五个技能入口选段；没有执行项目或验证作者声称的效果。以下“值得借鉴”是设计判断，不能视为已通过本集合评测。

| 项目 | Star 快照 | 覆盖场景 | 借鉴点与优先级 |
| --- | ---: | --- | --- |
| [Superpowers](https://github.com/obra/superpowers) | 282,884 | 工程、技能编写 | A：用例驱动指令改进、交付前核对证据；不继承整套强制仪式 |
| [Anthropic Skills](https://github.com/anthropics/skills) | 175,065 | 通用、办公、创作 | A：技能编写和有／无技能评测。不同目录许可不同 |
| [Composio Awesome Claude Skills](https://github.com/ComposioHQ/awesome-claude-skills) | 74,645 | 办公、连接器、发现 | C：按真实任务发现候选；连接器依赖与具体技能要分别审查 |
| [Marketing Skills](https://github.com/coreyhaines31/marketingskills) | 48,223 | 营销、文案、增长 | B：共享产品背景、按任务拆分技能；采用前辨别通用指导与集成推荐 |
| [Obsidian Skills](https://github.com/kepano/obsidian-skills) | 48,002 | 办公、知识管理 | B：围绕 Markdown、Canvas 等具体格式交付；工具操作和文件编辑分别处理 |
| [Agentic Awesome Skills / AAS](https://github.com/sickn33/agentic-awesome-skills) | 46,127 | 集合管理、检索 | C：精确选择、清单校验、变更预览；当前基础无需引入其完整控制系统 |
| [Humanizer](https://github.com/blader/humanizer) | 45,010 | 写作与创作 | B：保留原意、匹配作者样本、去掉空泛表达；不把词表变成统一口吻 |
| [Scientific Agent Skills](https://github.com/K-Dense-AI/scientific-agent-skills) | 43,654 | 研究与分析 | A：证据质量、备选解释、混杂因素；科研工具及医学流程不属于首批范围 |
| [Vercel Agent Skills](https://github.com/vercel-labs/agent-skills) | 30,944 | 前端与设计 | B：规则按影响排序、问题绑定具体场景；技术规则需要对应栈和版本 |
| [宝玉 baoyu-skills](https://github.com/JimLiu/baoyu-skills) | 25,735 | 中文创作、媒体 | B：写作、排版、配图等任务拆分与小套装；发布和生成工具留到实际需要时 |

A = 为首批建设提供方法；B = 后续专项候选；C = 发现或集合管理参考。优先级依据本项目阶段，和 Star 排名无关。

## 这轮纠正的认识

1. `K-Dense-AI/claude-scientific-skills` 已转到 `K-Dense-AI/scientific-agent-skills`；`sickn33/antigravity-awesome-skills` 已转到 `sickn33/agentic-awesome-skills`。记录规范地址与固定提交，避免以后读错版本。
2. Anthropic README 明确区分 Apache 2.0 的开源技能和仅源码可见的文档技能；K-Dense 也说明文档技能保留 Anthropic 的条款。不能从整仓热度或顶层许可推断每个目录的授权。
3. AAS 的 README 区分代码工具的 MIT 和原创非代码内容的 CC BY 4.0，另有第三方来源说明。候选登记保留此差异，复制前仍需查具体文件。
4. 高星工程套装不一定适合人物分析；小众 LoveHelper 的“先给回复、后讲依据”恰好适合关系任务。先明确要改善的行为，再选参考来源。

上述变更与许可说明对应各仓库固定 README，见快照的 `readme_url`；API 无法识别许可时使用 `null`，不解释为“没有许可”。

## 第一次吸收的决策

以已有路线图中的 P1、P2 作为一个可试用小批次：人物证据分析 + 关系复盘。女娲和 LoveHelper 提供领域设计，Distilly／自己.skill 提供修订思路，Anthropic／Superpowers／Scientific Agent Skills 提供编写与验证方法。

每个优点都必须转为本地可观察行为，例如“保留反证”对应矛盾对话用例，“回复优先”对应用户只问下一句的用例。不能仅在文档中列出优点就声称已吸收。

执行边界、源文件与验收已整理在 [新对话执行说明](first-absorption-handoff.md)。本轮只完成准备，两个技能还没有实现。
