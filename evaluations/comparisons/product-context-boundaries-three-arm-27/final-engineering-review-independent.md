# Round 34 最终独立工程复核

日期：2026-09-14

## Findings first

最终无开放 P0、P1、P2 或 P3，可提交。

本次终审发现并修正 1 项 P2 测试完整性问题：Round 34 的 raw-present 测试原本只核对 artifact 哈希、部分 frozen 字段与匿名包映射，没有从 ignored run 独立证明正式命令唯一性、54 行输出有效性、三臂 runtime、preflight、prepared config/tests、两套实际安装包和校准原件。现已补全这些重投影检查，并加入不完整 run-meta、重复 eval、失效 summary 和失效 preflight 的协调变异负测。未修改 Skill、catalog、题目、评分、校准或活动结果。

## 复核者角色转换

本复核者是 Round 34 原始匿名质量评分者。评分时只读取 `blind-review.json` 与 `blind-review-form.json`，对 arm 映射保持盲态。本次工程复核发生在揭盲后，已知道 candidate 与 arm 身份；只校验原评分、第二任务的揭盲后复核、运行证据和发布材料的工程一致性，没有重新评分候选。

揭盲后的语义复核由第二个模型辅助任务完成。它不是原匿名评分者，只复核唯一的 `false`，并在知道 arm 身份的情况下保留原判。两个评审都是模型辅助任务，不是独立人工评审。

## 评分、偏好与校准

从匿名包、揭盲键与原完成评分重新联接 18 个 review、54 个候选与 216 个布尔，结果为：

| Arm | 输出 | 标准通过 | 完整输出 | 唯一偏好 |
| --- | ---: | ---: | ---: | ---: |
| baseline | 18 | 71/72 | 17/18 | 0 |
| ours | 18 | 72/72 | 18/18 | 1 |
| upstream | 18 | 72/72 | 18/18 | 0 |

其余 17 个 review 持平。唯一 `false` 为 `retirement-banner-does-not-collapse-cohorts-r2` 的 candidate C，揭盲后是 baseline 的 criterion 1。该答案保留了两类账户窗口，但没有明确或等价说明横幅缺少账户范围与迁移日期、不能单独推翻合同账户窗口，并预设了“横幅修正时间”。揭盲后复核保留该失败，`corrections=[]`；原始与校准分数、完整输出和偏好完全相同。

## 核心失败与 gate

按冻结 `core_criteria` 重算，原始层和零更正的校准层一致：

| Mechanism | Case | baseline | ours | upstream |
| --- | --- | ---: | ---: | ---: |
| publication-scope | `scoped-incident-does-not-revoke-availability` | 0/3 | 0/3 | 0/3 |
| publication-scope | `retirement-banner-does-not-collapse-cohorts` | 1/3 | 0/3 | 0/3 |
| stakeholder-authority | `approval-threshold-excludes-current-quote` | 0/3 | 0/3 | 0/3 |
| stakeholder-authority | `privacy-veto-is-not-purchase-approval` | 0/3 | 0/3 | 0/3 |
| bounded-evidence-update | `incompatible-studies-cannot-be-pooled` | 0/3 | 0/3 | 0/3 |
| bounded-evidence-update | `approved-document-bounded-revision` | 0/3 | 0/3 | 0/3 |

冻结 gate 只比较 ours 与 baseline：同一机制的两题必须同时出现 ours 每题至少 2/3 核心失败、baseline 每题至多 1/3，且 54 份输出全部有效。upstream 只是上下文 arm，不参与触发。ours 六题均为 0/3，所以三个机制均未触发，不打开候选设计。

## 运行、哈希与包边界

冻结提交为 `977af538a891126ad560e7286dd3cd9b778ef2ef`，存在于 `origin/main` 并是当前 HEAD 的祖先。当前 protocol、cases、本地 Skill、上游入口与许可、provenance 及 preparer 均与冻结 Git blob 和机器报告一致：

