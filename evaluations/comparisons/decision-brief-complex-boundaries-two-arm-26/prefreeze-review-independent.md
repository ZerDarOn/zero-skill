# Round 33 冻结前独立复核

## Findings

当前没有开放的 P0–P3。

- **P2，已修正：两道题与活动用例表面高度同构。** 原 `approved-choice-new-parity-evidence` 基本复用了活动题 `preserve-approved-decision-history` 的离线 A/B、既有批准、竞争项新近补齐、无同口径成本和是否重开选型；原 `small-pilot-does-not-prove-rollout` 也复用了有限试点改善、未测硬阈值和推广决定。它们不能充分支持“六个未参与当前 Skill 编写的新表面”。冻结候选已分别改为无障碍资格与退出成本，以及内部可用性完成数与月末峰值 P95；机制不变，事实表面、角色、指标和决策语境已分离。与六个活动题逐题比较后，没有发现剩余题面重复。
- **P2，已修正：prepare 回归对隔离和公平性的断言不足。** 原测试只证明完整 hard criterion 字符串没有逐字出现在合并后的 prompt，并只比较单个 `SKILL.md`。当前测试额外冻结活动 cases 和 prepare 脚本字节，比较源包与复制包的完整相对文件集合及每个文件字节，要求生成项的 `vars` 只能包含 `prompt`，逐题证明 baseline 与 ours 的业务提示只差固定显式调用前缀，并证明 provider 配置除臂隔离目录和 home 路径外一致。

## 设计复核

六题按 `decision-history`、`constraint-and-denominator`、`role-and-evidence` 三个机制各两题组织，ID 与六个活动用例不相交。人工逐题核对确认，每一项 hard criterion 所需的事实、权限、状态、数值、未知项和输出范围都在题面中出现；没有依赖题外答案。冻结的 `review_policy` 要求接受语义等价答案、不要求逐字复述、不得增加后验要求，并把偏好与布尔标准分开。

两道字符上限题均有覆盖四项标准的可行示例。按 Python `len` 对中文、数字、拉丁字母和标点统一计数，示例分别为 97/120 与 91/130 字符。其余题的一个段落、三句话或无标题单段限制也足以容纳所需事实。该计数说明只证明设计可行；正式评阅仍应沿用题面与 criterion 中已经冻结的“字符含中文、数字与标点”口径。

每题前三项为核心标准。一次重复只要任一核心项为 false 就记为核心失败。候选门槛要求同一机制两题均满足 ours 每题至少 2/3 次核心失败且 baseline 每题至多 1/3 次核心失败，并要求全部 36 份输出有效。因此任一单题、单次偶发失败、两臂共同高失败或跨机制拼接都不能打开候选设计；即使通过，也只允许打开最小候选设计。

重算规模为 `6 cases × 2 arms × 3 repetitions = 36 outputs`。按每题每次将两臂组成一个匿名评阅项，共 `6 × 3 = 18` 项；每个输出四个布尔标准，共 `36 × 4 = 144` 个判断。两臂冻结为相同模型 `gpt-5.6-sol`、medium、只读、无网络、隔离 git 根与用户 home，公共提示和业务正文相同；ours 仅增加固定的显式 Skill 调用前缀并安装冻结包。

不加入 Anthropic `doc-coauthoring` arm 的理由成立：其目标是较长的协作写作流程，不是等价的单轮决策简报。Witchcat `decision-records` 嵌在工程工作流，且已记录的固定提交没有覆盖该入口的统一许可证。把二者作为设计来源而不作为计分 arm，可避免流程范围和组装许可成为质量混杂；本轮结果也不能外推为对这些上游流程的质量比较。

## 冻结字节

- `README.md`: `08c1544f87c740dab78468c3d0ff8fbcd6239416230f63d80ebf47b01eab53b2`
- `promptfoo.json`: `a0c4124b17bb731a46f1436008dbf976b0206614f415c9967c898878bf1b2951`
- `cases.json`: `21670547b8ee96b09a0b145d06433ec34f71cad8821137ac139afd9c9b63c426`
- `tests/test_decision_brief_complex_comparison.py`: `ae9c797beef52b8015da688864d4b316ae59e658627c26317d7169a500148da8`
- `prepare_skill_comparison.py`: `4eca5a4c2caeffbeca6663ecf49ce8f9e293f86372593abfb3d794ea1d1b788b`
- 活动 `evaluations/cases/decision-brief-draft.json`: `7cfe377e96097d77fd0ab5d409d542b1d7c05740c05ac24fc05523961450ee72`
- Skill 文件 `SKILL.md`: `1ef140aae7f7d154c6013fb3adabf91cd973ab9d9fd24a777c81a9f80947c938`
- Skill 包指纹: `d66fc65cda321f4a9718c5517ff17e87f704646c9de07d9afb9cb4b4b1495c17`
- prepared config: `d13d1e09ba6f7d80af6992657bfe9dc1adabf2c905a63dd89eea683bd9780bbc`
- prepared tests: `e3d7fd741ff8a17652a62d8f0cd8e1550f5e8b3203ee32913fde68de3e2819ef`

## 限制与冻结建议

本次是非盲、模型辅助的独立设计复核，没有运行正式模型，也没有产生质量结论。新表面与语义标准仍需人工判断；测试只能锁定已审阅字节与可机械验证的隔离、公平性、数量和结构。显式调用比较不证明逐条 Skill 加载、隐式发现、真实审批系统效果、多人协作或长期决策效果。

在上述修正和本文件记录的哈希下，当前候选可以冻结。正式运行必须使用这些字节，保留失败且不重试，并在揭盲前完成逐项布尔评阅与偏好记录；任何协议、题面、prepare 脚本、活动 cases 或 Skill 包字节变化都应重新做冻结前复核。
