# 第六次技能吸收报告

日期：2026-09-09。起点提交：abb328dc674a29da249d380521501257998b1804。

## 当前阶段

第六批已完成实现与单次合成诊断：新增 `decision-brief-draft` 与 `file-organization-plan` 两个 0.1.0、`experimental`、原创自包含技能，登记总数为十四个；两组各四个用例已由 `planned` 仅修改 `stage` 为 `active`。既有十二个技能包未修改。本批尚未提交、推送、安装或发布。

## 来源核查范围与许可边界

### 决策简报起草

- 固定入口为 Anthropic Skills 提交 41bbe19d1a1a7eaab5e7bb9050a417e5c6cffc8f 的 [skills/doc-coauthoring/SKILL.md](https://github.com/anthropics/skills/blob/41bbe19d1a1a7eaab5e7bb9050a417e5c6cffc8f/skills/doc-coauthoring/SKILL.md)，已实际阅读完整入口。
- 采用：先明确读者和文稿目的；按材料逐段形成、修订有范围的草稿；从未参与讨论的读者视角检查术语、依据和理解缺口。
- 舍弃：固定 5—10 个问题和 5—20 个候选项；每一步都等待确认；强制建立文件或调用特定编辑工具；没有真实独立会话却宣称完成读者测试。
- 许可检查：[固定 doc-coauthoring 目录树](https://github.com/anthropics/skills/tree/41bbe19d1a1a7eaab5e7bb9050a417e5c6cffc8f/skills/doc-coauthoring)只显示 SKILL.md，没有目录许可证；[固定仓库树](https://github.com/anthropics/skills/tree/41bbe19d1a1a7eaab5e7bb9050a417e5c6cffc8f)没有 LICENSE，固定根 LICENSE raw 路径返回 404；[固定 README](https://github.com/anthropics/skills/blob/41bbe19d1a1a7eaab5e7bb9050a417e5c6cffc8f/README.md)只概括“许多技能”为 Apache-2.0，并另列部分文档技能为 source-available。该概括不足以证明 doc-coauthoring 的具体许可覆盖，因此本轮记录为具体许可未完整核实。没有复制原文、模板或示例。

### 文件整理方案

- 固定入口为 Composio Awesome Claude Skills 提交 be2a406907dbc61b73e6827ded415c96139d13a2 的 [file-organizer/SKILL.md](https://github.com/ComposioHQ/awesome-claude-skills/blob/be2a406907dbc61b73e6827ded415c96139d13a2/file-organizer/SKILL.md)。浏览缓存未取得 raw 页面后，2026-09-09 通过 [固定 raw URL](https://raw.githubusercontent.com/ComposioHQ/awesome-claude-skills/be2a406907dbc61b73e6827ded415c96139d13a2/file-organizer/SKILL.md) 使用 Invoke-WebRequest 读取，返回 HTTP 200、11,312 字节；已阅读完整入口。
- 采用：先限定范围；按用途而不只按扩展名组织；在动作前呈现逐项去向；显式处理冲突与待确认对象。
- 舍弃：自动扫描用户目录；运行 find、md5、mv 等 shell 示例；仅凭旧修改时间归档；同名或同大小直接判重复；固定无空格、数字前缀等命名审美；自动执行和固定维护日历。
- 许可检查：[固定 file-organizer 目录树](https://github.com/ComposioHQ/awesome-claude-skills/tree/be2a406907dbc61b73e6827ded415c96139d13a2/file-organizer)只显示 SKILL.md，没有目录许可证；固定仓库根 LICENSE raw 路径返回 404。[固定 README](https://github.com/ComposioHQ/awesome-claude-skills/blob/be2a406907dbc61b73e6827ded415c96139d13a2/README.md#license)声明仓库采用 Apache-2.0，同时明确个别技能可能有不同许可；该入口没有许可字段，因此只记录仓库级声明，具体技能许可未完整核实。没有复制上游脚本、模板或示例。

## 方法到本地用例的追踪

| 方法 | 采用或舍弃 | 本地行为 | 覆盖用例 |
| --- | --- | --- | --- |
| 读者与目的先行 | 采用 | 让未参会读者理解决策、时点、选项和依据 | recommendation-is-not-approval、reader-context-without-invention |
| 逐段有界修订 | 采用 | 更正传播到受影响建议，同时保持未授权内容与状态 | bounded-decision-revision |
| 独立读者测试 | 舍弃为默认 | 可自查理解缺口；未实际运行独立会话就不声称测试 | reader-context-without-invention |
| 限定目录范围 | 采用并收紧 | 只规划给定清单，排除项不分析、不移动 | keep-project-dependencies |
| 显式变更清单与冲突 | 采用 | 每个来源有唯一去向或保留理由，大小写规则按输入 | collision-aware-mapping |
| 同名、大小或日期启发 | 舍弃为结论 | 重复需内容与用途证据；修改时间不替代拍摄时间 | same-name-is-not-duplicate、dates-are-not-capture-time |

## 运行前评分设计

### 通用判定

- 每条 must_include 与 must_avoid 都标注来自用户要求、输入事实或任务不变量，并独立做语义判断。全部必要项满足且没有禁止项才算全约束通过；核心任务和格式遵循分别记录。
- 接受语义等价结构和措辞。决策简报不固定标题、段数或评分表；文件方案不固定编号后缀、目标命名或表格形式。建议必须有材料依据，但不要求复述本报告措辞。
- 可选内容不进入必要项合取。用户允许条件建议或暂缓时两者都可；文件可以安全改名、保留原位或使用子目录时，任一满足唯一性和用途的方案都可。简洁表格不是默认禁项，只有编造权重或只给无解释分数才失败。
- “每个来源恰好一次”按一个来源恰好一个决定或映射判定；原路径和目标同时出现、解释中再次引用文件名不算重复分配。依赖目录可以用一个整体映射明确涵盖三项，不隐藏要求四行表格。
- 忠实转述输入已给的核实状态不算声称模型执行：组 2 的逐字比较、两个产品已确认的区域和用户提供的 EXIF 都可以引用。只有无依据声称本轮新完成扫描、比较、批准、移动或验证才触发禁止项。
- 建议与已执行严格分开。任何声称已经批准、发送、读者测试、扫描、移动、删除、释放空间或验证文件的回答，按相应用例禁止项处理。

### 数量、逻辑、范围和未知检查

| 用例 | 数量与格式 | 且或关系 | 范围、分母或未知处理 |
| --- | --- | --- | --- |
| recommendation-is-not-approval | “短”不按精确字数评分；必须实际交稿 | 决策时点、选项代价、建议/偏好/批准边界和未知负责人都需要 | 负责人未知，不转成无人负责或自造负责人 |
| tradeoff-under-hard-constraint | 不限定模板或条目数 | 硬约束、两项成本周期和可辩护建议均需要 | 成本保留估计范围与每年口径 |
| bounded-decision-revision | 恰好一个建议段，不要求一句话 | 新成本、未变事实与建议传播均需要；Orbit 倾向或承认区间重叠后暂缓均可 | 只改建议段；更正不等于人物观点反转，也不证明 Orbit 在所有实际价格下更便宜 |
| reader-context-without-invention | 短草稿，不以精确字数制造失败 | 术语、决策、试点观察和关键缺口都需要 | 准确率未知；条件建议或暂缓二者任选 |
| same-name-is-not-duplicate | 两个给定组都需分析 | 组 1 待核实且组 2 保留用途差异 | 同名同大小不证明内容；内容相同不证明用途可删 |
| collision-aware-mapping | 两个来源各有一个决定；重复解释文件名不算多次分配 | 移动项有安全唯一目标；保留项说明原因；无需强制复述碰撞原理 | 按明确的大小写不敏感口径检查结果目标 |
| keep-project-dependencies | 四个范围内文件都覆盖；一个整体目录映射可覆盖依赖组三项 | 依赖组三项保持关系，独立 PDF 有用途去向 | private/raw 不进入分析范围，不强制四行表格 |
| dates-are-not-capture-time | 四个文件各恰好一次 | 两个已知日期正确归档，两个未知日期保持未知 | 修改时间不是拍摄时间；未知可保留或 Needs-Date |

### 可接受等价与失败边界

- recommendation-is-not-approval：接受推荐任一选项、条件建议或清楚列出需权衡后再定，只要依据来自材料并区分陈的偏好与组织批准；把偏好写成已定失败。
- tradeoff-under-hard-constraint：接受建议 Harbor，或说明 QuickBase 只有在数据区域事实改变后才可重考虑；用低价覆盖欧盟硬约束失败。
- bounded-decision-revision：接受依据较低估计区间条件性倾向 Orbit；也接受说明 90—95 万元区间重叠、Nova 原有成本优势理由不再成立，暂不确定唯一更便宜选项并等待可比报价。不要求固定出现“重叠”一词，但不能断言 Orbit 在所有可能实际成本下都更便宜；继续用旧 Nova 范围、增加未授权章节或声称用户改主意失败。
- reader-context-without-invention：接受以测得准确率达到 95% 为条件推广，或在测量前暂缓；从 18→12 分钟推算准确率失败。
- same-name-is-not-duplicate：组 1 可建议哈希或逐字比较来确认内容是否相同，但安全合并或删除还需用途、引用与保留要求；组 2 可忠实转述已完成的逐字比较并保留两者，不能把输入已有比较误判成模型声称新执行，也不能删除已知用途路径。
- collision-aware-mapping：接受描述性重命名、独立子目录或保留原位；只按最终映射检查大小写折叠后的唯一性。若回答主动讨论原名归档风险才要求其碰撞解释正确，不强制安全答案复述原理。
- keep-project-dependencies：接受 site 原位保留或整个目录连同相对布局迁入 WebProject；只把 logo 挪到 Images 或触碰排除目录失败。
- dates-are-not-capture-time：接受未知照片留原位或进入 Needs-Date；用同步修改时间生成 Photos/2023/07 或 Photos/2026/01 失败。

## 预检与冻结

运行前只读预检修正了四类判分边界：决策修订允许依据较低估计区间倾向 Orbit，也允许说明区间重叠后暂缓；表格本身不失败，只有编造权重或无解释评分才失败；文件碰撞按安全最终目标判定；“每个来源恰好一次”按一个决定或映射判定，而不是按字符串出现次数。用例随后冻结，baseline 与 skill 使用相同 prompt、材料和约束；激活时只改 `stage`。

## 实现与运行

- 运行环境：Windows 上的 Codex CLI；`gpt-5.6-sol`，reasoning effort 为 `medium`。
- 隔离：每例使用新的临时目录，`codex exec --ephemeral --ignore-user-config`，只读沙箱、无工具。
- 对照：八次 baseline 后冻结技能包，再进行八次显式加载 skill 的运行；16 次有效生成均在第一次模型启动成功，没有模型重试或启动失败。
- 一次本地编排脚本在模型启动前因对尚不存在的目标调用 `Resolve-Path` 而退出；修正路径处理后开始正式运行。该事件不计入模型启动或生成。
- baseline 合计 101,853 ms、122,192 input tokens、90,112 cached input tokens、1,286 output tokens、121 reasoning tokens；skill 合计 117,462 ms、128,918 input tokens、94,208 cached input tokens、1,814 output tokens、171 reasoning tokens。时间是本地编排观测区间，不是模型服务端延迟。

## 指纹与结果

| 技能 | 包指纹 | planned 用例指纹 | active 用例指纹 | 全约束 baseline→skill | 核心 baseline→skill |
| --- | --- | --- | --- | --- | --- |
| `decision-brief-draft` | `afeac5b3289068acd814c3b90b3f666d684da63c0f894cb88d52042d958f90c9` | `ed459e1659d2467bdf1e915516ee8c9d9cb270068bdaaf4642c3cec50538edb6` | `0c8d2000e9199ff13d116e10fb614df916a4091bd74af142e9548af64c39af0f` | 4/4→4/4 | 4/4→4/4 |
| `file-organization-plan` | `29807ca18292940f4c90d17d92f200f1ec9944639c37b0a0c68a9825a6d7aff4` | `927f8cb4253d58af8f3a26b98aaeb741f6379780a35e93122b2bc8585b3beb14` | `91aeec54c092857a90f07859c33a1478c8d12908a92ff2e90a0402cc1c75cf04` | 4/4→4/4 | 4/4→4/4 |

两组均无严格通过数改善，也无退化。决策修订 baseline 原句“Orbit 第一年成本估计为 85—95 万元，低于 Nova 的 90—110 万元”忠实列出输入估计范围，且两个端点均更低；它没有断言 Orbit 在所有可能实际成本下都更便宜。依据冻结标准“不要求固定出现重叠一词”，复核后判为通过。此次只修正评分和理由，未修改原始输出、用例、技能包或其指纹，也未重跑。

完整 prompt、原始输出、事件、stderr、退出状态、用量、时间、快照、哈希和逐项理由保存在 [诊断证据](../evaluations/reports/sixth-absorption-0.1.0-diagnostic.json)。

## 导出、检查与复核

- 已生成 `dist/decision-brief-draft-0.1.0.zip` 与 `dist/file-organization-plan-0.1.0.zip`，未覆盖既有 ZIP。两包都只含顶层 `bundle-manifest.json` 和对应技能目录中的 `SKILL.md`；manifest 的包指纹与当前目录指纹一致。
- 诊断报告共 16 条唯一运行记录，均为退出码 0、第一次启动成功；planned 与 active 快照除 `stage` 外一致，报告内技能正文、包指纹和 active 用例指纹均与当前文件一致。
- `python scripts/validate_collection.py` 通过；`python -m unittest discover -s tests -v` 共运行 27 项，26 项通过，1 项因当前 Windows 环境没有创建符号链接的权限而跳过；`git diff --check` 通过。
- 主任务模型已只读复核原始 prompt、输出、事件、stderr、用量、快照、哈希、ZIP 和评分修订，未发现新的实质问题。这是协作模型复核，不是独立人工评审。

## 限制与结论

每例只运行一次，技能为显式加载，评分由实施代理完成而非独立人工评审；未测试自动发现、稳定收益或真实决策质量。无工具隔离也没有执行发送、独立读者测试、磁盘扫描、内容比较、移动、删除和恢复验证。文件整理 baseline 已全部通过，两个包都没有在本轮证明严格通过数增益，因此继续保持 `experimental` 与 `evidence: null`。来源许可边界仍以本报告的固定提交核查为准，没有复制第三方文件。
