# Round 32 揭盲后独立语义校准与决策复核

日期：2026-09-14

## Findings first

### [P2] 原匿名评分包含 10 个语义假阴性

原始 216 个布尔判断中有 76 个 `false`。逐项复核后，10 项答案已经用等价语义满足冻结标准，原判因要求逐字复述或把复合标准机械拆解而错误；它们应在独立校准层由 `false` 改为 `true`。原匿名评分及揭盲结果保持不变，结构化更正保存在正式运行目录的 `review-calibration-independent.json`。

更正分为三类：

- flag 四分支共 7 项：答案已经把“仅关闭失败”解释为关闭路径异常、随机/非稳定因素、配置或实验偏差，并明确不能归因于新解析器；“开关都成功”也转向未复现或未控制条件。冻结标准允许这些等价表达，不要求逐字写“先复核 flag 身份”。
- `finished-only-query-hides-stalled-jobs-r2` 的 upstream C2 共 1 项：答案查询完整 25 条状态，并在全部进入终态时解释为任务后来恢复、转而核对状态变更记录。这与转向 dashboard 快照时点或数据选择解释语义等价。
- `same-job-id-different-retry-attempts` 的 ours r2/r3 C1 共 2 项：两份答案均保留 attempt 1 的 `array/aa71`、attempt 2 的 `null/bb09`、attempt 3 无字段摘要及不能拼链的结论，并用“同次相邻边界证据缺失”概括缺失记录。要求再次逐字列出 worker/publisher/queue 名称会重复同一语义。

其余 66 项 `false` 均保留。它们存在实际遗漏：未检查查询计划、未遵守第二项检查的进入条件或结果分支、未查询完整批次、2×2 设计未固定同一个大 payload、未补齐指定 attempt 的三段边界、未保留 B1 命中 3 项/10:02 重启/B2 miss 的完整事实、未明确 HTTP 200 空结果盲点，或把单次返回 3 笔当作验证通过而缺少授权隔离、状态码与数量并行观察及重复成功条件。没有放宽标准，也没有新增扣分。

校准后没有开放 P0、P1、P2 或 P3。上述 P2 只影响计分解释，不改变冻结 gate 或候选决定。

## 身份、盲态与读取范围

本复核是模型辅助独立任务，不是本轮匿名评分者，也不是独立人工评审。复核发生在评分完成并揭盲之后，已知 candidate、arm 和 Skill 身份，因此不是盲评。偏好完全沿用原匿名评分，没有重评。

读取范围包括：

- 比较目录的 `promptfoo.json`、`cases.json`、`README.md`、`prefreeze-review-independent.md`；
- 正式运行 `debug-current-systematic-three-arm-25-formal-20260914-v1` 的 `blind-review.json`、`blind-review-key.json`、`blind-review-completed-independent.json`、`review-result-blind-review-completed-independent.json`、`summary.json`、`run-meta.json`、`frozen.json`；
- 当前 `skills/engineering/debug-evidence-triage/SKILL.md` 与 `references/example.md`；
- 组装上游 `superpowers-systematic-debugging/b36e0829c6d0140e93cfef2ca599b1b07d4a7797` 的 `provenance.json` 与 `SKILL.md`。

除上述文件外没有读取其他运行材料；没有修改 Skill、活动 cases、catalog、协议、匿名包、揭盲键、完成评分或评分结果。

## 原始与校准汇总

运行包含 18 个 review、54 个候选输出和 216 个布尔判断；54/54 输出有效。原始评分有 140 个 `true`、76 个 `false`；校准后为 150 个 `true`、66 个 `false`。

| Arm | 输出 | 原始通过 | 校准通过 | 原始完整输出 | 校准完整输出 | 原始偏好 | 校准偏好 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| baseline | 18 | 51/72 | 53/72 | 4/18 | 6/18 | 5 | 5 |
| ours | 18 | 45/72 | 50/72 | 1/18 | 3/18 | 1 | 1 |
| upstream | 18 | 44/72 | 47/72 | 1/18 | 4/18 | 0 | 0 |

18 个 review 中有 6 个非空偏好，另 12 个为平局。校准只改布尔判断，不重新推断偏好，因此偏好保持 baseline 5、ours 1、upstream 0。

## 逐题核心失败

一次输出只要任一 `core_criteria=[0,1,2]` 为 `false`，即计一次核心失败。数值顺序为 baseline / ours / upstream。

