# 第三十二轮质量打磨：当前故障证据排查与 Systematic Debugging 前向盲测

日期：2026-09-14

## 本轮问题

`debug-evidence-triage` 0.1.1 在第二十二轮只和无 Skill 比较，尚未与固定的成熟上游做同版前向测试。本轮比较无 Skill、当前 `debug-evidence-triage` 0.1.1 与 Superpowers 固定提交中的 `systematic-debugging`，重点检查观察覆盖、因果区分和跨执行身份连续性。

上游技能覆盖从根因调查到实现、测试和完成验证的更长流程。本轮只比较三者共同覆盖的单轮、只读、中文诊断切片；组装包闭合了 `systematic-debugging` 同目录引用，但没有纳入它后续调用的 `test-driven-development` 和 `verification-before-completion` 兄弟技能，因此不能把结果外推到完整 Superpowers 工作流。

## 固定设计

协议、六题、三臂配置、当前 Skill 与上游包在提交 `674321cbe70acf6bbafd1cdafb23fda3e34d53da` 冻结并推送。上游固定为 Superpowers 提交 `b36e0829c6d0140e93cfef2ca599b1b07d4a7797`，保留 MIT LICENSE 和原始字节，不运行其中脚本。当前包与上游包指纹分别为 `5c880634b3b728ec83a26efdc7f186c33f1196a1e6c6cfce6ea29cf4d2862e72` 和 `17c82641ac6528efd6c1728206442de6ca345314a176a8448c351191b35ca731`。

三臂使用同一个 `gpt-5.6-sol`、medium、公共提示和只读隔离配置；每题每臂重复三次，共 `6 × 3 × 3 = 54` 份输出、18 个匿名评阅项和 216 个布尔判断。失败保留且不重试。

六题按三个机制各两题组织：

- `observation-coverage`：零次 HTTP 500 是否掩盖 HTTP 200 空结果；只查 `finished_at IS NOT NULL` 是否隐藏停滞任务。
- `causal-discrimination`：超时恢复与索引上线同时发生时如何拆分解释；功能开关与 payload 大小混杂时如何设计四分支检查。
- `execution-identity-continuity`：相同 job id 的不同 retry attempt 是否能拼接；相同 session id 跨进程启动是否仍是同一执行链。

候选门槛在运行前写定：同一机制的两题中，当前 Skill 必须每题至少 `2/3` 次出现核心失败，同时 baseline 每题最多 `1/3` 次核心失败，且 54 份输出全部有效，才允许打开最小候选设计。上游只作设计参照，不参与本地改版门槛。

冻结前独立复核发现并修正两项 P2。功能开关题原先要求“三个分支”，实际冻结标准有四个分支；上游 provenance 原先可能被误读成完整工作流，随后明确同目录引用闭合但两个兄弟技能未组装。修订后复核无未解决 P0–P3，才冻结并运行。

## 正式结果

预检 3/3 完成且只验证基础设施，不计分。正式运行 54/54 完成，三个臂各 18 行；provider error、禁止工具轨迹和 Promptfoo 失败均为 0。

| arm | 原始完整通过 | 原始标准通过 | 校准完整通过 | 校准标准通过 | 匿名唯一偏好 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 无 Skill | 4/18 | 51/72 | 6/18 | 53/72 | 5 |
| `debug-evidence-triage` 0.1.1 | 1/18 | 45/72 | 3/18 | 50/72 | 1 |
| `systematic-debugging` | 1/18 | 44/72 | 4/18 | 47/72 | 0 |

原匿名评分共有 76 个 `false`。计分后，第二个模型辅助任务逐项复核全部 76 项，确认其中 10 项已经用等价语义满足冻结标准：功能开关题 7 项、停滞任务题 1 项、retry attempt 题 2 项。它们在并列校准层由 `false` 改为 `true`，其余 66 项保留。原始匿名评分、揭盲结果和偏好均未覆盖或重算。

校准没有改变排名：baseline 在原始与校准标准分、完整输出和匿名偏好上都领先两个 Skill 臂。本轮没有证据表明当前 Skill 提升了诊断质量，也没有证据表明上游切片优于 baseline。

## 核心失败与门槛

每格顺序为 baseline / 当前包 / 上游；一次输出只要任一冻结核心标准失败，就计一次核心失败。

