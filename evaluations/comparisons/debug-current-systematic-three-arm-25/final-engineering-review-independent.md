# Round 32 最终独立工程复核

日期：2026-09-14

## Findings first

**无开放的 P0–P3 发现，可以提交。** 本次终审没有修改业务 Skill、冻结协议、原始匿名评分、揭盲映射、语义校准、catalog 或活动用例；只新增本复核记录。

公开机器报告可由本机保留的冻结文件、Promptfoo 运行摘要、匿名包、揭盲键、原始完成评分、揭盲评分结果和结构化校准文件逐项重建。在没有 ignored raw run 的新 checkout 中，固定证据投影、冻结 Git blob、公开输出及校准项仍可校验报告；不能仅凭已提交文件重建 provider 事件，这一限制已披露。

## 原始评分与校准层

- 匿名包含 18 个 review、54 个候选和 216 个布尔判断。原始汇总为 baseline `51/72`、ours `45/72`、upstream `44/72`；完整输出为 `4/18`、`1/18`、`1/18`；偏好为 `5/1/0`，另有 12 个平局。
- 原始层共有 76 个 `false`。`review-calibration-independent.json` 含 10 个唯一更正键，每个都指向原始评分中实际存在的 `false`，candidate 与揭盲 arm 对应，且全部只作 `false→true`。原始匿名评分、揭盲结果和偏好文件的哈希均未改变。
- 校准后汇总为 baseline `53/72`、ours `50/72`、upstream `47/72`；完整输出为 `6/18`、`3/18`、`4/18`。偏好继续使用原始盲评分的 `5/1/0`，没有与校准布尔重新混合为新的盲态偏好。
- 十项更正分布为 flag 四分支 7 项、完成态查询 1 项、retry attempt 事实概括 2 项。校准理由逐项保存在公开报告中；其余 66 个失败保持不变。
- 校准由第二个、揭盲后且知道 arm 身份的模型辅助任务完成。部分等价语义判断仍有可争议空间，尤其是 flag 反常分支是否必须逐字要求“先复核”；因此它被明确保留为并列解释层，不能替代原始盲评或独立人工审计。由于两种口径均不触发 gate，该不确定性不改变本轮版本决定。

## 核心失败与冻结门槛

按冻结 `core_criteria=[0,1,2]` 独立重算，原始与校准逐题核心失败均与机器报告一致：

| case | 原始 baseline / ours / upstream | 校准 baseline / ours / upstream |
| --- | --- | --- |
| `zero-five-hundreds-misses-empty-success` | 3 / 3 / 3 | 3 / 3 / 3 |
| `finished-only-query-hides-stalled-jobs` | 1 / 2 / 2 | 1 / 2 / 1 |
| `bundled-timeout-and-index-recovery` | 3 / 3 / 3 | 3 / 3 / 3 |
| `flag-cohort-confounded-by-payload-size` | 3 / 3 / 3 | 1 / 1 / 1 |
| `same-job-id-different-retry-attempts` | 1 / 3 / 3 | 1 / 3 / 3 |
| `session-id-reused-across-process-boot` | 3 / 3 / 3 | 3 / 3 / 3 |

冻结 gate 要求同一机制两题均满足 ours 至少 `2/3` 核心失败、baseline 至多 `1/3` 核心失败，并有 54 份有效输出。原始口径中 ours 的三个机制均达到自身失败条件，但 baseline 每个机制都有一题为 `3/3`，所以全部不触发。校准口径中观察覆盖和执行身份仍被 baseline 的配对失败阻断；因果区分还因 flag 题 ours 降至 `1/3` 而不满足自身条件。两层均不打开候选设计，上游继续为 context-only。

## 运行、冻结来源与包身份

