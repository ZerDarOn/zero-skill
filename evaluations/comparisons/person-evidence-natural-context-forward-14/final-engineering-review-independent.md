# 第二十一轮最终独立工程复核

## Findings

### P2：暂存报告写入了用户专属绝对路径，不宜进入可共享证据

位置：`docs/quality-polish-round-21.md:47`、`evaluations/reports/person-evidence-natural-context-round-21-diagnostic.json:50`。

流程偏差应当披露，但初始文本把它记录为用户专属绝对路径（现规范化为 `$CODEX_HOME/skills/repo-conventions/SKILL.md`），会暴露本机 Windows 账户名并把诊断证据绑定到不可移植的个人目录。仓库约定明确不写入账户信息；机器报告也应能在其他环境中解释，而不依赖某台机器的 home 路径。路径在入库前脱敏，原发现语义不变。

如果直接提交，公开或跨机器分享补丁时会无必要地泄露本地账户标识，也会让同一语义偏差在不同机器上产生不同证据哈希。

建议把两处统一规范化为 `$CODEX_HOME/skills/repo-conventions/SKILL.md`、`<user-home>/.codex/skills/repo-conventions/SKILL.md` 或仅记录 `repo-conventions/SKILL.md`，保留“超出允许边界”的事实即可。修改机器报告后需同步重算 decision/evidence projection 哈希并更新测试常量。

### P2：评阅者证明投影没有覆盖“是否独立人类”、模型、推理等级和说明

位置：`tests/test_person_evidence_natural_context_round21.py:36-50`；被遗漏字段见 `evaluations/reports/person-evidence-natural-context-round-21-diagnostic.json:54-57`。

`reviewer_projection()` 只投影 `kind`、arm 盲性、既往暴露和文件访问偏差，没有投影 `model`、`reasoning_effort`、`independent_human` 与 reviewer `note`。decision projection 与 evidence projection 都复用这个不完整投影。

纯内存负向变异已确认：把 `independent_human` 从 `false` 改为 `true`，或改写模型、推理等级、note，当前 evidence projection SHA-256 全部保持不变；相反，改写 `file_access_boundary_clean` 会正确改变哈希。现有测试也没有对前四个字段做直接断言，因此这些重要限制声明可被静默改写而测试仍通过。

这不会改变当前 67/72、70/72 或候选门槛，但会削弱机器报告对评审身份与方法限制的完整性证明，甚至允许把模型辅助评审误标成独立人类评审。

建议把 `model`、`reasoning_effort`、`independent_human`、`note` 加入 `reviewer_projection()`，重算 decision/evidence 哈希，并至少增加 `independent_human` 与 `model` 的负向变异测试。

### P3：artifact/prepared 哈希被常量断言固定，但不属于 evidence projection 根

位置：`tests/test_person_evidence_natural_context_round21.py:70-75`、`:140-159`。

当前测试精确断言 `prepared_hashes` 与八个 `artifact_hashes` 的发布值，本次本地复核也逐项重算并确认八个运行产物全部匹配；因此当前数据没有错误。不过 `evidence_projection()` 只包含 freeze commit、source hashes、reviewer 和语义化 review 项，不包含 `prepared_hashes` 或 `artifact_hashes`。改写这些映射不会改变 evidence root，原始运行文件发生后续漂移也不会由当前单测重算发现。

若 evidence projection 被定义为“语义证据根”，当前设计可以接受，但应在报告中明确其范围；若期望一个根哈希同时证明原始产物链，应把 prepared/artifact 哈希映射加入投影并增加相应负向变异。此项不影响当前决策，列为低优先级完整性改进。

未发现 P0 或 P1 问题。上述两项 P2 修复前，不建议把当前补丁作为最终证据提交。

## 重点核对结果

### 1. 报告可从冻结输入、完整输出、布尔评分和匿名映射复算

通过。

- 冻结比较包含 6 题、2 臂、3 次重复；运行原始结果为 36 行。
- 机器报告包含 18 个配对 review、36 个候选和 144 个 criterion 布尔值。
- 将机器报告逐项与 `blind-review.json`、`blind-review-completed-independent.json`、`blind-review-key.json` 对照，task、criteria、output、score、notes、preference、arm 和 package fingerprint 的字段差异数为 0。
- 报告中的 `case_id + arm_id + output_sha256` 多重集与 `results.json` 的 36 行完全相同。
- 独立复算得到 baseline 67/72、13/18 完整、偏好 3；ours 70/72、16/18 完整、偏好 5；平局 10，与机器报告一致。