- protocol：`82731f1012a1421d3e88c7c591c836bf40bd2c3afc80a805de8477f025cfe768`；
- cases：`109c493b3a13d178d67128dd0d181d47209ffbfbfa26c6f9cdb212aac897b7de`；
- preparer：`4eca5a4c2caeffbeca6663ecf49ce8f9e293f86372593abfb3d794ea1d1b788b`；
- 本地 `SKILL.md`：`4ac3a2e079310984f19fd09688ba04b0b10259c391e2510b8f16b077131a50e1`；
- 本地包：`f821cb134112decd46c07b8b50d5fef7e03c4bbae91d6af68344e45552dbc4c5`；
- 上游 `SKILL.md`：`6dfd6bd485f62448385844cb9eceefcee0977c843d7a1c9e6077590d4e19d1ec`；
- 上游 MIT `LICENSE`：`b70d71e24e40fce5da8f4b6f9cd862096a048e433db7f3c8cac5e348e6d34591`；
- 上游 provenance：`49bab9352c7b3c6185418d9443c7f5cdc2d895d5406d7fb7b2ea415aa13d8f91`；
- 上游包：`802ecb5ec6a435db0ea22a1b95a67450bd0e4c5d3c8f3d8f8ef5525ef77c49de`；
- prepared config：`7bf0aaee00b0b4a95a48e6ea4b64638ce9880403b8a6a6c25e6a5835ae1e0957`；
- prepared tests：`54592764c1f7b8c4169ba74a9c9a913f3b95c5dfce2649181c993350dce230ac`。

正式 run 的 11 个机器报告 artifact 哈希均与 ignored 文件一致，其中原匿名评分为 `66609d37f1a7b0c354da3b642e0d1c00946d1edf9ad76a727fc2b12dc78a426d`，零更正校准为 `a4308208a071a7126940a6f2cb4a39ef55d142ef1f5fd70eee70b4d0dfdb5f5e`。公开 evidence projection 为 `522d357dad423b0a2a2a76fda1eabaf59fa14d812256f300b5bab8d540584034`。

独立解析 `results.json` 得到 54 行，三臂各 18 行；54/54 均为非空输出、Promptfoo success 与 grading pass，raw `finalResponse` 与输出一致，54 个事件均为 `agent_message`。`run-meta.json` 只记录一次 `eval --repeat 3 --no-cache`，预期/结果/通过行均为 54，失败行为 0。preflight 三臂各 1 行，3/3 成功且不计分。

prepared 目录中的 config/tests 哈希与 frozen 一致；ours 和 upstream 在 `prepared/skills` 及实际 `fixtures/.agents/skills` 中的文件清单、逐文件字节与包指纹也都与 frozen 一致。上游运行包只含 `SKILL.md` 和 MIT `LICENSE`，不含脚本；没有执行或全局安装上游内容。

## 成本、当前状态与公开边界

从 summary 重算的本轮差值为：

- ours 对 baseline：token `+12.4%`、记录成本 `+34.0%`、中位延迟 `+14.1%`；
- upstream 对 baseline：token `+28.5%`、记录成本 `+50.5%`、中位延迟 `+13.4%`；
- ours 对 upstream：token `-12.5%`、记录成本 `-10.9%`、中位延迟 `+0.6%`。

运行前 `product-context-brief` 有 7 个活动用例，当前已将六个冻结题加入，共 13 个；全仓从 178 增至 184。Round 33 历史测试现在固定当时报告的 178，同时要求当前总数不得低于 178；Round 34 测试精确固定当前 184。

Skill 正文无 diff，catalog 无 diff，仍为 0.1.0、`experimental`、`evidence: null`。README、evaluations README 与 Round 34 文档均将结果限定为六个合成、中文、单轮、显式、只读任务的接近天花板样本，没有宣称普遍优于 baseline 或上游，也没有升为 `verified`。

机器报告不含本机绝对路径、用户名或真实人物/账户资料，所有业务材料均为合成内容。新克隆可核对机器报告内嵌的输出、评分、校准、决策、来源哈希与固定 projection，但由于 Promptfoo 原始产物被 Git 忽略，不能在干净检出中独立复建 provider 事件。

## 残余限制

两个 Skill arm 的 `rows_with_expected_skill_call` 都是 0；本轮显式运行没有强制 Skill 读取 trace，不能证明每条轨迹都加载了包。upstream 在公共提示下被收窄为一次性文本整理子任务，本轮不是其完整发现、对话、版本或保存工作流排名。

样本只包含六题、一个生成模型、一个模型辅助匿名评分者和每臂三次重复。ours 与 upstream 在 72 项标准中均无失败，样本鉴别力有限。它不覆盖隐式路由、真实发布或权限系统、写盘、多轮协作、客户研究或营销效果。

## 验证

- `python -m unittest tests.test_product_context_round34 tests.test_product_context_boundaries_comparison tests.test_decision_brief_round33 -v`：17 项通过。
- `python scripts/validate_collection.py`：通过。
- `python -m unittest discover -s tests -v`：250 项通过，1 项因 Windows 本机没有创建 symlink 权限而跳过。
- `git diff --check`：通过。
- 独立只读重投影：54 行原始 results、18 个 review、216 个布尔、唯一 `false`、零校准、逐题核心失败、三机制 gate、三组成本比例、冻结 Git blob、prepared 及全部 artifact 哈希均一致。
