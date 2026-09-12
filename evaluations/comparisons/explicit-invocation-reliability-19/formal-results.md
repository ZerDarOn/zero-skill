# Round 26 正式结果

日期：2026-09-13

## 结论

冻结协议下的 80 条单轮轨迹全部完成并通过运行可靠性门禁。canary 与 business 两个队列各有 40 条轨迹，所有轨迹都只有一条最终 agent message、一次回合完成事件、唯一且匹配的 thread id，并且没有策略阻断、禁止事件、损坏 JSONL、非零退出或 Skill 加载过程播报。

- canary baseline：20/20 运行成功，冻结令牌泄漏 0 次。
- canary probe：20/20 运行成功，两道题各 10 次都精确返回对应冻结令牌。
- business baseline：20/20 运行成功。
- business `conversation-rehearsal`：20/20 运行成功。

零容忍门禁中的 baseline 技术失败、canary Skill 失败、canary 令牌泄漏和 business Skill 失败均为 0，结论为 `qualified`。

本次运行还记录了描述性开销。business baseline 的单轮中位耗时为 `7414.0 ms`，输入加输出 token 合计 `195259`；`conversation-rehearsal` 臂分别为 `8984.5 ms` 和 `215422`，在这 20 对单轮样本中高 `21.2%` 和 `10.3%`。这些数字受输出长度、缓存与并发调度影响，只用于记录本次运行成本，不能当成稳定性能基准或质量分数。

## 运行边界

两个正式目录均在冻结提交 `c773fb138b8a08848a151bbd0061258a49a2e039` 推送后重新准备，使用 `gpt-5.6-sol`、medium、只读沙箱、隔离 HOME/CODEX_HOME、关闭网络、apps、plugins 与 multi-agent。每个队列按种子 `260913` 将 40 个任务随机提交给 4 个 worker；没有补跑、筛选或拼接轨迹。

canary 用合成 Skill 的隐藏令牌验证同一执行机制确实能加载 Skill 正文。business 只验证真实 `conversation-rehearsal` 队列的输出传输和运行完整性；它不逐条证明业务 Skill 正文被加载，也不重新评价回答质量。

## 原始证据指纹

正式原始目录由 `.gitignore` 排除，仓库中的机器报告保存完整的 80 条分类投影和以下原始文件 SHA-256，以便本地存在 raw artifacts 时重算。

| 队列 | frozen.json | run-meta.json | native-results.json | job order |
| --- | --- | --- | --- | --- |
| canary | `67b92449e1c2c7cde1a50bcd2dacc3e8c06bb271d4b42b448dbaff3be120316c` | `dd6aa8c899f6d14a1e739044d944ac8bcb4cf63d2a56947658425197f2daa44a` | `e0bb6b08e1af9c52ed6ac6bf9b8dabd9ba2d084f2c699b697e765dc669289214` | `304aa2906a61f56333f755bd2f7a14611e938d0c022b78f9e4da64fc808c8619` |
| business | `7d9714a121137c52964c91c824cd5c2ed06156a74329e652c9eed4584c6d85bd` | `e7d96b82678b4daa76a305cf5bc9b5603e02b5f4045c1bb521ba1f1da66b48d3` | `054553c927eaaec467aaca2437397b7d94f86f4983c50bb024af67976f8daca0` | `4532f45c5acb54bf3eea761f3ce2a322aed288f9aa8dc28de9bc3e350fcba492` |

联合分析文件位于 canary 正式目录的 `invocation-reliability-analysis.json`，SHA-256 为 `d551882dc00a64c4ef20fdfa27c614df3b5d4153b6732f59b9c2d616b0a92e35`；机器报告记录同一指纹。

## 限制与决策

80/80 只说明本次主机、模型、配置和样本下没有复现第 25 轮 v1 的单次失效，不能证明长期失败率为零。样本规模不足以给出狭窄的故障率置信上界，也不能把 canary 的加载证明转移为每一条 business 轨迹的加载证明。

本轮不修改 `conversation-rehearsal`、版本、catalog 状态、evidence 或 active cases。结果只关闭本轮的基础设施调查门禁；它不提升 Skill 的质量评分或成熟度。
