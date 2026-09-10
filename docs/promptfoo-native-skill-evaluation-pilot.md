# Promptfoo 原生 Skill 评测基建与首轮 pilot

日期：2026-09-11

本轮把 Promptfoo 0.123.0 的 `openai:codex-sdk` provider 接入仓库，用真实 Codex Skill 发现代替把 `SKILL.md` 直接拼进用户提示。目标是先证明 Skill 确实进入运行时，再比较无 Skill、本仓库 Skill 和固定上游 Skill 的输出。

## 评测链路

评测分为四步：

1. 准备器复制完整 Skill 包，为每个实验臂生成独立目录，并冻结模型、用例、Promptfoo 配置和包指纹。
2. 运行器把材料复制到仓库外的临时目录，为每个实验臂创建独立 Git 根、`HOME`、`USERPROFILE` 和 `CODEX_HOME`。它只复制现有 Codex 登录文件，结束后由临时目录清理。
3. Codex 使用只读沙箱；网络、网页搜索、宿主 apps、plugins 和多代理能力均关闭。结果缺失、实验臂错配、外部 MCP 或网页搜索轨迹会使基础设施门禁失败。
4. 摘要器先核对冻结哈希与覆盖数，再把候选输出随机匿名化。评阅完成后，单独的计分器验证每项标准都是布尔判定，最后才读取映射键并汇总各实验臂。

Promptfoo 的 `skillCalls` 只识别通过命令直接读取 `SKILL.md` 的情况。此次原生显式调用由运行时加载 Skill，没有产生这种命令事件，因此本仓库不把缺失的 `skillCalls` 当作未加载证据。发现门禁改用只存在于合成 Skill 正文中的隐藏令牌，并要求无 Skill 基线不得命中。

## 发现门禁

正式探针为 `promptfoo-native-discovery-canary-06`，使用 `gpt-5.6-sol`、medium、每臂一次：

- 无 Skill 基线没有命中隐藏令牌；
- 项目级 `.agents/skills/discovery-token` 精确返回 `CERULEAN-FALCON-SKILL`；
- 两个实验臂均没有 MCP 或网页搜索轨迹；
- 门禁状态为 `passed`。

结果 SHA-256 为 `c19b9efc831474dc0da5a37cd186fa22a1ba973b03a2c37575b5c94b3721526a`。早期探针曾在没有独立 Git 根时漏掉项目 Skill，并调用宿主 GitHub 连接器查找同名内容；该失败记录保留在本地被忽略的运行目录，促成了 Git 根和宿主集成隔离修复。

独立用户目录下的 Skill 在诊断探针中没有被当前 Promptfoo/Codex 组合发现，因此当前合格路径仅为项目级 `.agents/skills`。不能把 `home` 安装模式当作已验证路径。

## 三方质量 pilot

`prose-three-arm-native-01-explicit-pilot-r1` 使用六个预先冻结的合成润色任务。每个任务分别进入：

- `baseline`：无 Skill；
- `ours`：显式调用 `prose-polish`，包指纹 `9c3315b7…9a1`；
- `upstream`：显式调用固定提交的 Humanizer 3.0.0，包指纹 `45114696…26b`。

计划值是每臂每题三次，本轮只执行一次，共 18 次调用。结果 SHA-256 为 `aeff67da98a9fe2e398d9052fc3b18eb2f95360f865ce423bca7a2c848c581c4`。18 行结果完整，没有 provider 错误、MCP 或网页搜索轨迹。

冻结标准的模型辅助盲评结果如下。评阅者在打开映射键前逐项记录判断；这不是独立人工评审。

| 实验臂 | 标准通过 | 完整通过输出 | 盲评偏好 | 总 token | 估算成本 | 中位延迟 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 无 Skill | 22/24 | 5/6 | 1 | 58,409 | 0.120628 | 14.10 s |
| prose-polish | 22/24 | 5/6 | 2 | 64,796 | 0.163434 | 14.21 s |
| Humanizer | 22/24 | 4/6 | 2 | 98,190 | 0.300530 | 17.33 s |

相对无 Skill，`prose-polish` 总 token 增加 10.9%，估算成本增加 35.5%，中位延迟增加 0.7%；Humanizer 分别增加 68.1%、149.1% 和 22.9%。三组硬标准均为 91.67%，当前样本没有显示本仓库 Skill 带来净通过率提升。

随仓库保存的[脱敏诊断证据](../evaluations/reports/promptfoo-native-skill-evaluation-pilot-diagnostic.json)包含发现门禁输出、六题三方输出、逐项布尔评分、揭盲结果与关键散列；不包含认证信息、会话标识、临时目录或原始系统轨迹。

差异集中在两题：

- W04 的三组都在压缩通知时省略了“原定本周六”。本仓库 Skill 与基线还把“周日来不了”缩成了泛指“无法参加”；Humanizer 保留了周日条件。
- W02 中 Humanizer 把“修好一点才有意思”改成“没白折腾”，没有完整保留作者原来的主观意思；本仓库 Skill 与基线保留了该含义。

## 当前结论

这套链路已经能区分基础设施失败、Promptfoo 断言失败和真实输出差异，并能冻结失败而不把绿色状态当作质量证明。首轮 pilot 支持继续改进 `prose-polish` 的日期变更和条件限定保真；它不支持把任一 Skill 标为 `verified`，也不足以给三个实验臂做一般性排名。

在修订 Skill 前保留这组结果。下一轮先增加或强化“压缩时保留原定值、改后值和适用条件”的案例，再对新旧包做同题、同模型、至少三次重复。自然语言自动路由应另开 implicit comparison，不能与这次显式应用结果混在一起。Promptfoo 包版本已固定为 0.123.0，但导出的结果没有单独暴露底层 Codex SDK/运行时构建号，这是跨时间复现仍需补齐的版本证据。

实现与运行说明见 [Promptfoo 原生 Skill 对照](../evaluations/promptfoo/README.md)。方法参考 [Promptfoo Test Agent Skills](https://www.promptfoo.dev/docs/guides/test-agent-skills/)、[Promptfoo OpenAI Codex SDK](https://www.promptfoo.dev/docs/providers/openai-codex-sdk/) 和 [OpenAI Evaluation best practices](https://developers.openai.com/api/docs/guides/evaluation-best-practices)。

后续针对该失败的 0.1.2 修订与三次回归见[第六轮质量打磨](quality-polish-round-06.md)。
