# Round 30 揭盲后独立决策复核

## Findings first

未发现 P0、P1、P2 或 P3。匿名评分中的六个 `false` 均符合冻结标准；独立校准层不改动任何布尔值。三臂各为 `70/72`、`16/18` 完美输出、0 个偏好，三个机制均未触发冻结门槛。因此本轮不授权候选设计、Skill 修改、升版、catalog 状态变化或 evidence 变化。

## 复核范围与文件边界

本次读取了比较目录的 `README.md`、`promptfoo.json`、`cases.json`、`prefreeze-review-independent.md`；正式运行目录的 `blind-review.json`、`blind-review-key.json`、`blind-review-completed-independent.json`、`review-result-blind-review-completed-independent.json`、`summary.json`、`run-meta.json`、`frozen.json`；以及已提交的 `article-visual-plan`、catalog、active cases 和固定 Baoyu provenance/package。未读取 `results.json` 或 `prepared/`。

评阅者是模型辅助独立任务，不是独立人工视觉设计评审。评阅者在评分前只对臂映射保持盲态，并如实记录此前接触过协议和 Skill 修订；评分完成后才读取映射。本复核为揭盲后的同一独立任务。

## 原始评分与独立校准

原始匿名评分共有 18 个 review、54 个候选输出和 216 个布尔值，其中 210 个 `true`、6 个 `false`。所有 18 个 `preferred_candidate` 均为 `null`。

| Arm | 输出 | 完美输出 | 通过标准 | 偏好 |
| --- | ---: | ---: | ---: | ---: |
| baseline | 18 | 16 | 70/72 | 0 |
| ours | 18 | 16 | 70/72 | 0 |
| upstream | 18 | 16 | 70/72 | 0 |

六个 `false` 的揭盲归属如下：

| Review | Candidate / Arm | 标准 | 类型 | 复核 |
| --- | --- | ---: | --- | --- |
| `owner-corrected-human-review-flow-r1` | A / upstream | K4 | 非核心 | 输出在“退回申请人修改”后新增“重新提交”节点；冻结 K4 明确禁止材料外节点，原判保留。 |
| `owner-corrected-human-review-flow-r2` | A / ours | K4 | 非核心 | 同上，原判保留。 |
| `owner-corrected-human-review-flow-r2` | B / baseline | K4 | 非核心 | 同上，原判保留。 |
| `owner-corrected-human-review-flow-r2` | C / upstream | K4 | 非核心 | 同上，原判保留。 |
| `owner-corrected-human-review-flow-r3` | A / baseline | K4 | 非核心 | 同上，原判保留。 |
| `unequal-cohort-observed-rates-r3` | A / ours | K2 | 核心 | 输出写出 `12/20` 与 `14/18`，但没有显示冻结 K2 明确要求的 `60%` 和约 `77.8%`。分数可数学换算不等于回答已呈现百分比，原判保留。 |

“重新提交”在现实流程中可能合理，但题面最终口径只给出“未通过则退回申请人修改”；把它画成下一节点仍是材料外扩展。cohort 输出中的两个分数与百分比数学等价，但 K2 检查的是回答中是否准确呈现分数及其百分比，不能用可推导性替代显式呈现。校准后仍为 210/216，三臂聚合不变。

## 逐题核心失败与门槛

一次输出只要任一冻结 `core_criteria` 为假，即计一次核心失败。

| Case | baseline | ours | upstream |
| --- | ---: | ---: | ---: |
| `retracted-metric-evidence-summary` | 0/3 | 0/3 | 0/3 |
| `owner-corrected-human-review-flow` | 0/3 | 0/3 | 0/3 |
| `unequal-cohort-observed-rates` | 0/3 | 1/3 | 0/3 |
| `qualitative-themes-without-intensity` | 0/3 | 0/3 | 0/3 |
| `global-style-with-local-content-correction` | 0/3 | 0/3 | 0/3 |
| `delete-and-insert-with-stable-ids` | 0/3 | 0/3 | 0/3 |

冻结门槛要求同一机制两题中，ours 每题至少 `2/3` 次核心失败，baseline 每题至多 `1/3` 次核心失败，并且 54 份输出全部有效。逐机制结果：

