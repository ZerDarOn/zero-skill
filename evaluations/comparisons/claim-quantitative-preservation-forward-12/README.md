# Claim quantitative preservation forward 12

这是 `claim-evidence-review` 0.1.0 的第二组独立前向诊断，复测第十八轮只在一个题型中出现的多批样本数字遗漏。它不预设0.1.1：先判断遗漏是否跨表面、跨重复稳定出现，并比较无Skill是否有同样问题。

四个新合成任务覆盖：两个业务队列与共享复核、存在缺失分母且方向不一的地区材料、终点不同的两项随机试验，以及严格两条项目符号的跨产品压缩。所有题目都要求保留会改变结论的核心分子、分母、前后值或终点范围；不要求机械复述无关数字。

无Skill与0.1.0使用相同的 `gpt-5.6-sol`、`medium`、任务正文和只读隔离环境。Skill臂采用项目级显式调用；硬标准不进入生成提示。四题、两臂各重复三次，共24个独立输出，失败不重试。

正式运行前由另一个同项目任务检查算术、来源依赖、缺失分母、两项试验的终点差异，以及两条项目符号约束是否公平。协议冻结后先提交再运行。

只有0.1.0在至少两个新题型中重复漏掉影响结论的核心定量信息，且baseline明显更少出现，才达到设计0.1.1候选的门槛。若失败只集中于一个题型或两臂同样出现，则保持0.1.0并记录残留。

本实验不测试隐式发现、联网核验、真实研究质量或独立人工领域评审。

准备命令：

    python evaluations/promptfoo/prepare_skill_comparison.py --spec evaluations/comparisons/claim-quantitative-preservation-forward-12/promptfoo.json

运行、汇总与盲评沿用 [evaluations/promptfoo/README.md](../../promptfoo/README.md)。
