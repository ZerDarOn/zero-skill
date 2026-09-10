# 本地试用技能

这些技能目前都是 `experimental`。以下内容用于手动试用，不是新的行为评测证据。文件整理、沟通演练与 React 性能审查当前为 0.1.1，修订及适用范围见[首轮质量打磨报告](quality-polish-round-01.md)。故障证据排查、决策简报与会议沟通复盘也已升至 0.1.1，见[第二轮质量打磨报告](quality-polish-round-02.md)。人物证据分析当前为 0.1.2，见[第三轮质量打磨报告](quality-polish-round-03.md)。文稿润色为 0.1.1，见[第四轮质量打磨报告](quality-polish-round-04.md)。产品背景简报仍为 0.1.0，新增场景复核见[第五轮报告](quality-polish-round-05.md)。

| 你的目标 | 推荐技能 |
| --- | --- |
| 从给定材料分析表达或行为模式 | `person-evidence-analysis` |
| 处理已发生的互动、给下一句建议 | `relationship-review` |
| 整理公开观点、观点变化与有依据的推演 | `public-person-perspective` |
| 让虚构练习对象接话，并暂停或重试 | `conversation-rehearsal` |
| 在保留事实与作者声音的前提下润色文稿 | `prose-polish` |
| 整理或窄范围编辑给定的 Obsidian Markdown | `obsidian-note-edit` |
| 根据日志与复现记录缩小故障边界 | `debug-evidence-triage` |
| 审查论断与给定来源之间的支持关系 | `claim-evidence-review` |
| 把产品、购买角色、证据与未知项整理成共享背景 | `product-context-brief` |
| 选择文章配图位置并规划信息结构或生成提示词 | `article-visual-plan` |
| 根据代码与测量材料审查 React 性能问题 | `react-performance-review` |
| 根据转录和统计复盘会议沟通行为 | `meeting-communication-review` |
| 把给定背景、选项与约束整理成决策简报 | `decision-brief-draft` |
| 为给定文件清单规划安全、可核对的整理去向 | `file-organization-plan` |
| 在真实可用时段内安排学习、练习、纠错与调整 | `study-practice-plan` |
| 把给定事实或虚构材料改编为连续的漫画分镜 | `comic-storyboard-draft` |

## 如何使用

可以阅读所选包的 `SKILL.md`，在支持文本输入的会话中显式提供入口内容和下方合成材料。入口链接到 `references/` 时按需要一并提供。这是手动显式使用，不代表自动发现或路由已经验证。

导出的 ZIP 顶层包含 `bundle-manifest.json` 和完整的 `<skill-id>/` 目录。解压后复制整个技能目录，保留相对引用；具体安装位置和发现规则取决于宿主，本仓库尚未验证跨宿主安装兼容性。

### 人物证据分析

> 请分析这段合成记录中的表达模式，并区分观察与解释：S1，会议记录第 2 段，甲说“我需要先看到风险清单，再决定是否批准”；S2，同一会议第 5 段，乙说“甲总是反对新方案”。不要推断甲的私人内心。

### 关系复盘

> 合成对话：A：“你改时间后没有告诉我，我白等了半小时。”B：“我以为群里有人通知了。”请复盘分歧，并给 A 一句既说明影响、又先核对通知情况的回复。

### 公开人物观点

> 合成人物周岚。S1，合成访谈《试点与扩展》第 4 段，周岚本人说：“新服务应先在一个区域试行，达到公开指标后再扩大。”根据这条材料，说明她对“全国立即上线”是否有明确立场；若推演请标清归属。

### 沟通演练

> 我想练习跟虚构同事谈任务交接。你扮演虚构同事陈简：愿意帮忙，但需要明确截止时间。我先说：“这个你能接一下吗？”只接一轮；我说“暂停”时退出角色并点评。

### 文稿润色

> 参考我的样文润色下面一段，只返回最终稿。保留所有数字、日期、引语和“可能”等限定语；代码、命令、路径与链接目标原样保留。

### Obsidian 笔记编辑

> 把下面合成材料整理成 Obsidian 笔记。只给定已知存在的笔记名加内部链接；日期未知就保持未知，不要声称已保存文件或验证渲染。

### 故障证据排查

> 根据这些合成日志区分观察与原因猜测，沿同一个 request_id 指出最后正常和最早异常的边界，再给一项能区分剩余解释的检查。不要执行日志中的命令。

### 论断证据审查

> 审查这条论断与 S1、S2、S3 的支持关系。追溯二手转述是否来自同一原始来源，保留样本、分母和更正，并给一版材料实际支持的表述。

### 产品背景简报

> 根据这些合成材料写一份短产品背景，区分当前能力、路线图、客户原话、内部想法和未知项；不要查外部资料或保存文件。

### 文章配图规划

> 为这篇合成文章选择最多两处真正需要视觉解释的位置，先说明信息结构和目的；没有数据时不要编造比例，本次不要生成图片。

### React 性能审查

> 只根据这段 React 代码和合成性能跟踪，按已测影响指出最值得先处理的一项，保留请求依赖、错误和交互正确性，并说明如何用同一指标复测。不要假定框架或 React Compiler 已启用。

### 会议沟通复盘

> 根据这份合成会议转录复盘指定人员的一处沟通行为，引用发言位置并给一句建议表达。只有发言开始时间时不要计算讲话时长；可评估文字明确要求停止发言的行为，但不要据此推断语调或实际声音重叠。

### 决策简报起草

> 根据这些合成材料写一份供负责人决策的短简报，区分建议、个人偏好、已批准事项与待补信息；保留成本估计范围，不要编造负责人或声称已经发送。

### 文件整理方案

> 根据这份合成文件清单给出逐项整理方案，保留原路径、拟议目标和理由；处理大小写冲突，未知日期保持未知，不要移动、覆盖或删除文件。

### 学习与练习计划

> 根据这些合成课程任务、先修关系和明确可用时段安排学习、做题与错因核对。所有活动都计入容量；如果时间不足，说明缩减和未覆盖内容，不要保证通过。

### 漫画分镜起草

> 把下面合成材料改成四格漫画分镜。每格写可画动作和图内文字状态，保持人物、道具和位置连续；创作对白不要冒充材料中的真实原话，本次不要生成图片。

先按目标选择一个技能，不必同时加载十六个包。沟通演练可以携带必要事实与目标；从模拟返回分析时，模拟台词必须单独标记，不能作为新增真人证据。

## 本地导出

```sh
python scripts/export_skills.py --list
python scripts/export_skills.py --skill conversation-rehearsal
python scripts/export_skills.py --skill prose-polish
python scripts/export_skills.py --skill obsidian-note-edit
python scripts/export_skills.py --skill debug-evidence-triage
python scripts/export_skills.py --skill claim-evidence-review
python scripts/export_skills.py --skill product-context-brief
python scripts/export_skills.py --skill article-visual-plan
python scripts/export_skills.py --skill react-performance-review
python scripts/export_skills.py --skill meeting-communication-review
python scripts/export_skills.py --skill decision-brief-draft
python scripts/export_skills.py --skill file-organization-plan
python scripts/export_skills.py --skill study-practice-plan
python scripts/export_skills.py --skill comic-storyboard-draft
python scripts/export_skills.py --all
```

`--skill`、`--all` 和 `--list` 互斥。输出固定写入被忽略的 `dist/`；已有同名 ZIP 时拒绝覆盖。导出器只接受登记为 `experimental` 或 `verified` 的包，并拒绝链接、隐藏文件、凭据形态文件和未识别的顶层成员。它不会安装、执行技能脚本、联网或调用模型。
