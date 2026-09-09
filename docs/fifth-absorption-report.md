# 第五次技能吸收报告

日期：2026-09-09。起点提交：55bf386082e07a84931abb2f4b97434f81de1d97。

## 当前阶段

生成前预检与修订已经完成，八例评分标准随后冻结。react-performance-review 与 meeting-communication-review 0.1.0 已实现并登记为 experimental，八个用例只把 stage 从 planned 改为 active；prompt、输入、路由和评分标准未再改变。既有十个技能包没有修改。

## 来源核查范围与边界

### React 性能审查

- 固定入口为 Vercel Agent Skills 提交 063bee94c3f4df8453406c830b0a7df0f2860278 的 react-best-practices/SKILL.md。实际阅读了入口的分类与规则索引，以及同提交下 async-parallel.md、rerender-derived-state-no-effect.md、rerender-memo.md。
- 采用：按已测影响排序；只并行互不依赖且允许同时发生的操作；纯派生值不经冗余 Effect 回写；缓存建议需要具体重复成本依据。
- 舍弃：复制完整规则库；照搬上游的 CRITICAL 等级或数字收益；把任意 await 改成 Promise.all；把 memo 当作普遍规则。
- React 技术条件另用 2026-09-09 访问的官方 React 19.2 memo 与 You Might Not Need an Effect 页面核对。官方文档只作技术核验，不登记为技能上游。
- 许可边界：固定入口元数据声明 MIT；没有成功取得该固定提交的独立仓库根 LICENSE 或技能目录 LICENSE 正文，因此只记录元数据声明，不表述为已完成完整许可文本核验。本批不复制第三方代码、示例或文案。

### 会议沟通复盘

- 固定入口为 Composio Awesome Claude Skills 提交 be2a406907dbc61b73e6827ded415c96139d13a2 的 meeting-insights-analyzer/SKILL.md。实际阅读了行为模式、参与/倾听分析、建议格式、文件扫描和长报告部分。
- 采用：用可定位的发言例子支持观察；区分倾听、表达和主持行为；给具体但不伪造事实的改进表达。
- 舍弃：把口头禅或谨慎措辞自动解释为紧张、回避；在缺少持续时间、重叠或完整转录时计算时长；默认扫描会议目录；强制长报告和跟踪流程。
- 许可边界：固定仓库 README 声明集合为 Apache-2.0，同时提醒个别技能许可可能不同；没有成功取得该提交独立根 LICENSE 正文或 meeting-insights-analyzer 目录许可证，入口 frontmatter 也没有许可字段。因此只记录仓库声明与未核实范围，不称具体技能许可已完整核验。本批只做原创方法吸收。

## 方法到本地用例的追踪

| 方法 | 采用或舍弃 | 本地规则 | 覆盖用例 |
| --- | --- | --- | --- |
| 请求依赖图 | 采用 | 只重叠独立调用，保留权限、数据和错误语义；本例没有取消信号，不测试取消语义 | independent-versus-dependent-work |
| 缓存与 memo 需收益依据 | 采用 | 简单计算和无卡顿记录不构成批量缓存理由 | avoid-unjustified-memo |
| 派生值与外部同步分离 | 采用 | 纯派生值可在渲染期计算，外部同步 Effect 保留 | derived-work-and-state |
| 按实际影响排序 | 采用 | 已测主要成本优先于微小或未测模式 | prioritize-observed-cost |
| 可定位的行为证据 | 采用 | 观察附发言位置，建议不回写为事实 | hedging-in-context、one-actionable-rephrase |
| 指标口径与分母 | 采用并收紧 | 轮次、时长、字数分开；比例明确分母和材料完整性 | turns-are-not-duration、compare-with-denominators |
| 口头禅等于心理状态 | 舍弃 | 谨慎措辞结合样本与上下文，不推断稳定人格或动机 | hedging-in-context |
| 缺失数据仍输出固定统计 | 舍弃 | 未知保持未知，只报告可计算的窄指标 | turns-are-not-duration、compare-with-denominators |

## 运行前评分设计

### 通用判定

