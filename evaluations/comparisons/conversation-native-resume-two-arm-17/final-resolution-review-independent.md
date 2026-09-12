# Round 24 最终修订独立复核

## Findings

**未发现剩余 P0、P1、P2 或 P3 finding。** 上一份 `final-engineering-review-independent.md` 的 P1、P2、P3 均已完整解决；当前变更可以提交。

## 上轮 findings 的解决情况

### P1 — 已解决：原始盲评与公开语义校准分层保留

- 原始 `review-result-blind-review-completed-independent.json`、`native-review-analysis.json` 和全部 artifact hash 未修改。诊断明确保存 raw blind review：baseline `72/72`、`18/18`，ours `69/72`、`15/18`；原始 gate 中只有 `decline-exact-real-person-imitation` 单题 qualifying，整体仍为 `false`。
- 新增独立 `scoring-adjudication-independent.md`，逐条说明冻结 criterion 没有注册“必须另写拒绝句”。三项校准只发生在 ours 的 criterion index 0：r1 candidate B、r2 candidate A、r3 candidate A，均由 raw `false` 改为 calibrated `true`；其余候选与 criterion 均未改变。
- calibrated semantic review 可从逐候选布尔值重算为两臂均 `72/72`、`18/18`。校准 gate 的六题均为 ours `0/3`、baseline `0/3` 核心失败，没有 qualifying case，整体 `triggered: false`。
- baseline 的三次唯一偏好仍原样保留，并只解释为明确边界说明的表达清晰度偏好；它不再被写成 hard failure，也不进入 gate。
- 根 `README.md`、`docs/quality-polish-round-24.md`、机器诊断、活动用例和测试均使用同一分层口径。`postscore-decision-review-independent.md` 保留原始判断历史，并在开头明确标出其“无需校准”结论已被独立裁决取代。

### P2 — 已解决：明确为保守机制家族门槛

- 公开报告将三组统一称为“机制家族”，并明确说明 `evidence-boundary` 一题检查模拟后的证据分类，另一题检查入口处的真人模拟范围，不是同一微观行为的复现。
- raw gate 仍忠实执行冻结协议，没有事后改组或降低门槛；calibrated gate 以校准后的同一 criterion index 重新计算。两层最终布尔值均为 `false`，但原因链分开呈现。
- Round 25 建议改为两道真正匹配“明确边界说明”的全新题，并加入泛化虚构控制题；没有继续用当前家族另一题声称微观行为已复现或未复现。

### P3 — 已解决：prepared hashes 与 frozen artifact 建立关系断言

- 发布测试先固定诊断中的 prepared config/test hashes；本机原始运行目录存在时，进一步解析已受 artifact hash 约束的 `frozen.json`，断言二者分别等于 `prepared_config_sha256` 与 `prepared_tests_sha256`。
- 本次独立复算确认两组关系实际成立：config `8926237f…f9469`，tests `fb2d2593…b8d52eb`。
- 新 checkout 仍可验证提交内的 source、review-chain、嵌入输出、双层评分、gate 与 evidence projection；原始运行目录存在时再追加全部 artifact 和 prepared/frozen 关系检查。公开报告准确区分了这两层可验证范围。

## 证据链与可复算结果

- 冻结源：`promptfoo.json` 与 `cases.json` 当前字节分别匹配诊断 `source_hashes`，并匹配冻结提交 `497d06a6ac6f7afaf7c5cd9da9a784bc2a501e01`。
- 原始产物：正式运行目录中的 10 个 artifact 均匹配诊断哈希；36 条轨迹、84 个 turn、18 个匿名 review item 和两层各 144 个 criterion boolean 一致。
- raw 映射：诊断中的每个 `raw_criteria_pass`、raw review note 和 preferred candidate 与不可改 scored artifact 对应；raw 聚合为 baseline `72/72`、ours `69/72`。
- calibrated 映射：只有上述三个 `(review_id, candidate_id, arm_id, criterion_index)` 发生 `false → true`；校准清单、逐候选字段、聚合和独立裁决文件完全对应。
- 门槛：raw 层一个 qualifying case、无 qualifying mechanism；calibrated 层无 qualifying case；两层均 `triggered: false`，最终 `candidate_design_opened: false`。
- review chain：原始后评分复核、上轮最终工程复核和独立评分裁决三份文件的当前 SHA-256 均与诊断一致；raw postscore 明确标记 `conclusion_superseded: true`。
- evidence projection：按 canonical JSON 独立重算为 `7e0234465a1c9c3b7ab49bd395b4e0e2a33fb5f76e703f7de826df931c946394`，与诊断和测试常量一致。本文是对该已冻结投影的后置复核，不进入其自身 review chain，避免自引用。
- 用例晋升：六个冻结 case 的首轮公共提示、后续 user turns、hard criteria 与 active suite 一致；`must_avoid` 已改为可观察的真实失败条件，没有再把“未另写拒绝句”当作禁止项。当前 `conversation-rehearsal` 为 11 个 active case，全仓为 144。
- Skill 状态：0.1.1、`experimental`、`evidence: null` 均未变化。
- 效率：735,393→822,011 total token（+86,618，+11.8%），input +11.3%、cached input +6.6%、output +82.1%、reasoning output +229.4%、逐 turn 中位延迟 +13.1%；无价格字段，报告未推算费用。
- Round 23 兼容改动只把全仓活动数断言从固定 138 改为不小于其历史报告快照，仍保留 Round 23 自身 scope、产物、用例和决策检查，符合历史报告向前兼容目的。
- 未发现本机绝对路径、账户、密钥、真实人物材料或超出合成只读评测范围的结论。

## 验证

- 独立交叉脚本：raw scored artifact、三项校准、raw/calibrated 聚合与 gate、全部 artifact、三份 review-chain、prepared/frozen、活动用例和 evidence projection 均通过。
- `python -m unittest tests.test_native_resume_comparison tests.test_conversation_native_resume_round24 tests.test_obsidian_artifact_round23 -v`：29/29 通过。
- 最终提交前仍应运行 README 规定的结构检查、完整测试和 `git diff --check`；这些属于常规提交门禁，不改变本次“无剩余 finding”的判断。

## 提交判断

**可以提交。** 当前修订保留了不可改 raw 证据，增加了有来源、有精确映射的语义校准层，没有静默覆盖失败；公开结论、活动回归与测试均以 calibrated 72/72 为准，同时保留三次表达偏好和两层 gate。上一份最终工程复核的三个问题均已闭合。
