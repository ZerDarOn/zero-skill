# 第二十二轮最终独立工程复核

日期：2026-09-13
复核范围：当前工作区中第 22 轮全部待提交改动，以及冻结协议、指定运行目录和计分后独立复核所构成的证据链

## Findings

**P0：无。**

**P1：无。**

**P2：无。**

**P3：无。**

未发现阻止提交的问题。公开叙述、机器报告、活动回归和保护测试一致；当前改动可以进入提交门禁。

## 公开报告可重算性

对 `debug-evidence-boundaries-forward-15-promptfoo-20260912T183847Z-d054a8` 做了独立来源对账：

- 机器报告的 21 个 review item 与 `blind-review.json`、`blind-review-key.json`、`blind-review-completed-independent.json` 和 `review-result-blind-review-completed-independent.json` 按 `review_id` 逐项合并，题目、重复号、purpose、任务正文、四条 hard criteria、候选原文、候选身份、原始布尔、偏好和 notes 的差异数为 0。
- `promptfoo.json` 与 `cases.json` 的 source SHA-256 和 `frozen.json` 一致；准备后的 `promptfooconfig.json`、`tests.json` 哈希也与 frozen manifest 及机器报告一致。
- 八份运行产物逐文件重新计算 SHA-256，全部等于机器报告的 `artifact_hashes`：`frozen.json`、`results.json`、`summary.json`、匿名 packet、key、空表、完成评分和 scored result 均已覆盖。
- `summary.json` 的两臂运行字段与机器报告 `experiment.arms[].runtime` 逐字段一致；两臂各 21 行，全部 Promptfoo 行有效，provider error 和禁止工具行均为 0。
- 冻结前独立复核与计分后语义复核的文件哈希分别匹配 `prefreeze_review_sha256` 和 `semantic_calibration.review_sha256`。

因此，公开机器报告不是只保存汇总数字；它携带 42 份完整输出、随机化映射、原始与校准布尔和评阅说明，可从冻结 cases、匿名 packet/key、scored result 与 summary 重新形成当前分析。

## 原始评分与语义校准分层

两层结果保存清楚，没有静默改写：

- 原始层完整保留匿名评分的 `false`、notes、偏好和揭盲结果，机器报告明确引用原评分文件及其 SHA-256。
- 校准层单列 `semantic_calibration`，披露复核者看过协议和当前 Skill、并非盲评者或独立人类；六项 correction 均限定为 timeout 题第 1 条 `false → true`。
- `raw_artifacts_modified=false`、`preferences_recomputed=false` 与磁盘证据一致。校准没有删除原始层，也没有改写运行目录文件。
- 原始与校准 decision projection 分别有固定 SHA-256；校准 projection 还绑定原始 projection、六项 corrections、语义复核者和复核文件。

公开 `README.md`、`evaluations/README.md` 和 `docs/quality-polish-round-22.md` 均先报告原匿名口径，再明确说明六项计分后校准及校准口径，没有把 `71/84`、`72/84` 冒充原盲评分数。

## 分数、核心、门槛与效率复算

逐候选重算结果如下：

| 口径 | baseline | 当前 0.1.1 | 偏好与平局 |
| --- | --- | --- | --- |
| 原匿名评阅 | `68/84`，`11/21` 完整 | `69/84`，`11/21` 完整 | 各 3 次偏好，15 次持平 |
| 六项语义校准后 | `71/84`，`13/21` 完整 | `72/84`，`13/21` 完整 | 不重算偏好，仍为 3 比 3 与 15 次持平 |

规模为 21 个匿名配对、42 个输出、168 个 criterion booleans；review id 共 21 个且全部唯一。

逐题核心与冻结序号一致。原始口径为 clock `0/0`、ordered `0/0`、control `0/0`、quiet `0/0`、timeout `3/3`、GET `0/0`、decisive 诊断 `0/0`；校准后仅 timeout 变为 `0/0`。顺序均为 baseline/当前包。

两种门槛均正确为未触发：

- 原始口径中证据链组和验证等价性组没有合格题；副作用安全组的 timeout 是两臂共同 `3/3`，不满足 baseline 每题不超过 `1/3`，且同组 GET 的当前包为 `0/3`。
- 校准口径中三个组的全部核心错误均为 `0/3`，当前包没有题达到 `2/3`。
- decisive 子串题标为 `diagnostic-control`、`eligible=false`，没有进入任何两题候选组。

