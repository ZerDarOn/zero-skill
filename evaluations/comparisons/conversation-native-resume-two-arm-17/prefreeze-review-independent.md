# Round 24 原生 resume 比较：预冻结独立工程复核

结论：**当前未发现 P0–P3 finding，最终 spec 的 v2 preflight 已通过，可以冻结评测协议。** 此前发现的 fixture/包绑定、resume 只读 sandbox、thread selector、题目设计、规模术语和 analyzer 揭盲映射问题均已解决。v2 只证明正式运行前的基础设施与证据链可行，不是质量评分。

## Findings

### P1 — 实际执行 fixture 未绑定冻结包，包错位可被记录为正确 arm

`run_native_resume.py:458` 直接把 `prepared/fixtures/<arm_id>` 复制到轨迹 workspace；运行前调用的 `verify_prepared` 只重算 `prepared/skills/<arm>/<skill>` snapshot，不验证 fixture 中真正会被 Codex 发现的 `.agents/skills`。随后 `run_native_resume.py:469` 直接把 frozen arm 声明的 `skill_package_sha256` 写入结果，并没有从实际 workspace 或 fixture 重新计算。摘要器只比较这个自报字段与 frozen arm。

因此冻结后若把 Skill 注入 baseline fixture、删除或替换 ours fixture，runner 仍可能执行错包并把轨迹标成正确 arm。现有 `test_rejects_arm_package_injection_mismatch` 只篡改结果 JSON 的自报哈希，不能发现 fixture 自身错位。

修复建议：运行每条轨迹前对实际 fixture 或复制后的 workspace 做机械检查。baseline 必须没有目标 Skill；ours 的 `.agents/skills/conversation-rehearsal` 必须与 frozen `skill_package_sha256` 相同。把实际测得的 fixture/workspace 包哈希写入结果，并由摘要器重算或绑定；增加“向 baseline fixture 注入包”和“修改/删除 ours fixture 包”的负向测试。

**Resolution：已解决。** runner 现在先逐字验证 `prepared/fixtures`，每条轨迹复制后又在 `git init` 前验证实际 execution workspace。baseline fixture 必须为空；ours 项目 Skill 必须与冻结 snapshot 的文件清单和包哈希一致。run metadata 保存实测 fixture manifests，新增 baseline 注入和 ours 字节修改两项负测，均能拒绝错位。

### P2 — resume 轮没有显式声明只读 sandbox，证据也只检查首轮

`build_codex_command` 只在首轮命令加入 `--sandbox read-only`（`run_native_resume.py:229`）；`exec resume` 分支没有该参数。`validate_turn` 同样只要求首轮命令包含只读 sandbox（`summarize_native_resume.py:127`）。这不足以支撑两臂每轮都处于相同只读隔离条件，以及 target-selection 文档所要求的“验证 resume 后边界不漂移”。禁止工具事件可以发现已经发生并被事件记录的工具调用，但不能替代启动参数本身的冻结与验证。

修复建议：确认当前 Codex CLI 对 `exec resume` 支持的参数位置，并让每次 resume 显式携带 `--sandbox read-only`；摘要器和命令测试逐轮断言。若 CLI 只能继承首轮设置，则必须用可核验的会话配置/事件证据证明继承，而不是仅在文档中声明。

**Resolution：已解决。** `sandbox_mode="read-only"` 现在位于所有首轮和 resume 命令的公共配置参数中；摘要器逐轮重算并拒绝缺失，命令测试覆盖两种命令。未知 item type 也改为一律触发工具门禁失败。

### P2 — 记录命令的显式 thread ID 校验没有固定 selector 位置

实际 builder 当前把 thread ID 放在 resume 命令倒数第二项，且不使用 `--last` 或 `--ephemeral`，这部分实现正确。但摘要器只检查 `expected_thread_id in command`（`summarize_native_resume.py:131`）。协调修改可以把 selector 换成其他 ID，再把预期 ID 塞入另一个参数值，仍通过记录级验证。现有伪 ID 测试恰好把预期 ID 完全移除，没有覆盖这种修改。

修复建议：按冻结命令结构断言 `command[-2] == expected_thread_id`、`command[-1] == "-"`，并验证仅出现一次；增加“selector 为假 ID、预期 ID 出现在无关参数”的负向测试。

**Resolution：已解决。** 摘要器现在要求 stdin `-` 为最后一项、resume selector 精确为倒数第二项且 thread ID 只出现一次；负测覆盖假 selector 加把真实 ID 塞入无关参数。

### P2 — 六题无逐字重复，但两题高度复用 active 拓扑，另有一项标准不可稳定观察

六题确实组成 phase-boundary、state-isolation、evidence-boundary 三组各两题，文本、人物和具体事实均不是旧题逐字复制。但：

