# 第二十轮最终独立工程复核

## Findings

### 阻塞发现

#### [P1] Round 20 重算测试没有闭合报告的来源与决策完整性链

涉及位置：

- `tests/test_claim_quantitative_confirmatory_round20.py:43-49`
- `tests/test_claim_quantitative_confirmatory_round20.py:70-73`
- `tests/test_claim_quantitative_confirmatory_round20.py:132-136`
- `tests/test_claim_quantitative_confirmatory_round20.py:217-221`
- `evaluations/reports/claim-quantitative-confirmatory-round-20-diagnostic.json:42`

当前 staged 数据经本次直接核对是正确的：冻结提交、运行产物、盲评包、揭盲映射、评分结果、报告内输出和活动用例全部实际吻合。但新增测试没有把这些关系固化为可持续的回归保护：

1. 测试只断言 `freeze_commit` 字符串等于固定提交号，再用**报告自身提供**的 `source_hashes` 检查当前工作树文件；它没有从 `8b72878a41b6963fd411b1619adf308b79c439d9` 读取 `promptfoo.json` 与 `cases.json` 并验证提交内字节。若以后同时修改当前协议文件、活动用例和报告中的源哈希，冻结提交号保持不变，现有断言仍可通过。
2. `decision_projection_sha256` 只与一个常量字符串比较，没有像 `test_claim_evidence_round18.py` 那样从 reviewer、逐项 `criteria_pass` 和 `preferred_candidate` 重新构造规范投影。按 Round 18 已有的规范投影算法重算当前 Round 20 内容，得到 `18290d5de78ac8a32e4a00f4ebe1c54a2b24e91fbe047eb4c0d298a931e9d121`，而报告记录的是 `e0a7b7ab3a50cd5dd21a58024f81ac77b109bae6b1a1904b8e6464045a5aa346`；仓库中没有定义另一种能复现后者的 Round 20 投影算法。因此该字段目前是不可复算的声明，不是有效完整性校验。
3. 每个 `output_sha256` 只与同一报告内的 `output` 自校验。修改内嵌输出并同步更新其哈希仍会通过；测试没有把报告条目绑定到固定的盲评包/结果投影。类似地，活动用例只与当前 comparison 文件比较，没有再锁到冻结提交内题面。

影响：当前结论没有算错，但测试名称所承诺的“保护已发布 Round 20 报告”并未覆盖最关键的证据来源关系。后续对题面、具体评分落点或内嵌输出的协同改动可能在总分、逐题汇总和当前文件自洽的情况下通过测试，造成冻结证据被静默改写。对于以可追溯评测证据为交付物的仓库，这是提交前应修复的阻塞项。

建议修复：

- 明确定义一个稳定、规范化的 Round 20 决策/证据投影，并在测试中从报告内容重新构造后计算 SHA-256；至少纳入 reviewer 关键声明、`review_id`、冻结题面/硬标准哈希、candidate 到 arm 映射、输出哈希、逐项布尔值和偏好。
- 从冻结提交读取 `promptfoo.json`、`cases.json` 的 blob 并核对 `source_hashes`，或把冻结提交 blob 的固定 SHA-256 作为独立常量验证，不能只比较当前文件与报告自报哈希。
- 将报告条目投影锁到盲评包、揭盲键和评分结果的固定投影摘要；若正式测试不依赖被忽略的运行目录，应在报告中保存可独立复算的规范投影，并在测试中与硬编码的已审计摘要比较。
- 更新报告中的 `decision_projection_sha256` 为按明确算法实际重算的值，并添加负向测试，证明移动一次失败标准、替换一次输出或修改冻结题面会失败。

### 非阻塞发现

除上述完整性门禁外，未发现新的非阻塞实现问题。报告已经如实保留 `summary.json` 只是盲评前 `awaiting-human-review` 快照、评阅者并非独立人工、盲性依赖流程声明，以及显式 Skill 条件缺少逐次 `skillCalls` 遥测等限制。

## 已独立核对通过的事实

### 冻结协议与运行来源

