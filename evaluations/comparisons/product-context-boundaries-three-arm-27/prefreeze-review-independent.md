# Round 34 冻结前独立复核

日期：2026-09-14

## Findings first

当前没有开放的 P0–P3。

- **P2，已修正：一题与活动用例语义骨架过近。** 原 `unpublished-help-draft-does-not-prove-ga` 与活动题 `newer-sales-note-does-not-resolve-conflict` 都是“较新非权威文本宣称全面开放，正式记录仍是邀请测试，缺少发布或权限确认”，不足以支持六个新表面的声明。冻结候选改为 `retirement-banner-does-not-collapse-cohorts`：权益登记区分新账户停售和120个已有合同账户限期可用，较新的模糊退役横幅缺账户范围与迁移日期。它仍测试 `publication-scope`，但换成 cohort 与时间窗口边界。
- **P2，已修正：冻结测试没有在 `FREEZE_COMMIT=PENDING` 时真正锁定活动 cases，且没有明确比较三臂隔离 home。** 当前测试无条件核对活动 cases SHA-256；逐臂验证 `working_dir` 和 `CODEX_HOME`、`HOME`、`USERPROFILE` 只按臂名变化；同时锁定 provider ID、标签顺序、其余 provider 配置、业务提示与显式调用前缀。
- **P2，已修正：上游来源记录可被协调修改，fixture 文件集合未被明确限制。** 当前测试固定 `provenance.json` 自身哈希，要求 provenance 恰好登记根 LICENSE、上游 SKILL 和包内 LICENSE，限制 fixture 和运行包的准确文件集合，并继续核对每个登记文件与包指纹。
- **P3，已修正：表格行数存在 Markdown 分隔线歧义。** `privacy-veto-is-not-purchase-approval` 已明确要求表头外恰好5个数据行，Markdown 分隔线不计。测试加入合法两列表格示例。
- **P3，已修正：README 用“高星”修饰上游。** Star 数不构成质量证据且会变化，已删除该描述；固定提交、版本、许可和任务范围保留。

## 题面与隐藏标准

六题按 `publication-scope`、`stakeholder-authority`、`bounded-evidence-update` 三个机制各两题组织，ID 与七个活动题不相交。替换后，各新题与活动题的最高字符级相似度为0.242；该数值只作辅助，最终由人工逐题比较事实结构、来源类型、角色、指标和所需动作。

人工复核确认每项 hidden criterion 所需事实都在题面中：总体开放与局部事件可以并存；新账户停售、已有合同账户窗口和横幅缺口均明确；128万元报价可直接应用100万元权限阈值；隐私否决、采购决定和付款执行的权限分别给出；两项研究的单位、时长、分母、观察结果与限制完整；受保护文档及两个获准更新均提供了原文。标准不依赖题外答案，review policy 接受语义等价并禁止后验加项；只有题面明确要求逐字保留的文档片段按字节判断。

## 范围、格式与三臂公平性

两道限长题均存在覆盖全部标准的单段答案，独立示例分别为86/120和85/150字符。其余格式也可同时满足：三条产品状态要点、四行角色结论、表头加五个数据行的两列表格，以及只改 Target Audience 与 Goals 的完整文档均有测试示例。四行角色题可将采购执行和两个未知项放在第四行，不需要漏掉角色边界。

三臂共用同一个模型、推理等级、只读无网络配置、公共提示和任务正文。baseline 不安装 Skill；ours 与 upstream 都只增加同结构的显式调用前缀并分别安装一个项目级冻结包。prepared 回归证明 provider 配置除臂隔离目录和 home 路径外一致，三臂题面只在对应 Skill ID 的调用前缀上不同，`vars` 只有 `prompt`，hard criteria 不进入模型 prompt。

公共提示把任务限定为一次性文本交付，并统一禁止读取、提问、保存和同步。这收窄了上游完整工作流，但同样适用于本地 Skill，并与本轮只比较共同覆盖的文本整理子任务一致。本轮结果不能外推为完整产品营销流程排名。

