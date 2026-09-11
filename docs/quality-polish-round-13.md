# 第十三轮质量打磨：隐式路由证据门禁

日期：2026-09-11

## 目标

第十二轮已经证明 `meeting-communication-review` 0.1.2 在显式加载的冻结任务中有定向收益，但还不能证明自然任务会自动加载它。本轮先补齐隐式路由的可观测性，再决定是否运行会议业务对照。

此前的 canary 只检查隐藏令牌。模型即使没有读取技能正文，也可能声称使用了技能或猜出一个类似令牌。Promptfoo 0.123.0 的 Codex SDK provider 已提供 `skill-used`／`not-skill-used` 断言；其信号来自成功读取目标 `SKILL.md` 的命令，属于启发式轨迹证据。

## 基建修订

准备器现在对 `invocation: implicit` 自动加入两层断言：

- 项目技能实验臂必须出现目标技能的 `skill-used`；
- 无技能基线必须出现对应的 `not-skill-used`。

摘要器会提取 `skillCalls` 与 `attemptedSkillCalls`，按实验臂统计目标技能读取，并为质量评测生成单独的 `routing_gate`。完整输出存在但读取轨迹缺失时，质量评测状态为 `routing-failed`，不会进入有效质量结论。显式 `$skill-id` 可能由运行时直接注入正文而不产生 shell 读取，因此显式评测继续使用输出与冻结标准，不强制该启发式信号。

这层规则有四类回归：准备结果包含正负路由断言；隐式发现有轨迹时通过、无轨迹时失败；隐式质量有轨迹时进入盲评、无轨迹时停止；显式发现原行为保持不变。

## 真实 canary

在提交 `5e9b030fe3edefe2d3ed98d651a5e9cef21528cd` 上运行同一份合成自然请求，模型为 `gpt-5.6-sol`、中等推理，每臂一次。项目技能只安装在隔离 Git 根的 `.agents/skills/discovery-token/`，两臂使用独立 HOME/CODEX_HOME，断网并关闭网页搜索、apps、plugins 与多代理。

| 实验臂 | 最终输出 | 目标 `skillCalls` | Promptfoo 判定 |
| --- | --- | ---: | --- |
| 无技能基线 | `NATIVE_SKILL_DISCOVERY_PROBE_OK` | 0 | 未误读技能，但隐藏令牌不匹配 |
| 项目技能 | `NATIVE_SKILL_DISCOVERY_PROBE_OK` | 0 | `Missing required skill(s): discovery-token` |

两条 provider 响应完整，没有 MCP 或网页搜索条目，传输与结果完整性门禁有效；隐式发现门禁失败。项目技能臂没有返回只存在于 `SKILL.md` 的 `CERULEAN-FALCON-SKILL`，也没有成功读取轨迹。这个结果比“模型说自己用了技能”更严格地说明：当前宿主尚不能为该隔离配置提供隐式正文加载证据。

本轮还尝试把一次性执行目录移到仓库授权根内，并直接请求读取项目相对 `SKILL.md`；模型仍报告读取被隔离策略拒绝，provider 也没有成功读取轨迹。该目录调整没有解决问题，已经撤回，没有进入提交。

## 决策与影响

发现门禁未过，因此没有继续运行会议业务的隐式质量对照，避免把“未加载技能时碰巧答得好”写成技能收益，也避免无效消耗额度。

第十二轮的显式三臂结论保持不变：0.1.2 在三题聚焦对照中为 9/9 完美输出，另一次复跑为 8/9；这些数字只支持显式加载条件。`meeting-communication-review` 仍为 0.1.2、`experimental`，本轮没有修改技能包、活动用例或 catalog。

后续需要在能产生成功 `SKILL.md` 读取轨迹的 Codex SDK 宿主上先通过合成 canary，再运行同任务 baseline／隐式技能对照。独立人工盲评仍是另一项未完成门槛。

## 校验

- `python scripts/validate_collection.py`：通过；
- `python -m unittest discover -s tests -v`：共执行 59 项，58 项通过，1 项因 Windows 无符号链接权限跳过；
- Promptfoo trace canary：2/2 响应完整，隐式路由门禁失败，失败已保留。

材料：

- [脱敏诊断证据](../evaluations/reports/promptfoo-implicit-routing-round-13-diagnostic.json)
- [Promptfoo 原生评测说明](../evaluations/promptfoo/README.md)
- [隐式发现规格](../evaluations/promptfoo/implicit-discovery.json)
- [第十二轮会议质量报告](quality-polish-round-12.md)
- [Promptfoo: Test Agent Skills](https://www.promptfoo.dev/docs/guides/test-agent-skills/)
- [Promptfoo: OpenAI Codex SDK](https://www.promptfoo.dev/docs/providers/openai-codex-sdk/)