效率数字由两臂 summary 原值重新计算无误：总 token `209450 → 231822`，差 `22372`、增加 10.7%；prompt token 增加 10.9%，completion token 增加 5.0%，记录成本增加 21.7%，中位延迟增加 25.3%。质量文档已明确这些数字不能外推为一般成本规律。

## 证据绑定与篡改检测

机器报告和保护测试覆盖了完整的证据层次：

- source：冻结提交、模型、推理等级、协议源文件哈希；
- prepared：生成后的 Promptfoo config 与 tests 哈希；
- artifact：八份原始运行、匿名评阅和揭盲产物哈希；
- reviewer：盲评者与语义复核者的任务、模型、先验暴露、文件边界及人类独立性披露；
- semantic review：复核文件哈希、六项 correction、原产物未修改和偏好未重算；
- decision projection：原始与校准评分决定分别投影；
- evidence projection：将上述哈希、评阅者、随机化臂映射、输出哈希、两层布尔和偏好纳入同一固定摘要。

定向测试不只检查静态常量。它从嵌入候选重新计算两层总分、完整输出、逐题结果和核心错误，并将任务与 frozen cases、Skill 指纹和新 active cases 对账。负向测试覆盖 source hash、artifact hash、原始布尔、校准布尔、盲评者身份与文件边界、语义复核者身份与 note、语义复核文件哈希；其中对候选原文与 `output_sha256` 同时修改的协调篡改仍会改变 evidence projection，测试已实际通过该场景。

当前投影不把未来新增 active cases 锁死在历史总数；测试用下界允许后续轮次扩充。这不影响本次一致性，因为本轮另行精确重算为 debug 13、全仓 132，七个新增 active case 的 prompt 与 hard criteria 也逐项等于冻结版本。

## 文档、活动案例与当前状态

- `README.md` 当前阶段、`evaluations/README.md` 第 22 轮段落、质量文档和机器报告均使用 debug 13、全仓 active 132、42 输出、原始与校准两套分数以及“不打开候选”的同一结论。
- 七个 `regression-*` 案例完整保留冻结 prompt 和四条 hard criteria，并补充 synthetic input、原 comparison case id、预期路由和非空 `must_avoid`；未改变旧六题。
- `catalog/collection.json` 中 Skill 仍为 0.1.1、`experimental`、`evidence: null`，当前包指纹仍为 `5c880634b3b728ec83a26efdc7f186c33f1196a1e6c6cfce6ea29cf4d2862e72`。
- 决定层保持 `skill_changed=false`、`version_changed=false`、`candidate_design_opened=false`、新增活动案例 7；没有把诊断结果升级成 `verified`。

## 隐私、路径与结论边界

待提交公开文件中未发现本机绝对路径、用户名、线程 ID、账户信息、访问密钥或真实生产载荷。完整输出只涉及冻结的合成标识和合成故障材料。

报告明确披露两位评阅者都是模型辅助独立子代理，语义复核非盲；没有声称独立人类评审。结果限定于一个模型、一个推理等级、显式 Skill 和合成题，不外推真实生产排障、工具自主执行、隐式路由、其他模型或最终修复效果。

## 验证

- `python -m unittest tests.test_debug_evidence_boundaries_round22 -v`：3 项通过。
- `python scripts/validate_collection.py`：通过。
- `python -m unittest discover -s tests -v`：共发现 77 项，76 项通过，1 项因当前 Windows 无符号链接权限跳过。
- `git diff --check`：通过。

本次只新增本最终独立复核文件；没有修改报告、协议、测试、活动案例、文档或运行产物，没有提交或推送。

## 结论

**P0-P3 均无 findings，可以提交。** 公开报告可从冻结输入与匿名/揭盲证据重算，原始与六项语义校准分层明确，两种候选门槛、逐题核心、总分、偏好和效率数字正确。证据投影覆盖来源、准备、产物、两位复核者及两套评分，定向测试能够发现内容与配套哈希同时变化的协调篡改；文档、13 个 debug active case 和全仓 132 项计数一致，未发现隐私或结论越界。
