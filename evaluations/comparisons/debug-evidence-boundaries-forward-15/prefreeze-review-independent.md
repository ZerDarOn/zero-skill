# 第二十二轮 debug-evidence 协议冻结前独立复核

日期：2026-09-13
复核范围：暂存区中的 `README.md`、`promptfoo.json`、`cases.json`，以及六个活动案例、`debug-evidence-triage` 0.1.1 和既往工程三方项目

## Findings

**P0：无。**

**P1：无。**

**P2：无。**

**P3：无。**

未发现阻止冻结或需要修改协议的事项。当前版本可以冻结。

## 新题与既有材料的独立性

七题没有复用六个活动案例的具体实体、字段、记录或代码，也没有复用工程三方对照的两个异步补丁项目。它们与活动案例共享技能本来要测的机制，但均加入了会改变判断路径的新变量：

| 新题 | 最近的既有案例 | 独立性判断 |
| --- | --- | --- |
| `clock-skew-trace-over-wall-time` | `trace-request-boundary` | 既有题只排除不同 request_id 的干扰；新题必须校正跨主机时钟并以 trace/span 父子关系推翻原始时间顺序，结论路径不同。 |
| `ordered-runtime-and-key-checks` | `two-ordered-checks` | 既有题追踪 locale 的两个连续边界；新题先以失败 consumer 的实际 build/flag 决定是否进入 gzip 到 object-key 的第二项检查，依赖门槛不同。 |
| `control-plane-complete-workload-old` | `local-pass-is-not-deployed-fix` | 新题加入 rollout complete 与三 consumer 部分更新、不同事件类型成功等相互冲突证据；不是旧题“线上全为旧镜像”的换名复刻。 |
| `quiet-dashboard-without-partition-reconnect` | `recovery-is-not-verification` | 新题要求同时恢复 broker 分区、同房 20 路并发重连和 session 唯一性；低并发 dashboard 安静不能替代这一复合触发。 |
| `timeout-idempotency-key-not-enforcement` | 无直接活动案例 | 同时保留提交状态未知和幂等实现未知，检查的是生产重放决策，不是一般恢复验证。 |
| `get-endpoint-has-read-repair-write` | 无直接活动案例 | 同一 request_id 的 UPDATE 审计与状态前后变化证明读形接口有写副作用，新增了隔离验证与路由/版本分支。 |
| `decisive-substring-role-reproduction` | `decisive-reproduction` | 两题都作“证据已充分时停止索要日志”的诊断，但具体机制从 falsy 默认值变为角色子串匹配，失败输入、修复和回归集合均不同。 |

工程三方对照测量的是 `memo` 与 `document` 两个合成 Python 异步项目中的补丁和回归测试产物；本轮七题只评价材料不全时的分析建议，不与那两个项目的任务形状或缺陷机制重复。

## 题面泄露与 hard criteria

- 公共提示和七个题面都没有包含任何完整 hard criterion 文本。题面给出的输出长度、检查数量、禁止执行和隐私约束属于用户任务契约，不是隐藏评分答案。
- `ordered-runtime-and-key-checks` 明示剩余解释 A/B 及缺失证据，是为了固定待区分假设；模型仍需推出先核对失败 consumer 的实际 build/flag，且只有新 normalizer 已生效才继续检查同一 `m-5` 的 normalizer 输出与对象键边界。题面没有直接给出该依赖顺序或分支结论。
- `get-endpoint-has-read-repair-write` 明示 UPDATE 审计，是判断副作用所需观察；该题实际区分的是能否拒绝生产批量调用、提出隔离单次检查并保留复现/不复现分支。明示观察不等于泄露完整合格回答。
- 每题四条标准都能仅从候选输出判定。单条内部的多个短语属于同一结论所需的紧密组成部分，例如时钟题第1条的 trace/parent、偏移换算和排除 `t-19` 共同构成“不要用原始墙钟拆断同一链”；没有把无关事实捆进核心错误计数。
- 等价答案边界充分：ordered 第1条不强制编号；时钟与 ordered 的边界检查接受语义等价方案；GET 核心不要求逐项复述 UPDATE、更新行数和状态变化；其余标准也按机制、状态或安全分支判定，而非固定措辞匹配。

## 核心映射与主要结论

