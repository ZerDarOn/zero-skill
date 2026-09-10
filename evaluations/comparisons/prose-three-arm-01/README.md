# 润色技能三方探索性对照

比较无技能、prose-polish 0.1.1、Humanizer 3.0.0 固定提交。六个新合成任务，各组各两次，共 36 次独立生成；本轮不修改待测技能，也不把新题并入原来的 94 个活动用例。

## 冻结材料

- [协议](protocol.json)：模型、加载方式、重复次数、评分方法和限制。
- [任务与评分标准](cases.json)：提示与硬性标准分别保存；只有提示进入生成会话。
- [运行器](run_comparison.py)：复用前轮 CLI 调用方式；随机交错组别，保存每次提示、输出、事件、用量和错误。
- [上游来源](../../fixtures/upstreams/humanizer/9862685f575c65a8247f90369951df1b3416e3d6/provenance.json)及 [MIT 许可证](../../fixtures/upstreams/humanizer/9862685f575c65a8247f90369951df1b3416e3d6/LICENSE)。原始 SKILL.md 是全部运行时指令，无需另一个技能或脚本。附带 openai.yaml 仅用于记录 UI 元数据，不进入提示。

调用现有 Codex 登录，生成时固定 gpt-5.6-sol / medium，独立只读临时工作目录，忽略用户配置。共同提示禁止工具操作；这不是工具被物理禁用的证明，实际调用记录需另查。上游完整运行时指令及本地完整包被显式注入，未验证自动发现或渐进加载。三组可能共享宿主默认指令，未证明宿主完全无其他默认上下文。

## 执行与复核

从仓库根目录执行 `python evaluations/comparisons/prose-three-arm-01/run_comparison.py` 会发起 36 次模型调用，应仅在用户授权模型评测时运行。脚本先生成冻结快照和源文件哈希，再发起调用；每次执行创建新的被忽略目录，不覆盖此前运行。失败保留，不自动重试。两个并发进程只用于平衡执行顺序，不是协作开发代理。

结果初存 `evaluations/runs/prose-three-arm-01-<id>/`。评阅者先读取 `blind-review.json`，写入逐项评分后，才查看 `blind-key.json`。匿名化隐藏组名，但评阅者知道技能设计且自己编写任务，因此不能称为独立盲测。清楚度和文风各按 0–2 记录，单独呈现；不与事实/任务约束混成总分。

评分协议采用运行前冻结标准。检查字数或受保护片段可以机械辅助，事实含义仍需逐项阅读。任何复核修订须保留旧判定、修订理由和揭示分组的时点。最终公开证据仅包含本轮合成材料和已获许可的上游文件，不包含账户凭据。

方法参考：[OpenAI Evaluation best practices](https://developers.openai.com/api/docs/guides/evaluation-best-practices)。本轮是小样本探索，不能由某组通过数或主观偏好推导整体技能排名，亦不能提升为 verified。
