# Round 33 最终独立工程复核

日期：2026-09-14

## Findings first

最终无开放 P0、P1、P2 或 P3，可提交。

本次终审初始发现 1 项 P2 文档错误：`postscore-decision-review-independent.md` 曾声称当前活动 cases 的字节与冻结提交一致。实际上，提交 `e9eca46` 中是运行前 6 题，当前文件是决策后追加六题的 12 题版本。现已修正为两层叙述，机器报告中的 postscore 文档哈希与 evidence projection 也随之重算；评分、校准、门槛、Skill 和活动结果均未改动。

## 复核者身份与任务分层

本复核者同时是 Round 33 原始匿名评分者。原评分时只读取匿名包与空表单，对 arm 映射保持盲态，并记录 `prior_protocol_exposure=false`、`prior_skill_revision_exposure=false`。本次是揭盲后的工程一致性终审，已知道 arm 身份，只重投影原始评分与已保留的校准层，没有重新解释或更改任何布尔判断。

揭盲后的 1 项语义校准由第二个模型辅助任务完成；该任务不是原匿名评分者，但已知道 candidate 与 arm 身份。工程复核、原始盲评和身份已知的语义校准是三个不同层次，都不是独立人工评审。

## 评分、更正与偏好重算

从 `blind-review.json`、`blind-review-key.json`、`blind-review-completed-independent.json` 与揭盲结果重新联接 18 个 review、36 个候选和 144 个布尔判断，得到：

| Arm | 输出 | 原始标准通过 | 校准标准通过 | 原始完整输出 | 校准完整输出 | 唯一偏好 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| baseline | 18 | 63/72 | 64/72 | 10/18 | 10/18 | 0 |
| ours | 18 | 68/72 | 68/72 | 14/18 | 14/18 | 5 |

18 个 review 中有 5 个唯一偏好 ours，0 个唯一偏好 baseline，13 个持平。偏好没有改变布尔分数。

原始层共有 13 个 `false`。校准文件只把 `approved-choice-new-qualification-evidence-r3` 中 baseline 候选 B 的 criterion 2 从 `false` 改为 `true`；答案原文已把退出成本标为不可比、记录尚未重新表决，并把当前动作限制为重开评估，因此这是对冻结标准的语义等价更正。该输出仍有 criterion 0 失败，所以完整输出与核心失败计数不变。

其余 12 个 `false` 全部保留：3 个遗漏 Atlas 当时是唯一已确认 AA 选项的原批准依据，2 个输出在要求无标题时加了标签，6 个未给出 A 恢复演练在 4 小时内与超过 4 小时的完整正反分支，1 个编造财务负责人的批准权。结构检查确认只存在这 1 项 `false→true`，没有 `true→false`、偏好重评或原始文件覆写。

## 核心失败与两层 gate

按冻结的 `core_criteria=[0,1,2]` 直接重算，原始层与校准层均为：

| Mechanism | Case | baseline | ours |
| --- | --- | ---: | ---: |
| decision-history | `approved-choice-new-qualification-evidence` | 2/3 | 1/3 |
| decision-history | `cost-correction-does-not-revoke-approval` | 0/3 | 0/3 |
| constraint-and-denominator | `normalize-three-year-cost-basis` | 0/3 | 0/3 |
| constraint-and-denominator | `no-feasible-option-with-one-unknown` | 3/3 | 3/3 |
| role-and-evidence | `executive-preference-without-approval-authority` | 0/3 | 0/3 |
| role-and-evidence | `small-usability-check-does-not-prove-rollout` | 0/3 | 0/3 |

冻结 gate 要求同一机制的两题同时出现 ours 每题至少 2/3 核心失败、baseline 每题至多 1/3 核心失败，且 36 份输出全部有效。三个机制在原始层和校准层均未同时满足两臂阈值，因此两层都不触发 gate，不打开候选设计。

## 运行有效性与成本

正式 `results.json` 独立解析出 36 行，baseline 与 ours 各 18 行；36/36 的输出非空、`success=true`、grading pass，且 raw `finalResponse` 与可见输出相同。raw 事件共 36 个，均为 `agent_message`，无工具事件。`summary.json` 同时给出零 provider error、零 forbidden-tool row；`run-meta.json` 绑定唯一正式 `eval --repeat 3 --no-cache` 命令、36 个预期/实际/通过行与零失败行。不计分 preflight 为 2/2 成功且 infrastructure valid。

从 summary 重算 ours 相对 baseline：

