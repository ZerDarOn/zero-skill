# 当前故障证据排查三方前向比较

本轮比较无 Skill、`debug-evidence-triage` 0.1.1 与 Superpowers 固定提交的 `systematic-debugging`。Round 22 已覆盖时钟偏移、运行版本、验证等价性、副作用安全和决定性最小复现；本轮只用六个未参与当前 Skill 编写的新合成表面，检查观测是否覆盖原失败、混杂变量能否拆开，以及重试或重启后能否保持执行身份。

## 固定设计

三臂使用同一个 `gpt-5.6-sol`、medium、只读隔离配置、公共提示与任务正文。两个 Skill 臂采用项目级显式调用。每题每臂重复三次，共 `6 × 3 × 3 = 54` 份输出、18 个三候选匿名评阅项和 216 个布尔判断。失败保留且不重试。

六题按三个机制各两题组织：

- `observation-coverage`：监控排除了原客户端与200空结果；完成态查询遗漏停滞任务。
- `causal-discrimination`：一次发布同时更改索引与超时；feature flag 与payload大小完全混杂。
- `execution-identity-continuity`：同一job ID下不同重试attempt不能拼链；同一session ID跨boot不能当作同一进程连续状态。

每题四项硬标准，其中 `core_criteria` 在运行前指定。候选门槛要求同一机制的两题都出现当前 Skill 至少 `2/3` 次核心失败，同时 baseline 每题最多 `1/3` 次核心失败，且54份输出全部有效。满足门槛只允许打开最小候选设计，不直接改 Skill、升版或改变 catalog；上游只作设计参照，不参与本地改版门槛。

## 上游边界

上游固定为 `obra/superpowers@b36e0829c6d0140e93cfef2ca599b1b07d4a7797`，运行包只包含 `systematic-debugging` 及其同目录文件引用，并把仓库 MIT LICENSE 一并放到包根。所有同目录文件引用均在包内闭合，来源字节保持不变，布局组装记录在 `provenance.json`；`find-polluter.sh` 仅作为上游文本资源保留，不安装、不执行。原 Skill 在修复和完成验证阶段还会调用仓库内另两个 sibling skills（`test-driven-development` 与 `verification-before-completion`）；本轮只要求只读诊断建议，不进入这些阶段，因此两者没有组装进运行包，也不能把本轮结果外推到完整上游工作流。

Superpowers 的系统调试流程还包含实际复现、改码、测试驱动与完成前验证。本比较只评估题目材料内的只读诊断建议，不能作为完整调试流程或仓库的一般排名。
