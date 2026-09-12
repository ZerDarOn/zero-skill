# Round 23 揭盲后独立语义与门禁复核

结论：**未发现需要改分的 finding。metadata-corrected review 与 corrected score result 可以作为本轮计分依据；不打开本地 `obsidian-note-edit` 0.1.1 候选设计。**

## Findings

无。唯一失败 `retarget-existing-not-planned-note-r2 / upstream / criterion 4` 符合冻结标准；其余 215 个 true 与 53 份完整输出的语义抽查未发现误判。

## 唯一失败复核

该项揭盲映射为 candidate C → upstream。其 note 通过机械精确比较：JSON 可解析、固定字段形状有效，note 与 expected artifact 相同，仅省略允许的末尾单个 LF。

冻结 criterion 4 要求：`message` 必须“区分已确认重命名与计划目标”，且不能声称扫描、保存或验证渲染。candidate C 的 message 是：

> 已将正文中的现有入口目标改为“路线图”，保留显示文字；代码块及其他内容未改。

它准确报告了已确认入口的修改，也没有虚构外部操作，但只用“其他内容未改”笼统覆盖剩余内容，没有指出 `季度复盘` 仍是计划目标、未创建链接。相同评阅项中的 baseline 与 ours 都明确写出“计划项……未改”。因此 C 的 criterion 4 判 false 符合冻结标准，不应校正为 true。criterion 1–3 保持 true 也正确：完整 note、计划纯文本、frontmatter、显示文字和 fenced 示例均满足要求。

## 其余语义评分抽查

- 54 份输出的 criterion 1 均由 `artifact-checks.json` 判 true；因此每份 note 已覆盖各题的目标修改、未授权字节和格式边界。机械记录显示所有输出均可解析、note 精确匹配，无制品失败。
- `change-one-frontmatter-scalar` 的九份 message 均只报告顶层数字 `score` 从 3 改为 4，没有声称保存或渲染；四项全 true 正确。
- `convert-one-line-to-warning-callout` 的九份 message 均只报告指定两行 warning callout 转换并保持其余内容，没有外部验证声称；四项全 true 正确。
- `leave-unverified-target-unlinked` 的九份 message 均说明 `临时方案` 不在已确认清单或尚未确认，因此未应用链接；没有反推目标绝对不存在，四项全 true 正确。
- `plain-markdown-date-local-edit` 的九份 message 均只报告正文日期局部修改；有的未重复列举 URL 和代码块，但 criterion 4 只要求固定 JSON 且不声称实际文件或应用验证，结合精确 note，四项全 true 正确。
- `resize-one-visible-embed-only` 的九份 message 均只报告可见图片宽度从 320 改为 480，没有声称附件存在或 Obsidian 渲染；结合精确 note，四项全 true 正确。
- `retarget-existing-not-planned-note` 的 r1、r3 三臂及 r2 baseline/ours 都明确区分现有入口修改与计划项未改，四项全 true 正确。
- 18 个评阅项均无唯一 preferred candidate。17 项三者全四项通过；唯一有差异的 r2 中 baseline 与 ours 并列最佳、upstream 较低，单选偏好无法表达两者并列，因此 `preferred_candidate: null` 与评阅 notes 一致。三臂 preferred count 均为 0。

## 独立复算

| Arm | Criteria | 完整输出 | 输出数 | 唯一偏好 |
| --- | ---: | ---: | ---: | ---: |
| baseline | 72/72 | 18/18 | 18 | 0 |
| ours | 72/72 | 18/18 | 18 | 0 |
| upstream | 71/72 | 17/18 | 18 | 0 |

复算与 `review-result-blind-review-completed-independent-metadata-corrected.json` 完全一致。corrected review 文件的实际 SHA-256 为 `37a6d995c46f3eb6cd3ed2d63829e7806fb4a5f63afa040a68b7200e1a68d609`，与 corrected score result 的 `review_sha256` 一致。

### Criterion 1 失败

每题、每臂均为 `0/3`：

