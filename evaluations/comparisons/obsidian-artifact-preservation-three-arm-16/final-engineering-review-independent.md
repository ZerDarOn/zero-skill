# Round 23 最终工程质量门禁：独立复核

结论：**复核提出的 1 项 P1 和 2 项 P2 均已解决；当前未发现 P0–P3 finding，可以提交。** 正式运行的数据、分数、成本、包指纹和元数据更正经独立复算一致；活动题、偏好表述和机器证据门禁也已完成针对性修正。

## Findings

### P1 — 所谓“协调篡改”门禁没有从正式 run/review 文件重建证据链

`tests/test_obsidian_artifact_round23.py` 只读取诊断报告内嵌的 items、哈希声明和 `evidence_projection`，再与同一个未提交测试文件里的 `EXPECTED_PROJECTION_SHA256` 常量比较。测试没有读取正式 run 目录中的 `frozen.json`、`summary.json`、`blind-review.json`、key、`artifact-checks.json`、原始/更正 review 或 corrected score result，也没有对报告列出的 13 个 `artifact_hashes` 和 4 个 `review_hashes` 重新计算实际文件哈希。

因此 `test_coordinated_evidence_mutations_are_rejected` 目前只证明“改报告但不更新投影常量”会失败。若同时修改报告中的输出/评分/哈希声明、投影和测试常量，测试可以通过，而正式运行产物完全不必变化。`docs/quality-polish-round-23.md` 所称测试会核对 13 个正式运行产物、4 份评审哈希并复算效率数字，也高于测试的实际覆盖：成本部分只硬编码抽查了若干百分比，并未从 runtime 字段完整重算三组 token/prompt/completion/cost/latency 差异。

建议修复：让测试以正式 run/review 文件为输入，逐个重算文件 SHA-256，并由 blind packet、key、artifact checks 和 corrected review 重建 18×3 输出、映射、逐标准评分与总分；直接比较原始和更正 review 的 `reviews`，以及更正前后 score result 的评分内容；从 runtime 原值公式化复算全部成本百分比。负向测试应同时更新报告的内部哈希和投影，确认它仍因外部正式产物不匹配而失败。

**Resolution：已解决。** 测试现在公式化复算三组完整效率差异，直接重算四份已提交 review 的文件哈希，并在本地正式 run 存在时逐一核验 13 个 artifact 文件。协调篡改负测会同步重算被改报告的内部 evidence projection，仍被独立固定投影及来源、包、评审文件和报告内部约束拒绝。原始 run 受 Git 忽略，fresh clone 不能独立重建这 13 份文件；文档已准确披露该限制。

### P2 — 提升到 active suite 的六题不是冻结运行任务的自包含等价物

冻结比较通过 `promptfoo.json` 的 `common_prompt` 给每题补充固定两字段 JSON、完整 `note`、简短 `message` 等输出协议；active case 只复制了 `cases.json` 的裸 `prompt`，没有带入该公共协议。尤其 `leave-unverified-target-unlinked` 要求“在 message 里”说明原因，但 active prompt 本身没有定义 `message` 字段；其余若干题也没有独立要求返回完整 Markdown。现有测试反而强制 active prompt 等于冻结裸 prompt，因此会固化这个缺口。

这不改变 10/138 的结构计数，但六条 active 回归并未忠实复现本轮正式模型任务。建议将公共协议折入每个 active prompt，或让 active runner 有被测试绑定的等价公共协议；测试应比较最终渲染后的任务语义，并验证 active 的 must-include/must-avoid 与冻结 hard criteria 的映射，而不是要求裸 prompt 字节相等。

**Resolution：已解决。** 六条 active prompt 均逐字前置冻结 `common_prompt`，固定两字段 JSON、完整 `note`、简短 `message` 和不得虚构工具操作等约束已经自包含；测试逐题绑定最终组合文本及相应 must-include/must-avoid。

### P2 — “18 项偏好全部并列”误述了一项两方最佳并列

正式结果的 18 项 `preferred_candidate` 均为 null，准确含义是“18 项均无唯一偏好”。其中 17 项三臂全标准通过；`retarget-existing-not-planned-note-r2` 是 baseline 与 ours 并列最佳、upstream 因 criterion 4 失败。README、evaluations/README 和轮次文档写成“18 项偏好全部并列”，容易被理解为 18 项三方同分，并与 72/72、72/72、71/72 冲突。

建议统一改为：“18 项均无唯一偏好；17 项三方并列，1 项 baseline 与 ours 并列最佳。”机器报告中的 `ties: 18` 也应改名为 `no_unique_preference_count` 或附上相同解释。

