# 首批行为评测计划

## 目标与范围

本轮验证两个 `experimental` 技能在真实、隔离模型会话中的行为增益，不把结构检查当作行为证据，也不据此标记 `verified`。

- 技能：`person-evidence-analysis`、`relationship-review`
- 用例：仅运行 `expected_route` 非空的 8 个用例，每个用例各跑 baseline 与 skill，共 16 次
- 暂不运行：4 个 `expected_route: null` 的邻接路由用例；显式加载技能不能证明自动发现或自动路由
- 首批门槛：先跑 `sparse-reply`、`contradiction`、`reply-first`、`clear-decline` 四组配对；若隔离执行稳定，再补齐其余四组

## 隔离与可复现性

- 执行器：本机 Codex CLI 非交互 `exec`
- 会话：`--ephemeral --ignore-user-config`
- 模型：`gpt-5.6-sol`
- 推理强度：`model_reasoning_effort="medium"`
- 沙箱：`read-only`
- 工作目录：使用临时隔离目录；baseline 不放仓库技能。首轮发现 Windows 只读沙箱会阻止技能会话读取临时 `SKILL.md`，因此有效 skill 运行改为在提示中内嵌完整技能包，并禁止工具调用
- 输入：会话只看到公共执行说明、原始用户请求、合成材料，以及所属组的完整技能包；不提供 `must_include`、`must_avoid` 或预期结论
- 记录：保存 CLI 版本、模型、推理强度、公共上下文、开始/结束时间、退出码、包指纹、用例指纹和原始最终输出

`model_reasoning_effort` 的键名和值范围以 OpenAI 官方 Codex 配置参考为准；CLI 参数以本机 `codex exec --help` 为准。

## 评分与修订规则

- 完成输出后，才按用例的 `must_include` / `must_avoid` 做语义评分，并写明实际证据与判定理由
- 对每一对标注相对结果：改进、无差异或退化，不预设技能一定更好
- `contradiction` 与人物技能示例内容接近，报告中单独标记其示例重叠风险，不把该项当作强泛化证据
- 只有真实输出暴露明确失败或指令冲突时才做小幅修订；一旦技能包变化，更新版本/指纹并重跑受影响用例
- 原始运行写入已忽略的 `evaluations/runs/`；评测报告写入 `docs/first-behavior-evaluation-report.md`

## 完成条件

1. 明确区分实际运行、未运行、结构检查、模型评分与人工评审。
2. 给出逐用例结果、相对比较、局限与下一阶段建议。
3. 保持两个技能为 `experimental`，除非另有独立证据、路由验证和人工评审。
4. 运行 README 规定的两条仓库检查命令，并保持本轮改动未提交、未推送。
