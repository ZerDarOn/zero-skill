# 第 23 轮运行前独立复核（二次）

结论：**当前仍不建议冻结，需先补 1 项 P2 负向回归测试。** 上一次独立复核的两个 P1 和一个 P2 均已由实现与运行证据关闭；本次未发现 P0、P1 或 P3 问题。剩余 P2 不表示路径校验实现错误，而是新增信任边界没有满足仓库明确的回归测试要求。

## Findings

### P0

无。

### P1

无。

### P2：新增的 frozen cases 路径边界没有负向回归测试

- 位置：`evaluations/comparisons/obsidian-artifact-preservation-three-arm-16/prefill_artifact_review.py:244-251`；`tests/test_obsidian_artifact_comparison.py:21-261`。
- 问题：`prefill_run` 现在先验证 `cases_path` 为字符串，再将其相对 `ROOT` 解析，并用 `relative_to(ROOT.resolve())` 拒绝仓库外路径；这段实现能阻止普通 `..` 逃逸和解析后落在仓库外的绝对路径。但当前六个定向测试没有调用 `prefill_run` 的这条失败路径，也没有构造仓库外 `cases_path`。测试新增覆盖了身份字段、prepare prompt、许可复制和规模，却没有覆盖本次同时新增的路径校验。
- 后果：未来删除或弱化 `relative_to` 检查时，本轮测试仍会全绿。仓库 `AGENTS.md` 明确要求“新增或更改校验逻辑先补充能体现错误输入或错误接受的测试”，所以当前证据尚不满足冻结约定。
- 要求：增加一个不触碰真实 run 的临时目录测试，构造哈希有效但 `cases_path` 指向仓库外的 frozen evidence，并断言 `prefill_run` 抛出 `frozen cases path must stay inside the repository`；若直接测试解析辅助函数，也应同时覆盖 `..` 与仓库外绝对路径。测试通过后，本项可关闭。

### P3

无。作为非阻塞增强，可将身份字段负向测试参数化覆盖 `IDENTITY_KEYS` 的四个键；当前实现中的固定集合和递归遍历已清楚覆盖这四个键，现有测试也分别验证了 packet 深层候选与 form 记录两条输入路径，因此不单列 finding。

## 上次三项 findings 关闭情况

1. **旧题重复已关闭**：`resize-one-visible-embed-only` 改为只调整一个可见图片 embed 的宽度，保护 frontmatter、cover wikilink、普通文本、Obsidian 注释、fenced 示例、空行和块 ID。现有四个活动题没有图片 embed 尺寸编辑；它也不再复用本地 `references/example.md` 的已确认 wikilink 重定向任务。六题现在各自覆盖 embed 宽度、frontmatter 数字、普通 Markdown 局部文本、callout 转换、未确认目标 no-op、已确认重命名与计划目标分离。
2. **MIT 许可闭包已关闭**：固定 fixture 根 `LICENSE` 以相同 SHA-256 `64c64d48361edfe8610016441bf593256ea9b67f133b00f47c55aa29ee878567` 复制到 `skills/obsidian-markdown/LICENSE`；provenance 明确记录源 URL、位置复制、无源字节修改及六项文件哈希。prepare 草案中的 upstream snapshot 和 `.agents/skills/obsidian-markdown` 安装副本均包含 `LICENSE`，且与根许可证逐字节相同；冻结 upstream manifest 也包含该文件。
3. **匿名预填输入边界已关闭**：`reject_identity_fields` 在读取评分内容前递归遍历 packet 与 blank form，拒绝任意层级的 `arm_id`、`skill`、`skill_package_sha256`、`randomization_salt`。现有负向测试证明深层 packet 候选和 form 记录中的身份字段会失败。正常路径仍只写每个候选的第 1 项，要求原四项全为空，不修改第 2–4 项、偏好或 notes，并且生成的 checks 不含 arm 映射。

## 全量协议复核

- **六题与答案唯一性**：六个 `expected_note` 都由用户指定的局部动作唯一推出。第 5 题是有界 no-op，完整 note 唯一；`message` 允许措辞差异，由语义标准判断。每题四项标准区分完整制品、局部语义、保护范围和响应/证据边界，没有把可选文风当作唯一答案。
- **LF 边界**：六个 expected note 均以恰好一个 LF 结束且不含 CR。匹配函数只允许完全一致或候选少最后一个 LF；额外 LF、内部空白变化与 CRLF 均失败，负向测试通过。
- **模型 prompt 隔离**：prepare 产物有 18 个实际测试 prompt，vars 只有 `prompt`；没有 `expected_note` 字段名、没有 hard criteria 字段或任何完整 criterion 文本。第 5 题的正确 note 与输入原文相同，因此其 expected 字符串必然作为 no-op 原始材料出现在三臂 prompt 中；这是任务输入，不是 prepare 注入隐藏答案。其他五题的 expected artifact 均未作为完整字符串命中 prompt。
- **制品评分**：第 1 项在揭盲前机械比较 note；JSON 围栏、额外文字、非对象、缺少字符串 note 或制品多改均失败。字段形状和 message 真实性留在第 4 项，schema 状态同时写入机械记录。偏好独立存在，不能覆盖 hard criteria。
- **规模**：prepare 生成 `6 cases × 3 arms = 18` 个测试定义，frozen repetitions 为 3，因此计划输出是 54。每份四项标准，共 216 个布尔判断；匿名表单为 18 个三候选评阅项。
- **三臂一致性**：三臂固定 `gpt-5.6-sol`、`medium`、同一公共提示和任务正文；baseline 无 Skill，ours 与 upstream 均为项目级显式调用。baseline fixture 为空；ours 包含入口与唯一引用；upstream 包含入口、三个引用和 MIT LICENSE。各 Skill 包文件与哈希进入 frozen manifest。
- **门槛可复算**：case 固定记录三种 mechanism，每种两个题。揭盲后可按 case/repetition 的机械第 1 项统计 ours 与 baseline：同一机制两个不同题各自 ours 失败至少 2/3，且对应 baseline 均不超过 1/3，才打开候选设计。upstream、第 2–4 项和偏好均不参与，规则没有跨机制合并空间。
- **隐私与副作用**：材料均为合成笔记，只有 `example.test` 和公开上游来源 URL；未见本机路径、账户、密钥或真实 vault 内容。provider 固定 read-only、approval never、network false、web disabled、host apps/plugins false、隔离 Git 根与用户目录。common prompt 禁止工具与保存/扫描/渲染声明。
- **结论边界**：README 把结果限定为完整 Markdown 文本制品与字节保真，不声称验证真实 Obsidian 文件写入、链接存在性扫描、阅读视图渲染或插件集成；prepare、结构测试和本次复核均未被当作模型行为结果。

## 验证记录

- `python -m unittest tests.test_obsidian_artifact_comparison -v`：6/6 通过；其中 prepare 级测试实际生成临时草案。
- 独立临时 prepare：成功生成 18 个测试定义；计划输出 54、布尔判断 216；hard criteria prompt 命中 0；两个 upstream LICENSE 副本均与源许可证哈希相同；frozen upstream manifest 含 `LICENSE`；检查后已删除临时目录。
- `python scripts/validate_collection.py`：通过。
- `python -m unittest discover -s tests -v`：83 个测试通过，1 个因 Windows 无符号链接权限跳过；无失败。
- 未运行模型、未安装 Skill、未提交、未推送。

## 冻结判定

补齐 frozen cases 仓库外路径的负向回归测试并重跑定向测试、结构校验和全量单元测试后，可冻结并进入正式三臂运行。当前二次复核本身仍只是静态、机械与测试证据，不是行为评测结果。
