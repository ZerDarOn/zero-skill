# 第二十五轮质量打磨：沟通演练显式边界确认

日期：2026-09-13

## 本轮问题

第 24 轮发现：无 Skill 的回答三次主动写出真人模仿与读心限制，而 `conversation-rehearsal` 0.1.1 只用“泛化虚构”标签限定角色。该差异最终不属于当时冻结标准的失败，但形成了重复的表达清晰度偏好。本轮用全新的单义题面确认它，同时检查边界说明是否会污染纯虚构演练。

协议在模型运行前冻结于提交 `34f959447fbe3d62ebfd9edff6493eb006cc6936`。两道 `explicit-boundary-clarity` 题无条件要求先写一句简短边界，再给泛化虚构角色的一轮回应；两道 `generalized-fiction-control` 题要求直接进入纯虚构回应，不加入无关免责声明。每个机制恰好两题，每臂每题三次。

预注册门槛只看第一项硬标准。同一机制的两题都必须出现 ours 至少 `2/3` 失败且 baseline 至多 `1/3` 失败，才允许打开最小候选设计。总分、单题差异和偏好不能越过门槛。

## 第一次正式运行与基础设施修复

正式 v1 完整保留了 24 条轨迹，但只有 23/24 技术有效，因此不进入质量评分。唯一无效项是 ours 的 `generic-counterpart-no-boundary-detour` 第 2 次：显式 Skill 路径先输出一条“将使用沟通演练技能”的进度消息，随后尝试读取 Skill 文件时被只读策略拒绝，再输出最终角色回应。事件流有两条 `agent_message`，而 output-last 制品只有后一条，违反唯一消息绑定门禁。

这次失败还暴露了 summarizer 的缺陷：runner 已保存回合内的真实 thread id，但旧逻辑在无效回合停止前没有把它写到轨迹顶层，summarizer 因而把合法失败记录误判为证据不一致。提交 `a1fe2c8a9d358656c34034dc296b6289fddf117d` 做了最小修复：

- runner 在停止无效轨迹前保留已观察到的 thread id；
- summarizer 只兼容旧式“无效轨迹顶层为 null、回合证据有可验证 thread id”的形状；
- 非空伪造 thread id 仍被拒绝，技术有效标准没有放宽；
- 新增两个精确回归，确保失败可以汇总为 `infrastructure-invalid`，而不是被丢失或改写成成功。

v1 不计分，但必须作为一次 **Skill 显式调用操作可靠性观察** 保留。基础设施无效标签不等于该现象与 Skill 调用无关。

## 完整 v2 与盲评

修复后从相同 spec、cases、prepared config、prepared tests 和技能包重新运行完整 24 条轨迹，没有拼接 v1 的 23 条成功样本。v2 达到 24/24 条轨迹、24/24 个生成回合技术有效：每条轨迹都有独立 thread id、独立临时工作区和 HOME；只读沙箱、禁用网络、应用、插件与多代理；没有 `--last`、`--ephemeral`、受阻工具尝试或多消息回合。

独立盲评者只读取匿名 packet 与空白表单，完成 12 个评审项、24 个候选和 96 个布尔判断。揭盲后的独立复核逐项重读输出，并复算匿名映射、评分和门槛；没有修改原始评分。

| arm | 硬标准 | 完整输出 | 唯一偏好 |
| --- | ---: | ---: | ---: |
| baseline | 48/48 | 12/12 | 0 |
| `conversation-rehearsal` 0.1.1 | 48/48 | 12/12 | 0 |

两道显式边界题中，两臂每次都先说明不能替真人发言或精确还原、保证反应或语气、判断内心，然后交付合规的泛化回应。两道纯虚构控制题中，两臂每次都直接进入一轮角色回应，没有添加真人边界、免责声明或规则说明。

四题的两臂第一项标准失败数全部为 `0/3`，两个机制都没有 qualifying case，候选门槛为 `false`。第 24 轮的边界表达差异没有在明确要求边界句的新题面中复现；本轮也没有观察到 Skill 相对 baseline 的质量提升。

## 运行开销

v2 中 ours 相对 baseline：

- input + output token：117,076 → 129,315，增加 12,239（10.5%）；
- input token 增加 9.6%，cached input 不变；
- output token 增加 165.1%；reasoning output 从 0 增至 1,062，零基线不计算百分比；
- 每回合中位延迟：7,594 ms → 8,945 ms，增加 17.8%。

CLI 事件没有价格字段，因此不能换算实际费用；这些差异只描述本轮 24 条样本。

## 技能与仓库决定

本轮不修改 Skill。`conversation-rehearsal` 保持 0.1.1、`experimental`、`evidence: null`。原因是两臂都达到冻结上限，门槛没有触发，也没有证据支持版本、状态或 evidence 晋升。

四道确认题已晋升到活动合成回归集，沟通演练用例从 11 条增至 15 条，全仓活动用例从 144 条增至 148 条。机器报告嵌入 v2 的完整题面、输出、输出哈希、盲评分、运行统计、门槛、复核哈希和证据投影；本机原始运行存在时还会核对 v1/v2 产物哈希。

## 限制与下一步

这是单一模型、单一推理等级、四道合成单轮题和模型盲评，不能证明一般等价、真实人际效果或隐式路由质量。盲审文件边界是评审者声明，不是外部访问审计。v1 只有一次无效样本，不能估计稳定失败率；v2 没有复现，也不能证明风险已经消失。

下一轮应把“输出质量”和“显式 Skill 加载可靠性”拆成两条线。质量侧保留本轮四题作为回归；基础设施侧若再修改加载路径，应专门重复测试受限只读环境下的 Skill 发现、读取、单一最终消息和失败证据保全。

## 对应证据

- [机器诊断](../evaluations/reports/conversation-explicit-boundary-round-25-confirmatory.json)
- [冻结比较说明](../evaluations/comparisons/conversation-explicit-boundary-two-arm-18/README.md)
- [静态冻结预检](../evaluations/comparisons/conversation-explicit-boundary-two-arm-18/preflight-validation.md)
- [独立冻结前复核](../evaluations/comparisons/conversation-explicit-boundary-two-arm-18/prefreeze-review-independent.md)
- [独立揭盲后复核](../evaluations/comparisons/conversation-explicit-boundary-two-arm-18/postscore-decision-review-independent.md)
- [最终独立工程审查](../evaluations/comparisons/conversation-explicit-boundary-two-arm-18/final-engineering-review-independent.md)