- 正式 run 的 `frozen.json`、`run-meta.json`、`results.json`、`summary.json`、三个匿名制品、完成评分、揭盲评分和校准文件均匹配报告中的 SHA-256。预检 summary 哈希也一致。
- `run-meta.json` 对应一次正式 `--repeat 3 --no-cache` 运行，expected/result/passed 为 `54/54/54`、failed 为 0；summary 标记基础设施有效，三臂各 18 行，provider error 与 forbidden-tool row 均为 0。预检三臂各一行且不计分。
- 冻结提交 `674321cbe70acf6bbafd1cdafb23fda3e34d53da` 是当前 HEAD 的祖先并位于 `origin/main`。从该提交读取的协议、六题、当前 `SKILL.md` 和上游 provenance Git blob 哈希分别为 `71d0d8c4…20d`、`9ab66e76…d18`、`0e3541d6…5266`、`3d3d8044…6cfd`，与报告一致，且均为 LF。
- 当前 Skill 包指纹为 `5c880634b3b728ec83a26efdc7f186c33f1196a1e6c6cfce6ea29cf4d2862e72`；组装上游包指纹为 `17c82641ac6528efd6c1728206442de6ca345314a176a8448c351191b35ca731`。正式 prepared 的两套 Skill 副本与冻结包逐文件一致。
- 上游固定于 `obra/superpowers@b36e0829c6d0140e93cfef2ca599b1b07d4a7797`，MIT LICENSE 随包保留，七个第三方文件逐字匹配原固定 fixture。包闭合 `systematic-debugging` 的同目录引用，脚本只作为文本资源保留且未执行；`test-driven-development` 与 `verification-before-completion` 两个后续 sibling skills 明确排除，因此结论没有外推到完整 Superpowers 工作流。

## 当前仓库状态与文档

- 六个冻结 prompt 原样加入活动回归；`debug-evidence-triage` 从 13 例增至 19 例，全仓活动用例从 166 增至 172。新增项均标记为合成材料并绑定原 comparison case。
- Round 31 的跨轮测试仍固定其公开报告当时的总数为 166，同时把当前仓库断言改为 `>= 166`。这只允许后续轮次增加活动用例，仍会拒绝历史报告数字变化或总数回退；Round 32 测试另行固定当前总数为 172。
- `skills/` 与 `catalog/` 没有工作树差异。`debug-evidence-triage` 仍为 0.1.1、`experimental`、`evidence: null`，报告中的 Skill 包指纹未变。
- README、评测索引和 `docs/quality-polish-round-32.md` 同时报告原始与校准分数，明确 baseline 在两种口径下领先，没有把校准覆盖成原始盲评，也没有声称当前 Skill 或上游优于 baseline。
- 文档准确披露匿名评审有此前协议/Skill 暴露、校准为身份可见的第二个模型辅助任务、并非人工评审，以及单轮中文只读显式调用的外推边界。
- 运行成本百分比从 summary 的 tokens、记录成本和中位延迟重算一致：ours 相对 baseline 为 `+10.9% / +23.6% / +1.0%`，upstream 相对 baseline 为 `+24.0% / +55.7% / +3.7%`，ours 相对 upstream 为 `-10.6% / -20.6% / -2.7%`。文档只把它们描述为本次记录，不作为稳定性能基准。
- 新增公开材料为合成任务；扫描未发现本机绝对路径、用户名、访问密钥或真实账户资料。

## 修复

终审期间，全量测试暴露 Round 31 测试把当轮历史总数 166 误写成永久当前总数。该测试已改为同时断言 Round 31 报告仍为 166、当前总数不低于 166；Round 32 自身继续精确断言 172。该修复没有修改历史报告、业务 Skill、评分或活动用例。本独立复核另新增本记录。

## 验证命令与结果

```powershell
python -m unittest tests.test_debug_round32 tests.test_debug_current_systematic_comparison -v
# 10 tests，全部通过

python -m unittest tests.test_debug_round32 tests.test_debug_current_systematic_comparison tests.test_prose_round31 -v
# 17 tests，全部通过

python -m unittest discover -s tests -v
# 228 tests，全部通过；1 个与本轮无关的环境性 skip

python scripts/validate_collection.py
# PASS

git diff --check
# 通过，无输出
```

另以独立只读脚本按 `review_id + candidate_id` 连接匿名包、揭盲键、完成评分与 scored review，应用 10 个结构化更正后重算两层汇总、逐题核心失败、三个机制 gate、活动用例总数、包指纹、Git blob 与运行制品哈希。

## 剩余限制

- 原始匿名评阅和揭盲后语义校准均为模型辅助判断；校准知道 arm 身份，可能受身份偏差影响。公开同时保留两层是可审计边界，不等于完成独立人工复核。
- 大量失败为三臂共享，显示这些复合硬标准对单轮回答较难；本轮只能说明预注册的差异门槛未满足，不能据此断言 Skill 无需改进。
- 结果只覆盖六个合成、中文、单轮、只读诊断表面和一个模型/推理等级，不验证真实复现、系统访问、改码、测试、部署、隐式发现或完整上游工作流。
- raw Promptfoo 产物仍被 Git 忽略；新 checkout 可验证公开投影和冻结来源，但不能重建 provider 事件或实时成本。