| Mechanism | Case | 原始核心失败 | 校准核心失败 |
| --- | --- | ---: | ---: |
| observation-coverage | `zero-five-hundreds-misses-empty-success` | 3/3 / 3/3 / 3/3 | 3/3 / 3/3 / 3/3 |
| observation-coverage | `finished-only-query-hides-stalled-jobs` | 1/3 / 2/3 / 2/3 | 1/3 / 2/3 / 1/3 |
| causal-discrimination | `bundled-timeout-and-index-recovery` | 3/3 / 3/3 / 3/3 | 3/3 / 3/3 / 3/3 |
| causal-discrimination | `flag-cohort-confounded-by-payload-size` | 3/3 / 3/3 / 3/3 | 1/3 / 1/3 / 1/3 |
| execution-identity-continuity | `same-job-id-different-retry-attempts` | 1/3 / 3/3 / 3/3 | 1/3 / 3/3 / 3/3 |
| execution-identity-continuity | `session-id-reused-across-process-boot` | 3/3 / 3/3 / 3/3 | 3/3 / 3/3 / 3/3 |

两项 same-job C1 更正没有改变 ours 的逐题核心失败次数，因为相同输出仍有 C2 的真实失败。

## 冻结 gate 复算

冻结 gate 只比较 ours 与 baseline，并要求同一机制的两题同时满足：ours 每题核心失败至少 `2/3`，baseline 每题至多 `1/3`；54 份输出还必须全部有效。upstream 只作上下文。

### 原始评分口径

| Mechanism | ours 两题均 ≥2/3 | baseline 两题均 ≤1/3 | 触发 |
| --- | --- | --- | --- |
| observation-coverage | 是 | 否：zero-five-hundreds 为 3/3 | 否 |
| causal-discrimination | 是 | 否：两题均为 3/3 | 否 |
| execution-identity-continuity | 是 | 否：session/boot 为 3/3 | 否 |

### 校准口径

| Mechanism | ours 两题均 ≥2/3 | baseline 两题均 ≤1/3 | 触发 |
| --- | --- | --- | --- |
| observation-coverage | 是 | 否：zero-five-hundreds 为 3/3 | 否 |
| causal-discrimination | 否：flag 为 1/3 | 否：timeout/index 为 3/3 | 否 |
| execution-identity-continuity | 是 | 否：session/boot 为 3/3 | 否 |

两种口径下 54 份有效输出条件都满足，但三个机制均未同时满足 ours 与 baseline 条件。

## 决策

**不打开 `debug-evidence-triage` 候选设计。** 原始评分与语义校准后都没有任何机制触发冻结 gate。校准改变总分、完整输出数以及 flag 题的绝对失败解释，但没有形成“ours 在同机制两题重复失败且 baseline 稳定通过”的预注册模式。

本轮不授权修改或升版 Skill，不修改 catalog、evidence 或活动 cases，也不把 upstream 总分用于本地改版门槛。原始偏好 5/1/0 不能与校准布尔混合后重新解释成新的盲评偏好。

## 运行与来源一致性

`run-meta.json` 记录单次正式 Promptfoo 运行、`--repeat 3 --no-cache`、54 个预期与实际结果、54 个通过行、退出码 0 和 `completed`。`summary.json` 标记 infrastructure valid，三臂各 18 行，provider error 与 forbidden-tool 行均为 0。

冻结 spec、cases、prepared config/tests、当前 Skill 包及组装 upstream 包哈希与冻结前复核一致。上游 provenance 明确同目录资源闭合、后续 sibling skills 未组装、脚本未执行；本轮文本只读诊断不能外推到完整 Superpowers 工作流。

## 验证与限制

结构化校准经独立脚本验证：10 个更正键唯一；每个键都对应原评分中实际存在的 `false`；candidate/arm 映射与揭盲结果一致；只存在 `false→true`；原始文件哈希未变。两种汇总、逐题核心失败、偏好和 gate 均由评分结果加更正集合重算。

本复核是揭盲后的模型辅助语义复核，可能受已知 arm 身份影响，不能替代新的独立人工复核。样本只覆盖六个合成、单轮、显式 Skill、只读文本诊断任务，一个模型和三次重复；不验证真实系统访问、实际复现、代码修改、测试执行、隐式路由或完整上游工作流。校准文件是并列解释层，不覆盖原始匿名评分。
