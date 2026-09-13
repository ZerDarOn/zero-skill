# 第二十九轮质量打磨：文章配图规划三方前向盲测

日期：2026-09-13

## 本轮问题

`article-visual-plan` 0.1.0 已覆盖信息型位置选择、定性证据保真、局部修订和显式流程图，但原有四题不足以判断三个边界：上限是否会被当成配额、弱证据是否会被视觉结构放大，以及增删一项时能否保留既有计划状态。

本轮将它与无 Skill 基线、Baoyu Skills 固定提交 `6b7a2e417500561a5ecdd0b168332f4142584617` 的 `baoyu-article-illustrator` 做三方对照。上游是包含偏好配置、确认、生图、写盘和文章回填的完整流程；当前本地 Skill 是文本规划器。为了保持可比性，本轮只测试共同覆盖的单轮文本规划子任务，不评价两个完整产品的总能力。

## 固定设计

协议、六题和上游夹具在提交 `527fccee203bbc3f18515c4d2c7c2881f8a7d1b0` 冻结并推送。三臂使用同一个 `gpt-5.6-sol`、medium、公共提示与只读隔离配置；每题每臂重复三次，共 `6 × 3 × 3 = 54` 份输出和 18 个三候选匿名评阅项。失败保留且不重试。

六题按三个机制各两题组织：

- `value-based-selection`：没有信息关系时明确选择零张；只有一个反馈循环时不填满三张上限。
- `evidence-strength`：将伴随关系与人手缺口保留为有限观察；并排呈现异组定性反馈但不制造排名。
- `plan-state-preservation`：在两个稳定 ID 之间新增固定项；删除中间项并保留 ID 缺口与其余行的逐字内容。

每题四项硬标准，核心标准及候选门槛在运行前写定。只有同一机制的两题中，当前 Skill 每题至少 `2/3` 次核心失败、baseline 每题最多 `1/3` 次核心失败，且 54 份输出全部有效，才允许打开最小候选设计。上游只用于设计参照，不参与本地改版门槛。

## 上游来源与边界

上游完整 Skill 目录按固定提交保存，逐文件 SHA-256、根 MIT 许可证和修改声明写入 provenance。文件使用 Git 对象原字节提取，没有安装或执行上游脚本，也没有登记为本地原创 Skill。

固定源自身有一个保留缺口：`references/usage.md` 中的 `references/style-presets.md` 若按当前文件解析会落到不存在的二重 `references/references/` 路径，实际目标文件存在于包内。本轮六题不依赖该链接，夹具没有静默修正第三方字节。

## 正式结果

预检 3/3 完成且基础设施有效，未计分。正式运行 54/54 完成，三个臂各 18 行；provider error、禁止工具轨迹和 Promptfoo 失败均为 0。

匿名评阅结果完全相同：

| arm | 完整通过 | 标准通过 | 唯一偏好 |
| --- | ---: | ---: | ---: |
| 无 Skill | 18/18 | 72/72 | 0 |
| `article-visual-plan` | 18/18 | 72/72 | 0 |
| `baoyu-article-illustrator` | 18/18 | 72/72 | 0 |

18 个评阅项全部为平局。六题三个臂的核心失败也全部为 `0/3`，所以三个机制均未触发候选门槛。独立揭盲后复核重新聚合 216 个布尔判断、逐题核心失败与证据哈希，没有发现 P0–P3 问题，也没有改分。

## 鉴别力与成本

三臂全满分形成天花板效应。这能说明六个明确、合成、单轮的文本规划题没有暴露失败，但不能证明当前 Skill 优于无 Skill 或上游，也不能估计更难、含糊或真实文章中的相对帮助。

本次运行中，当前 Skill 相对 baseline 的总 token 多 `10.9%`、记录成本多 `47.5%`、中位延迟多 `22.3%`。上游相对 baseline 的对应增量为 `45.5%`、`113.6%` 和 `8.5%`。当前 Skill 相对上游少 `23.8%` token、少 `31.0%` 记录成本，但中位延迟多 `12.7%`。这些数字只描述本次 Promptfoo 记录，会受输出长度、缓存、定价和调度影响，不是稳定性能基准。

## 技能与仓库决定

`article-visual-plan` 正文、版本和 catalog 均不变，继续是 0.1.0、`experimental`、`evidence: null`。包指纹仍为 `e02fed142a73421a2cc091bfea0d6faefef4c8035e671d4866e65708e9973a87`。

六个前向题加入活动回归，该 Skill 从 4 例增至 10 例，全仓从 148 例增至 154 例。它们是运行前冻结的任务与标准，不是根据输出倒推的回归题。公开机器报告保存 54 份合成输出、匿名评分投影、运行汇总、来源与产物哈希、门槛和限制；原始 Promptfoo 产物仍被忽略，本机存在时测试会按哈希重新绑定。

本轮没有独立人工视觉设计评审，也没有测试隐式路由、实际生图、渲染质量、文件回填、编辑器集成或真实读者理解，因此不满足 `verified` 条件。

## 下一步

下一轮不应修改或重跑这六题来制造差异。更有价值的方向是预注册一组仍可唯一评分、但减少题面直接提示的前向任务，例如跨段证据冲突、图表类型与证据强度冲突、对既有长计划的非相邻增删，以及规划与完整生成提示词之间的粒度切换。先确认这些题能区分 baseline 与至少一个 Skill 臂，再考虑是否存在需要修订的重复机制。

## 对应证据

- [机器报告](../evaluations/reports/article-visual-plan-three-arm-round-29-diagnostic.json)
- [冻结协议](../evaluations/comparisons/article-visual-plan-three-arm-22/README.md)
- [冻结前独立复核](../evaluations/comparisons/article-visual-plan-three-arm-22/prefreeze-review-independent.md)
- [揭盲后独立复核](../evaluations/comparisons/article-visual-plan-three-arm-22/postscore-decision-review-independent.md)
- [固定上游来源](../evaluations/fixtures/upstreams/baoyu-skills/6b7a2e417500561a5ecdd0b168332f4142584617/provenance.json)
