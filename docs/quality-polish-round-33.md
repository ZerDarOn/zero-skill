# 第三十三轮质量打磨：复杂决策边界前向盲测

日期：2026-09-14

## 本轮问题

`decision-brief-draft` 0.1.1 只有六个活动合成用例。0.1.0 到 0.1.1 的两个新增题都通过，尚未观察到版本增益；复杂材料中的决策历史、硬约束与比较口径、角色权限与有限证据仍缺重复前向测试。本轮用六个未参与当前 Skill 编写的新表面，比较无 Skill 与当前 0.1.1。

该技能曾参考 Anthropic `doc-coauthoring` 的读者视角与有界协作方法，以及 Witchcat 的决策记录方法。前者是较长的协作写作流程，后者嵌在工程工作流且已记录提交没有覆盖该入口的统一许可证；两者都不是等价的单轮决策简报产品，因此本轮没有把它们组装成计分 arm，也不形成对上游的质量比较。

## 固定设计

协议、六题、两臂配置、当前 Skill 与冻结前独立复核在提交 `e9eca467b68a6e7fc29a6a6a0e6e8d672b49901c` 固定并推送。两臂使用同一个 `gpt-5.6-sol`、medium、公共提示和只读隔离配置；Skill 臂采用项目级显式调用。每题每臂重复三次，共 `6 × 2 × 3 = 36` 份输出、18 个匿名评阅项和 144 个布尔判断。失败保留且不重试。

六题按三个机制各两题组织：

- `decision-history`：新资格证据消除原批准依据的独有性，但不产生新批准；成本更正不撤销基于未变硬约束的既有批准。
- `constraint-and-denominator`：一次性实施费与年费归一到三年口径；一个选项违反硬约束、另一个关键条件未知时不强行选择。
- `role-and-evidence`：高管偏好与工作组建议不等于有权委员会批准；小规模内部可用性检查和未测生产底线不能支持全员推广。

候选门槛在运行前写定：同一机制的两题中，当前 Skill 必须每题至少 `2/3` 次出现核心失败，同时 baseline 每题最多 `1/3` 次核心失败，且 36 份输出全部有效，才允许打开最小候选设计。总分和主观偏好不能替代这个门槛。

冻结前独立复核发现并修正两项 P2。两道初稿分别与已有决策历史题、有限试点题高度同构，随后换成无障碍资格与退出成本、内部可用性与月末峰值 P95 的新表面；prepare 测试也补上活动题和 preparer 字节、完整包字节、两臂 provider 公平性、显式调用前缀差异与 rubric 隔离。修订后无开放 P0–P3，才冻结并运行。

## 正式结果

不计分预检 2/2 完成且基础设施有效。正式运行 36/36 完成，两臂各 18 行；provider error、禁止工具轨迹和 Promptfoo 失败均为 0。

| arm | 原始完整通过 | 原始标准通过 | 校准完整通过 | 校准标准通过 | 匿名唯一偏好 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 无 Skill | 10/18 | 63/72 | 10/18 | 64/72 | 0 |
| `decision-brief-draft` 0.1.1 | 14/18 | 68/72 | 14/18 | 68/72 | 5 |

原匿名评分共有 13 个 `false`。计分后，第二个模型辅助任务逐项复核全部 13 项，确认其中 1 项 baseline 答案已经用等价语义把当前动作限定为重开评估，没有在成本缺口未补时完成新选型。该项只在并列校准层由 `false` 改为 `true`；原始评分、揭盲结果和偏好均保留。

其余 12 项有实际缺口：3 项遗漏“当时只有 Atlas 达到 AA”这一原批准依据，2 项违反无标题范围，6 项缺少 A 恢复演练的完整正反结果分支，1 项编造财务负责人的批准权。校准项所在输出仍有另一项核心失败，所以两臂完整输出数、逐题核心失败和门槛均未改变。

当前 Skill 在这组六题中领先 baseline：原始和校准标准分更高，完整输出多 4 份，5 次清楚的匿名偏好也全部给当前 Skill。这个结果是当前版本在冻结样本中的正向证据，不足以形成一般胜率、上游排名或 `verified` 结论。

