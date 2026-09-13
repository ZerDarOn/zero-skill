# Round 29 独立预冻结复核

## Findings first

最终字节未发现 P0、P1、P2 或 P3 问题，可以冻结。复核期间发现的来源换行转换、上游已存断链披露、不可观察硬标准、零图题理由未入题面、上游强制配置流程干扰，以及质量汇总器未拒绝 `command_execution` / `file_change` 的问题，均已在冻结前关闭；本结论只针对修正后的工作区。

## 评测设计

六题均为合成前向题，与当前四个活动用例没有 ID 或题面复用。三个机制各有两题：价值选择分别具有唯一的零图与单图结论；证据强度题只要求保留题面给出的定性关系、替代解释和不可比较边界；计划状态题允许新增行的语义等价措辞，同时逐字锁定未修改行、稳定 ID 和顺序。四项硬标准均可由匿名最终文本观察；真实工具、文件和生图行为单独由原始 provider items 与运行有效性门禁判断。比例、语言、数量、风格和禁用表达均来自题面，没有把可选审美偏好提升为硬标准。

三臂使用相同模型、推理等级、只读隔离、公共约束和任务正文。公共约束明确跳过偏好配置、`EXTEND.md`、首次设置、确认、生图、写盘和文章回填，因此 Baoyu 的端到端流程不会因共同规划子任务之外的阻塞步骤被额外处罚。显式 Skill 臂仍会收到准备器生成的显式调用前缀，这是被测加载方式本身；上游只作为解释性上下文，不进入本地候选门槛，也不能据此推断两个完整产品的总排名。

准备器生成 18 个 case-arm 项；正式三次重复得到 `6 × 3 × 3 = 54` 份输出。汇总器按 case 和 repetition 形成 18 个匿名三候选评阅项，四项硬标准合计 216 个布尔判断，映射盐和 arm/Skill 信息只写入独立 key。评分器要求完整布尔表并在揭盲后聚合；`preferred_candidate` 不改变逐项标准。

候选门槛可由冻结 cases、盲评结果和映射重算：一次输出的任一 `core_criteria` 为假即为一次核心失败；只有同一机制的两题都满足 ours 每题至少 `2/3` 次核心失败、baseline 每题至多 `1/3` 次核心失败，并且 54 份输出全部有效时，才打开最小候选设计。单题、跨机制、非核心项、偏好和 upstream 结果没有触发入口。

## 固定来源与归属

GitHub API 返回的固定提交为 `6b7a2e417500561a5ecdd0b168332f4142584617`，树未截断；`skills/baoyu-article-illustrator/` 的 37 个源文件与夹具逐项对应。provenance 共记录 39 项：仓库根许可证、37 个原始 Skill 文件，以及复制到实验包内的许可证。对 39 个固定 raw URL 的复核显示，本地字节、记录 SHA-256 与远端字节完全一致，Markdown 和许可证均为 LF；MIT 许可证随准备后的上游包携带。

上游 `references/usage.md` 中唯一真实的 Markdown 断链已原样保留并在 README 与 provenance 披露：其中 `references/style-presets.md` 从当前文件解析会多出一层 `references/`。实际目标文件已在完整包内，六题不读取 usage 或依赖该链接。其余看似路径的内容是输出文件模板，不是包依赖。没有安装或运行第三方代码，没有修改第三方源字节，也没有把第三方内容登记为本地原创 Skill。

## 宿主与证据边界

当前 Windows 命令沙箱 provisioning 故障不妨碍不需要命令的一次性文本规划，但不证明工具链恢复。质量汇总器现在会把可观察的 `command_execution`、`file_change`、MCP、网页搜索和 Codex app provider item 判为基础设施无效，评分器拒绝对这种状态揭盲计分。若工具尝试在 provider item 形成前即被宿主拒绝，通用 Promptfoo 结果未必能够观察到；README 已明确不把该不可见情形宣称为已覆盖。

本复核没有读取未来正式运行输出或 arm 映射。评阅计划是独立模型辅助评阅，不是独立人工视觉设计审计；本轮也不覆盖隐式路由、实际图像质量、文字渲染、文件落盘、生图后端、编辑器集成或真实读者理解。`skills/creation/article-visual-plan/SKILL.md`、活动用例和 catalog 未被本轮修改。

## 验证

执行并通过：

```powershell
python -m unittest tests.test_article_visual_comparison tests.test_promptfoo_skill_summary -v
python scripts/validate_collection.py
python -m unittest discover -s tests -v
git diff --check
```

定向组合为 23 项通过；全仓为 183 项通过、1 项因当前 Windows 无符号链接权限而跳过。另以只读脚本核对了固定提交 GitHub tree、39 个 raw URL 的字节与 SHA-256、Markdown 相对链接闭包、活动题面差异，以及准备后 18 项的提示词/夹具隔离；没有运行正式模型任务。
