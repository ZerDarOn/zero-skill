# 第 23 轮运行前独立复核（最终关闭）

结论：**未发现 P0–P3 finding，可以冻结当前协议并进入正式三臂运行。** 该结论只批准冻结题目、包、评分与运行约束；它不是模型行为结果，也不预判任一臂的表现。

## Findings

- P0：无。
- P1：无。
- P2：无。
- P3：无。

## 最后 P2 关闭证据

`test_prefill_run_rejects_frozen_cases_path_outside_repository` 在 `evaluations/runs` 下使用自动清理的临时 run，写入 comparison id 正确、但 `cases_path` 为 `../outside-cases.json` 的 frozen evidence，以及能让流程到达路径校验的最小 summary。测试直接调用 `prefill_run`，并断言抛出 `frozen cases path must stay inside the repository`。

该测试进入真实入口，而不是只测试复制出来的表达式。`prefill_run` 在读取盲包、表单或仓库外 cases 文件之前完成解析后边界检查，因此验证了错误输入会在副作用前被拒绝。本项满足仓库对新增校验逻辑必须具有错误输入回归测试的要求。

## 全量协议关闭状态

- **题目独立性**：首题现为可见图片 embed 宽度调整，不再重复旧活动题或本地示例中的 wikilink 重定向。六题分别覆盖 embed、frontmatter 数字、普通 Markdown 局部文本、callout、未确认目标 no-op、确认重命名与计划目标分离。
- **唯一 expected note 与 LF**：每题修改位置、替换内容和保护范围确定，完整 note 可唯一推出。六个 expected note 均以恰好一个 LF 结束且不含 CR；机械匹配只额外允许候选省略这个终止 LF，内部空白、CRLF 或额外 LF 不会被放过。
- **prompt 隔离**：prepare 级测试实际生成 18 个测试定义，模型 vars 只有 `prompt`，不包含 `expected_note` 字段、hard criteria 字段或 criterion 文本。no-op 题的原始输入与正确 note 相同属于任务材料本身，不是隐藏答案注入。
- **匿名机械预填**：packet 与 blank form 在评分前递归拒绝 `arm_id`、`skill`、`skill_package_sha256`、`randomization_salt`；正常路径只填第 1 项，要求所有项目原先为空，不覆盖第 2–4 项、偏好或 notes。输出保留解析状态及 expected/output/actual note 哈希，不包含臂映射。
- **第三方闭包**：固定提交、MIT、原始 URL、复制说明与六项逐文件哈希在 provenance 中闭合。仓库根许可证原字节复制到 upstream Skill；prepare 后的 snapshot 和项目安装副本均携带 LICENSE，冻结 manifest 也包含它。
- **三臂与规模**：baseline 无 Skill；ours 和 upstream 均项目级显式调用。三臂固定相同模型、推理强度、公共提示、任务正文和只读隔离约束。`6 × 3 arms = 18` 个测试定义，重复 3 次得到 54 份输出；每份 4 项标准，共 216 个布尔判断和 18 个三候选匿名评阅项。
- **门槛复算**：每个 mechanism 固定两个题。揭盲后按 case/repetition 的机械第 1 项即可重算 ours 与 baseline：同一机制两个题分别满足 ours 失败至少 2/3 且 baseline 不超过 1/3 才打开候选设计。upstream、第 2–4 项与偏好不进入门槛。
- **隐私与副作用**：材料为合成笔记，只含 `example.test` 与公开上游来源；没有本机路径、账户、密钥或真实 vault 内容。provider 固定 read-only、approval never、network false、web disabled、host apps/plugins false、隔离 Git 根与用户目录，提示禁止工具调用及虚构保存、扫描或渲染验证。
- **结论边界**：README 明确这里只验证返回的完整 Markdown 制品和字节保真，不能证明真实 Obsidian 文件编辑、链接存在性扫描、阅读视图渲染或插件集成。结构校验、prepare 和本复核均未被表述为行为通过。

## 验证记录

- `python -m unittest tests.test_obsidian_artifact_comparison -v`：7/7 通过；包含路径越界、身份泄漏、LF、prepare prompt/规模、许可与 provenance 检查。
- `python scripts/validate_collection.py`：通过。
- `python -m unittest discover -s tests -v`：84 个测试通过，1 个因 Windows 无符号链接权限跳过；无失败。
- `git diff --check`：通过。
- 未运行模型、未安装 Skill、未提交、未推送。

## 冻结判定

当前 `cases.json`、`promptfoo.json`、本地与 upstream Skill 包、provenance、预填脚本及对应测试可以作为第 23 轮冻结输入。正式运行后仍须保持盲评、机械第 1 项、独立偏好和揭盲顺序，并按 README 的候选门槛报告结果。
