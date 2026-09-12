# Round 26 独立冻结前复核

日期：2026-09-13

## 结论

未发现仍未解决的 P0–P3 问题。当前候选可以冻结，但这只批准冻结协议与运行基础设施，不批准修改 `conversation-rehearsal`，也不构成正式 80 条轨迹的可靠性结论。

复核期间曾发现两项会影响门禁解释的问题：baseline 将冻结令牌嵌入说明文字时未计为泄漏，以及裸 `skill` 子串会误伤 `skillful` 等普通正文。当前字节已改为检测 baseline 输出中包含的完整冻结令牌，并以路径标记或明确的加载/读取/运行/使用表达识别过程播报；对应负向测试已通过。这两项在本报告定稿时均已关闭。

## 复核范围与发现

- canary 与 business 是两个独立队列。canary 的 probe 臂用只存在于合成 `SKILL.md` 的两个令牌证明显式加载机制；business 只检查 `conversation-rehearsal` 轨迹的单一最终消息、事件绑定、策略阻断、回合完整性与过程播报，不做回答质量评分。通用 Promptfoo 摘要器会拒绝 `operational` 类型，避免误入质量盲评。
- baseline 的准备后提示不含两个冻结令牌，也不含显式 Skill 调用前缀；baseline 执行 fixture 为空。冻结令牌虽然存在于准备目录的断言元数据和协议中，但 native runner 只把对应 arm 的执行 fixture 复制到独立临时工作区，并只提交 `vars.prompt`，因此这些评分数据不会进入 baseline 模型上下文。
- runner 对每个 job 都保留一条结果。超时和非零退出保留原始输出、JSONL、stderr 与哈希；job 级异常保留 `setup_error` 和无效轨迹。normalizer 要求完整的 case × arm × repetition 键集合，不能通过删除失败轨迹得到完整运行。analyzer 将失败保留为带原因和证据哈希的 incident。
- 四个门禁量分别计算：两个 baseline 臂只以 `attempts - technical_valid` 计技术失败；canary probe 以全部 operational failure 计 Skill 失败；canary baseline 以完整冻结令牌是否出现在输出中计 secret leak；business ours 以全部 operational failure 计业务 Skill 失败。baseline 的非技术正文诊断可以留在 incident 中，但不会混入 baseline technical failure。
- protocol 绑定 preparer、runner、normalizer、analyzer、两个 spec 和两个 Skill 包的 SHA-256。analyzer 在写结果前验证两个 run，并要求 `--output` 位于所提供的任一 run 目录内；它不能借分析命令向业务 Skill 目录新增文件。当前工作树中 `skills/relationships/conversation-rehearsal` 与 `catalog/collection.json` 均无差异，协议和结果决策也固定 `skill_change_authorized: false`。

## 80 条轨迹独立重算

每个队列均为 2 cases × 2 arms × 10 repetitions = 40 条唯一单轮轨迹，两个队列合计 80 条。按 runner 的 JSON 序列化和 `random.Random(260913).shuffle` 独立重算：

- canary：40/40 个唯一 job，顺序不同于生成前顺序，job-order SHA-256 为 `304aa2906a61f56333f755bd2f7a14611e938d0c022b78f9e4da64fc808c8619`。
- business：40/40 个唯一 job，顺序不同于生成前顺序，job-order SHA-256 为 `4532f45c5acb54bf3eea761f3ce2a322aed288f9aa8dc28de9bc3e350fcba492`。

runner 按该随机列表向线程池提交任务，并在 `run-meta.json` 保存列表和哈希；最终 `native-results.json` 的排序只用于稳定存储，不改变提交顺序。analyzer 会从冻结 cases、arms、重复数和种子重新生成完整键集合与顺序，拒绝缺失、重复、未知或顺序哈希不符的运行。

## 忽略目录中的真实预检

两个预检目录均由 `.gitignore` 的 `evaluations/runs/` 规则忽略。独立读取并重新验证 `frozen.json`、`run-meta.json`、prepared 输入、执行 fixture、`native-results.json` 和 raw events 后得到：

- canary：4/4 technical valid，4/4 operational success；probe 两条输出分别严格等于对应冻结令牌，baseline 两条均未包含令牌；提交顺序哈希 `08a7cce1edbda5c5f311e9a02f4b2a0a7d62188355bb9904056044d0ab875da1`。
- business：4/4 technical valid，4/4 operational success；baseline 与 ours 均为 2/2；提交顺序哈希 `2021408dbb41d2828b3b7cafb187a0013bbb2cf686cb6e8463fbe1e2c80da2d3`。
- `preflight-validation.md` 列出的 10 个文件 SHA-256 全部与 raw 文件一致；两个 Skill package 哈希和两个 job-order 哈希也与 frozen/run metadata 一致。

预检只覆盖每个 case/arm 一次，共 8 条轨迹。它证明候选协议在该次主机环境可运行，但不能替代正式的 80 条轨迹，不能与正式结果拼接，也不能估计长期失败率为零。

## 验证记录

- `git diff --check`：通过。
- `python scripts/validate_collection.py`：通过。
- `python -m unittest discover -s tests -v`：137 项通过，1 项因 Windows 缺少创建符号链接权限而跳过；无失败。
- 额外 read-only 重算：两个正式队列共 80 个唯一 job；两个预检队列共 8 条 raw 轨迹，均能由当前 normalizer 与 analyzer 重新分类。

## 限制与冻结建议

canary 证明的是同一宿主、模型、显式调用方式和隔离配置下的合成 Skill 加载机制，并不逐条证明 business 队列中的 `conversation-rehearsal` 正文确实被加载。business 队列只回答输出传输与运行完整性问题。正式运行仍必须从冻结提交重新准备两个全新目录，各执行 10 次，不重试失败，不筛选或拼接轨迹，并用冻结 analyzer 统一生成门禁结论。

建议冻结当前协议、spec、两组 Skill 包和四个基础设施文件的当前哈希，然后执行正式运行。任何正式失败都应保留为数据并只打开基础设施调查；不得据此修改业务 Skill、版本、catalog 状态或 evidence。
