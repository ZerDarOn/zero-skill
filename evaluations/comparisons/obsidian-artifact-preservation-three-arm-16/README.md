# Obsidian artifact preservation three-arm 16

本轮比较无 Skill、`obsidian-note-edit` 0.1.0，以及 Obsidian Skills 固定提交 `a1dc48e68138490d522c04cbf5822214c6eb1202` 的 `obsidian-markdown`。目标是检查模型提交的完整 Markdown 制品能否完成窄编辑并保持未授权字节、格式意图和链接目标状态。先冻结任务与验收，不先修改本地 Skill。

第三方臂只把固定入口及其 `PROPERTIES.md`、`EMBEDS.md`、`CALLOUTS.md` 引用作为提示资料；原文件、MIT 许可证、提交和逐文件哈希保存在 `evaluations/fixtures/upstreams/obsidian-skills/a1dc48e68138490d522c04cbf5822214c6eb1202/`。仓库根许可证以原字节复制到评测包内，provenance 明确记录这一位置复制；不安装或运行上游脚本，也不把第三方内容登记为本地原创 Skill。

## 为什么使用文本制品协议

2026-09-13 的合成 canary 在隔离临时 Git 根中尝试原生 `workspace-write`：评测会话能够识别明确调用的本地 Skill，但读取命令与 `apply_patch` 均被宿主策略拒绝，目标文件没有改变。该结果只说明当前工具链无法完成受控文件写入，不能算成任何 Skill 的行为失败。

因此正式比较保持只读会话，让候选返回固定 JSON：`note` 是编辑后的完整 Markdown，`message` 是实际改动或未改原因。运行器不执行候选命令、不访问真实 vault；后续只把 `note` 当文本制品与冻结 `expected_note` 比较。它能验证完整制品和字节保真，仍不能证明真实 Obsidian 工作区编辑、链接存在性扫描、渲染或插件集成。

## 六个任务与机制

- 受保护字节：只调整一个可见图片 embed 的宽度；只更新一个 frontmatter 数字标量。
- 格式范围：普通 Markdown 的局部日期修订；只把一行转换成指定 warning callout。
- 目标状态：未确认目标保持纯文本；已确认重命名与计划新建笔记分开处理。

每题包含原始完整笔记、明确修改范围、四项 hard criteria 和一个不进入模型 prompt 的 `expected_note`。待测模型只看到公共提示与 `prompt`；`expected_note` 保留在冻结 `cases.json`，供运行后机械验收和独立评阅使用。

## 规模与评分

三臂使用相同的 `gpt-5.6-sol`、`medium`、只读隔离环境和任务正文；两个 Skill 臂都采用项目级显式调用。每题每臂重复三次，共 `6 × 3 × 3 = 54` 份输出、18 个三候选匿名评阅项和 `54 × 4 = 216` 个布尔判断。

第 1 项是制品核心：输出必须是可解析 JSON，其中 `note` 与冻结 `expected_note` 逐字一致，只允许候选省略 expected 末尾恰好一个 LF。该项在揭盲前由确定性脚本填入匿名表单，并记录解析状态、expected/output SHA-256；评阅者不能改写它。其余三项由不知道臂映射的评阅者依据随机化候选、冻结任务和标准判断。偏好独立记录，不能覆盖 hard criteria。

输出出现 JSON 代码围栏、混入额外文字、缺少字符串 `note`，或 Markdown 存在额外改写时，第 1 项失败。`message` 的字段形状、真实改动陈述和不虚构保存／扫描／渲染证据由第 4 项判断，不混入制品字节比较。

## 候选门槛

本地 0.1.0 的改版门槛只比较 ours 与 baseline；upstream 用于观察设计取舍，不参与本地候选触发。只有同一机制的两个不同题都出现 ours 至少 `2/3` 次第 1 项制品失败，且 baseline 在每个对应题均不超过 `1/3`，才打开最小 0.1.1 候选设计。单题失败、跨机制各失败一题、两臂共同失败、只在第 2–4 项失败、偏好差异或 upstream 表现都不能触发。达到门槛也只授权候选设计，不直接修改、升版或发布。

## 冻结前检查

独立复核应确认：六题没有复刻现有四个活动用例；expected artifact 可从用户任务唯一推出；末尾 LF 规则没有掩盖其他空白变化；hard criteria 不把一种可选文风当唯一答案；第三方引用闭包、许可证和哈希完整；候选门槛能从匿名机械结果复算；所有材料都是合成笔记且不含本机路径、账户、密钥或真实 vault 信息。

准备命令：

```sh
python evaluations/promptfoo/prepare_skill_comparison.py --spec evaluations/comparisons/obsidian-artifact-preservation-three-arm-16/promptfoo.json
```

运行、匿名评阅和揭盲步骤见 [Promptfoo 评测说明](../../promptfoo/README.md)。
