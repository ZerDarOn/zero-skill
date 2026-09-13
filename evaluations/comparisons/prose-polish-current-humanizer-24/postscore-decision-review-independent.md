# Round 31 揭盲后独立决策复核

日期：2026-09-14

## Findings first

**无 P0–P3 发现。** 评分文件、匿名映射、汇总数字、冻结门槛与运行有效性在允许读取的材料内一致。六个 `false` 均应保留，不需要校准；它们只反映一项局部的夸大表达收敛失败，不授权修改当前 Skill。

## 独立复算

正式运行完成 `54/54` 份输出，三个 arm 各 18 份。`run-meta.json` 记录一次 `--repeat 3 --no-cache` 的 eval，expected/result/passed 均为 54、failed 为 0；`summary.json` 显示三臂各 18 行、provider error 与 forbidden tool row 均为 0。冻结 spec、cases 与当前 `SKILL.md` 的 SHA-256 分别为：

- `promptfoo.json`: `b1109cc9fc2d69e440fdb2c4d523778d889499ab7224e1009d79b03117a92eb3`
- `cases.json`: `2fdd0ce433b9c581165800c128f9461a41f8fcbf72360fae66b21d4282f95898`
- `prose-polish/SKILL.md`: `ec8bd7f0fa2d418bec700676cc1faa169b23e1cf369ac25a8ec381f38b70f0bf`
- `frozen.json`: `ce8c24e610b18bcdb7e201b4f1960a123fe82bccf139ee97e8f450b6444bf070`，与 `run-meta.json` 一致。
- `results_sha256`: `6b4862597fda606aa09dac0e591646ef80e756cec75adc9396d557bfc657e5b6`，在 run meta 与 summary 中一致。

对 completed review、blind key 与 scored review 逐项连接后，216 个布尔均一致：

| arm | 输出 | 完整通过 | 通过标准 | 偏好 |
| --- | ---: | ---: | ---: | ---: |
| baseline | 18 | 17 | 71/72 | 1 |
| ours (`prose-polish`) | 18 | 16 | 70/72 | 0 |
| upstream (`humanizer`) | 18 | 15 | 69/72 | 0 |

唯一偏好来自 `restrained-voice-with-fixed-closing-r3` 的匿名候选 A，揭盲后对应 baseline。偏好不参与冻结候选门槛。

## 六个 false 的语义复核

六个 false 全部是 `restrained-voice-with-fixed-closing` 的 criterion index 2。该标准同时要求逐字保留末句，并删除或实质收敛原稿中的“圆满成功”和“每个人都高度赞扬”。分布如下：

| repetition | baseline | ours | upstream |
| --- | --- | --- | --- |
| r1 | false | false | false |
| r2 | true | true | false |
| r3 | true | false | false |

这些失败应保留：相关候选仍使用“很成功”“圆满结束”“顺顺利利”，并继续写“每个人都给出很高评价”“个个都说好”“大家赞扬”“每个人都赞许/夸修得好”等全员正面反应。即使个别成功措辞有所减弱，保留全员赞扬仍未满足要求收敛的另一半。

原稿本身提供了成功和全员赞扬，故这些表达不是凭空新增的活动事实或他人反应；criterion index 1 与 3 保持 `true` 是合理的。扣分只落在专门要求收敛夸大的 index 2，没有把“保留原稿事实”误判成“新增事实”，也没有用主观文风偏好扩大扣分。r2 的 baseline 与 ours、r3 的 baseline 已删除全员赞扬并把活动改为中性或较弱的“办一场/顺利开展”，因此 index 2 判 `true` 也一致。

## 逐题核心失败

任一 `core_criteria` 为 false 即计一次输出核心失败。复算结果：

| case | baseline | ours | upstream |
| --- | ---: | ---: | ---: |
| scoped-migration-plan-under-limit | 0/3 | 0/3 | 0/3 |
| triple-eligibility-with-exceptions | 0/3 | 0/3 | 0/3 |
| audit-invalidates-metric-keeps-quote | 0/3 | 0/3 | 0/3 |
| partial-rollback-keeps-schedule-revision | 0/3 | 0/3 | 0/3 |
| restrained-voice-with-fixed-closing | 1/3 | 2/3 | 3/3 |
| intentional-fragments-no-change-control | 0/3 | 0/3 | 0/3 |

## 冻结门槛

门槛要求同一机制的两道题都满足：ours 每题至少 `2/3` 核心失败，baseline 每题最多 `1/3` 核心失败，并且 54 份输出全部有效。upstream 是 context-only，不参与触发。

| 机制 | ours 条件 | baseline 条件 | triggered |
| --- | --- | --- | --- |
| bounded-condition-preservation | false（两题均 0/3） | true | false |
| revision-history-control | false（两题均 0/3） | true | false |
| author-voice-restraint | false（2/3 与 0/3） | true（1/3 与 0/3） | false |

`author-voice-restraint` 只有一题出现 ours 的重复核心失败；同机制的原样保持控制题为 0/3。根据预注册规则，不能把单题信号、总分差或 upstream 的 3/3 失败拼成机制级触发。因此 **不打开最小候选设计**，也不授权 Skill 修改、升版、catalog/evidence 变化或后验修改标准。该局部信号可保留为未来不同表面的前向观察目标。

## 评审边界

本轮只测试六个合成、单轮、文本润色任务，单一模型与推理等级，Skill 为显式项目调用。它没有验证隐式发现、真实作者满意度、编辑工作流、文件写入、发布、AI 检测规避、其他语言分布、其他模型或一般文笔排名。

匿名评分与本次揭盲复核均为模型辅助任务，不是独立人工编辑评审。本复核者也是该匿名评分文件的填写者：评分阶段对 arm mapping 保持盲态，揭盲后才连接 key；因此 arm 映射隔离成立，但 post-score 语义复核不是第二位独立评分者。六个 false 的复核保留原始判断，没有改分或重算偏好。

## 读取范围

本复核读取了：

- `evaluations/comparisons/prose-polish-current-humanizer-24/{promptfoo.json,cases.json,README.md,prefreeze-review-independent.md}`
- `evaluations/runs/prose-polish-current-humanizer-24-formal-20260914-v1/{frozen.json,run-meta.json,summary.json,blind-review-completed-independent.json,blind-review-key.json,review-result-blind-review-completed-independent.json}`
- `skills/creation/prose-polish/SKILL.md`

未读取 `results.json`、`results.html`、prepared 目录或其他未授权运行文件。

## 验证命令

```powershell
python -m json.tool evaluations/runs/prose-polish-current-humanizer-24-formal-20260914-v1/review-result-blind-review-completed-independent.json > $null
Get-FileHash -Algorithm SHA256 evaluations/comparisons/prose-polish-current-humanizer-24/promptfoo.json,evaluations/comparisons/prose-polish-current-humanizer-24/cases.json,evaluations/runs/prose-polish-current-humanizer-24-formal-20260914-v1/frozen.json,skills/creation/prose-polish/SKILL.md
```

另用只读 Python 投影按 `review_id + candidate_id` 连接 completed review、blind key 与 scored review，重算 216 个布尔、三臂聚合、逐题核心失败及三个 mechanism gate。