## 核心失败与门槛

| 机制 | 题目 | baseline | 当前包 |
| --- | --- | ---: | ---: |
| decision-history | `approved-choice-new-qualification-evidence` | 2/3 | 1/3 |
| decision-history | `cost-correction-does-not-revoke-approval` | 0/3 | 0/3 |
| constraint-and-denominator | `normalize-three-year-cost-basis` | 0/3 | 0/3 |
| constraint-and-denominator | `no-feasible-option-with-one-unknown` | 3/3 | 3/3 |
| role-and-evidence | `executive-preference-without-approval-authority` | 0/3 | 0/3 |
| role-and-evidence | `small-usability-check-does-not-prove-rollout` | 0/3 | 0/3 |

原始与校准的核心失败完全相同。决策历史机制中当前包为 `1/3`、`0/3`，不满足自身两题失败阈值；约束与口径机制是一题两臂均 `3/3` 失败、配对题均通过，既不是当前包特有问题，也不是双题重复；角色与证据机制两题均无核心失败。三个机制都没有触发门槛，不打开候选设计。

`decision-brief-draft` 正文、版本和 catalog 均不变，继续是 0.1.1、`experimental`、`evidence: null`，包指纹仍为 `d66fc65cda321f4a9718c5517ff17e87f704646c9de07d9afb9cb4b4b1495c17`。六个冻结题加入活动回归，该 Skill 从 6 例增至 12 例，全仓从 172 例增至 178 例。

两臂在恢复演练题都连续遗漏完整正反分支，说明这个表面对模型本身较难。因为配对的三年口径题都通过，且 baseline 同样失败，不能围绕已经揭示的单题直接扩写 Skill。应把这个信号留给新的硬约束未知项表面复测。

## 运行成本

当前 Skill 相对 baseline 的总 token 多 `13.2%`、记录成本多 `66.3%`，中位延迟少 `1.1%`。两臂总 token 分别为 197,946 与 174,874；记录成本分别为 0.3458544 与 0.2079536；中位延迟分别为 8,944.5 ms 与 9,043.5 ms。

这些数字只描述本次 Promptfoo 记录，会受输出长度、缓存、定价和调度影响，不是稳定性能基准。质量提升和记录成本增加都只适用于本次冻结样本。

## 评审与外推边界

匿名评审由 `gpt-6-astra`、medium 的独立模型辅助任务完成，只读取匿名包与空表单，对两臂随机映射保持盲态；评审者记录此前没有接触本轮协议或 Skill 修订。揭盲后的语义校准由另一个模型辅助任务完成，不是原评分者，但已知 arm 身份，可能受身份偏差影响；它不能替代独立人工评审。

本轮只覆盖六个合成、单轮、中文、显式项目级调用、只读文本任务。它没有验证每条轨迹实际加载 Skill、隐式发现、真实审批系统、多人协作文档、文件写入、读者研究、执行结果或长期决策质量。原始 Promptfoo 产物仍被 Git 忽略；公开机器报告嵌入合成输出、原始与校准评分、校准项和哈希，新克隆可检查已提交证据，但不能独立重建 provider 事件。

## 下一步

当前决策简报技能补上了复杂边界的重复前向证据，继续追加相近单轮题的边际收益有限。下一轮转向另一个证据较薄、且能在当前只读环境中形成可判定结果的技能；恢复演练题保留为回归，等出现新的双硬约束未知项表面再判断它是否构成跨题机制。

## 对应证据

- [机器报告](../evaluations/reports/decision-brief-complex-round-33-diagnostic.json)
- [冻结协议](../evaluations/comparisons/decision-brief-complex-boundaries-two-arm-26/README.md)
- [冻结前独立复核](../evaluations/comparisons/decision-brief-complex-boundaries-two-arm-26/prefreeze-review-independent.md)
- [揭盲后独立语义校准与决策复核](../evaluations/comparisons/decision-brief-complex-boundaries-two-arm-26/postscore-decision-review-independent.md)
- [最终独立工程复核](../evaluations/comparisons/decision-brief-complex-boundaries-two-arm-26/final-engineering-review-independent.md)