| 机制 | 题目 | 原始核心失败 | 校准核心失败 |
| --- | --- | ---: | ---: |
| observation-coverage | `zero-five-hundreds-misses-empty-success` | 3/3 / 3/3 / 3/3 | 3/3 / 3/3 / 3/3 |
| observation-coverage | `finished-only-query-hides-stalled-jobs` | 1/3 / 2/3 / 2/3 | 1/3 / 2/3 / 1/3 |
| causal-discrimination | `bundled-timeout-and-index-recovery` | 3/3 / 3/3 / 3/3 | 3/3 / 3/3 / 3/3 |
| causal-discrimination | `flag-cohort-confounded-by-payload-size` | 3/3 / 3/3 / 3/3 | 1/3 / 1/3 / 1/3 |
| execution-identity-continuity | `same-job-id-different-retry-attempts` | 1/3 / 3/3 / 3/3 | 1/3 / 3/3 / 3/3 |
| execution-identity-continuity | `session-id-reused-across-process-boot` | 3/3 / 3/3 / 3/3 | 3/3 / 3/3 / 3/3 |

原始口径下，当前包三个机制都满足自身的两题失败阈值，但 baseline 每个机制至少一题也有 `3/3` 核心失败。校准口径下，观察覆盖与执行身份仍因相同的 baseline 失败而不能触发；因果区分还因为功能开关题三臂均降为 `1/3` 而不满足当前包阈值。两种口径都没有出现“当前包在同机制两题重复失败、baseline 稳定通过”的预注册模式。

因此不打开候选设计。`debug-evidence-triage` 正文、版本和 catalog 均不变，继续是 0.1.1、`experimental`、`evidence: null`。六个冻结题加入活动回归，该 Skill 从 13 例增至 19 例，全仓从 166 例增至 172 例。

这个决定不把 Skill 总分较低解释成“无需改进”。本轮大量失败是三臂共享的困难或与 baseline 成对出现；用已揭示题目直接改指令会把评测集变成训练集。后续应先转向其他证据较薄的技能；等出现新的同机制表面，再检验观察完整性和执行身份是否形成当前包特有的可复现缺口。

## 运行成本

当前 Skill 相对 baseline 的总 token 多 `10.9%`、记录成本多 `23.6%`，中位延迟多 `1.0%`。上游相对 baseline 的总 token 多 `24.0%`、记录成本多 `55.7%`，中位延迟多 `3.7%`。当前 Skill 相对上游少 `10.6%` token、少 `20.6%` 记录成本，中位延迟少 `2.7%`。

这些数字只描述本次 Promptfoo 记录，会受输出长度、缓存、定价和调度影响，不是稳定性能基准。更长的上游工作流也不等同于更差的完整产品设计。

## 评审与外推边界

匿名评审由 `gpt-6-astra`、medium 的独立模型辅助任务完成，只读取匿名包与空表单，对三臂随机映射保持盲态。评审者披露此前看过协议和技能修订，盲态只覆盖候选身份映射。揭盲后的语义校准由另一个模型辅助任务完成，不是原匿名评分者，但已知 arm 身份，可能受身份偏差影响；它不能替代新的独立人工评审。

本轮只覆盖六个合成、单轮、中文、显式项目级调用、只读诊断任务。它没有验证隐式发现、真实系统访问、复现、代码修改、测试执行、部署、生产安全结果或完整上游工作流。原始 Promptfoo 产物仍被 Git 忽略；公开机器报告嵌入合成输出、原始与校准评分、校准项和哈希，新克隆可检查已提交证据，但不能独立重建 provider 事件。

## 下一步

当前故障排查技能已经补上与固定成熟上游的同版三方证据。下一轮转向其他证据较薄的技能，优先检查已有上游参照、但严格前向证据仍有限的窄编辑或内容技能；本轮六题保留为活动回归，不围绕已揭示答案调规则。

## 对应证据

- [机器报告](../evaluations/reports/debug-current-systematic-round-32-diagnostic.json)
- [冻结协议](../evaluations/comparisons/debug-current-systematic-three-arm-25/README.md)
- [冻结前独立复核](../evaluations/comparisons/debug-current-systematic-three-arm-25/prefreeze-review-independent.md)
- [揭盲后独立语义校准与决策复核](../evaluations/comparisons/debug-current-systematic-three-arm-25/postscore-decision-review-independent.md)
- [最终独立工程复核](../evaluations/comparisons/debug-current-systematic-three-arm-25/final-engineering-review-independent.md)
- [固定 Superpowers 来源](../evaluations/fixtures/upstreams/superpowers-systematic-debugging/b36e0829c6d0140e93cfef2ca599b1b07d4a7797/provenance.json)
