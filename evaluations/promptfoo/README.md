# Promptfoo 原生 Skill 对照

这一层使用 Promptfoo 调用真实 Codex SDK，让 Codex 从各实验目录的 `.agents/skills/` 发现技能。它补充原有显式拼接诊断，不替代冻结用例、逐项标准和人工复核。

## 评测边界

- 同一份合成任务分别进入无技能、本仓库技能和固定上游技能目录。
- 每个实验臂在仓库外拥有独立 Git 根、`HOME`、`USERPROFILE` 和 `CODEX_HOME`，避免继承仓库规则或用户 Skill。
- 临时 `CODEX_HOME` 只复制现有 `auth.json`；运行结束由系统临时目录清理，不保存或散列凭据。
- Codex 默认采用只读沙箱；诊断规格可显式选择仅限临时实验根的 `workspace-write`。网络、网页搜索、宿主 apps、plugins 和多代理能力均关闭，不继承完整进程环境。
- 模型、推理等级、用例、Promptfoo 配置和完整 Skill 包指纹写入 `frozen.json`。准备后修改配置、测试或包快照会被拒绝。
- 结果缺失、实验臂错配、provider 响应不完整、MCP 或网页搜索轨迹都会使基础设施门禁失败。
- 原始结果保存在被忽略的 `evaluations/runs/`。Promptfoo 通过或隐藏令牌命中都不能单独把 Skill 标为 `verified`。

当前只把项目级 `.agents/skills` 作为合格安装路径。独立用户目录安装在当前 Promptfoo/Codex 组合的诊断中未被发现；`home` 与 `both` 仅保留为实验模式。

## 先跑发现门禁

任何质量评测前先证明项目级 Skill 能被当前运行时发现：

```sh
python evaluations/promptfoo/prepare_skill_comparison.py --spec evaluations/promptfoo/discovery.json
python evaluations/promptfoo/run_skill_comparison.py --run <上一步输出目录>
python evaluations/promptfoo/summarize_skill_comparison.py --run <同一目录>
```

只有 `summary.json` 中 `status: "passed"` 才继续。该门禁要求项目 Skill 精确返回只存在于合成 `SKILL.md` 中的隐藏令牌，同时基线不得命中，所有实验臂不得调用 MCP 或网页搜索。

显式门禁通过后，可另跑隐式发现门禁：

```sh
python evaluations/promptfoo/prepare_skill_comparison.py --spec evaluations/promptfoo/implicit-discovery.json
python evaluations/promptfoo/run_skill_comparison.py --run <上一步输出目录>
python evaluations/promptfoo/summarize_skill_comparison.py --run <同一目录>
```

隐式门禁不给任务添加 `$skill-id`，无技能与项目 Skill 两组收到完全相同的自然请求。准备器会为项目 Skill 实验臂追加 `skill-used`，并为基线追加 `not-skill-used`；通过需要隐藏令牌与成功读取 `SKILL.md` 的轨迹同时成立。它只证明当前运行时能按描述发现这个合成探针，不证明业务 Skill 一定会自动触发或回答质量更高。

当前宿主的隐式门禁仍未通过；直接指定项目内 Skill 文件的 read-only 与 workspace-write 诊断也未读到隐藏令牌。2026-09-11 加入 trace 断言后的复跑中，项目技能臂 `skillCalls` 为0，Promptfoo 明确报告缺少 `discovery-token`。详见[第十三轮隐式路由证据门禁](../../docs/quality-polish-round-13.md)和[最新脱敏证据](../reports/promptfoo-implicit-routing-round-13-diagnostic.json)；早期诊断见[第七轮评测校准](../../docs/quality-evaluation-round-07.md)。在读取链路解决前，这项结果只能记为宿主评测阻塞，不能判成业务 Skill 路由失败。

Promptfoo 的 `skillCalls` 是根据成功读取 `SKILL.md` 的命令推断出的启发式信号。隐式评测缺少该信号时，本仓库将其记为未证明路由，并以 `routing-failed` 停止质量结论。原生显式 `$skill-id` 可能由运行时直接加载正文而没有命令轨迹，因此显式评测不强制这项断言。

## 三方质量评测

`evaluations/comparisons/prose-three-arm-01/promptfoo.json` 比较：

- `baseline`：没有项目 Skill；
- `ours`：当前 `prose-polish` 完整包；
- `upstream`：固定提交的 Humanizer 3.0.0。

Skill 配置中的 `invocation` 可设为：

- `explicit`：仅该实验臂的任务前增加显式 `$skill-id` 调用，适合测“应用 Skill 后是否有帮助”；
- `implicit`：各组收到完全相同的自然任务，同时要求技能臂出现 `skill-used`、基线出现 `not-skill-used`，适合另测自动路由。

先做一个用例、一次重复的预检：

```sh
python evaluations/promptfoo/prepare_skill_comparison.py --spec evaluations/comparisons/prose-three-arm-01/promptfoo.json --case W04
python evaluations/promptfoo/run_skill_comparison.py --run <上一步输出目录> --repeat 1
python evaluations/promptfoo/summarize_skill_comparison.py --run <同一目录>
```

确认基础设施有效后，再准备新目录运行完整计划；不要复用预检目录：

```sh
python evaluations/promptfoo/prepare_skill_comparison.py --spec evaluations/comparisons/prose-three-arm-01/promptfoo.json
python evaluations/promptfoo/run_skill_comparison.py --run <上一步输出目录>
python evaluations/promptfoo/summarize_skill_comparison.py --run <同一目录>
```

摘要器会生成：

- `summary.json`：覆盖数、基础设施门禁、隐式路由轨迹、每臂 token、成本和延迟；
- `blind-review.json`：不含实验臂或 Skill 名称的匿名候选；
- `blind-review-form.json`：待填写的逐项布尔评分；
- `blind-review-key.json`：揭盲映射，评分完成前不要打开。

填写评分表的副本并补充 `reviewer.kind` 后，执行：

```sh
python evaluations/promptfoo/score_blind_review.py --run <运行目录> --review <已完成评分文件>
```

计分器会拒绝缺项、`null`、候选错配或被篡改的盲评材料，随后生成按实验臂揭盲的结果。模型辅助评阅必须明确标记，不能写成人工独立评审。

运行器固定使用 Promptfoo 0.123.0，通过 `npx --yes` 获取。真实运行会消耗当前 Codex 账户额度；准备、摘要和单元测试不会调用模型。

首轮实际证据见 [Promptfoo 原生 Skill 评测基建与首轮 pilot](../../docs/promptfoo-native-skill-evaluation-pilot.md)和[脱敏诊断证据](../reports/promptfoo-native-skill-evaluation-pilot-diagnostic.json)。

后续的旧版／新版定向回归见[第六轮质量打磨报告](../../docs/quality-polish-round-06.md)和[0.1.2 脱敏证据](../reports/prose-preservation-0.1.2-promptfoo-diagnostic.json)。

LF 规范化后的当前包复跑与硬长度上限修订见[第九轮质量打磨](../../docs/quality-polish-round-09.md)和[0.1.3 脱敏证据](../reports/prose-output-limits-0.1.3-promptfoo-diagnostic.json)。

参考：

- [Promptfoo: Test Agent Skills](https://www.promptfoo.dev/docs/guides/test-agent-skills/)
- [Promptfoo: OpenAI Codex SDK](https://www.promptfoo.dev/docs/providers/openai-codex-sdk/)
- [OpenAI: Build skills](https://developers.openai.com/codex/skills)
- [OpenAI: Evaluation best practices](https://developers.openai.com/api/docs/guides/evaluation-best-practices)
