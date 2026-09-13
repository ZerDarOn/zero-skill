# 第二十七轮质量打磨：隐式发现宿主边界

日期：2026-09-13

## 本轮问题

第二十六轮证明项目级显式 Skill 调用在 80 条冻结轨迹中运行完整，但现有业务质量对照多数依赖显式加载。要评价自然任务能否自动触发 Skill，必须先证明宿主既能选择路由，也能读取正文；否则业务回答差异无法归因于 Skill。

本轮只做这个加载链诊断。它使用合成 probe，不评价任何业务 Skill，也不允许根据基础设施失败修改 Skill 内容。

## 冻结设计

合成 `implicit-discovery-probe` 提供“雾灯索引”和“纸鸢归档”两个自然触发表面，各对应一个只存在于 `SKILL.md` 正文的令牌。baseline 与 probe 收到逐字相同的题面，题面不含 Skill id、路径或令牌；无可用说明时必须返回 `ROUTE-NOT-AVAILABLE`。

协议与分析器在提交 `6cb20962d7ee679da829278434d07a35d3a5a101` 完成独立冻结前复核并推送。正式队列为 2 题 × 2 臂 × 3 次，共 12 条单轮轨迹，使用 `gpt-5.6-sol`、medium、项目级隐式安装、只读沙箱和 4 个 worker。

分析器把证据拆成四层：精确读取尝试证明 `route_selected`；严格输出正文令牌证明 `body_loaded`；stderr 单列 `policy_blocked`；线程、回合、消息、输出绑定和允许命令共同决定 `transport_valid`。近似路径、回答中复述路径、失败命令、缺少退出码、组合 shell 命令或空输出都不能伪造成功。

## 正式结果

12 条全部完成，无补跑、筛选或拼接。baseline 6/6 传输完整并严格返回备用值。probe 6/6 都选中了目标 Skill 路径，但 6/6 被宿主策略阻止读取正文，令牌加载为 0/6，传输有效为 0/6。

| 臂 | route selected | body loaded | policy blocked | transport valid |
| --- | ---: | ---: | ---: | ---: |
| baseline | 0/6 | 0/6 | 0/6 | 6/6 |
| probe | 6/6 | 0/6 | 6/6 | 0/6 |

每条 probe 还产生一条加载过程消息和一条最终备用消息，因此单一消息与 output-last 绑定都失败。专用 analyzer 的状态为 `route-selected-load-blocked`。

## 决定

零容忍门禁未过：probe 正文加载失败、策略阻断和传输失败均为 6，上限均为 0。后续业务 Skill 隐式质量对照已停止，基础设施调查保持打开。

本轮没有修改任何业务 Skill、版本、catalog、evidence 或活动用例。当前十六个 Skill 仍为 `experimental`，活动用例仍为 148 项。失败定位在宿主加载链，不能解释成 Skill 内容质量下降。

## 证据与限制

公开机器报告保存 12 条脱敏分类投影、原始制品哈希、完整门禁和决定。ignored raw 在本机存在时可由测试重新归一化、分类并与报告逐条比对。独立复核验证运行完整性、冻结哈希、证据分层和停止条件。

结论只适用于当前主机、模型、配置、项目级安装和两个合成触发表面。路由 6/6 不等于正文加载；这轮不评分回答质量，也不说明其他宿主版本、沙箱模式、全局安装或模型会有相同结果。

## 对应证据

- [冻结协议说明](../evaluations/comparisons/implicit-discovery-host-boundary-20/README.md)
- [冻结前预检](../evaluations/comparisons/implicit-discovery-host-boundary-20/preflight-validation.md)
- [独立冻结前复核](../evaluations/comparisons/implicit-discovery-host-boundary-20/prefreeze-review-independent.md)
- [正式结果说明](../evaluations/comparisons/implicit-discovery-host-boundary-20/formal-results.md)
- [机器报告](../evaluations/reports/implicit-discovery-host-boundary-round-27.json)
- [独立运行后复核](../evaluations/comparisons/implicit-discovery-host-boundary-20/postrun-review-independent.md)
