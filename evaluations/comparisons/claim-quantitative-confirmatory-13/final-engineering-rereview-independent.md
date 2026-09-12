# 第二十轮最终工程聚焦二审

## Findings

### 阻塞发现

无。上一轮指出的 P1 证据完整性缺口已关闭。

### 非阻塞发现

无。没有发现由本次修复引入的新歧义、错误绑定或测试失真。

## P1 关闭核对

### 冻结来源

- `test_claim_quantitative_confirmatory_round20.py` 现在使用独立固定的 `expected_source_hashes`，不再信任报告自身提供的哈希作为唯一预期值。
- 固定值为：
  - `promptfoo.json`：`83ab64fea30ea4f45db2df89afd7423de6ccf01bc852e58e1a7765ce86a5c94f`
  - `cases.json`：`55ab72fc651d7fd917e581162c8fa542431865cc8bb5ad398dea9bc9e13c7b6e`
- 本次独立读取冻结提交 `8b72878a41b6963fd411b1619adf308b79c439d9` 中两个 blob 并计算 SHA-256，结果与上述固定常量、报告 `source_hashes` 及当前冻结协议文件全部一致。
- CI 默认浅克隆时不依赖 `git show`，而是以已经独立核实的固定 blob SHA 常量约束当前文件，这是合理的可移植实现；冻结提交与常量的历史关系由本次独立复核确认。

### 决策投影

- 测试已按 Round 18 的既有规范，从 reviewer 的关键盲评/暴露声明、逐条 `criteria_pass` 和 `preferred_candidate` 重新构造决策投影。
- 使用 UTF-8、`ensure_ascii=false`、键排序和紧凑分隔符进行规范化后，独立重算得到 `18290d5de78ac8a32e4a00f4ebe1c54a2b24e91fbe047eb4c0d298a931e9d121`。
- 该值与报告及测试固定预期完全一致，不再是不可复算的常量声明。

### `round20-evidence-projection-v1`

新增证据投影采用明确的规范化规则，并稳定包含：

- 冻结提交与两份固定源哈希；
- reviewer 的类型、盲于实验臂映射、协议暴露和既有 Skill 修订暴露声明；
- 每条 `review_id`、`case_id`、`repetition`；
- 完整任务文本 SHA-256 与硬标准列表的规范 JSON SHA-256；
- 每名候选的 `candidate_id`、`arm_id`、Skill 包指纹、输出 SHA-256 和逐项评分布尔值；
- 每组匿名比较的偏好候选。

独立重算得到 `412449a205c54e2c0308e8f4a59e5f035d309e96daddad0af9c8191a94622c97`，与报告中的 `evidence_projection.sha256` 和测试固定值一致。候选 arm 与包指纹共同纳入，因此偏好候选可以确定映射到具体实验臂，无需重复存储派生的 `preferred_arm`。

### 报告条目与冻结题面

测试现在直接读取固定哈希约束下的 `promptfoo.json` 与 `cases.json`，逐条验证：

- 报告 `purpose` 等于冻结 case；
- 报告 `hard_criteria` 等于冻结硬标准；
- 报告完整 `task` 等于冻结 `common_prompt + "\n\n" + case.prompt`。

因此报告条目、源文件固定哈希和证据投影已经形成闭环；活动用例仍由同一测试继续逐条绑定冻结 prompt 与硬标准。

### 负向保护

新增负向测试在内存副本上分别修改：

1. 源哈希；
2. 硬标准；
3. 输出及同步更新后的输出哈希；
4. 单项评分布尔值。

四种修改重算后均不等于固定证据投影摘要。主测试同时固定源哈希、决策摘要和证据摘要，所以不能通过同步改写报告摘要规避检查。上述覆盖直接对应上一轮 P1 提出的协同修改风险。

## 聚焦测试记录

运行：

```text
python -m unittest discover -s tests -p test_claim_quantitative_confirmatory_round20.py -v
```

结果：2 项测试全部通过：

- `test_report_recomputes_scores_gate_and_current_state`：通过；
- `test_evidence_projection_detects_coordinated_mutations`：通过。

另行执行的只读复算确认冻结提交 blob 哈希、决策投影和证据投影均得到预期值。

## 最终结论

**P1 已关闭，可以通过本轮最终工程门禁。** 最新 staged 的报告与 Round 20 测试现在能够保护冻结来源、匿名评分决定、候选输出和实验臂映射之间的关键证据关系。保留原 `final-engineering-review-independent.md` 作为首次评审记录是正确的；本次未发现剩余阻塞项或非阻塞项。
