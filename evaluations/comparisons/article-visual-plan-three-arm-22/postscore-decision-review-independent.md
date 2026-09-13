# Round 29 独立揭盲后决策复核

## Findings first

未发现 P0、P1、P2 或 P3 问题。评分聚合、逐题核心失败、三个机制的冻结门槛、运行有效性投影和盲评声明相互一致。冻结候选门槛未触发，不应据此修改 `article-visual-plan` 0.1.0、升版或改变 catalog 状态。

## 独立重算

揭盲映射的 18 个 review ID 与匿名包、完成评分和评分结果一一对应；每项都恰有 A、B、C 三个候选，并且映射后各含 baseline、ours、upstream 一次。逐候选重新汇总得到：

| arm | outputs | perfect outputs | criteria passed | criteria total | preferred |
| --- | ---: | ---: | ---: | ---: | ---: |
| baseline | 18 | 18 | 72 | 72 | 0 |
| ours | 18 | 18 | 72 | 72 | 0 |
| upstream | 18 | 18 | 72 | 72 | 0 |

这些数字与 `review-result-blind-review-completed-independent.json` 完全一致。18 个评阅项的 `preferred_candidate` 均为 `null`；偏好没有改变任何硬标准或聚合结果。

按每题冻结的 `core_criteria` 重算，一次输出只要任一核心项为假才计一次核心失败。结果如下：

| mechanism | case | baseline | ours | upstream |
| --- | --- | ---: | ---: | ---: |
| value-based-selection | choose-zero-for-reflective-note | 0 | 0 | 0 |
| value-based-selection | choose-one-loop-not-fill-quota | 0 | 0 | 0 |
| evidence-strength | correlation-with-staffing-alternative | 0 | 0 | 0 |
| evidence-strength | qualitative-groups-not-ranked | 0 | 0 | 0 |
| plan-state-preservation | add-one-visual-preserve-existing-rows | 0 | 0 | 0 |
| plan-state-preservation | remove-one-visual-keep-id-gap | 0 | 0 | 0 |

三个机制的 ours 两题均为 `0/3` 核心失败，未达到每题至少 `2/3` 次核心失败的必要条件；baseline 同样均为 `0/3`。因此 value-based-selection、evidence-strength、plan-state-preservation 三个机制都不触发门槛。upstream 和偏好在冻结门槛中没有触发入口。

## 运行有效性与证据绑定

`run-meta.json` 记录计划与实际均为 54 行，54 行通过、0 行失败，Promptfoo 校验和正式命令退出码均为 0，状态为 `completed`。`summary.json` 将三臂各归集为 18 行，每臂 provider error 和 forbidden tool row 都为 0，`infrastructure_valid=true`，计划与执行重复数均为 3。因此在本轮公开投影层，`required_valid_outputs=54` 已满足。

交叉哈希均匹配：run metadata 绑定 frozen 文件；frozen 绑定当前 spec 与 cases；summary 与 run metadata 指向同一个 results SHA-256；summary 绑定匿名包和揭盲 key；评分结果绑定完成评分文件。关键哈希为：

- frozen：`8b31ea64f0efe0de846c98f67b9b9d80620afcd6021882a5237b29df7b69520e`
- results 投影：`f6dfc93a1c487d2ace20c9ddcb3eb01734928852e3f852c3f0f6baa942175c72`
- blind packet：`f3256b643fd17c77ec41d3f222f3dcc12bb6fc1669fcd26a879249ed2fcd2be7`
- blind key：`a3dac7bce1ef933be888066045688ead54c5998806dd10872c054421429f6135`
- completed review：`89ad323d96eeac1873cc1ae3c860ac13bfaed89646c7982598a3f78f93bc4fff`
- scored result：`3820204ae41d200fa0af09a25906c44b94ddb4702d265d44cbf1da1f95e7066a`

本次复核按授权没有读取 `results.json` 或 `prepared/`，因为上述投影与哈希之间没有矛盾。因此 54 份输出有效性结论是对 run metadata、summary 和其 results 哈希绑定的独立交叉核算，不是重新解析 raw provider rows；不可观察的预路由工具失败仍受预冻结文档所述边界限制。

## 盲态与评分时序

匿名包的结构字段没有 `arm_id`、Skill 名称或包哈希；臂信息只存在于独立 key。完成评分文件声明：`kind=model-assisted-independent-task`、`independent_human=false`、`blind_to_arm_mapping=true`，并如实记录 `prior_protocol_exposure=true`、`prior_skill_revision_exposure=true`。它只列出匿名包和空白评分表两个 allowed files，`blind_file_boundary_clean=true` 且 `unexpected_files_read=[]`。

本独立任务实际先在只读匿名边界内完成并写定评分，之后才在本次明确授权下读取 key；完成评分文件的 SHA-256 被后生成的 scored result 固定。上述过程和声明支持本次盲态，但它仍是任务级程序与评阅者声明，不是外部系统访问日志审计。`summary.json` 的 `awaiting-human-review` 是通用汇总器在评分前写入的工作流状态；实际评阅者明确不是人类，不能把该状态文字转述为人工审计。

## 对 0.1.0 与 catalog 的影响

本轮没有为 0.1.0 发现冻结门槛所定义的候选设计信号，因此不授权修改 Skill、升版或打开最小候选设计。结果可以作为固定包 `e02fed142a73421a2cc091bfea0d6faefef4c8035e671d4866e65708e9973a87` 在这六个合成规划任务上的模型辅助运行记录，但不能作为相对 baseline 或 upstream 的增益证据。

catalog 状态与 evidence 应保持现状。本轮没有独立人工评审，也没有测试实际图片、生成后端、落盘、集成或读者效果，因而不满足将 Skill 标记为 `verified` 的充分依据。本复核遵守允许文件范围，没有读取 catalog 当前内容；这里给出的是冻结决策对 catalog 的影响，而不是对 catalog 文件现状的再核验。

## 鉴别力限制

三臂在 18 次输出中均达到 72/72，形成明显的天花板效应。它证明这些明确约束、文本型、单轮合成题没有暴露失败，却无法估计 Skill 的相对提升、完整产品能力、较难边界下的稳健性，甚至不能区分“Skill 有帮助”与“题面本身已足够明确”。每题三次重复也不能弥补题目难度不足。

因此本轮正确决策是保留 0.1.0 与现有 catalog 状态，并把全满分记录为低鉴别力结果。后续若继续评测，应另行预注册更有区分度但仍可唯一评分的前向任务；不得修改或重跑本轮冻结任务来制造差异。

## 复算命令

本次使用只读 Python 脚本加载获准的 JSON，按 `review_id → candidate_id → arm_id` 合并匿名包、key 和完成评分，逐臂累加 outputs、perfect、criteria 与 preference；再从 `cases.json` 的 `core_criteria` 逐题计算核心失败，并按 `promptfoo.json` 的 decision gate 分组判断三个 mechanism。另以 SHA-256 逐项核对 spec、cases、frozen、summary、packet、key、completed review、scored result 与 run metadata 的引用。没有读取禁止的正式 results 或 prepared 目录。