- 总 token：197,946 对 174,874，`+13.2%`；
- 记录成本：0.3458544 对 0.2079536，`+66.3%`；
- 中位延迟：8,944.5 ms 对 9,043.5 ms，`-1.1%`。

这些只是本次 Promptfoo 记录，不是稳定性能基准。`rows_with_expected_skill_call=0` 也意味着此评测没有逐轨迹证明 ours 实际加载 Skill。

## 冻结、哈希与当前状态

冻结提交为 `e9eca467b68a6e7fc29a6a6a0e6e8d672b49901c`，存在于 `origin/main` 且是当前 HEAD 的祖先。重算确认：

- protocol `a0c4124b17bb731a46f1436008dbf976b0206614f415c9967c898878bf1b2951`；
- cases `21670547b8ee96b09a0b145d06433ec34f71cad8821137ac139afd9c9b63c426`；
- prepared config `d13d1e09ba6f7d80af6992657bfe9dc1adabf2c905a63dd89eea683bd9780bbc`；
- prepared tests `e3d7fd741ff8a17652a62d8f0cd8e1550f5e8b3203ee32913fde68de3e2819ef`；
- 当前 Skill 单文件 `1ef140aae7f7d154c6013fb3adabf91cd973ab9d9fd24a777c81a9f80947c938`；
- Skill 包指纹 `d66fc65cda321f4a9718c5517ff17e87f704646c9de07d9afb9cb4b4b1495c17`；
- 原始匿名评分 `314cbb432c1ad3cd62a0ea7e962f349fe4b8a7498b460cf49bf4ee338e8f525c`；
- 语义校准 `fa543531dc32aeb4e2121271c614093131f6e55e1c65d13f08f88dcf80cbd753`；
- 修正后 postscore 文档 `2b78c6afe6946d365a079ff93a869cdb94556733e9a46b2711e29c25f09537ba`；
- 修正后公开 evidence projection `7e9c258da9e6a2e7112e2bbee418cbcc6efe674b648a91041fcefd3459920f03`。

所有机器报告列出的正式 run artifact 均与本机 ignored run 逐文件 SHA-256 一致。公开报告的输出、原始布尔、校准布尔、arm 映射、运行汇总、校准来源和审查者边界可由本机原始证据重投影。报告不包含本机绝对路径、用户名或私人资料；材料均为合成内容。

运行前活动用例为 6 题，决策后将六个冻结题原样加入，当前为 12 题，SHA-256 为 `c3b9d8ce75bfa24d91d550e03fcd8a67bf8024afa4cea684daace71dc5e9191e`；全仓活动用例从 172 增至 178。`decision-brief-draft` 的 Skill 正文无 diff，仍为 0.1.1；catalog 无 diff，仍为 `experimental`、`evidence: null`。Round 31 与 Round 32 的跨轮测试现在分别锁定当时报告总数 166 与 172，同时允许后续轮次只增不减；Round 33 测试精确锁定当前 178。

## 来源、公开边界与残余限制

Anthropic `doc-coauthoring` 和 Witchcat `decision-records` 只是设计参考；冻结 protocol、prepared config、results、匿名包和揭盲键只有 baseline 与 ours 两个计分 arm。公开文档没有将本轮结果外推为对两个参考的质量排名，也如实保留了 Witchcat 固定来源的许可边界。

公开报告自包合成输出、两层评分、唯一校准、决策与哈希，因此新克隆可验证已提交的证据投影和当前状态。由于原始 Promptfoo 产物被 Git 忽略，新克隆不能独立重建 provider 事件或证明其原始性；只有保留 ignored run 的本机能做逐产物复核。

结果只覆盖六个合成、单轮、中文、显式项目级调用、只读文本任务，一个生成模型、一个模型辅助匿名评分者与每臂三次重复。它不证明隐式路由、真实审批、文件写入、多人协作、读者效果或长期决策质量，也不支持将当前 Skill 标记为 `verified`。

## 验证

- `python -m unittest tests.test_decision_brief_round33 tests.test_decision_brief_complex_comparison tests.test_debug_round32 tests.test_prose_round31 -v`：22 项通过。
- `python -m unittest discover -s tests -v`：238 项通过，1 项因 Windows 本机无创建 symlink 权限而跳过。
- `python scripts/validate_collection.py`：通过。
- `git diff --check`：通过。
- 独立只读重投影脚本：核对 36 行 raw results、18 个 review、144 个布尔、1 项校准、6 题核心失败、两层 gate、全部公开 artifact/source hash 与成本百分比，均一致。
