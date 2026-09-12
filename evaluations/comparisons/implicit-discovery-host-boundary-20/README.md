# 隐式发现宿主边界

这是第 27 轮冻结候选，只诊断自然提示下的项目 Skill 路由选择与正文加载，不做业务回答质量比较。

第 13 轮的 Promptfoo SDK canary 没有观察到成功 `SKILL.md` 读取。第 26 轮确认项目级显式调用在 80 条冻结轨迹中运行完整后，本轮重新用原生 CLI 隔离链测试隐式发现。2026-09-13 的不计分 exploratory 显示：模型能选择合成 `discovery-token` 并尝试读取精确 Skill 路径，但只读策略阻止读取，最终没有返回正文令牌。将 cwd 与 HOME 移到仓库授权根并在 wrapper 中实际请求 `workspace-write` 仍被宿主策略阻止；不再尝试无沙箱模式。

正式候选使用一个新的合成 `implicit-discovery-probe`，提供两个自然触发表面和两个只存在于 `SKILL.md` 正文的令牌。baseline 与 probe 收到逐字相同的提示；提示不出现 Skill id、路径或令牌。每题每臂重复三次，共 12 条单轮轨迹。

分析器分开记录：

- `route_selected`：`command_execution` 或显式 `exec_command failed` stderr 出现边界完整的 `.agents/skills/implicit-discovery-probe/SKILL.md` 路径；
- `body_loaded`：最终输出严格等于该题冻结令牌；
- `policy_blocked`：stderr 出现策略阻断；
- `transport_valid`：线程、回合、JSONL、单一最终消息和输出绑定完整，且没有非预期命令。

零容忍门禁要求 baseline 不选中路由、不泄漏令牌、没有策略阻断、传输完整并返回冻结备用值；probe 每次都选中路由、加载正文、没有策略阻断且传输完整。门禁未过时停止，不运行任何业务 Skill 隐式质量对照。无论结果如何，本轮都不授权修改 Skill、版本、catalog、evidence 或活动用例。

预检与正式运行必须使用不同目录，失败不重试、不筛选、不拼接。正式运行只有在协议、分析器、包和运行基础设施哈希冻结并通过独立复核后才能开始。
