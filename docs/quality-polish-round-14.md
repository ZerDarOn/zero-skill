# 第十四轮质量检查：关系沟通三方盲测

日期：2026-09-11

## 范围

本轮检查 `relationship-review` 0.1.1 的实际指令价值，并与无 Skill 和公开的 LoveHelper 做同题比较。六个运行前冻结的合成任务覆盖：

- 对方疲惫并取消邀约时的一句回复；
- 有双向窗口时自然、轻微的暧昧；
- 连续推迟且不另提时间的混合信号；
- 明确拒绝及不要到单位等待的边界；
- 单次未回复是否被升级为冷暴力或控制；
- 帮忙投入与见面、主动交流不对称时的具体做法。

每题三个实验臂各执行一次，共 18 个独立 `gpt-5.6-sol` medium 会话。Skill 臂收到完整指令包的内联快照，基线不接收 Skill。任务正文相同，评分标准没有进入生成提示；会话使用只读沙箱，不允许工具调用，失败不重试。

## 为什么选择 LoveHelper

2026-09-11 刷新时，没有发现高 Star 且任务、许可、固定提交都适合本轮的专门恋爱 Skill。LoveHelper 只有 3 Star，但其 `relationship-copilot` 正好处理聊天、下一句和后续动作，固定提交 `1e391e26fd1c1bfee06e4daa9b439086a098a49b` 有 MIT 许可证与署名文件，因此作为贴近领域的对照，不作为高热度或总体质量代理。

评测夹具保存五个上游文件的原路径和原字节，逐文件 SHA-256 已核对；没有安装或执行其 OCR、评分脚本及其他程序。完整来源见[固定夹具](../evaluations/fixtures/upstreams/love-helper/1e391e26fd1c1bfee06e4daa9b439086a098a49b/provenance.json)。

## 运行与盲评

18/18 记录有效，没有超时、空输出或工具轨迹。运行器先生成匿名候选与独立映射 key。另一个同项目 Codex 任务收到的指令只允许读取匿名 packet 和空白评分表，禁止读取 key、原始 records、Skill 或协议；它在 57 个标准项全部填为布尔值后，本任务才运行既有计分器揭盲。评阅者仍是模型，不是独立人工关系专家。

| 实验臂 | 标准通过 | 完整输出 | 盲评偏好 | Token |
| --- | ---: | ---: | ---: | ---: |
| 无 Skill | 19/19 | 6/6 | 0 | 91,807 |
| `relationship-review` 0.1.1 | 19/19 | 6/6 | 2 | 100,757 |
| LoveHelper `relationship-copilot` | 16/19 | 5/6 | 0 | 174,983 |

Token 包含输入和输出；三组提示包大小不同，数字不能直接解释为稳定成本差异。

## 观察

短回复、轻暧昧、明确拒绝和单次未回复四题三组都完整通过。模型已有较强的通用关系沟通能力，这些题没有测出 Skill 的硬标准增益。

本地 Skill 在“连续推迟”题获得偏好。它用一句回复把下一次主动权留给对方，并建议暂停连续追问；LoveHelper 同样通过，但额外输出“降温位”和“这轮策略”标签。这个差异支持当前 Skill 不强制关系阶段和固定报告形状的设计。

“单向付出”是唯一拉开硬标准的题。本地 Skill 保留“对方兴趣有限、习惯被动或近期确实忙”等不确定性，给出减少非必要帮忙、一次明确邀约和观察替代行动的步骤，获得偏好。LoveHelper 输出“大概率工具人/熟人位、约 10 分、功能位”，还给出“这次不接工具人订单了”的带刺话术，因此在不确定性、非惩罚边界和避免强制评分三项失败。

这个失败印证了上游审查时已经识别的风险：关系分数和进攻性框架容易把有限记录升级为确定位置，并让建议带上羞辱或施压意味。LoveHelper 的可发送回复优先、引用具体聊天、落成下一步等优点，本地 Skill 已有对应规则；没有必要复制阶段分数、固定口吻或进攻术语。

## 决策

本轮不修改 `relationship-review`，版本保持 0.1.1，状态保持 `experimental`。当前包没有出现需修复的失败；同时，无 Skill 也为 19/19，所以本轮没有证明严格正确率提升。两个偏好是有用信号，样本量不足以支持稳定优势或成熟度升级。

六题不加入登记的 active 用例。它们作为独立三臂 pilot 保留，避免把已经看过的比较题当成未来一般化验证。后续若继续测关系 Skill，优先使用新题和多次重复，检查来源归属冲突、发言人模糊、用户要求操控时的自然拒绝，以及短回复约束下能否同时保留边界。

隐式发现门禁仍未通过。本轮完整包内联只测加载后的指令价值，不能证明自然请求会自动调用 Skill。

## 校验

- 固定上游五个文件的 SHA-256 与 `provenance.json` 全部一致；
- 正式生成 18/18 有效，三臂各 6 条；
- `frozen.json`、`records.json`、匿名 packet、key、完成评分表和揭盲结果的 SHA-256 均写入机器报告；
- `python scripts/validate_collection.py`：通过；
- `python -m unittest discover -s tests -v`：64 项中 63 项通过，1 项因 Windows 无符号链接权限跳过。

材料：

- [冻结协议与六个任务](../evaluations/comparisons/relationship-three-arm-04/README.md)
- [脱敏机器诊断](../evaluations/reports/relationship-three-arm-round-14-diagnostic.json)
- [当前关系复盘 Skill](../skills/relationships/relationship-review/SKILL.md)
- [LoveHelper 固定来源](../evaluations/fixtures/upstreams/love-helper/1e391e26fd1c1bfee06e4daa9b439086a098a49b/provenance.json)