- 每个 must_include 与 must_avoid 独立进行语义判断，不以关键词命中代替含义判断。全部必要项满足且没有禁止项才算全约束通过；核心任务成绩另行记录，不用核心通过掩盖格式或边界失败。
- 标准前缀明确来源：输入事实来自该例合成材料，用户要求来自 prompt，任务不变量来自技能边界。评分不得在看到 baseline 后新增要求或改变口径。
- 接受语义等价回答。React 并发接受 Promise.all，或为所有已启动 Promise 立即建立错误处理的等价安排；不把先启动两个 Promise 后依次 await 且可能遗留先拒绝 Promise 的写法无条件判对。派生值不强制 useMemo；性能改善不强制 transition 等 API；会议建议不要求复述固定模板。
- 建议、条件与已执行严格区分。回答若把建议描述成已经修改、测量、发送、承诺或验证，按对应 must_avoid 判失败。

### 数量、逻辑与分母检查

| 用例 | 数量边界 | 且或关系 | 分母或未知处理 |
| --- | --- | --- | --- |
| independent-versus-dependent-work | 最多 2 项，1 或 2 项均可 | 可重叠部分与必须保留的依赖均需覆盖，可在同一项内表达 | 不涉及比例；错误语义也必须保留 |
| avoid-unjustified-memo | 最多 2 句话，1 或 2 句均可 | 当前不建议批量缓存；未来重考虑条件是可选扩展，若提及则必须有具体收益依据 | Compiler 未知，不得推成未启用或已启用 |
| derived-work-and-state | 只给 1 项局部改善 | 移除冗余派生更新，且保留外部同步 | 框架和 Compiler 未知，不阻塞局部结论 |
| prioritize-observed-cost | 恰好 1 个性能问题；验证可在同一项内 | 主要成本、最小方向、验证与正确性均需覆盖 | 145ms 是步骤记录，180ms 是输入 p95，不互相替代 |
| turns-are-not-duration | 未限定回答条目数 | 轮次统计是可选替代；若报告则不能据此回答时长或打断 | 若报告轮次则 A 为 2/4 已记录轮次；不报告不扣分；时长和打断均未知 |
| hedging-in-context | 恰好 2 点：一处合理谨慎且一处改进 | 两类都必须出现，各自有位置依据 | 3 家样本支持谨慎；负责人未知保持未知 |
| compare-with-denominators | 未限定条目数 | 两个比例和不可证明提升的判断都需要 | A=3/8=37.5%；B 可见部分=4/6≈66.7%；B 缺失 10 分钟 |
| one-actionable-rephrase | 恰好 1 个改进点和 1 句建议改写 | 改进点与改写都要保留事实、条件和未知责任 | 不新增负责人、日期或承诺 |

### 可接受等价与失败边界

- independent-versus-dependent-work：接受对前两个使用 Promise.all，或为所有已启动 Promise 立即建立错误处理的等价请求图；任一 user/flags 失败都应使整体 reject，且不得吞错或留下未处理拒绝。两者都失败时不要求保留原串行报错优先级；无条件提前 fetchInvoices 失败。本例没有取消信号，不评分取消语义。
- avoid-unjustified-memo：接受只回答“当前没必要”“先保持简单”而不补充未来条件；若扩展未来条件，须有具体收益证据。“永远不要 memo”或宣称缓存已提升性能失败。
- derived-work-and-state：接受直接计算 visible，或在明确昂贵条件下有条件缓存；删除 analytics 同步或把副作用放进渲染失败。
- prioritize-observed-cost：接受减少重算、复用或有条件延后非紧急计算；把 Badge 或未测回调列为第二问题、虚构收益失败。
- turns-are-not-duration：轮次统计可不报告且不扣分；若报告，接受“2/4”“一半已记录轮次”，但须明确不是时长。称其为讲话时长、用相邻时间戳补时长或断言没有打断失败。
- hedging-in-context：接受对 10:03 问题和 10:05 转页的组合定位；把“可能”单独诊断为回避或编造负责人失败。
- compare-with-denominators：接受 66.7%、约三分之二等价表示，但必须保留 4/6 口径；仅比较 3 到 4 次或据此宣称能力提升失败。
- one-actionable-rephrase：建议可以要求当场确认负责人或说明负责人待确认，但不能指定未知人选；多条建议、多个候选句或把改写冒充原话失败。

## 预检记录

主任务完成了生成前只读预检。预检修订了四处边界：轮次替代统计与未来缓存条件改为条件评分；并发例明确任一独立读取失败都须使整体 reject、不得吞错或遗留未处理拒绝，且不测试取消；谨慎表达例只要求为可改进点给表达建议。修订后结构、数量、且或、未知与分母自查通过。

## 运行与指纹

