# Round 25 最终独立工程审查

日期：2026-09-13

## Findings

未发现未解决的 P0–P3。本次审查没有修改 Round 25 的协议、原始运行、评分、报告、活动用例、Skill 或 catalog；仅新增本审查记录。当前结果可以提交。

## 证据链复算

从 v2 本机原始产物重新核对了 frozen、native results、匿名 packet、揭盲 key、盲评表单、scorer 输出与 analyzer 输出。12 个 review id、24 个唯一轨迹、A/B 映射、thread id、逐回合输出、输出哈希、96 个布尔判定和 12 个偏好均能一一对应；机器报告内嵌的题面、输出、评分及 arm 映射与原始链一致。

报告中的源文件、prepared config/tests、Skill 包、v2 运行产物及揭盲后复核均有 SHA-256 绑定。聚合结果可从报告项目重算为 baseline `48/48`、`12/12` 完整、0 个唯一偏好，以及 ours `48/48`、`12/12` 完整、0 个唯一偏好。两个机制下两臂的第一项标准均为 `0/3` 失败，因此没有 qualifying case，候选门槛为 `false`。固定证据投影覆盖冻结提交、执行设施提交、源、prepared 产物、原始产物、评审链、arm、完整项目、v1 无效尝试、分析与决定；测试会拒绝在重新计算投影哈希后协同修改输出、评分、门槛、无效运行计分状态或复核哈希。

## v1、v2 与运行可靠性

v1 原始目录保持 `23/24` 技术有效，唯一无效轨迹为 `generic-counterpart-no-boundary-detour--ours--r2`：该回合有两个 `agent_message`，输出文件只对应最后一个消息，因而不满足唯一消息门槛。v1 标记为 `infrastructure-invalid`、`quality_scored: false`，其 23 个成功结果没有拼入 v2。

提交 `a1fe2c8a9d358656c34034dc296b6289fddf117d` 只修复失败证据保全：runner 在停止无效轨迹前保留事件中已观察到的真实 thread id；summarizer 兼容旧失败记录的特定空顶层 thread id 形状，同时继续拒绝错误的非空 thread id。定向负向测试覆盖该兼容分支和伪造 thread id 拒绝。v2 在相同冻结 spec、cases、prepared 产物和 Skill 包下独立完整重跑，达到 `24/24`，没有复用 v1 结果。公开文字明确把 v1 留作一次显式 Skill 调用波动观察，并明确 v2 未复现不能证明该风险已消失。

## 表述与仓库状态

README、轮次文档和机器报告都把评审者写为模型评审者；文档还明确说明文件访问边界来自评审者声明，并非外部访问审计。结果没有写成人工验收，也没有据此提升 Skill：`conversation-rehearsal` 仍为 0.1.1、`experimental`、`evidence: null`，Skill 文件和 catalog 均未改动。四题使用合成姓名与合成情境，活动用例从 144 增至 148，其中该技能从 11 增至 15；文本均为有效 UTF-8、LF，未发现真实聊天、账户、密钥或用户资料。

## 验证

- `python -m unittest tests.test_conversation_explicit_boundary_round25 -v`：7 项通过。
- 模拟没有本机 raw run 的 checkout：同一测试集 6 项通过，raw hash 测试按设计跳过 1 项。
- `python -m unittest tests.test_native_resume_comparison -v`：23 项通过。
- `python scripts/validate_collection.py`：通过。
- `git diff --check`：通过。

剩余限制与公开文档一致：这是单模型、单推理等级、四道合成单轮题和模型盲评；它不能证明一般等价、真实人际效果、隐式路由质量或显式 Skill 调用的长期稳定性。