| Mechanism | ours 条件 | baseline 条件 | 触发 |
| --- | --- | --- | --- |
| `source-revision-control` | 未满足 | 满足 | 否 |
| `evidence-compatible-encoding` | 未满足 | 满足 | 否 |
| `compound-plan-state` | 未满足 | 满足 | 否 |

upstream 按冻结协议仅作设计上下文，不进入候选门槛。

## 运行有效性与哈希

`run-meta.json` 记录 Promptfoo `0.123.0`、单次 `--repeat 3 --no-cache` 正式命令、54 个预期结果行、54 个实际结果行、54 个 Promptfoo 通过行、退出码 0 和状态 `completed`；没有失败后补跑或筛选的记录。`summary.json` 标记 `infrastructure_valid: true`，三臂各 18 行，provider error 与可观察 forbidden-tool 行均为 0。

由于本复核按任务边界没有读取 `results.json`，运行有效性结论来自 `run-meta.json` 与 `summary.json`，并核对二者声明相同的 results SHA-256；本复核没有从原始 provider events 再次重建该结论。

已复算的关键绑定：

- spec SHA-256：`85a3b9acb6a1b039ae59973042b961362a265b5cbbe5bbeecb47ed99cb691faf`
- cases SHA-256：`08073406fd3fa237a051e6d4a1e59cff05b331e99cbc44007524e39df5b8915a`
- frozen SHA-256：`e80b13c6d4e0692aea0966ac28d13af6af17eb7933a6eb8437f3c295807d6363`
- blind packet SHA-256：`ce7d44bc4b842526282e01704b7c697529fec90b03f8f9cc1cc4e31224749dbc`
- blind key SHA-256：`ecf0ca0c8af23a59b980f4fb39686d79a4b4331944b003df4de946fec3a3c3b3`
- completed blind review SHA-256：`fc0867cf22b0daad40aa44a652b1d6349f56a4b5ed3d5bc5e772ccfd2dd174e8`
- scored review SHA-256：`6eb6f86a785e260a31410da1d9838000befacf348f82cc4567c5339d31807ae8`
- summary SHA-256：`54690583c617ff08f5b053629d7c285f12e071d76a38765da7683680997f63ef`
- run metadata SHA-256：`48687b1812c2b929dba8251e24639e04e8668756323a2f4e08ac9dc3f1f96f08`
- results SHA-256 声明：`a87620d2563f237820c41011441956ca1418cb707fdc18819164b6b1e1908f4b`
- ours package SHA-256：`e02fed142a73421a2cc091bfea0d6faefef4c8035e671d4866e65708e9973a87`
- upstream package SHA-256：`761701b48cbc7fe9eba501cd9f22bb3989e653417474662bf4d4268741824ea3`
- fixed upstream provenance SHA-256：`5d172e072c1be1196d8a3a2193a5bc517f7afcc2a496363eff1a187ccf38382b`

`frozen.json` 的逐文件哈希、字节数和两个 package fingerprint 均从当前已提交包重算一致。固定上游仍包含 MIT 许可证和既有 provenance 边界。

## 决策

- 不打开最小候选设计。
- 不修改 `article-visual-plan`，不升版。
- catalog 继续为 `0.1.0`、`experimental`、`evidence: null`。
- 本轮不能标记 `verified`，也不能宣称 ours 优于 baseline 或 upstream。
- 六题可以按冻结 prompt、hard criteria 和 core criteria 原样加入 active regression cases。它们是前向合成任务，并捕获了材料外节点和百分比显式呈现两类失败；加入 active 不等于 Skill 质量认证。当前 article visual active cases 为 10，加入后应为 16。

## 鉴别力与限制

相较 Round 29 的三臂全满分，本轮至少产生了六个可解释的标准失败，因此能暴露更细的遵循问题。但三臂最终完全同分、完美输出数相同、偏好全为空，而且唯一核心失败只出现一次，仍不足以估计 Skill 的相对帮助或形成产品排名。

范围仍只有六个合成、单轮、文本规划任务，一个模型、一个推理等级、每臂三次重复。没有测试隐式路由、实际图片、文字渲染、生成后端、文件回填、编辑器集成、完整上游工作流或真实读者理解。模型辅助匿名评阅及本次模型辅助揭盲复核均不能替代独立人工视觉设计评审。