模型为 gpt-5.6-sol，reasoning effort 为 medium。每例在新的临时目录中使用 codex exec --ephemeral --ignore-user-config、只读沙箱且无工具；baseline 不含技能，skill 组显式加载所属完整包。共 16 次有效单轮生成，模型启动 16 次，全部首轮成功，启动失败 0、重试 0。

| 技能 | planned 用例指纹 | active 用例指纹 | 包指纹 |
| --- | --- | --- | --- |
| react-performance-review | 48565d287c6d9219d2b199b44f82bc1462e7221b0da0ac10f9cdf81da9e29482 | 3f023e1505a3adccdcac9cfef5dbc9c809f89076d9ad2e54cecacccbf1294623 | f2dd9c4759eefb5c3fdaa2447634ff9ee9d22ff1916ef47f8f9ec5ccfa7ab780 |
| meeting-communication-review | 18a68b544aa75fbf1b2509a1de3fd89407f557851a00bf7f446378f2e510846a | 5e8685ecafc026a6faa16ec6bd0d281c7a289b6a4958658a100654d2e0dced5e | 5acbbae22930d5a6fde52ef0dbed9563e4381c3e0dcb9a55f93a74456faeb1bf |

baseline 总观察时长 125,839 ms，输入／缓存输入／输出／推理 token 为 122,307／88,064／1,935／683；skill 组为 115,008 ms 和 129,733／102,400／1,613／202。时长是本地编排观察区间，不是服务端延迟。

## 评分结果

| 技能 | 全约束 baseline→skill | 核心任务 baseline→skill | 严格改善 | 退化 |
| --- | --- | --- | --- | --- |
| react-performance-review | 3/4→4/4 | 4/4→4/4 | 1 | 0 |
| meeting-communication-review | 3/4→3/4 | 3/4→4/4 | 1 | 1 |

React 的改善出现在 prioritize-observed-cost：baseline 正确选中已测 145ms 的 rankResults 并给出验证，但无条件要求按 results、query 缓存，没有先确认相同输入组合是否会重复；skill 输出先区分无关重渲染与每次 query 改变的必要计算，再按条件选择复用或算法改善。其余三例两组均通过。

会议的改善出现在 hedging-in-context：baseline 正确识别合理谨慎与未回应问题，但在建议中编造“由我牵头”和“最晚周五前给出决定”；skill 输出保留负责人未知并只建议明确确认。退化出现在 one-actionable-rephrase：skill 输出的改进方向、事实和责任边界正确，核心任务通过，但引号内建议由两个句号分成两句话，不满足冻结的“1 句建议改写”；baseline 满足该格式。因此会议组全约束净值仍为 3/4，不应表述为整体提升或零退化。

逐项 must_include、must_avoid、证据片段、全部原始输出、事件、stderr、运行参数、时间、用量和哈希见 evaluations/reports/fifth-absorption-0.1.0-diagnostic.json。评分由本次执行任务中的 Codex 完成，不是独立人工评审。

## 限制与交付状态

每例只运行一次且使用合成材料；显式加载不测试自动发现与路由。无工具隔离环境没有运行 React 应用、测量真实性能、读取音频、扫描会议目录或发送反馈，也不能证明跨项目兼容、转录质量、员工表现或稳定聚合收益。两组强 baseline 都已通过 3/4；React 有一项净改善，会议同时有一项改善和一项格式退化，均不足以证明长期稳定收益；许可核查缺口仍按上文保留，没有复制第三方文件。

交付前检查通过：python scripts/validate_collection.py 通过；python -m unittest discover -s tests -v 共 27 项，26 通过、1 项因当前 Windows 无符号链接权限而跳过；git diff --check 与新增文件行尾空白检查无报错。

只导出了两个新 ZIP，现有十个归档未覆盖：dist/react-performance-review-0.1.0.zip 只含 bundle-manifest.json 与 react-performance-review/SKILL.md，manifest 包指纹为 f2dd9c4759eefb5c3fdaa2447634ff9ee9d22ff1916ef47f8f9ec5ccfa7ab780；dist/meeting-communication-review-0.1.0.zip 只含 bundle-manifest.json 与 meeting-communication-review/SKILL.md，manifest 包指纹为 5acbbae22930d5a6fde52ef0dbed9563e4381c3e0dcb9a55f93a74456faeb1bf。

当前保持未提交、未推送，供主任务复核。