- `pause-review-resume-new-opening` 与 active `pause-and-retry` 都是“首轮扮演→暂停点评→用新开场恢复且不得带入旧分支”，核心判断高度相同。
- `simulation-not-real-person-evidence` 与 active `correction-and-evidence-export` 都要求停止模拟后拒绝把模拟台词升级为现实人物证据，核心证据边界高度相同。
- `fact-correction-versus-role-style` 的 criterion 1 要求第 3 轮“使用更正后的下周一到期信息”。一个自然且正确的温和回应可能只接受“周末安排转账”，既不重复周五也不复述下周一；这种省略无法观察模型是否保留了更正状态，容易在“必须明确说出下周一”和“只要不沿用周五”之间产生评分分歧。

这不会破坏三组配对，但会削弱“全新前向题”结论和 criterion 1 的可复算性。冻结前应替换或明确标注两条为既有机制回归；若目标是六条全新题，需换成不复用 active 轨迹拓扑的场景。criterion 1 应冻结可直接观察的要求，例如明确要求第 3 轮在回应中提到下周一，或把标准改成“不把周五称为当前到期日”，不要把未说出的内部状态作为通过条件。

**Resolution：已解决。** A1 已改为暂停生成两个互斥用户备选、随后只把明确选中的 B 带回同一分支，不再复用 pause/retry 拓扑；B1 第 3 轮题面明确要求判断周末相对当前到期日是否来得及，使 criterion 可直接观察；C1 在 README 与 purpose 中明确标为 native-session paraphrase regression，因此最终口径是五个 forward checks 加一个显式回归。

### P3 — README 把 36 条轨迹写成 36 个 review items

`README.md:3` 写“36 trajectory-level review items”。实际 packet 以 `case × repetition` 分组：正式规模是 18 个匿名 review items，每项比较 2 个候选轨迹，共 36 条被评分轨迹和 84 次生成。测试在单次重复时也验证 6 个 packet items，而不是 12 个。

修复建议：改为“18 anonymous review items compare 36 trajectories containing 84 generated turns”，并与后续报告术语一致。

**Resolution：已解决。** README 现准确写为 18 个匿名 review items、36 条 trajectories、84 次 generated turns。

### P1 — analyzer 未把 packet/key 映射绑定回真实 trajectories

`analyze_native_review.py` 调用了 `normalize_trajectories` 并取得完整、已验证的 `trajectories`，但之后没有使用它们验证匿名 packet 和 blind key。`recompute_review` 只比较 packet/key/review/scored 的 review ID 与 candidate ID 集合，并信任 packet 的 `case_id`、`repetition` 以及 key 的 `arm_id`、`trajectory_id`、`thread_id`。因此协调修改 packet/key、summary 中对应哈希和 scored result 后，可以把一个 review ID 映射到另一 case/repetition，或把同一 item 的两个 candidate 都映射为 `ours`，从而改变 criterion 1 的 per-case 失败数和候选门槛归属，而真实运行 trajectories 不变。

此外，packet/key/scored 的顶层和 candidate 映射使用 dict comprehension，未先验证 ID 唯一；重复 ID 会被静默折叠。现有三次重复端到端测试只覆盖正常正例和门槛触发，没有覆盖协调交换 case、双 ours 映射或重复 ID。

修复建议：以 `(case_id, repetition, arm_id)` 索引 normalize 后的真实 trajectories，逐 review item 验证 `review_id == f"{case_id}-r{repetition}"`、冻结 user turns/criteria、packet candidate turns等于对应 trajectory raw outputs，并验证 key 的 trajectory/thread/arm/package 映射逐项唯一且每 item 恰有 baseline 与 ours。所有 artifact 列表先显式拒绝重复 ID。增加交换 case/repetition、双 ours、伪 trajectory/thread 和重复 ID 负测；保持 gate 只读取冻结 criterion index 0。

**Resolution：已解决。** `analyze_review` 现在读取 key 中已验证格式的随机盐，以 normalize 后的真实 trajectories 确定性重建完整 packet 与 key，并要求两份现存文件逐字结构相等；因此 review ID、case、repetition、user turns、candidate outputs、arm、package、trajectory 和 thread 映射都绑定到真实证据。packet/key/review/scored 的列表使用 `unique_index` 显式拒绝缺失或重复 ID。新增负测覆盖跨 case 交换 user turns 并同步摘要哈希、双 candidate 映射 ours、伪 trajectory/thread，以及重复 scored review ID，均被拒绝。门槛仍只读取冻结 `criterion_index: 0`，总分和偏好不参与触发。

## 已通过的核对

- `promptfoo.json` 冻结 6 题、2 臂、3 次重复；题目总轮数 14，对应 36 条轨迹、84 次逐轮生成、144 个 criterion 布尔值。三组机制各恰好两题。
- 六题没有与现有 active case 逐字重复；上述 P2 是拓扑与核心判断重复，不是字节重复。
- hard criteria 没有以完整字符串进入生成 prompt。prepare 后 baseline 首轮只有 common prompt 与题面，ours 只额外加入显式 `$conversation-rehearsal` 调用；后续只提交冻结的当前用户消息。
- runner 实际使用 `codex exec resume <thread_id> -`，没有 `--last` 或 `--ephemeral`；每条轨迹有独立 HOME、Git workspace 和证据目录。首轮从唯一 `thread.started` 取 ID，后续事件必须返回同一 ID；摘要器拒绝跨轨迹复用 ID。
- 每轮保存 prompt、output、JSONL、stderr、usage、返回状态及其哈希，并保存此前真实输出的哈希链。修正后的实现把 output-last-message 与 JSONL 中唯一 agent message 绑定；协调更新 output 及其哈希、但保留旧事件的负向测试会失败。
- 技术失败会停止该轨迹后续轮次但保留失败记录；摘要状态变成 `infrastructure-invalid`。通用评分器只接受 `awaiting-human-review`，因此技术失败不能进入正式评分。
- blind packet 只包含冻结任务、标准、匿名候选及有序输出，没有 arm ID、Skill、包哈希、thread ID 或 randomization salt；这些仅在 key 中。packet、key、form 和 summary 使用 write-once，内容不同则拒绝覆盖。
- 当前包错位测试能发现结果元数据与 frozen arm 不同，但不能发现 P1 所述实际 fixture 错位。