## 上游来源与字节

远端只读复核确认提交 `5b2c0007766c6a1cf1d53fd8fc73e979e0821022` 存在。固定 raw `skills/product-marketing/SKILL.md` 为2.1.0，9433字节，SHA-256 `6dfd6bd485f62448385844cb9eceefcee0977c843d7a1c9e6077590d4e19d1ec`，与 fixture 完全一致。固定根 LICENSE 是 Corey Haines 2025 MIT 文本，1069字节，SHA-256 `b70d71e24e40fce5da8f4b6f9cd862096a048e433db7f3c8cac5e348e6d34591`，与根 fixture 和包内副本完全一致。

`provenance.json` 准确记录仓库、完整提交、MIT、检索时间和仅复制许可证的修改；其 LF 规范化字节 SHA-256 为 `49bab9352c7b3c6185418d9443c7f5cdc2d895d5406d7fb7b2ea415aa13d8f91`。上游包只含 `SKILL.md` 与 `LICENSE`，没有脚本可被安装或执行。

## 冻结规模与字节

设计规模可重算为 `6 cases × 3 arms × 3 repetitions = 54 outputs`、`6 × 3 = 18` 个三候选匿名评阅项和 `54 × 4 = 216` 个布尔判断。失败保留且不重试。gate 只比较 ours 与 baseline，并要求同一机制两题都满足 ours 每题至少2/3次核心失败、baseline 每题至多1/3次核心失败及54份输出全部有效；upstream 只作上下文。

- `README.md`: `abb9047c6e0116cb41f07fb0d04a4072dd2770f6dbafae87b0fba538210fd4dc`
- `promptfoo.json`: `82731f1012a1421d3e88c7c591c836bf40bd2c3afc80a805de8477f025cfe768`
- `cases.json`: `109c493b3a13d178d67128dd0d181d47209ffbfbfa26c6f9cdb212aac897b7de`
- `tests/test_product_context_boundaries_comparison.py`: `87695d6d3b79eaf7d17014d38b78d81e0577f4fa927e68926eac87ca5b927759`
- `prepare_skill_comparison.py`: `4eca5a4c2caeffbeca6663ecf49ce8f9e293f86372593abfb3d794ea1d1b788b`
- 活动 cases: `15ff60f439b044d5714fcb54d67f3fb42ce8b37d96cc01f88be4f605e6fe91ec`
- 本地 Skill 包: `f821cb134112decd46c07b8b50d5fef7e03c4bbae91d6af68344e45552dbc4c5`
- 上游 Skill 包: `802ecb5ec6a435db0ea22a1b95a67450bd0e4c5d3c8f3d8f8ef5525ef77c49de`
- prepared config: `7bf0aaee00b0b4a95a48e6ea4b64638ce9880403b8a6a6c25e6a5835ae1e0957`
- prepared tests: `54592764c1f7b8c4169ba74a9c9a913f3b95c5dfce2649181c993350dce230ac`

## 开放事项、限制与建议

没有开放的 P0–P3。`FREEZE_COMMIT` 仍是预冻结阶段的 `PENDING` 占位；创建包含当前候选字节的冻结提交后，应在正式运行元数据与后续结果复核中绑定实际提交，不得把 `PENDING` 当作运行来源声明。

本次是非盲、模型辅助的独立设计复核，没有运行正式模型，也没有产生三臂质量结论。新表面、语义标准和上游任务可比性仍包含人工判断；测试只能锁定已审阅字节及机械可验证的数量、格式、包、提示和 provider 边界。显式调用比较不证明逐条 Skill 加载、隐式发现、真实发布或权限系统、写盘、多轮协作和营销效果。

在本文件记录的字节下，候选可以创建冻结提交。正式模型运行应在提交绑定和同字节 prepare 检查通过后进行；任何 protocol、cases、prepare 脚本、Skill 包、upstream fixture 或活动 cases 变化都应重新做冻结前复核。
