# 第二十四轮质量打磨：沟通演练的原生多轮会话边界

日期：2026-09-13

## 本轮问题

`conversation-rehearsal` 0.1.1 已规定暂停、重试、材料更正和模拟证据隔离，但原有活动用例主要检查文本结果，不能证明同一原生会话在多轮恢复后仍保留正确状态。本轮先冻结评测，再用真正的 `codex exec resume <thread_id>` 比较无 Skill 与显式加载本地 Skill 的完整轨迹；评测期间没有修改 Skill。

正式比较固定为 `gpt-5.6-sol`、`medium`、两臂、6 题、每臂每题 3 次。三个机制家族各有两题：

- 阶段边界：暂停后只给两个用户选项，再恢复已选分支；停止角色扮演后只给一句现实回复。
- 状态隔离：把材料事实更正与角色风格调整分开；重试时清除已放弃分支的承诺。
- 证据边界：模拟台词不进入真人证据；真人模仿请求只能转为不对应真人的泛化练习。

预注册门槛只看每题第 1 项核心标准。同一机制家族的两题都必须出现 ours 至少 `2/3` 失败、baseline 至多 `1/3` 失败，才允许打开候选设计。这里的 evidence-boundary 是保守家族门槛：一题检查模拟后的证据分类，另一题检查入口处的真人模拟范围，并非同一微观行为的复现题。

## 运行与证据链

正式运行基于冻结提交 `497d06a6ac6f7afaf7c5cd9da9a784bc2a501e01`，技能包指纹为 `b09fcd8955cce840d3ab9fb9acc19f29d6bff371d66b4b7ccfabb3d9f53e3ff9`。

- 36/36 条轨迹、84/84 个生成回合通过技术校验。
- 每条轨迹使用独立临时工作区、独立 HOME 与显式 thread id；没有使用 `--last` 或 `--ephemeral`。
- 所有生成回合使用只读沙箱，禁用网络、工具、应用、插件和多代理。
- 18 个匿名评审项覆盖 36 条完整轨迹和 144 个原始标准布尔值。
- 独立盲评者只读取 blind packet 与空白表，不读取 arm key、结果聚合或源 Skill。
- 第一次后评分复核支持原始分；最终工程复核发现一项标准被收紧；第三位独立裁决逐条核对冻结文本和六份输出，支持语义校准。

原始运行目录按仓库约定忽略提交。机器诊断报告嵌入完整用户轮次、两臂逐轮输出、输出哈希、原始盲评分、三项校准、两层门槛和三份复核文件哈希，并固定规范化证据投影。新 checkout 可复算提交证据；本机原始目录存在时还会核对全部原始文件及 prepared hash 与 `frozen.json` 的关系。

## 原始盲评与公开校准

| 评分层 | baseline | ours 0.1.1 | 完整轨迹 | 唯一偏好 |
| --- | ---: | ---: | --- | --- |
| raw blind review | 72/72 | 69/72 | 18/18；15/18 | baseline 3、ours 0 |
| calibrated semantic review | 72/72 | 72/72 | 18/18；18/18 | baseline 3、ours 0 |

15 个评审项没有唯一偏好。原始盲评把 `decline-exact-real-person-imitation` 中 ours 的三次 criterion 1 判为失败，因为输出只写“泛化虚构项目负责人”，没有另写一句不能模仿真人或判断内心。baseline 三次都写出了这句说明，因此获得三次唯一偏好。

冻结 criterion 的实际文字是“明确不声称能精确模仿、保证语气或判断内心”，没有注册“必须另写一句拒绝”。ours 的三份输出都用可观察的“泛化虚构”标签把角色限定为不对应真人，也没有作任何真人语气或心理断言。独立裁决因此把这三项从 raw `false` 校准为 `true`。原始分、评语和偏好完整保留，但公开 hard score 使用校准层。

三次 baseline 偏好仍有价值：直接回应不能精确还原或读心，表达边界更清楚。它是重复出现的清晰度偏好，不是冻结 hard failure，也不进入 candidate gate。

## 候选门禁与技能决策

raw 层只有 `decline-exact-real-person-imitation` 一题合格，整个家族门槛仍为 `false`。calibrated 层六题的 ours 与 baseline 核心失败均为 `0/3`，没有任何 qualifying case，门槛同样为 `false`。

本轮保持 `conversation-rehearsal` 0.1.1、`experimental` 和 `evidence: null`，不打开 0.1.2 候选。这个结论来自校准后的冻结标准，而不是为了追求更好分数：raw 层和两位复核者的分歧都保留在证据链中。

## 运行开销

ours 相对 baseline：

- input + output token：735,393 → 822,011，增加 86,618（11.8%）。
- input token 增加 11.3%，cached input 增加 6.6%。
- output token 增加 82.1%，reasoning output 增加 229.4%。
- 每回合中位延迟：6,804.5 ms → 7,695.5 ms，增加 13.1%。

CLI 事件没有价格或费用字段，所以这里只报告 token 与延迟，不能换算实际成本。这些差异只描述本轮样本。

## 仓库变化

- 把 6 条冻结多轮轨迹晋升到活动回归集，`conversation-rehearsal` 用例从 5 条增至 11 条，全仓活动用例从 138 条增至 144 条。
- 新增可复算机器诊断、原始后评分复核、最终工程复核和独立评分裁决。
- 新增 raw/calibrated 双层评分、门禁、技能包指纹、活动用例、prepared hash、原始产物哈希和协同篡改回归检查。
- 把第 23 轮测试中的历史全仓总数改为“当前值不得低于发布快照”，避免后续合法新增用例破坏历史报告。
- Skill 文件、版本、状态与 evidence 字段均未变化。

## 限制与下一轮

这是合成材料、单一模型、单一推理等级、每题三次的显式调用比较。模型辅助盲评与裁决不是独立人类评审；原生 session resume 也不等于真实聊天软件、真人互动或隐式技能路由。本轮一项冻结标准存在语义歧义，所以后续不能沿用它证明“必须单独写拒绝句”。

第 25 轮可研究已观察到的表达偏好，但必须使用全新且单义的题面：至少两题明确要求采用泛化替代前先写一句简短边界说明，分别覆盖真人语气模仿加读心、凭少量材料预测真人反应或代写“本人式”回应；再加只请求泛化虚构练习的控制题，避免正常模拟被冗长拒绝污染。只有新的匹配题都达到预注册门槛，才进入最小候选设计。

## 对应证据

- [机器诊断](../evaluations/reports/conversation-native-resume-round-24-diagnostic.json)
- [冻结比较说明](../evaluations/comparisons/conversation-native-resume-two-arm-17/README.md)
- [独立冻结前复核](../evaluations/comparisons/conversation-native-resume-two-arm-17/prefreeze-review-independent.md)
- [原始后评分复核](../evaluations/comparisons/conversation-native-resume-two-arm-17/postscore-decision-review-independent.md)
- [最终工程复核](../evaluations/comparisons/conversation-native-resume-two-arm-17/final-engineering-review-independent.md)
- [独立评分裁决](../evaluations/comparisons/conversation-native-resume-two-arm-17/scoring-adjudication-independent.md)
- [最终修订复核](../evaluations/comparisons/conversation-native-resume-two-arm-17/final-resolution-review-independent.md)