## 真实不计分 preflight

只读核对了受 Git 忽略的 `evaluations/runs/conversation-native-resume-preflight-20260913-v1`。该 preflight 只选择 `stop-roleplay-one-real-message`，baseline 与 ours 各运行 1 条两轮轨迹。run metadata、native results 与 summary 一致：2/2 trajectories、4/4 turns 均为 `technical_valid`，无 invalid trajectory。此后 common prompt 的隐私措辞被修正，导致最终 spec hash 与 v1 不同；因此 v1 只作为旧 spec 下的基础可行性记录，不能作为最终冻结字节的 preflight。

两臂使用不同且各自稳定的显式 thread ID；第 2 轮命令均为该 ID 的 native `resume`，selector 位置、stdin `-`、`sandbox_mode="read-only"`、禁用 last/ephemeral 均符合冻结门禁。baseline fixture manifest 为空；ours manifest 含冻结的 Skill 两个文件，并与包指纹一致。四轮 output 均与 JSONL 中唯一 `agent_message` 相同，事件、usage、prior-output hash chain 和 results hash 闭合；summarizer 给出 `infrastructure_valid: true`。

这项 v1 preflight 证明当前主机上的真实 Codex CLI 可以通过本比较的显式 resume 与证据门禁。它只有一个 selected case、每臂一次重复，没有做匿名质量评分，且使用修订前 spec，因此不计入正式 36 条轨迹、84 次生成、分数、偏好或候选门槛。

### Final-spec v2 resolution

随后只读核对了 `evaluations/runs/conversation-native-resume-preflight-20260913-v2` 与已提交候选文档 `preflight-validation.md`。文档记录的 spec、cases、frozen 和 native results 四个完整 SHA-256 分别为 `396258ed8b3490227997674c3725a5d6fa94839101783250d77e3258a1f4b765`、`e01512e42d6ba821b46538f50ef34aeb0d5a0eab2fd821afff4c75718baa7642`、`60e3df653226d902343669eb5af4d01285f8862777a1b9a9ef2dc9c4d7db3252` 和 `0d9821e79eb2793f247f122ac41a77e318bba11a98a308f420721e53ceaa961d`，均与当前 spec/cases 及 v2 文件实际字节一致；run-meta 与 summary 也绑定同一 results hash。

v2 使用最终 spec：baseline/ours 各 1 条两轮轨迹，2/2 trajectories、4/4 turns 全部 technical-valid。两臂 thread ID 不同，各自第 2 轮 resume 返回本轨迹首轮 ID；output 均绑定唯一 agent message，summarizer 给出 infrastructure-valid。fixture manifests、sandbox、stdin、禁用 last/ephemeral 和 hash chain 与 preflight 文档相符。至此最终字节的运行前门禁已满足。v2 仍只有一个 selected case、每臂一次重复且未做质量评分，不进入正式分数、偏好或候选门槛。

## 验证与限制

- `python -m unittest tests.test_native_resume_comparison -v`：最终稳定快照下 21/21 通过；未调用模型。包含 analyzer 正常链、三次重复门槛和四类协调映射篡改负测。
- 父代理最终全套测试：109 通过、1 跳过；跳过项为 symlink 权限环境限制。
- 复核过程中曾捕获一次并发编辑造成的 `summarize_native_resume.py:92` 字面量换行转义 `SyntaxError`；文件随后修正，13 项测试重跑通过，因此不列为当前 finding。
- 未运行正式模型评测，未验证真实 Codex CLI 的 84 次执行、网络/只读设置的宿主级效果或实际 token/延迟。
- 未修改 Skill、协议、runner、测试或文档；本文件是唯一复核产物。

## 门禁判断

- P0：无。
- P1：无；原 analyzer 映射 finding 已解决。
- P2：无；原三项均已解决。
- P3：无；原规模术语 finding 已解决。

最终判断：Round 24 比较的题目、runner、证据链、匿名评审、预注册门槛和 analyzer 相互闭合，P0–P3 均无 finding；final-spec v2 preflight 的文件绑定与 2/2 trajectories、4/4 turns 技术门禁也已独立核对通过，可以冻结评测协议并进入正式运行。正式运行仍必须使用完整 3 次重复并完成匿名评审；v1、v2 和单元测试都不产生正式质量分。