### 2. 来源、产物、决定、证据哈希和冻结提交

除 Findings 所述投影范围缺口外，当前值通过。

- freeze commit `359ef9533d8a7bc316e38659f53b18db10df5e9c` 是真实 commit，标题为 `test: freeze person evidence natural context protocol`。
- 该提交中的 `promptfoo.json`、`cases.json` Git blob 与当前冻结文件分别完全相同；当前 SHA-256 也与报告 `source_hashes` 一致。
- `frozen.json` 的 spec、cases、prepared config 和 prepared tests 哈希与机器报告一致。
- 八个 `artifact_hashes` 均已对本地原始运行产物重算，全部存在且匹配。
- 决策投影与证据投影可按测试的 canonical JSON 规则复算；输出、标准、评分、arm mapping、Skill 指纹和 freeze commit 均进入 evidence projection。
- 文件访问偏差相关字段进入 reviewer projection；`file_access_boundary_clean` 负向变异能够改变 evidence hash。

### 3. 候选门槛与 bounded 排除

通过。

- 来源机制三个案例 baseline/ours 核心错误依次为 `0/0`、`0/0`、`2/0`。
- 行动角色两个案例均为 `0/0`。
- 有限模式为 `0/0`，在报告中 `eligible: false`，且只列入 `diagnostic_only_cases`。
- 冻结门槛要求同一合格机制至少两个案例同时满足 ours `>=2/3` 且 baseline `<=1/3`。ours 六题全部为 0/3，没有任何合格案例，更不可能形成同机制两题。
- `qualifying_mechanisms` 为空、`triggered: false`，保持 0.1.2 的决定正确。偏好或非核心地点细节遗漏没有被错误用于开门。

### 4. 0.1.2 指纹、catalog、计数和回归镜像

通过。

- 当前包指纹为 `bf74c8e3288c5f5a3ca751235815089731aeed0ef3ee92b74e396251c93a33ef`；专用测试用仓库 validator 重新计算并通过。
- catalog 仍为 `0.1.2`、`experimental`、`evidence: null`，没有把诊断误标为 verified。
- `person-evidence-analysis` 活动案例当前恰为 16，全仓活动案例恰为 125。
- 六个新增回归案例全部存在，prompt 与 frozen prompt 完全相同，`must_include` 与 frozen hard criteria 完全相同；`kind: synthetic`、`comparison_case_id` 和非空 `must_avoid` 均正确，镜像差异数为 0。

### 5. Round 20 全局总数断言放宽

通过，范围合适。

`tests/test_claim_quantitative_confirmatory_round20.py` 把历史报告的全仓活动总数从恒等 `119` 改为“不低于报告快照 119”。Round 20 是历史证据测试，后续合法新增案例不应让它失败；其自身 claim suite 仍严格要求 17 例并逐项核对冻结镜像。Round 21 测试又以快照 125 建立新的下界。当前实际总数为 125，因此该改动不会掩盖从历史快照以下的删除，也没有扩大到忽略 Round 20 自身案例完整性的程度。

### 6. 文档披露

内容准确，但需修复 P2 的绝对路径。

- 文档明确披露评阅者是模型辅助而非独立人类，有协议与当前 Skill 先验。
- 明确披露额外读取通用 `repo-conventions` 文件、`file_access_boundary_clean: false`，同时没有把它误写成 arm mapping 泄漏。
- 明确限制为单模型、单推理等级、每臂 18 输出、项目级显式调用；隐式路由、真实资料、其他模型和生产使用均未测试。
- 正确说明 `summary.json` 的 Promptfoo pass 只代表执行完整，不替代正式匿名质量评分。

## 验证记录

- `python scripts/validate_collection.py`：通过。
- `python -m unittest discover -s tests -v`：74 项运行，73 项通过，1 项因 Windows 缺少符号链接权限跳过；无失败。
- `git diff --cached --check`：通过。
- 暂存补丁共 8 个文件，内容范围为 Round 21 报告、文档、活动回归、索引与两份相关测试；本复核没有修改这些既有文件。

## 最终判断

分数、候选决定、冻结输入、完整 36 输出、144 布尔、匿名映射、0.1.2 包状态和六个回归镜像均正确，Round 20 历史下界调整也合理。

**当前有两项 P2，建议修复后再提交：去除用户专属绝对路径；把完整 reviewer 方法身份字段纳入 decision/evidence projection 并补负向变异。** P3 的 artifact/prepared 投影范围可随后补强或明确文档语义。

本次只新增本评审文件，未修改其他文件。
