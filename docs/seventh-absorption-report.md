# 第七次技能吸收报告

日期：2026-09-09。起点提交：8e7cf43f0b39b3f6d9aaa3f98a935a59f3c50909。

## 当前阶段

第七批已完成实现与单次合成诊断：新增 `study-practice-plan` 与 `comic-storyboard-draft` 两个 0.1.0、`experimental`、原创自包含技能，登记总数为十六个；两组各四个用例已由 `planned` 仅修改 `stage` 为 `active`。既有十四个技能包未修改。本批尚未提交、推送、安装或发布。

## 来源核查范围与许可边界

### 学习与练习计划

- 固定入口为 Microsoft CAT Agent Skills 提交 `50f5d848ed68f2c8ffcf95f94e47c0a0370b819d` 的 [exam-prep-learning-plan-builder/SKILL.md](https://github.com/microsoft/cat-agent-skills/blob/50f5d848ed68f2c8ffcf95f94e47c0a0370b819d/submissions/exam-prep-learning-plan-builder/SKILL.md)。2026-09-09 通过固定 raw URL 只读取得 HTTP 200、10,975 字节并阅读完整入口；同目录含 `SKILL.md`、`assets/` 与 `metadata.json`，本轮没有读取或运行资产。
- 采用：按真实时间容量排计划；安排练习检查点、反馈纠错与后续复习；时间或进度变化后保留历史并重排剩余部分；容量不足时公开取舍。
- 舍弃：强制逐主题自评；按信心固定双倍分配；每主题固定重复次数或 4—7 天间隔；默认晚 7 点、固定休息日与 45—90 分钟时段；HTML 模板和日历文件流程；关于记忆效果的无来源断言。
- 许可与定位：已读取同提交 [LICENSE](https://github.com/microsoft/cat-agent-skills/blob/50f5d848ed68f2c8ffcf95f94e47c0a0370b819d/LICENSE) 的完整 MIT 正文。GitHub API 于 2026-09-09 返回 66 stars、未归档；这里只作为补充领域来源，不称为高星或有效性证据。没有复制入口、资产或模板。

### 漫画分镜起草

- 固定入口为 Baoyu Skills 提交 `6b7a2e417500561a5ecdd0b168332f4142584617` 的 [baoyu-comic/SKILL.md](https://github.com/JimLiu/baoyu-skills/blob/6b7a2e417500561a5ecdd0b168332f4142584617/skills/baoyu-comic/SKILL.md)，并阅读其直接引用的 [storyboard-template.md](https://github.com/JimLiu/baoyu-skills/blob/6b7a2e417500561a5ecdd0b168332f4142584617/skills/baoyu-comic/references/storyboard-template.md)。
- 采用：清楚的格／页层次；角色、道具、位置和动作连续；画面描述与图内文字分离；分镜先于后续绘制。
- 舍弃：EXTEND 配置门槛、固定问卷和确认步骤；风格预设；角色表、封面和提示词的默认强制产出；图像后端、并发、重试、文件写入、合并 PDF 与发布流程。
- 许可检查：固定技能目录包含入口、`references/` 与 `scripts/`，没有目录 LICENSE；固定根 [LICENSE](https://github.com/JimLiu/baoyu-skills/blob/6b7a2e417500561a5ecdd0b168332f4142584617/LICENSE) 是 MIT。固定 README 声明除另有说明外仓库使用 MIT、第三方代码和资产保留原许可；所读入口和模板未见单独例外。本轮只原创吸收方法，没有复制模板、预设、脚本或示例。

## 方法到本地用例的追踪

| 方法 | 采用或舍弃 | 本地行为 | 覆盖用例 |
| --- | --- | --- | --- |
| 容量核算 | 采用并收紧 | 学习、练习、反馈和主动安排的休息都进入同一时段预算 | fit-the-available-slots、compressed-plan-with-tradeoffs |
| 信心加权 | 舍弃为单一依据 | 自评只作线索，同时使用重要性、先修和给定练习表现 | confidence-versus-performance |
| 间隔与检查点 | 采用为可调策略 | 在真实窗口内安排复习和练习，不规定普遍最佳间隔 | fit-the-available-slots |
| 掉队后重排 | 采用 | 保留完成和遗漏历史，只调整剩余容量 | replan-without-rewriting-history |
| 分镜层次 | 采用并简化 | 每格给可画动作与图内文字状态，不强制封面或完整制作包 | continuous-four-panel-action、revise-one-silent-panel |
| 连续性 | 采用 | 角色、道具、位置与状态变化有可见动作连接 | continuous-four-panel-action、revise-one-silent-panel |
| 画面与文字分离 | 采用 | 区分图内文字、旁白／创作台词归属与图外制作说明 | fiction-is-not-a-quote、revise-one-silent-panel |
| 固定生成流程 | 舍弃 | 只交文本分镜，不调用生图、批处理或 PDF 合并 | 全部漫画用例 |

## 运行前评分设计

### 通用判定

- 每条必要项与禁止项分别标注用户要求、输入事实或任务不变量。全部必要项满足且没有禁止项才算全约束通过；另记录核心任务是否完成。
- 接受语义等价的计划、时间分配、镜头和文字组织，不要求复述本报告的措辞。输入给出的分钟数、练习结果和材料规则可以直接引用，不算模型声称完成外部核验。
- “不超过”不是“必须用满”，“比例不唯一”不能按隐藏比例评分；`fit-the-available-slots` 明确要求正的未分配缓冲，但不规定隐藏的最少分钟数；“恰好四格／三格”是明确格式约束。
- 建议与已执行分开。文本学习计划不能称为日历已更新、效果已验证；文本分镜不能称为图片已生成、视觉连续性已经通过成图检查。
- 不用“隐含”给普通措辞增加未说出的全称断言；同时仍按完整语义判断画面与文字。分镜若明确描绘与材料矛盾的效果，即使没有逐字写出禁止词也会失败。

### 数量、逻辑、范围和未知检查

| 用例 | 数量与格式 | 且或关系 | 范围、证据或未知处理 |
| --- | --- | --- | --- |
| fit-the-available-slots | 三个可用时段逐段安排或明确留空；须有正缓冲但不固定分钟数 | 全部最低任务且容量、先修同时满足 | 周三不可用；练习、反馈、主动休息都计时 |
| confidence-versus-performance | 三主题各有时间决定；总计最多 90，比例不唯一，有理由可为 0 | 重要性、自评和三组同难度当前表现共同考虑 | 一次表现是当前证据，不是永久掌握 |
| replan-without-rewriting-history | 只调整未来；周五最多 45、周六最多 60，不强制复述历史 | B 的练习与纠错、C 的练习与自测都需要 | 若提历史须准确；周四不可用 |
| compressed-plan-with-tradeoffs | 两段各最多 45，总计最多 90 | 基础 40 分钟完整先修；其余结合重要性、练习纠错和公开取舍 | 其余可部分完成；90 小于 160，不能声称全部最低需求完成 |
| continuous-four-panel-action | 恰好四格；每格有画面／动作和文字状态 | 初态、取钥匙、开门目标与连续变化都需要 | 不固定镜头；不强制每格有图内文字 |
| metaphor-keeps-the-rule | 恰好三格 | 护罩正确放置、限时延缓污染、不能保证无损且仍需撤离 | 虚构桌游规则；比喻可用、修正或放弃；回合数未知 |
| fiction-is-not-a-quote | 恰好三格；每格有场景和文字归属 | 事实顺序与归属边界同时满足 | 无逐字原话；创作台词可用但须明示 |
| revise-one-silent-panel | 只返回第二格；图外标签可用 | 与固定一、三格衔接且无图内文字 | 不把制作说明误判为图内文字 |

### 可接受等价与失败边界

- fit-the-available-slots：允许拆分任务或不使用某时段，只要全部最低需求在截止前完成、单段不超容量、先修正确并明确留下任意正的未分配缓冲；主动写出的休息计入容量。
- confidence-versus-performance：甲或丙可获得最多时间，也可给任一主题 0 分钟并说明依据；三个主题都需有决定，但不要求固定排序或倍数。只按自信机械分配、忽略当前同难度错误与重要性失败。
- replan-without-rewriting-history：B、C 可在周五周六间合理拆分；可只给剩余计划，不强制重印周一与周二。若提历史须准确，把周二遗漏改成完成或在周四排课失败。
- compressed-plan-with-tradeoffs：必须先完整安排 40 分钟基础方法；之后允许在其余三项间选择高价值子集或部分完成，只要承认未达到哪些最低需求并保留练习纠错。压缩先修或把截止后任务计入覆盖失败。
- continuous-four-panel-action：允许多种取钥匙与开门动作、镜头和无字设计；只要道具状态连续。不是必须逐格只发生一个动作。
- metaphor-keeps-the-rule：这是纯虚构桌游规则；可以不用盾牌，也可把护罩画成有时限且仍需撤离。画面或文字明确表现无限有效、保证无损或无需撤离都会失败，不要求必须出现某个禁止词。
- fiction-is-not-a-quote：旁白可概括事实；可在开头统一说明后逐格正常标注旁白／对白，不要求每个气泡重复免责声明。引号和正常镜头省略本身不失败，失败点是把创作内容冒充材料原话。
- revise-one-silent-panel：允许跑近、弯腰、伸手以及不破坏固定两格的辅助动作；“第二格：画面……”是图外制作说明，不算图内文字，也不强制写出“无文字”。返回完整三格、改动固定格或新增元素导致衔接冲突失败。

## 预检修订记录

主任务只读预检确认方向与结构可用，并在冻结前收紧六处边界：把“合理缓冲”改成明确但无固定分钟数的正缓冲；让三主题都有决定且统一同难度证据；取消剩余计划必须复述历史和额外解释段的隐藏要求；明确 40 分钟基础先修不可压缩、只有其余项可部分完成；把现实消防材料换成纯虚构桌游规则；允许无字第二格用纯动作自然满足要求，并删除对不冲突辅助元素的绝对禁令。通用评分同时保留语义判断，既不脑补全称，也不漏判画面明确呈现的矛盾效果。

## 实现与运行

- 运行环境：Windows 上的 Codex CLI；`gpt-5.6-sol`，reasoning effort 为 `medium`。
- 隔离：每例使用新的临时目录，`codex exec --ephemeral --ignore-user-config`，只读沙箱、无工具。
- 对照：八次 baseline 后原创并冻结技能包，再进行八次显式加载 skill 的运行；16 次有效生成均在第一次模型启动成功，没有模型重试或启动失败。
- 首次 baseline 命令误用 Windows PowerShell 5.1 读取无 BOM 的 UTF-8 脚本，中文字符串在解析阶段损坏并退出；没有启动模型。改用 `pwsh` 后按相同冻结用例正式运行。该事件记为一次预启动编排事件，不计入模型调用。
- baseline 合计 142,761 ms、122,334 input tokens、92,160 cached input tokens、2,360 output tokens、730 reasoning tokens；skill 合计 184,600 ms、129,996 input tokens、98,304 cached input tokens、3,411 output tokens、1,527 reasoning tokens。时间是本地编排观测区间，不是模型服务端延迟。

## 指纹与结果

| 技能 | 包指纹 | planned 用例指纹 | active 用例指纹 | 全约束 baseline→skill | 核心 baseline→skill |
| --- | --- | --- | --- | --- | --- |
| `study-practice-plan` | `1545072dae95bcca9111de599b6d8cf9399f5c46d7101a56ef41a7ca5d7202ac` | `3c99ef1145b69bcb76908635675084a9f1a0943dbd9b950782e3a6d64def914c` | `8ece0697b858907d031871d9431fa317ec51a637cdc33015a3941fb7c67c45b8` | 4/4→4/4 | 4/4→4/4 |
| `comic-storyboard-draft` | `80ea580ce35c1ae7619b156927e9d24d184bdf2faa5635603a700be269838229` | `6d4de84e984904d17978bd858575c4aad9297004c4cfff2ade19f420f0d87ecb` | `3b5f77cc6a49bca1772fc6a84bbff6e2c56cc5f825fa1012842e0da77370884a` | 4/4→4/4 | 4/4→4/4 |

两组均无严格通过数改善，也无退化。baseline 已能完成这些边界清楚的合成任务；skill 输出在若干例中更显式地说明证据或连续性，但当前冻结标准不把措辞完整度差异升级为额外通过。没有为了制造增益而改变用例或加强对 baseline 的隐含解释。

完整 prompt、原始输出、事件、stderr、退出状态、用量、时间、快照、哈希和逐项理由保存在 [诊断证据](../evaluations/reports/seventh-absorption-0.1.0-diagnostic.json)。

## 导出、检查与复核

- 已生成 `dist/study-practice-plan-0.1.0.zip` 与 `dist/comic-storyboard-draft-0.1.0.zip`，未覆盖既有 ZIP。两包都只含顶层 `bundle-manifest.json` 和对应技能目录中的 `SKILL.md`；manifest 的文件哈希和包指纹与当前目录一致。
- 诊断报告共 16 条唯一运行记录，均为退出码 0、第一次启动成功；baseline 与 skill 的用户消息一致，planned 与 active 快照除 `stage` 外一致，报告内技能正文、原始输出／事件／stderr 哈希、usage、包指纹和 active 用例指纹均与原始记录或当前文件一致。
- `python scripts/validate_collection.py` 通过；`python -m unittest discover -s tests -v` 共运行 27 项，26 项通过，1 项因当前 Windows 环境没有创建符号链接的权限而跳过；`git diff --check` 与第七批新文件空白检查通过。
- 实施代理按工程质量门禁复核后未发现新的正确性、安全、性能或维护性问题。运行脚本和原始长记录位于被忽略的 `evaluations/runs/`，不作为技能包内容。

## 限制与结论

每例只运行一次，技能为显式加载，评分由实施代理完成而非独立人工评审；未测试自动发现、稳定收益、真实学习提升、考试结果或生产级分镜质量。无工具隔离没有查询真实考试规则、创建日历、生成图片、检查成图连续性、合并文件或发布作品。两个 baseline 均已全部通过，本轮没有证明严格通过数增益，因此继续保持 `experimental` 与 `evidence: null`。Microsoft 来源只有 66 stars，定位为补充领域资料而非高星候选；两包均为原创表达，没有复制第三方入口、模板、资产、脚本或示例。
