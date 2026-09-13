# 第三十四轮质量打磨：产品背景复杂边界三方前向盲测

日期：2026-09-14。本轮比较无 Skill、`product-context-brief` 0.1.0 与固定 `marketingskills/product-marketing` 2.1.0。正式运行 54/54 份输出有效；当前包与上游均为 `72/72`、`18/18` 完整通过，无 Skill 为 `71/72`、`17/18`。样本接近天花板，能说明当前包在这些边界上没有落后，不能证明普遍优于无 Skill 或上游。

## 为什么测这一组

产品背景简报此前只有七个活动用例。早期同包完整复跑为 `7/7`，但新增三题的无 Skill 组也全部通过，且评分由实施代理完成。第 34 轮因此引入六个新表面、三次重复、随机匿名候选和第二个揭盲后复核任务：

- `publication-scope`：总体正式开放与局部故障同时成立；新账户停售与已有合同账户限期可用不能被模糊退役横幅压平。
- `stakeholder-authority`：金额阈值限制当前审批权；用户、推动者、隐私否决、采购批准和付款执行需要分开。
- `bounded-evidence-update`：不同单位与结果的研究不能拼接分母；已审批文档只能修改获准章节。

独立预冻结复核替换了一道与活动题过近的“较新草稿 vs 正式记录”题，并补强活动用例哈希、三臂 home/provider、公平提示、来源文件集合和上游许可证门禁。协议、题面和 Skill 包随后冻结在提交 `977af538a891126ad560e7286dd3cd9b778ef2ef`，正式运行前没有再修改。

## 上游参照

固定上游来自 `coreyhaines31/marketingskills@5b2c0007766c6a1cf1d53fd8fc73e979e0821022` 的 `product-marketing` 2.1.0，MIT 许可证、入口原文和逐文件哈希随评测 fixture 保存。它的优势是完整营销上下文模板、对话采集、版本与变更记录；本地技能强调给定材料的证据层次、角色权限、局部更新和不自动写盘。

公共提示把两者都限定为一次性文本交付，统一跳过读取仓库、追问、保存与同步。本轮比较的是共同覆盖的文本整理切片，不是完整营销上下文工作流排名，也没有安装或执行上游脚本。

## 运行与评分

三臂使用 `gpt-5.6-sol`、medium、项目级显式调用和隔离的只读目录。单题三臂预检为 3/3 有效；正式运行每题每臂重复三次，共 54 份输出、18 个三候选匿名评阅项和 216 个布尔判断。54 行均通过 Promptfoo，provider error、forbidden-tool 行和补跑均为 0。

匿名评阅结果：

| Arm | 标准分 | 完整输出 | 唯一偏好 |
| --- | ---: | ---: | ---: |
| 无 Skill | 71/72 | 17/18 | 0 |
| 当前 `product-context-brief` | 72/72 | 18/18 | 1 |
| 固定 `product-marketing` | 72/72 | 18/18 | 0 |

另有 17 项偏好持平。唯一 `false` 出现在无 Skill 的 `retirement-banner-does-not-collapse-cohorts` 第二次重复：回答保留了两类账户和期限，但没有说明横幅缺少账户范围与迁移日期，且预设横幅需要修正。揭盲后的第二个模型辅助任务按冻结标准保留原判，零校准更正，因此原始与校准分相同。

逐题核心失败只有上述 baseline `1/3`；当前包和上游六题均为 `0/3`。三个机制都没有出现“当前包在同机制两题各至少 `2/3` 次核心失败，而 baseline 对应每题至多 `1/3`”的预注册模式，候选设计不打开。

## 成本与决定

相对无 Skill，当前包本次总 token 增加 12.4%，记录成本增加 34.0%，中位延迟增加 14.1%；固定上游分别增加 28.5%、50.5% 和 13.4%。当前包相对上游少 12.5% token、少 10.9% 记录成本，中位延迟高 0.6%。这些只是本次运行记录，不能外推为稳定效率排名。

`product-context-brief` 保持 0.1.0、`experimental`、`evidence: null`，Skill 正文和 catalog 不变。六个冻结题加入活动回归，产品背景从 7 例增至 13 例，全仓从 178 例增至 184 例。接近满分的结果更适合作为回归覆盖，尚不足以升为 `verified`。

## 证据与限制

- [冻结比较与预冻结复核](../evaluations/comparisons/product-context-boundaries-three-arm-27/README.md)
- [揭盲后语义与 gate 复核](../evaluations/comparisons/product-context-boundaries-three-arm-27/postscore-decision-review-independent.md)
- [最终工程复核](../evaluations/comparisons/product-context-boundaries-three-arm-27/final-engineering-review-independent.md)
- [自包含机器诊断](../evaluations/reports/product-context-boundaries-round-34-diagnostic.json)

机器诊断嵌入全部合成输出、匿名原判、校准记录、逐题核心失败、运行统计和来源哈希。原始 Promptfoo 目录仍被 Git 忽略，干净检出不能复建 provider 事件。

本轮只有六个合成、中文、单轮、显式调用任务，使用一个生成模型和模型辅助评阅；没有独立人工评分。显式运行没有强制 Skill 读取 trace，因此结果不证明每条轨迹确实加载了对应包。未测试隐式路由、真实发布或权限系统、写盘、多轮协作、客户研究和营销效果。
