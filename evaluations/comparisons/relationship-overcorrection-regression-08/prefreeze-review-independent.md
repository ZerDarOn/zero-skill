# Independent pre-freeze review

- reviewer: `gpt-5.6-sol` medium
- date: 2026-09-11
- decision: **不可冻结**

## Findings

### 中：条件分支缺少完整发言人映射

- case: `conditional-options-without-clarification`
- location: `cases.json:25-29`
- problem: 题面只声明“②是我说的”或“③是我说的”，没有说明用户是否还说了其他句、其余句由谁说；但第二项标准直接把③认定为对方所说，并据此规定下一步。这与第三项标准“不进一步假定①属于谁”的边界不一致。
- consequence: 谨慎保留未定映射的合理回答可能被误判，两种条件分支也没有获得逻辑完备的输入。
- minimum fix: 为两个分支分别给出完整、互斥的逐句发言人映射，并确认两种对话序列都逻辑成立，再按该映射制定可观察标准。

### 低：门禁卡题只构成近邻迁移

- case: `disputed-access-card-handoff`
- location: `cases.json:33-39`; `README.md:3-5`
- problem: 该题仍沿用上一轮“我记得已做—对方称未收到—没有记录—共同核对—以后留确认”的相同证据结构，主要变化是把通知或文件版本替换成门禁卡。
- consequence: 可以检查已知规则是否回归，但不足以单独支撑“独立前向迁移”或较强泛化结论。
- minimum fix: 改用证据拓扑不同的来源争议；若保留本题，则在 README 中明确称为近邻迁移回归，并限制结论。

## Per-case review

- `clear-labeled-return-date-one-line`: 无发现。身份、日期和接受状态充分，标准能够公平检查是否多问或重新协商。
- `explicit-numbered-speaker-mapping`: 无发现。逐句映射明确，标准只检查可观察输出和是否重复追问。
- `conditional-options-without-clarification`: 有中等级发现，见上文；修正前阻断冻结。
- `disputed-access-card-handoff`: 有低等级发现，见上文。
- `mutual-specific-invitation`: 无发现。明确双向邀约与用户可用性足以支持简短确认，负向标准没有排除正常细节协调。
- `decline-with-concrete-alternative`: 无发现。具体替代时间构成持续协调，标准不会把正常简短确认误判为拒绝或含糊。

## Protocol review

- `promptfoo.json` 的 baseline 与 Skill 臂共享模型、reasoning effort、任务正文和运行约束；差异仅为项目级显式 `relationship-review` Skill。
- 硬标准位于 `cases.json`，未进入 `common_prompt` 或任务正文。
- 六题、两臂、三次重复的计划总数为 `6 x 2 x 3 = 36`。
- README 已说明显式加载、模型评阅、失败不重试、无隐式发现、无第三方上游及不使用真实材料；但门禁卡题若不重写，需要补充近邻迁移限制。

修正中等级发现并重新完成预冻结复核后，方可冻结、提交和运行。
