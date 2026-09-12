# Round 26 独立运行后复核

日期：2026-09-13

## 结论

未发现仍未解决的 P0–P3 问题。两个正式 ignored raw run、冻结协议与 analyzer、联合分析文件、候选机器报告和 `formal-results.md` 相互一致。独立重算结果为 80/80 operational success，四项零容忍门禁均为 0，当前 `qualified` 结论成立。

本结论只确认本轮运行可靠性门禁及证据投影，不构成回答质量评分，也不证明每一条 business 轨迹都加载了 `conversation-rehearsal`。

复核中曾发现 `formal-results.md` 将已经写入机器报告的联合分析 SHA-256 表述为未来动作。该 P3 文档问题已在本报告定稿前修正，当前文档明确指向 canary 正式目录中的 `invocation-reliability-analysis.json` 及其现有指纹，因此没有遗留 finding。

## 原始运行与冻结绑定

两个正式目录均受 `.gitignore` 的 `evaluations/runs/` 规则排除。冻结提交 `c773fb138b8a08848a151bbd0061258a49a2e039` 同时是当前 `main`、`origin/main` 和两个正式运行所声明的 freeze commit；从该提交到复核时，业务 Skill、catalog 和 active cases 没有差异。

协议 SHA-256 为 `85387b47d71a25b4c19c2cb10269afe2931b8e0aae7cb029fd7a3ccc32fe403f`。协议绑定的基础设施文件均与当前字节及机器报告一致：

- preparer：`4eca5a4c2caeffbeca6663ecf49ce8f9e293f86372593abfb3d794ea1d1b788b`
- runner：`cac3e238d717f7a268d9b6800bec11002eaa5d3e54ddf2458f65a2983e9912b5`
- normalizer：`91c336bc71b409adabe8c39668cbbb98b72fcb6bafcfc05c21faf899455daa9d`
- analyzer：`e384a6bab11e8c52600d60de0776fb3368c12fc4ff9b9ce67e50835c95c8c953`

canary 的 spec、cases、prepared config、prepared tests、Skill package、`frozen.json`、`run-meta.json`、`native-results.json` 和 job-order 指纹全部与 frozen、protocol 和机器报告的相应字段一致。关键 raw 指纹为：

- Skill package：`0d77227b068fd544342082d48d852a7549252058cf2c266ebce61c43e95aeb06`
- frozen：`67b92449e1c2c7cde1a50bcd2dacc3e8c06bb271d4b42b448dbaff3be120316c`
- run metadata：`dd6aa8c899f6d14a1e739044d944ac8bcb4cf63d2a56947658425197f2daa44a`
- native results：`e0bb6b08e1af9c52ed6ac6bf9b8dabd9ba2d084f2c699b697e765dc669289214`
- job order：`304aa2906a61f56333f755bd2f7a14611e938d0c022b78f9e4da64fc808c8619`

business 的同组绑定也全部一致：

- Skill package：`b09fcd8955cce840d3ab9fb9acc19f29d6bff371d66b4b7ccfabb3d9f53e3ff9`
- frozen：`7d9714a121137c52964c91c824cd5c2ed06156a74329e652c9eed4584c6d85bd`
- run metadata：`e7d96b82678b4daa76a305cf5bc9b5603e02b5f4045c1bb521ba1f1da66b48d3`
- native results：`054553c927eaaec467aaca2437397b7d94f86f4983c50bb024af67976f8daca0`
- job order：`4532f45c5acb54bf3eea761f3ce2a322aed288f9aa8dc28de9bc3e350fcba492`

联合分析文件的 SHA-256 为 `d551882dc00a64c4ef20fdfa27c614df3b5d4153b6732f59b9c2d616b0a92e35`。在禁止写入的独立复算中执行同一 analyzer 的全部验证与分类路径，所得对象与该 JSON 完全相等。

## 80 条轨迹独立重算

两个队列各自包含 2 cases × 2 arms × 10 repetitions = 40 条唯一轨迹，合计 80 条。normalizer 从 raw JSONL 重新校验了每条输出、事件、stderr、线程绑定、回合完成事件、禁止事件、命令、prompt、prior-output 链和对应 SHA-256；两个 run 都覆盖完整键集合，没有重复、未知或缺失轨迹。

独立分类结果：

| 队列与臂 | 尝试 | technical valid | operational success | operational failure |
| --- | ---: | ---: | ---: | ---: |
| canary baseline | 20 | 20 | 20 | 0 |
| canary probe | 20 | 20 | 20 | 0 |
| business baseline | 20 | 20 | 20 | 0 |
| business `conversation-rehearsal` | 20 | 20 | 20 | 0 |

canary probe 的两道题分别连续 10 次严格返回对应冻结令牌；canary baseline 的 20 条输出均未包含相应令牌。80 条轨迹均只有一条 agent message，并与 output-last 绑定；没有策略阻断、过程播报、禁止 item、超时、非零退出、损坏 JSONL 或线程/回合绑定错误。联合分析中的 incidents 为空。

四项零容忍门禁独立重算为：

- baseline technical failures：0
- canary Skill failures：0
- canary secret leaks：0
- business Skill failures：0

所有上限均为 0，因此四项检查均通过。失败没有被筛除：normalizer 要求完整的 80 个 case/arm/repetition 键，runner 与 run metadata 均记录 40/40 + 40/40，raw results 中也实际存在这 80 条轨迹。

## 机器报告与文字报告

机器报告中的两组 arm 汇总与联合分析逐字段相等。它保存的 80 条 `trajectory_evidence` 使用 trajectory id 稳定排序；按 id 与独立分类对齐后，全部分类、失败原因、技术有效性、消息数和三个证据哈希逐字段一致。

描述性运行数据也可从 raw usage 与 duration 重算：business baseline 中位耗时 `7414.0 ms`，输入加输出 token 为 `195259`；business Skill 臂为 `8984.5 ms` 和 `215422`，相对差异分别为 `21.2%` 与 `10.3%`。文字报告明确将其限制为本次开销记录，不称为稳定性能基准或质量分数。

机器报告和 `formal-results.md` 都明确：

- `quality_scored` 为 false，不改变质量结论或成熟度；
- canary 只证明合成 probe 自身正文在同一机制下被加载；
- business 只衡量输出传输和运行完整性，不逐条证明 `conversation-rehearsal` 正文被加载；
- 80/80 不能证明长期失败率为零；
- 不修改业务 Skill、版本、catalog、evidence 或 active cases，`skill_change_authorized` 为 false。

因此没有发现将运行可靠性结果越界扩展为质量结论、长期零故障结论或逐条业务 Skill 加载证明的表述。

## 验证与限制

- `git diff --check`：通过。
- `python scripts/validate_collection.py`：通过。
- `python -m unittest discover -s tests -v`：137 项通过，1 项因 Windows 缺少创建符号链接权限而跳过；无失败。
- 独立 raw 重算：80/80 technical valid，80/80 operational success，四项门禁均为 0；联合分析对象完全一致；两组 source/prepared/raw/job-order/package hashes 全部一致。

限制仍与正式报告一致：样本只覆盖一个主机、一个模型、一个 reasoning effort、两道 canary 题和两道 business 题，并采用 4 worker 并发。canary 的机制证据不能迁移成每条 business 轨迹的加载证据；本轮也没有重新评分业务回答质量。

建议接受当前 `qualified` 运行结论，并在把本审查加入 review chain 后冻结机器报告的最终 evidence projection。该建议不授权修改 `conversation-rehearsal` 或提升其版本、catalog 状态与 evidence。