**Resolution：已解决。** README、evaluations/README 和轮次文档均采用准确表述；机器报告改为 `no_unique_preference_count: 18`、`three_way_equal_items: 17` 和 `two_way_best_tie_items: 1`，测试重新约束这些计数。

## 已通过的独立核对

- 正式 run 有 18 个任务、54 份候选输出；报告内嵌了全部输出和 expected note。逐项对照 blind review、key、artifact checks 和 corrected review，任务、criteria、arm 映射、exact artifact 与评分均无差异。
- 独立复算总分：baseline 72/72、ours 72/72、upstream 71/72；完整通过数分别 18、18、17。唯一失败确为 `retarget-existing-not-planned-note-r2 / upstream / criterion 4`：输出消息只说改为“路线图”，没有按冻结标准区分“已确认改名”和“仅计划目标”。其余通过项抽查未发现语义误判。
- 三臂所有 case/mechanism 的 criterion 1 均为 0/3 失败；不满足打开本地 0.1.1 设计的冻结门槛。
- 报告中的成本变化均可由正式 runtime 复算：ours 相对 baseline 为 tokens +87.3%、prompt +85.6%、completion +239.1%、cost +116.9%、latency +67.7%；upstream 相对 baseline 为 +52.2%、+51.0%、+169.0%、+107.8%、+38.6%；ours 相对 upstream 为 +23.0%、+23.0%、+26.1%、+4.4%、+21.0%。
- 报告列出的 13 个正式运行产物哈希和 4 个评审文件哈希与当前文件实际字节一致。机器报告的 54 个 output SHA-256 和 expected-note SHA-256 也与其内嵌文本一致。
- 元数据更正透明：原始 review 与 metadata-corrected review 的 `reviews` 完全相同；原始与 corrected score result 的评分内容不变，只更新 reviewer 元数据及相应哈希。
- 冻结 comparison 与提交 `4f05815` 一致。当前/准备后的 ours、upstream 包文件和 manifest 指纹一致；上游 fixture 提交、MIT provenance、根 LICENSE 到包内 LICENSE 的字节复制关系闭合。
- active suite 的结构计数为 Obsidian 10、全仓 active 138。文档明确把结论限制为合成、只读文本制品测试，并明确没有真实 vault、渲染或隐式路由证据；未发现将本轮夸大为这些能力已验证的表述。

## 验证记录

### 推送后发现与解决

首个 push 的 GitHub Actions run `34716719510` 在 Ubuntu acceptance tests 失败。父代理随后用 `git archive` 生成的 clean checkout 复现：`test_prefill_run_rejects_frozen_cases_path_outside_repository` 假设受 Git 忽略的 `evaluations/runs` 目录已经存在，因此在干净检出中于测试准备阶段失败。这是测试夹具的目录前置条件遗漏，不是产品逻辑或冻结证据失败。

**Resolution：已解决。** 测试现在先执行 `runs_root.mkdir(parents=True, exist_ok=True)`，不再依赖工作树残留目录。修正后 prefill 定向测试 7/7 通过，本地主树全量测试 88 通过、1 跳过；`git archive` clean checkout 全量测试 88 通过、2 跳过。clean checkout 多出的跳过项正是受 Git 忽略的 Round 23 raw run 不存在时跳过本地 artifact 哈希核验，与本报告已披露的证据限制一致。该推送后 finding 已关闭，不改变最终 P0–P3 判断。

- `python -m unittest tests.test_obsidian_artifact_round23 -v`：修正后独立重跑，4/4 通过；本地 raw run 存在，13 个 artifact 哈希测试实际执行而非跳过。
- `python -m unittest discover -s tests -v`：父代理修正后重跑为 88 通过，1 跳过，0 失败；跳过项为 Windows symlink 权限条件。
- `python scripts/validate_collection.py`：通过。
- `git diff --check`：通过。
- 未运行模型，未修改协议、Skill 或运行产物，未提交或推送。

## 门禁判断

- P0：无。
- P1：无；原 1 项已解决。
- P2：无；原 2 项已解决。
- P3：无。

最终判断：在本次审查范围内，Round 23 的数据、文档、活动回归与工程门禁相互一致，可以提交。已知限制是原始 run 由 Git 忽略，fresh clone 只能核验自包含报告、冻结来源、已提交 review 和包指纹，不能脱离本地 run 目录重建原始服务输出；该限制已明确披露。
