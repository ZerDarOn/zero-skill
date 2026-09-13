# Round 33 揭盲后独立语义校准与决策复核

日期：2026-09-14

## Findings first

### [P2] 原匿名评分包含 1 个语义假阴性

原始 144 个布尔判断中有 13 个 `false`。逐项复核后，`approved-choice-new-qualification-evidence-r3` 的 candidate B（揭盲后为 baseline）已经用等价语义满足 criterion 2：答案写明退出成本不可比、委员会未重新表决，并给出“建议重开选型；重审前原批准不变”。在明日采购会的冻结语境中，这已经把当前动作限定为重开评估且没有在成本缺口未补时完成新选型；不应因没有逐字写“明天只决定是否”而判失败。

该项只在并列的 `review-calibration-independent.json` 中由 `false` 改为 `true`。原匿名评分、揭盲结果和偏好均未修改。

其余 12 个 `false` 保持不变：3 项确实遗漏“当时只有 Atlas 确认达到 AA”这一原批准依据；2 项违反“无标题”要求并输出“成本与状态：”标签；6 项没有给出冻结 criterion 要求的 A 恢复演练完整正反分支；1 项编造“最终采购仍需财务负责人批准”的权限。没有放宽标准、增加新标准或新增扣分。

校准后没有开放 P0、P1、P2 或 P3。上述 P2 仅修正评分解释，且不改变任何逐题核心失败数、冻结 gate 或最终决定。

## 身份、盲态与读取范围

本复核由模型辅助的独立任务完成，不是本轮匿名评分者，也不是独立人工评审。复核发生在评分完成并揭盲之后，已知 candidate、arm 与 Skill 身份，因此不是盲评。偏好完全沿用原匿名评分，没有重评。

读取范围包括比较目录的 `promptfoo.json`、`cases.json`、`README.md`、`prefreeze-review-independent.md`，当前 `skills/creation/decision-brief-draft/SKILL.md` 与活动 `evaluations/cases/decision-brief-draft.json`，正式 run 的匿名包、揭盲键、完成评分、揭盲结果、summary、run-meta、frozen，以及 preflight 的 summary 和 run-meta。为核对冻结提交，只读取了 git 对象 `e9eca46` 中对应文件的字节。

没有修改 Skill、活动 cases、协议、匿名评分、揭盲键、catalog 或任何正式运行原件。

## 原始与校准汇总

正式运行包含 18 个 review、36 个候选输出和 144 个布尔判断；36/36 输出有效。原始评分为 131 个 `true`、13 个 `false`；校准后为 132 个 `true`、12 个 `false`。

| Arm | 输出 | 原始通过 | 校准通过 | 原始完整输出 | 校准完整输出 | 原始偏好 | 校准偏好 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| baseline | 18 | 63/72 | 64/72 | 10/18 | 10/18 | 0 | 0 |
| ours | 18 | 68/72 | 68/72 | 14/18 | 14/18 | 5 | 5 |

18 个 review 中有 5 个偏好 ours、0 个偏好 baseline，另 13 个为平局。更正所在输出仍有 criterion 0 的真实失败，因此 baseline 完整输出数不变。

## 逐题核心失败

一次输出只要任一 `core_criteria=[0,1,2]` 为 `false`，即计一次核心失败。校准项所在输出仍因 criterion 0 为 false 而属于核心失败，所以原始与校准结果相同。

| Mechanism | Case | baseline | ours |
| --- | --- | ---: | ---: |
| decision-history | `approved-choice-new-qualification-evidence` | 2/3 | 1/3 |
| decision-history | `cost-correction-does-not-revoke-approval` | 0/3 | 0/3 |
| constraint-and-denominator | `normalize-three-year-cost-basis` | 0/3 | 0/3 |
| constraint-and-denominator | `no-feasible-option-with-one-unknown` | 3/3 | 3/3 |
| role-and-evidence | `executive-preference-without-approval-authority` | 0/3 | 0/3 |
| role-and-evidence | `small-usability-check-does-not-prove-rollout` | 0/3 | 0/3 |

## 冻结 gate 复算

冻结 gate 要求同一机制的两题同时满足：ours 每题核心失败至少 `2/3`，baseline 每题至多 `1/3`，并且 36 份输出全部有效。

