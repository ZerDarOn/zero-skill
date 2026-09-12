# 第二十轮质量打磨：定量保真确认性复测

日期：2026-09-13

## 范围

第十八、十九轮在五个相关题型、每臂15个输出中，揭盲后探索性观察到 `claim-evidence-review` 0.1.0 有4次核心数字遗漏，无 Skill 有2次。这个4比2只能触发确认性复测，不能直接证明退化或授权修改 Skill。

本轮在运行前冻结三个全新合成表面：相同比例但样本量不同、分母更正与另一组分母缺失、严格短表中的两批前后值。每题的核心遗漏标准和候选门槛都预先写明：只有0.1.0在至少两个题型各出现不少于 `2/5` 遗漏，且 baseline 在对应每题均不超过 `1/5`，才打开候选设计。

冻结前独立复核发现，更正题原先会把来源关系失败误计成数字遗漏。协议据此把定量状态、来源关系和总体结论拆开；二次复核确认可冻结。协议提交为 `8b72878a41b6963fd411b1619adf308b79c439d9`，当前包指纹为 `bfda03a341b9d1b62f2004b7854fca0d4e7712a730a95274e3f9a4b43f7d8e29`。

无 Skill 与0.1.0使用相同的 `gpt-5.6-sol`、`medium`、任务正文和只读隔离环境；每题每臂五次，共30个有效输出。没有 provider error、禁止工具调用、失败重试或排除。

## 结果

| 实验臂 | 标准通过 | 完整输出 | 偏好 | 总 token | 中位延迟 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 无 Skill | 44/45 | 14/15 | 1 | 147,025 | 10,834 ms |
| 0.1.0 | 45/45 | 15/15 | 7 | 160,611 | 11,059 ms |

另有7次持平。逐题结果为：

| 用例 | 无 Skill | 0.1.0 | 核心遗漏：无 Skill / 0.1.0 | 偏好：无 Skill / 0.1.0 |
| --- | ---: | ---: | ---: | ---: |
| 分母更正与另一组分母缺失 | 15/15，5/5完整 | 15/15，5/5完整 | 0/5 / 0/5 | 1 / 2 |
| 相同比例、不同样本量 | 14/15，4/5完整 | 15/15，5/5完整 | 1/5 / 0/5 | 0 / 4 |
| 严格短表中的两批前后值 | 15/15，5/5完整 | 15/15，5/5完整 | 0/5 / 0/5 | 0 / 1 |

唯一硬标准失败来自 baseline 的一次相同比例题：输出写出两批样本量和共同的25%，但没有同时保留 `5/20` 与 `125/500`。当前版在三个题型、15份输出中没有核心数字遗漏，因此没有任何题型达到候选门槛的第一条件。

本轮 `summary.json` 是盲评完成前生成的运行快照，状态为 `awaiting-human-review`；它只证明30份输出和基础设施门禁完整。正式质量分来自完成的匿名评阅、揭盲映射和 `review-result-blind-review-completed-independent.json`，不能用 Promptfoo 的执行通过行替代45项硬标准判断。

## 决定

保持 `claim-evidence-review` 0.1.0，不修改 Skill、不设计候选、不升版。第十八、十九轮的4比2风险信号没有在预注册确认轮中复现，不能再把它描述为稳定相对退化；本轮45/45和7次偏好也只是三个合成表面的有限结果，不能证明普遍优于无 Skill。

三个题全部加入活动回归，`claim-evidence-review` 从14项增至17项，全仓活动用例从116项增至119项。状态仍为 `experimental`，`evidence` 仍为 `null`。

## 成本与边界

0.1.0总 token 多13,586，约9.2%；completion token约多29.8%；记录成本约低0.7%；中位延迟约高2.1%。小额成本差受缓存与调用顺序影响，225毫秒延迟差也没有多轮运行或置信区间支持，均不能解释为稳定性能收益或退化。

- 全部材料为合成数据；
- 单模型、单推理等级、每臂15份输出；
- 使用项目级显式调用，隐式路由没有重测；
- 显式项目条件没有逐次 `skillCalls` 遥测；
- 评阅者是另一个 Codex 任务中的模型辅助匿名评审，不是独立人类领域评审；
- 最终文件无法单独强制证明评阅者未访问揭盲键，盲性依赖流程约束与评阅声明。

## 校验

- `python scripts/validate_collection.py`：通过；
- `python -m unittest discover -s tests -v`：71项中70项通过，1项因 Windows 无符号链接权限跳过。

材料：

- [冻结协议](../evaluations/comparisons/claim-quantitative-confirmatory-13/README.md)
- [首次冻结前复核](../evaluations/comparisons/claim-quantitative-confirmatory-13/prefreeze-review-independent.md)
- [修订后二次复核](../evaluations/comparisons/claim-quantitative-confirmatory-13/prefreeze-rereview-independent.md)
- [独立揭盲后决策](../evaluations/comparisons/claim-quantitative-confirmatory-13/postscore-decision-review-independent.md)
- [首次最终工程复核与P1发现](../evaluations/comparisons/claim-quantitative-confirmatory-13/final-engineering-review-independent.md)
- [P1修复后的工程二审](../evaluations/comparisons/claim-quantitative-confirmatory-13/final-engineering-rereview-independent.md)
- [自包含机器诊断](../evaluations/reports/claim-quantitative-confirmatory-round-20-diagnostic.json)
- [当前论断证据审查 Skill](../skills/research/claim-evidence-review/SKILL.md)