README 的核心序号与 `cases.json` 当前顺序一致，且每项失败都会改变主要排障判断：

| 题目 | 核心项 | 改变的主要结论 |
| --- | ---: | --- |
| `clock-skew-trace-over-wall-time` | 1 | 是否因原始墙钟时间而错误丢弃同一 trace 的因果链。 |
| `ordered-runtime-and-key-checks` | 2 | 是否先确认新 normalizer 在失败 consumer 实际生效，再决定需要下游字段追踪。 |
| `control-plane-complete-workload-old` | 2 | 是否把控制面 complete、本地通过或非原事件成功误写成线上已修复。 |
| `quiet-dashboard-without-partition-reconnect` | 1 | 是否把未覆盖分区与并发触发的安静窗口误写成已验证解决。 |
| `timeout-idempotency-key-not-enforcement` | 1 | 是否把超时或请求头存在误当成未提交或安全去重证据，从而允许盲目重发。 |
| `get-endpoint-has-read-repair-write` | 1 | 是否忽略已经观察到的写副作用而把 GET 当作只读生产验证。 |
| `decisive-substring-role-reproduction` | 1 | 是否在单变量复现已定位子串机制时仍拒绝诊断或索要无关证据；该项只作诊断。 |

特别核对的修订均已落盘：时钟题明确 API 与 publisher 同机；ordered 题使用 gzip/object-key 且不强制编号；控制面题使用 schema/invoice consumer；GET 核心接受对同请求 UPDATE 审计或状态变化的充分等价概括。这些修订没有改变 README 中的核心映射或候选结论。

## 同机制门槛与规模复算

三组各有两个合格题型，分组与核心映射均在 README 中唯一指定：

- 证据链组要求先用可靠身份或实际运行状态建立可追踪边界，再判断字段在何处变化；对应时钟题和 ordered 题。
- 验证等价性组要求实际工作负载身份与原触发条件都被覆盖；对应控制面题和安静 dashboard 题。
- 副作用安全组要求操作名称或接口声明不能替代实际提交、去重或写入证据；对应超时幂等题和 GET read-repair 题。

对任一组，可从盲评结果机械读取两题各自指定核心 criterion 的三次布尔值，分别计算 ours 与 baseline 的错误数。只有两题同时满足 `ours >= 2/3` 且对应题均满足 `baseline <= 1/3` 才触发；两臂共同失败、跨组各失败一题或单题失败均不触发。`decisive-substring-role-reproduction` 在 README 中明确为诊断控制，没有第二个同组题，也被明文排除于候选门槛。

结构复算结果为：7 个唯一题目，每题 4 条标准，共 28 条标准；2 臂、每题每臂 3 次，因此计划输出 `7 × 2 × 3 = 42`，逐项布尔判断为 `28 × 2 × 3 = 168`。`promptfoo.json` 的模型、推理等级、公共提示和只读默认环境对两臂相同；唯一预期差异是 ours 通过项目级显式调用当前 Skill。

## 隐私、副作用与证据边界

- 所有材料均明确为合成记录；标识符 `t-82`、`m-5`、`k-77`、`c-77` 和 `x1` 不含真实账户、聊天、密钥或生产载荷。
- 公共提示禁止工具和外部资料，并禁止声称执行检查、修复、部署或数据操作。Promptfoo 规格未覆盖默认 sandbox，准备脚本因此使用 `read-only`，同时关闭网络、Web 搜索、宿主 apps/plugins 和多 agent。
- 涉及生产风险的题目都要求非写入查询或隔离环境中的合成材料；明确拒绝生产盲目重放、生产造分区、批量 GET 旧记录和真实账户施压。
- 本协议只评估分析文本与建议质量；README 已明确不把它外推为真实生产排障、开放工具安全、部署权限或最终修复效果，也不据此标记 `verified`。

## 结论

**可以冻结，无 blocker。** 未发现 P0-P3 finding；题目与既有案例有可解释的机制连续性，但没有具体材料或项目重复。hard criteria 可观察、核心计数没有被无关复述污染，三组门槛和诊断排除可机械复算，42 份输出与 168 个布尔判断配置正确，隐私和副作用边界完整。

本次只新增本复核文件；没有修改 `README.md`、`promptfoo.json`、`cases.json`、Skill 或其他协议文件，没有运行模型，也没有提交。