| Mechanism | ours 两题均 ≥2/3 | baseline 两题均 ≤1/3 | 原始触发 | 校准触发 |
| --- | --- | --- | --- | --- |
| decision-history | 否：1/3、0/3 | 否：2/3、0/3 | 否 | 否 |
| constraint-and-denominator | 否：0/3、3/3 | 否：0/3、3/3 | 否 | 否 |
| role-and-evidence | 否：0/3、0/3 | 是：0/3、0/3 | 否 | 否 |

两种口径下有效输出条件均满足，但没有任何机制同时满足两臂阈值。

## 决策

**不打开 `decision-brief-draft` 候选设计。** ours 的原始和校准总分均高于 baseline，完整输出与偏好也更多，但冻结 gate 专门寻找“ours 在同一机制的两题中重复特有失败、baseline 稳定通过”的模式；本轮没有出现该模式。总分优势或偏好不能替代预注册门槛。

本轮不授权修改或升版 Skill，不修改 catalog 或活动 cases。Anthropic `doc-coauthoring` 与 Witchcat `decision-records` 只作为设计来源，正式 frozen、results 和揭盲键均只有 baseline 与 ours 两臂；本结果不能外推为对这两个上游流程的质量比较。

## 运行、提交与来源一致性

冻结提交 `e9eca46` 存在，是当前 HEAD 的祖先。比较 README、protocol、cases、冻结前复核、测试与当前 Skill 的现有字节均与该提交逐字节一致。冻结提交中的活动 cases 仍是运行前 6 题；当前文件是决策后追加六个冻结题的 12 题版本，其 SHA-256 为 `c3b9d8ce75bfa24d91d550e03fcd8a67bf8024afa4cea684daace71dc5e9191e`。正式运行的 `frozen.json` 绑定：

- protocol: `a0c4124b17bb731a46f1436008dbf976b0206614f415c9967c898878bf1b2951`
- cases: `21670547b8ee96b09a0b145d06433ec34f71cad8821137ac139afd9c9b63c426`
- prepared config: `d13d1e09ba6f7d80af6992657bfe9dc1adabf2c905a63dd89eea683bd9780bbc`
- prepared tests: `e3d7fd741ff8a17652a62d8f0cd8e1550f5e8b3203ee32913fde68de3e2819ef`
- Skill 包指纹: `d66fc65cda321f4a9718c5517ff17e87f704646c9de07d9afb9cb4b4b1495c17`
- 组装与当前 `SKILL.md`: `1ef140aae7f7d154c6013fb3adabf91cd973ab9d9fd24a777c81a9f80947c938`

`run-meta.json` 记录 `--repeat 3 --no-cache`、36 个预期和实际行、36 个通过行、退出码 0 与 `completed`。独立解析 `results.json` 得到 36 行；每行 success 和 grading pass 均为 true，输出非空，raw finalResponse 与公开输出相同，36 个事件全部只有 `agent_message`，没有工具事件。结果与 HTML 哈希分别为 `6478a52cca4bbdaf14afb8f599da95ec9088cf3a0574c779fde074332d290c99` 和 `1d6e50b2992cffef35ed50b4ad908a1def24d5c9c4d7d8f564a489fa120a8032`。

preflight 只执行一次重复中的一个 case、两臂共 2 行，2/2 成功且 infrastructure valid；它只证明运行链路可用，没有进入正式质量计分。正式 summary 也标记 infrastructure valid，两臂各 18 行，provider error 与 forbidden-tool 行均为 0。

## 验证与限制

结构化校准经独立一致性检查：更正键唯一，确实对应原评分中的 false，candidate/arm 与揭盲键一致，只存在 `false→true`，13 = 1 + 12，且所有来源哈希未变。总分、完整输出、偏好、逐题核心失败和 gate 都从匿名评分、揭盲键与该更正集合重新计算。

本复核是揭盲后的模型辅助语义复核，可能受已知 arm 身份影响，不能替代新的独立人工复核。样本只覆盖六个合成、单轮、中文、显式调用、只读文本任务，一个模型和三次重复。summary 中 `rows_with_expected_skill_call` 为 0，且冻结配置明确不做隐式 Skill trace 断言，因此本轮比较不证明每条 ours 轨迹实际加载 Skill；它也不验证隐式路由、真实审批系统、文档写入、多人协作或决策效果。校准文件只是一层并列解释，不覆盖原评分。
