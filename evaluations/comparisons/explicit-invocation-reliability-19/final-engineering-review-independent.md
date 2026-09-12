# Round 26 最终独立工程审查

日期：2026-09-13

## Findings

未发现未解决的 P0–P3。本次审查没有修改冻结协议、分析器、正式结果、机器报告、文档、测试、Skill、catalog 或活动用例；仅新增本审查记录。当前结果可以提交。

## 公开证据与本机原始运行

公开机器报告可在没有本机 raw run 的 checkout 中独立验证。测试从冻结 `protocol.json`、两组 spec/cases、当前基础设施文件、两个 Skill 包及报告内的 80 条 `trajectory_evidence` 重算任务全集、随机顺序哈希、arm 汇总、四项门禁和决定。固定 evidence projection 覆盖 scope、完整 experiment、analysis、decision 与 limitations；即使同步重算投影哈希，协同修改轨迹成功状态、门禁结果、复核哈希或质量决定仍会被固定指纹和字段级断言拒绝。

本机存在 ignored raw runs 时，测试会重新执行 analyzer 的 `normalize_trajectories` 和 `classify_trajectory`，逐项比对 80 条分类投影，并从原始 duration 与 usage 重算运行统计。此次复核确认：canary 与 business 各有完整的 40 条唯一轨迹，合计 `80/80` technical valid、`80/80` operational success；两道 canary 令牌在 probe 臂各精确返回 10 次，baseline 没有令牌泄漏；四项零容忍门禁的观测值均为 0。两组 source、prepared、raw artifact、job order、Skill package 与联合分析文件的 SHA-256 均与协议和报告一致，联合分析对象可完整重建且与保存文件相等。

直接扫描 80 条原始输出与 stderr，没有发现策略阻断、Skill 加载过程播报或相关读取/加载说明。每条公开轨迹均保留 output、events、stderr 三项哈希和单一 agent message 数量，报告的描述性 token 与中位延迟数据也能从 raw 重算。

## 声明边界与仓库状态

README、评测说明、正式结果和轮次文档都把本轮限定为显式调用链的运行可靠性检查。文字明确说明：canary 只证明合成 probe 自身正文在同一执行机制中加载；business 不逐条证明 `conversation-rehearsal` 正文加载，也没有重新评分回答质量；`80/80` 只代表冻结主机、模型、配置和样本中未复现，不能证明长期零故障。

从冻结提交 `c773fb138b8a08848a151bbd0061258a49a2e039` 到当前待提交结果，`skills/relationships/conversation-rehearsal`、`catalog/collection.json` 和 `evaluations/cases/` 均无差异。当前 Skill 仍为 0.1.1、`experimental`、`evidence: null`，活动用例仍为 148 条。本轮没有把运行门禁写成质量提升、成熟度提升或 `verified` 证据。

## 验证

- `python -m unittest tests.test_explicit_invocation_reliability_round26_report -v`：4 项通过。
- 模拟没有本机 raw run 的 checkout：3 项通过，raw 重算测试按设计跳过 1 项。
- `python -m unittest tests.test_explicit_invocation_reliability_round26 tests.test_invocation_reliability_analysis -v`：10 项通过。
- `python -m unittest discover -s tests -v`：141 项通过，1 项因 Windows 缺少创建符号链接权限而跳过。
- `python scripts/validate_collection.py`：通过。
- `git diff --check`：通过。

剩余限制与发布文档一致：当前样本仅覆盖一个主机、一个模型与推理等级、两个 canary 表面、两个 business 表面和项目级显式调用；不覆盖隐式发现、全局安装、其他模型、长对话或长期故障率。
