# Round 34 揭盲后独立语义校准与 gate 复核

日期：2026-09-14

## Findings first

没有开放 P0、P1、P2 或 P3。唯一原始 `false` 语义判定成立，校准层记录零更正。

`retirement-banner-does-not-collapse-cohorts-r2` 的 candidate C（揭盲后为 baseline）保留了新账户 9 月 1 日截止和 120 个已有合同账户可用至 12 月 31 日，但没有用明确或等价语义说明 S2 横幅缺少账户范围和迁移日期，因此不能单独推翻合同账户窗口。答案把全管理员可见的横幅称为“局部展示”，并要求确认“横幅修正时间”，反而预设横幅需要修正。把该项由 `false` 校准为 `true` 会放宽冻结的复合 criterion，故保留原判。

原匿名评分、偏好、揭盲键和正式运行文件均未修改；并列校准文件的 `corrections` 为空。

## 身份、盲态与范围

本复核由模型辅助的独立任务完成，不是本轮匿名评分者，也不是独立人工评审。复核发生在揭盲后，已知 candidate 与 arm 映射，因此不是盲评。

复核只判断全部原始 `false`，本轮共 1 项；没有复核或改动任何 `true`，没有新增或收紧标准，也没有重评偏好。读取了冻结 comparison 的 `promptfoo.json` 和 `cases.json`，正式 run 的 `summary.json`、`blind-review.json`、`blind-review-key.json`、`blind-review-completed-independent.json`、`review-result-independent.json`，以及唯一 false 所在候选输出。

没有修改 Skill、catalog、活动 cases、冻结协议、匿名评分或正式运行原件。

## 原始与校准汇总

正式评分包含 18 个 review、54 个候选输出和 216 个布尔判断。原始为 215 个 `true`、1 个 `false`；校准更正数为 0，所以两种口径完全相同。

| Arm | 输出 | 原始通过 | 校准通过 | 原始完整输出 | 校准完整输出 | 原始偏好 | 校准偏好 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| baseline | 18 | 71/72 | 71/72 | 17/18 | 17/18 | 0 | 0 |
| ours | 18 | 72/72 | 72/72 | 18/18 | 18/18 | 1 | 1 |
| upstream | 18 | 72/72 | 72/72 | 18/18 | 18/18 | 0 | 0 |

18 个 review 中有 1 个偏好 ours、0 个偏好 baseline 或 upstream，另 17 个为平局。偏好沿用匿名评分，不进入语义校准。

## 逐题核心失败

一次输出只要任一冻结 `core_criteria` 为 `false`，即计一次核心失败。校准没有更正，原始与校准结果相同。

| Mechanism | Case | baseline | ours | upstream |
| --- | --- | ---: | ---: | ---: |
| publication-scope | `scoped-incident-does-not-revoke-availability` | 0/3 | 0/3 | 0/3 |
| publication-scope | `retirement-banner-does-not-collapse-cohorts` | 1/3 | 0/3 | 0/3 |
| stakeholder-authority | `approval-threshold-excludes-current-quote` | 0/3 | 0/3 | 0/3 |
| stakeholder-authority | `privacy-veto-is-not-purchase-approval` | 0/3 | 0/3 | 0/3 |
| bounded-evidence-update | `incompatible-studies-cannot-be-pooled` | 0/3 | 0/3 | 0/3 |
| bounded-evidence-update | `approved-document-bounded-revision` | 0/3 | 0/3 | 0/3 |

## 三个机制的冻结 gate

冻结 gate 要求同一机制的两题同时满足：ours 每题核心失败至少 `2/3`，baseline 每题至多 `1/3`，且 54 份输出全部有效。upstream 是上下文 arm，不参与触发判定。

| Mechanism | ours 两题均 ≥2/3 | baseline 两题均 ≤1/3 | 原始触发 | 校准触发 |
| --- | --- | --- | --- | --- |
| publication-scope | 否：0/3、0/3 | 是：0/3、1/3 | 否 | 否 |
| stakeholder-authority | 否：0/3、0/3 | 是：0/3、0/3 | 否 | 否 |
| bounded-evidence-update | 否：0/3、0/3 | 是：0/3、0/3 | 否 | 否 |

三个机制在两种口径下都不触发。**不打开候选设计。** 总分、完整输出或单个偏好不能替代预注册的重复特有失败门槛。

## 运行完整性

正式 `summary.json` 记录计划和执行均为 3 次重复，三臂各 18 行，共 54/54 输出；54 行均通过 Promptfoo，provider error 和 forbidden-tool 行均为 0，`infrastructure_valid=true`。`summary.json` 的 `awaiting-human-review` 是生成匿名评分前的生命周期状态，不改变后续完成评分的 54/54 计数。

校准来源通过 SHA-256 绑定 comparison 的冻结 protocol/cases、匿名候选包、揭盲键、完成评分、揭盲结果与 summary。结构化校准记录 `1 = 0 + 1`，保留项唯一对应原始 false，candidate C 映射到 baseline，且不存在 `true→false` 或偏好改动。

## 限制

本复核是揭盲后的模型辅助语义检查，可能受已知 arm 身份影响，不能替代新的独立人工复核。它只复核原始 false，不对原始 true 做第二次正确性审计。

样本只覆盖六个合成、单轮、中文、显式调用任务，一个模型和三次重复。summary 中三臂的预期 Skill trace 行均为 0，因此本轮结果不证明每条 ours 或 upstream 轨迹实际加载了对应 Skill，也不支持对真实业务效果、隐式路由或广泛产品质量作外推。校准文件只是并列解释层，不覆盖匿名评分原件。
