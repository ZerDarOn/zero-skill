# 第二十六轮质量打磨：显式 Skill 调用可靠性

日期：2026-09-13

## 本轮问题

第二十五轮第一次正式运行的 24 条 `conversation-rehearsal` 轨迹中，有一条先输出 Skill 加载进度，再尝试读取项目 Skill 文件并被策略阻止，形成两条 agent message。该运行以 23/24 技术有效保留且不计分；完整 v2 达到 24/24，但单次不复现不足以判断显式调用链是否稳定。

本轮把这个问题从回答质量中拆出，只测显式 Skill 调用和最终输出传输的运行可靠性。它不重新评分业务回答，也不允许根据运行失败直接修改业务 Skill。

## 冻结设计

协议与运行基础设施在提交 `c773fb138b8a08848a151bbd0061258a49a2e039` 冻结并推送。两个独立队列都使用 `gpt-5.6-sol`、medium、项目级显式调用、只读沙箱、隔离 HOME/CODEX_HOME，并关闭网络、apps、plugins 和 multi-agent。

- canary 对比空 fixture 与合成 `explicit-invocation-probe`。两道题各有一个只存在于 probe `SKILL.md` 的令牌；probe 必须精确返回令牌，baseline 出现令牌则视为泄漏。
- business 对比无 Skill 与 `conversation-rehearsal` 0.1.1。两道题复用第二十五轮的真人边界与纯虚构任务形状，只检查单一最终消息、事件与线程绑定、完整回合、策略阻断和过程播报。

每队列为 2 题 × 2 臂 × 10 次，共 40 条单轮轨迹，合计 80 条。任务按冻结种子 `260913` 随机提交给 4 个 worker。预检与正式目录分开；正式运行没有补跑、筛选或拼接失败。

门禁为零容忍：baseline 技术失败、canary Skill 失败、canary 令牌泄漏、business Skill 失败的上限都为 0。失败只打开基础设施调查，不能触发 Skill、版本、catalog 或 evidence 变化。

## 正式结果

两个正式队列均为 40/40 technical valid、40/40 operational success：

| 队列与臂 | 尝试 | technical valid | operational success | failure |
| --- | ---: | ---: | ---: | ---: |
| canary baseline | 20 | 20 | 20 | 0 |
| canary probe | 20 | 20 | 20 | 0 |
| business baseline | 20 | 20 | 20 | 0 |
| business `conversation-rehearsal` | 20 | 20 | 20 | 0 |

canary probe 的两个令牌各精确返回 10 次，baseline 20 条输出没有令牌泄漏。80 条轨迹均只有一条 agent message，并与 output-last 制品绑定；没有策略阻断、Skill 加载过程播报、禁止事件、超时、非零退出、损坏 JSONL 或线程与回合绑定错误。

四项门禁的观测值全部为 0，因此正式结论为 `qualified`，第二十五轮 v1 的失效没有在本轮样本中复现。

## 运行开销

business baseline 的单轮中位耗时为 `7414.0 ms`，输入加输出 token 合计 `195259`；`conversation-rehearsal` 臂为 `8984.5 ms` 与 `215422`，分别高 `21.2%` 与 `10.3%`。输出长度、缓存和并发调度都会影响这些数值，因此它们只描述本次 20 对样本，不是稳定性能基准或质量分数。

## 独立复核与证据

独立运行后复核重新走过 analyzer 的完整验证与分类路径，所得对象与保存的联合分析 JSON 完全相等。它逐字段核对 80 条 `trajectory_evidence`，并重算 source、prepared、raw artifact、任务顺序、Skill package 和 analysis 指纹。复核关闭一处文字报告中的过时未来时表述，最终没有开放的 P0–P3。

公开机器报告保存 80 条脱敏分类投影、每条输出/事件/stderr 哈希、两组运行汇总、四项门禁、原始文件哈希、复核链和固定 evidence projection。原始运行仍位于被忽略的 `evaluations/runs/`，本机存在时测试会从 raw artifacts 重新分类并比对公开报告。

## 技能与仓库决定

本轮不修改 `conversation-rehearsal`。它保持 0.1.1、`experimental`、`evidence: null`，活动用例仍为 15 条，全仓仍为 148 条。

原因是本轮只回答运行链在冻结条件下是否复现失败。canary 证明合成 probe 自身的 Skill 正文被加载；business 队列只证明输出传输和执行完整性，不能逐条证明 `conversation-rehearsal` 正文被加载，更不能证明回答质量提高。

## 限制与下一步

80/80 只说明本次主机、模型、配置和样本下没有复现，不能证明长期失败率为零。测试只有两个 canary 表面和两个 business 表面，且固定为项目级显式调用；它不覆盖隐式发现、用户全局安装、其他模型、其他推理等级或真实长对话。

下一轮应优先测试隐式发现与路由，因为现有多数高质量对照仍依赖显式加载。应先用可证明加载的合成 canary 校准发现机制，再选少量边界清晰、触发相近的本地 Skill 做无显式名字的路由对照，并把“是否加载”和“回答是否更好”继续分开报告。

## 对应证据

- [机器报告](../evaluations/reports/explicit-invocation-reliability-round-26.json)
- [冻结协议说明](../evaluations/comparisons/explicit-invocation-reliability-19/README.md)
- [正式结果说明](../evaluations/comparisons/explicit-invocation-reliability-19/formal-results.md)
- [预检记录](../evaluations/comparisons/explicit-invocation-reliability-19/preflight-validation.md)
- [独立冻结前复核](../evaluations/comparisons/explicit-invocation-reliability-19/prefreeze-review-independent.md)
- [独立运行后复核](../evaluations/comparisons/explicit-invocation-reliability-19/postrun-review-independent.md)
