# Debug evidence boundaries forward 15

本轮复测 `debug-evidence-triage` 0.1.1 在未见合成故障材料中能否稳定保持证据链、验证等价性和副作用安全边界。历史诊断主要是已知问题、单次采样；工程三方对照又在完整小项目中三组全过，均不能回答材料不全时的建议质量是否有稳定差异。本轮先冻结新任务，不先修改 Skill。

七个任务分为三组可触发机制和一个诊断控制：

- 证据链：跨主机时钟偏移下按 trace/span 追踪；两项依赖检查先确认实际 consumer 配置，再追踪压缩字段到对象键。
- 验证等价性：schema 控制面完成但实际 consumer 仍旧；安静 dashboard 没有覆盖原分区与并发条件。
- 副作用安全：超时请求带幂等键但未证明去重；名为 GET 的接口实际出现 read-repair 写入。
- 诊断控制：决定性子串最小复现已经足够时，应直接给小范围修复并服从两句限制。该组只有一个题，只作诊断，不能单独触发候选。

两臂使用相同的 `gpt-5.6-sol`、`medium`、任务正文和只读隔离环境。当前 0.1.1 通过项目级显式 Skill 调用；每题每臂重复三次，共42份输出、168个布尔判断。Promptfoo 执行通过只表示输出和基础设施完整，质量分必须来自完成的匿名逐项评阅。

## 核心标准与候选门槛

每题四项硬标准，以下一项作为会改变主要排障判断的核心标准：

- 证据链：`clock-skew-trace-over-wall-time` 第1项；`ordered-runtime-and-key-checks` 第2项。
- 验证等价性：`control-plane-complete-workload-old` 第2项；`quiet-dashboard-without-partition-reconnect` 第1项。
- 副作用安全：`timeout-idempotency-key-not-enforcement` 第1项；`get-endpoint-has-read-repair-write` 第1项。
- 诊断控制：`decisive-substring-role-reproduction` 第1项，仅记录，不参与候选门槛。

只有同一合格机制的两个不同题型都满足以下条件，才打开 0.1.2 候选设计：当前 0.1.1 在每题至少出现 `2/3` 核心错误，baseline 在每个对应题型均不超过 `1/3`。单次失败、不同机制各失败一题、偏好或格式差异、两臂共同失败，以及诊断控制失败，都不能触发。达到门槛也只授权设计最小候选，不直接修改、升版或发布。

## 冻结前检查

协议提交前独立检查与复核应确认：是否与六个活动案例或既往工程项目重复；题面是否把结果预先告诉模型；硬标准是否可从材料观察且接受语义等价答案；核心项是否真正改变证据边界、验证状态或副作用判断；条件分支是否要求合理；候选门槛是否可机械复算。

本轮不测试真实生产排障、工具自主执行、部署权限、真实客户数据或最终修复效果。结果也不能单独建立一般 Skill 排名或 `verified` 证据。

准备命令：

```sh
python evaluations/promptfoo/prepare_skill_comparison.py --spec evaluations/comparisons/debug-evidence-boundaries-forward-15/promptfoo.json
```

运行、匿名评阅和揭盲步骤见 [Promptfoo 评测说明](../../promptfoo/README.md)。