- 冻结提交为 `8b72878a41b6963fd411b1619adf308b79c439d9`。
- 直接读取该提交内 blob 后，`promptfoo.json` 的 SHA-256 为 `83ab64fea30ea4f45db2df89afd7423de6ccf01bc852e58e1a7765ce86a5c94f`，`cases.json` 为 `55ab72fc651d7fd917e581162c8fa542431865cc8bb5ad398dea9bc9e13c7b6e`，均与报告及 `frozen.json` 一致。
- 报告列出的八个运行产物 SHA-256 均与运行目录实际文件一致。
- 报告 15 个条目的题面、硬标准、候选输出、揭盲 arm、逐项评分、评阅说明和偏好均与 `blind-review.json`、`blind-review-key.json` 及评分结果一致；报告输出按题型和 arm 形成的多重集合与 `results.json` 的 30 行原始输出完全一致。

### 分数、偏好与门槛

从 90 个布尔值独立重算得到：

| 实验臂 | 标准通过 | 完整输出 | 偏好 |
| --- | ---: | ---: | ---: |
| baseline | 44/45 | 14/15 | 1 |
| ours 0.1.0 | 45/45 | 15/15 | 7 |
| 持平 | — | — | 7 |

逐题核心遗漏为：

| 题型 | baseline | ours 0.1.0 |
| --- | ---: | ---: |
| `corrected-and-missing-denominators` | 0/5 | 0/5 |
| `equal-rate-different-denominators` | 1/5 | 0/5 |
| `strict-table-two-batches` | 0/5 | 0/5 |

冻结门槛要求 ours 在至少两个题型各有 `>=2/5` 核心遗漏，且 baseline 在对应每题均为 `<=1/5`。ours 三题均为 `0/5`，所以没有题型满足第一条件，`qualifying_cases=[]`、门槛未触发是正确结论。保持 `claim-evidence-review` 0.1.0、不开候选、不升版符合预注册权限边界。

### Token、成本与延迟

从 `results.json` 原始行重新汇总：

| 指标 | baseline | ours 0.1.0 | ours 相对变化 |
| --- | ---: | ---: | ---: |
| 总 token | 147,025 | 160,611 | +13,586（+9.24%） |
| completion token | 3,605 | 4,681 | +29.85% |
| 总成本 | 0.261012 | 0.2593048 | -0.65% |
| 中位延迟 | 10,834 ms | 11,059 ms | +225 ms（+2.08%） |

README、Round 20 文档和机器报告采用的 9.2%、29.8%、-0.7%、2.1% 均是合理四舍五入。文档也正确限制了推断：缓存构成和调用顺序会影响小额成本差，每臂 15 份输出不足以把 225 ms 差异解释为稳定性能变化。

### 包、活动用例与状态

- 当前包指纹重算为 `bfda03a341b9d1b62f2004b7854fca0d4e7712a730a95274e3f9a4b43f7d8e29`，与冻结运行和报告一致。
- `claim-evidence-review` 活动用例为 17 项，全仓活动用例为 119 项。
- 三个新增活动用例的 prompt 与冻结 `cases.json` 逐字一致，`must_include` 与冻结 `hard_criteria` 逐项一致；各自保留 `comparison_case_id` 绑定。
- catalog 仍为版本 `0.1.0`、状态 `experimental`、`evidence: null`，没有把本轮模型辅助合成评测误标成 `verified`。
- `README.md`、`evaluations/README.md` 与 `docs/quality-polish-round-20.md` 对总数、结果、门槛、版本决定及限制的表述一致。

### Round 19 历史接力

Round 19 测试把当前总数断言从精确等于 116/14 放宽为不低于其历史报告值，使后续新增用例不会破坏历史测试。它随后仍按四个冻结 `comparison_case_id` 逐项索引活动用例，并比较 prompt 与 `must_include`；删除任一 Round 19 历史用例会因缺少键而失败，修改其内容也会失败。因此这次放宽仍能保护 Round 19 历史用例不被删除或改写。当前精确总数 119/17 由新的 Round 20 测试负责。

## 检查记录

- `python scripts/validate_collection.py`：通过。
- `python -m unittest discover -s tests -v`：70 项测试中 69 项通过，1 项因 Windows 缺少符号链接权限跳过；与 staged 文档一致。
- 自定义只读证据链复算：冻结提交源哈希、八个产物哈希、30 行输出、90 个布尔值、盲评映射、报告条目、活动用例、包指纹及 catalog 状态均核对通过。

## 最终门禁

**暂不建议提交当前 staged 批次。** 运行结果和业务决策本身可信且一致，但应先修复 Round 20 报告测试的冻结来源、输出及决策投影绑定，再重新运行结构校验和完整测试。除这一项外，没有发现需要调整结果解释、版本决定或活动回归内容的问题。
