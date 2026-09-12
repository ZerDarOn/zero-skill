# 第 23 轮运行前独立复核

结论：**暂不建议冻结或运行**。发现 3 项需要在冻结前处理的问题，其中 2 项会直接影响本轮声明的评测边界或第三方包许可闭包，1 项削弱匿名预填的可审计性。除此之外，六题的 expected artifact、末尾 LF、prompt 隔离、评分规模、候选门槛、隐私和副作用边界均能复核。

## Findings

### [P1] `retarget-visible-wikilink-only` 重复了现有活动题的核心任务

- 位置：`cases.json` 的 `retarget-visible-wikilink-only`；既有 `evaluations/cases/obsidian-note-edit.json` 的 `repair-known-link`。
- 问题：两题都给出已确认的旧名到新名映射，要求只改正文可见 wikilink 的目标、保留显示别名，并逐字保留同名普通文本和 fenced `text` 代码块。新题增加了 frontmatter、Obsidian 注释、块目标和块 ID，但核心决策、正确动作和主要保护模式与旧题相同。它也高度贴近本地 Skill 的 `references/example.md`。
- 后果：README 中“六题没有复刻现有四个活动用例”的冻结条件不成立；`protected-bytes` 机制的一半样本不能作为独立前向题，且 ours 臂可能因包内近似示例获得额外提示优势。
- 要求：替换该题的核心决策，而不只是继续增加受保护区域。新题应覆盖旧活动题和包内示例未直接演示的窄编辑，例如保留复杂别名/转义/多块结构时修改另一类独立构件；替换后重新做旧题与包内示例对照。

### [P1] prepare 后的 upstream Skill 副本没有携带 MIT 许可文本

- 位置：`promptfoo.json` upstream `source` 指向固定提交下的 `skills/obsidian-markdown` 子目录；`prepare_skill_comparison.py` 只复制 `source` 内文件。
- 问题：源 fixture 根目录的 `LICENSE`、`provenance.json`、提交和五项逐文件哈希是完整且相互一致的，定向测试也验证了这些本地字节。但 prepare 草案中的两份 upstream Skill 副本只包含 `SKILL.md` 和三个 references，均没有 `LICENSE`。冻结清单同样只记录这四个 Skill 文件。MIT 文本要求版权和许可声明随软件副本或实质部分保留。
- 后果：仓库内源 fixture 的 provenance 闭合，但实际准备给第三方臂的复制包没有形成独立的许可闭包；若 run 目录被保存或交付，不能只依赖源 fixture 祖先目录中的许可证来说明该副本已携带声明。
- 要求：让 prepare 产物在 upstream snapshot 与项目级安装副本可审计地携带 MIT `LICENSE`，并把它纳入冻结文件清单/哈希；或者采用等价、明确且可测试的许可随附方案。修改后增加针对 prepare 产物的许可存在性与哈希测试。

### [P2] 预填脚本没有拒绝携带臂身份的“盲”输入

- 位置：`prefill_artifact_review.py:97-206`，尤其是候选读取与 `arm_mapping_opened: false` 的生成；`tests/test_obsidian_artifact_comparison.py:32-100`。
- 问题：脚本只从候选复制 `candidate_id` 和 `output`，因此正常输入下生成的 checks 不含 `arm_id`，也只写第 1 个布尔值，其他三项保持空白。但它没有验证 packet、item、candidate 或 blank form 中不存在 `arm_id`、`arm_mapping`、真实 provider label 等身份字段。即使输入已携带映射，脚本仍会产出 `arm_mapping_opened: false`。现有测试只覆盖干净输入和输出中没有 `arm_id`，没有覆盖拒绝带身份字段的输入。
- 后果：`arm_mapping_opened: false` 目前是未验证的声明，而不是由输入不变量推出的证据；异常或误生成的 packet 可能在预填阶段揭盲而不被脚本报告。
- 要求：对允许的盲 packet/form 结构做白名单校验，至少拒绝各层级的臂身份和映射字段，并补充负向测试。保留现有“所有值必须为空才预填”检查；它已经能防止覆盖第 2–4 项或既有第 1 项。

