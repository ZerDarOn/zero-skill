# Person evidence natural context forward 14

这是 `person-evidence-analysis` 0.1.2 的未见题前向评测，检查它能否在自然、信息较杂且要求简洁的材料中保持来源层级、行动角色和有界人物判断。第八轮两个 pilot 都只执行每题一次；当前版较常被偏好，但严格分含非关键复述要求，且“交出选择但保留执行责任”的一次共同遗漏没有稳定复现。因此本轮先确认，不预设候选或修改 Skill。

六个新合成任务覆盖：人物自述原因与实际后续、主管评价与两种决策行为、事故处置中的建议／最终决定／对外责任、社区活动中的地点选择与组织执行、三次同类行为及一个紧急例外，以及两句短答中的第三方标签与直接反证。任务没有复用第八轮的原句、书面选项偏好、模糊“她”指代或原责任场景。

无 Skill 与0.1.2使用相同的 `gpt-5.6-sol`、`medium`、任务正文和只读隔离环境。Skill 臂采用项目级显式调用；硬标准不进入生成提示。六题、两臂各重复三次，共36个独立输出，失败不重试。

本轮把硬分、核心错误与偏好分开。每题指定一项会改变人物结论的核心标准，一份输出在同一题最多记一次核心错误：

- 来源层级：`self-report-cause-and-follow-through` 第2条、`supervisor-label-and-mixed-decisions` 第1条、`two-sentence-source-and-counterevidence` 第2条。
- 行动角色：`incident-recommendation-and-accountability` 第2条、`community-location-and-organization` 第2条。
- 有界模式：`bounded-listening-pattern-with-exception` 第1条；该机制只有一个题，只用于诊断，不能单独触发候选。

只有同一机制在至少两个不同题型中满足以下全部条件，才打开0.1.3候选设计：0.1.2在每个题型都出现不少于 `2/3` 的核心错误，且 baseline 在每个对应题型均不超过 `1/3`。一次失败、不同机制各一题失败、仅偏好落后、仅格式失败或两臂共同失败都不触发。达到门槛也只授权设计最小候选，不能直接修改、升版或发布。

正式运行前由另一个同项目任务检查题面是否与旧轮重复、来源关系、行动角色、正向模式是否可支持、两句限制、硬标准可观察性、核心机制分组和候选门槛。协议冻结后先提交再运行；揭盲后不修改题面、硬标准或核心错误定义。

本实验不测试隐式发现、真实人物资料、联网研究、关系回复建议、开放工具行为或独立人工领域评审。

准备命令：

    python evaluations/promptfoo/prepare_skill_comparison.py --spec evaluations/comparisons/person-evidence-natural-context-forward-14/promptfoo.json

运行、汇总与盲评沿用 [evaluations/promptfoo/README.md](../../promptfoo/README.md)。