| Mechanism | Case | baseline | ours | upstream |
| --- | --- | ---: | ---: | ---: |
| protected-bytes | resize-one-visible-embed-only | 0/3 | 0/3 | 0/3 |
| protected-bytes | change-one-frontmatter-scalar | 0/3 | 0/3 | 0/3 |
| format-scope | plain-markdown-date-local-edit | 0/3 | 0/3 | 0/3 |
| format-scope | convert-one-line-to-warning-callout | 0/3 | 0/3 | 0/3 |
| target-state | leave-unverified-target-unlinked | 0/3 | 0/3 | 0/3 |
| target-state | retarget-existing-not-planned-note | 0/3 | 0/3 | 0/3 |

## 候选门禁

冻结门槛要求同一 mechanism 的两个不同题均出现 ours criterion 1 失败至少 `2/3`，同时 baseline 在各对应题均不超过 `1/3`。本轮 ours 在六题的 criterion 1 失败全部为 `0/3`，任何 mechanism 的第一层条件都不成立。

因此：

- **不打开**本地 0.1.1 候选设计；
- upstream 唯一失败位于 criterion 4，本来也不进入本地候选门槛；
- baseline 与 ours 都是 72/72、18/18，本轮没有证据支持修改当前本地 Skill，也没有证据支持宣称 ours 优于 baseline。

## 元数据更正与证据完整性

- 原始 `blind-review-completed-independent.json` 与 metadata-corrected review 的 `reviews` 完全相同；规范化后的 reviews SHA-256 都是 `83b3bcf24828b7c579bc7476502ec4c09a852c412420f19f272d1bce3cd17f5a`。
- 两文件的 `schema_version`、`comparison_id` 和顶层结构相同。变化只发生在 `reviewer`：model/reasoning effort 被更正，并补充盲态、先验暴露、允许文件、意外读取、是否人工和更正说明。
- 原始与 corrected score result 的 `arms`、`items`、`limitations`、`status` 完全相同；只有 reviewer metadata 及由 review 文件变化导致的 `review_sha256` 改变。
- `summary.json` 中 `results.json`、blind packet、key、blank form 的 SHA-256 均与当前文件一致。frozen spec、cases、当前/prepared ours 包和当前/prepared upstream 包的逐文件 SHA-256 均与 `frozen.json` 一致。
- 正式运行基础设施有效：三臂各 18 行，planned/executed repetitions 均为 3，无 provider error、forbidden tool row；总计 54 份输出。

## 结论与限制

本轮支持的窄结论是：在冻结的 6 个合成、文本制品型任务和每臂 3 次运行中，baseline 与 ours 均得到 72/72、18/18；upstream 因一次 message 未明确区分计划目标得到 71/72、17/18。所有三臂的 Markdown 制品本身均精确正确。

以下结论不能从本轮推出：

- 不能据此建立普遍 Skill 排名；样本只有六题，且任务结构窄、重复数为三。
- 不能证明真实 Obsidian 工作区写入、链接或附件存在性扫描、阅读视图渲染、插件集成。
- 不能把 baseline 与 ours 的同分解释为 Skill 无价值；本轮任务正文已经非常明确，可能形成天花板效应。
- 不能把 upstream 的单次 message 失败解释为其 Markdown 能力较差；它的 18 份 note 均精确正确。
- reviewer 是非人工的独立盲评。元数据更正的变更范围可由文件比较验证，但实际 reviewer 运行身份只能依赖更正后的 provenance 声明，不能从评分文本本身独立证明。
- summary 没有记录显式 Skill 调用轨迹，`rows_with_expected_skill_call` 为 0、`skill_calls` 为空；frozen evidence 能证明 Skill 包、显式调用 prompt 和运行条件，不能逐会话证明模型实际读取了 Skill 内容。

## 验证记录

- 独立解析 blind packet、key、artifact checks、metadata-corrected review 和 corrected score result，逐项重算 216 个布尔值、54 个完整输出归属、18 个偏好与逐题 criterion 1 失败。
- `python -m unittest tests.test_obsidian_artifact_comparison -v`：7/7 通过。
- `python scripts/validate_collection.py`：通过。
- `python -m unittest discover -s tests -v`：84 个测试通过，1 个因 Windows 无符号链接权限跳过；无失败。
- 未修改协议、Skill 或运行产物；未运行模型；未提交、未推送。