## 通过项

- **expected artifact 唯一性**：六题都把修改位置、目标文本和必须逐字保留的范围定死；`expected_note` 可由任务唯一推出。第 5 题是有界 no-op，完整 note 唯一，`message` 允许合理措辞差异并由第 3/4 项人工判断。
- **末尾 LF**：六个 `expected_note` 都以恰好一个 LF 结束且不含 CR。`exact_note_match` 只接受完全一致或候选恰好少这个终止 LF；额外 LF、内部空行变化和 CRLF 均失败。相关负向测试通过。
- **prompt 泄漏**：prepare 草案的 18 个测试中，hard criteria 在模型 prompt 的命中数为 0，criteria 只在 metadata 中。除第 5 题外，没有 `expected_note` 命中 prompt；第 5 题三臂各有一次命中，是因为正确结果就是用户提供的原笔记，属于 no-op 输入文本本身，不是 prepare 注入隐藏 `expected_note`。prepare 产物没有复制 `cases.json` 到候选 fixture。
- **机械预填范围**：正常盲输入下只写 `criteria_pass[candidate][0]`，并要求所有四项原先均为 `null`；偏好和 notes 不被修改。它记录原始输出、expected note 和实际 note 的 SHA-256，以及 JSON 解析/字段形状状态。需先修复上面的匿名输入校验缺口。
- **三臂包**：baseline fixture 为空；ours 完整包含 `SKILL.md` 与其唯一相对引用；upstream 完整包含入口引用到的 `PROPERTIES.md`、`EMBEDS.md`、`CALLOUTS.md`。三臂均为项目级显式调用，模型、推理强度和公共任务正文一致。upstream 的许可随附问题见 finding。
- **门槛可复算**：每题有固定 `mechanism`，门槛明确限定 ours 与 baseline，要求同一机制的两个不同题分别满足 ours 制品失败至少 `2/3` 且 baseline 不超过 `1/3`。机械第 1 项、case/repetition、揭盲映射和机制字段足以逐题重算；upstream、偏好和第 2–4 项不进入门槛。
- **规模**：prepare 生成 18 个 case-arm 测试定义（每臂 6 个），冻结 `repetitions=3`；运行器按冻结 repeat 执行时得到 `18 × 3 = 54` 份输出。每份 4 项 hard criteria，因此是 216 个布尔判断；匿名评阅项为 `6 × 3 = 18`，每项三候选。
- **隐私与副作用**：任务材料为合成笔记，使用 `example.test`，未见本机路径、账户、密钥或真实 vault 信息。冻结约束为 `read-only`、network false、web search disabled、host apps/plugins false，且提示明确禁止工具与保存/扫描/渲染声明。README 清楚限定这里只验证返回的文本制品，不能证明真实 Obsidian 工作区编辑、存在性扫描、渲染或插件集成，未把结构测试或草案 prepare 夸大为模型行为证据。

## 验证记录

- `python -m unittest tests.test_obsidian_artifact_comparison -v`：4/4 通过。
- `python evaluations/promptfoo/prepare_skill_comparison.py --spec evaluations/comparisons/obsidian-artifact-preservation-three-arm-16/promptfoo.json --output <临时目录>`：成功；仅检查草案，未调用模型，检查后已删除临时目录。
- 草案检查：18 个测试定义；baseline/ours/upstream 各 6；hard criteria prompt 命中 0；除 no-op 原文外无 expected artifact 命中；sandbox/network/web/apps/plugins 约束符合 README；upstream 草案副本未含 `LICENSE`。
- `python scripts/validate_collection.py`：通过。
- `python -m unittest discover -s tests -v`：81 个测试通过，1 个因 Windows 无符号链接权限跳过；无失败。
- 未运行模型、未安装 Skill、未提交、未推送。

## 冻结建议

在替换重复题、补齐 upstream prepare 副本的 MIT 许可随附，并让预填脚本拒绝带臂身份的盲输入后，再运行同一组结构校验、定向测试和临时 prepare 检查。当前结论仅是运行前静态与本地机械复核，不是三臂行为评测结果。
