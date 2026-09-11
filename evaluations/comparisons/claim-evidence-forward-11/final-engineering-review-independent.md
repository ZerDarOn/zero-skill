# 第十八轮待提交改动最终工程审查

日期：2026-09-11
审查基准：当前工作区相对 `HEAD`，以及冻结提交 `2dd75b3753748e0f40181d76fa152667d335e828`

## Findings

### [Low，已修复] 第十八轮测试原先只验证部分关键哈希的格式

位置：`tests/test_claim_evidence_round18.py:42-76`、`:150-183`

原测试只要求冻结提交为40位十六进制，prepared、artifact 和决策投影为64位十六进制；任意格式正确但内容错误的值都可能通过。这不会改变当前报告，但会削弱后续对机器证据被意外改写的检测。

已修复：测试现在固定冻结提交、2个 prepared 哈希和9个运行产物哈希的具体值，并从报告内嵌的 reviewer、18项标准判断和偏好重新计算无 notes 决策投影，核对 `8c98ddf359148697a0f0d9e8fb7b4fe0022b066a2334f7b3b517a8986efe4261`。

### [Low，已修复] 活动回归原先只绑定六个 ID，没有绑定冻结题面与硬标准

位置：`tests/test_claim_evidence_round18.py:266-283`

原测试能确认六个回归 ID 存在，却不能阻止题面或 `must_include` 在搬入活动用例时偏离冻结协议。这会让“六题进入回归”的声明存在内容漂移风险。

已修复：测试现在通过 `input.comparison_case_id` 建立一一映射，要求六个活动题的 `prompt` 与冻结题完全相同，并要求 `must_include` 与冻结 `hard_criteria` 完全相同。

### [Low，已修复] 两个编码投影哈希的规范化输入未解释，容易被误读为矛盾

位置：`evaluations/comparisons/claim-evidence-forward-11/postscore-decision-review-independent.md:82`

独立评审任务保存的 `9444624d...` 与仓库报告保存的 `8c98ddf...` 来自不同投影结构，二者都在修复前后稳定，但此前文档没有说明为什么数值不同。

已修复：文档现在分别说明前者包含 schema、comparison、reviewer 与 reviews，后者只包含 reviewer 与无 notes reviews，并使用紧凑键排序序列化；明确二者不能横向比较。

**没有剩余阻塞性或非阻塞性代码发现。** 下列逐项核对均通过；残余限制已单独列出。

## 逐项核对

### 1. README、评测说明与第十八轮报告数字

通过。

- `README.md:5`、`evaluations/README.md:170` 和 `docs/quality-polish-round-18.md:15-34` 均记录两臂 `52/54`、`16/18`，偏好 baseline 3、0.1.0 为7、另有8次持平。
- 三处都没有把7:3偏好写成严格质量提升；使用的是“未观察到严格净增益”“偏好不能替代严格分”或等价限制。
- 0.1.0 的229,099 token、baseline 的177,055 token、差值52,044和约29.4%一致。详细报告还保留 completion token约增加108.2%、记录成本约增加53.4%、中位延迟约增加19.7%。
- 逐题统计与机器报告一致：构成反转9/9对9/9；嵌入指令9/9对9/9；强证据9/9对9/9；字段更正8/9对9/9；有限日志9/9对9/9；共享数据8/9对7/9。

### 2. 自包含机器报告可重算性

通过。

独立脚本把 `evaluations/reports/claim-evidence-round-18-diagnostic.json` 与冻结盲包、揭盲键和 encoding-fixed 正式评分逐项对齐，结果无差异：

- 报告含18个 review item、36个候选输出和108个布尔判断；
- 每个 task、hard criteria、候选输出、候选到实验臂映射、评分、偏好和中文理由均与源产物一致；
- 36个 `output_sha256` 均由报告输出正文重算通过；
- overall 与六组 by-case 统计均能从内嵌 items 重算；
- 9个 `artifact_hashes` 均从当前保留的运行产物重新计算通过；
- encoding-fixed 评分的 `review_sha256` 与完成表哈希一致。

### 3. 包指纹、协议、冻结提交与活动用例数量

通过。

- 当前 `claim-evidence-review` 包指纹由仓库校验器重算为 `bfda03a341b9d1b62f2004b7854fca0d4e7712a730a95274e3f9a4b43f7d8e29`，与报告实验臂及最终决定一致。
- `promptfoo.json` 与 `cases.json` 的 SHA-256 同时匹配当前文件、`frozen.json` 和冻结提交中的字节内容。
- 当前 `HEAD` 为冻结提交 `2dd75b3753748e0f40181d76fa152667d335e828`，冻结协议目录相对该提交没有待提交修改。
- `claim-evidence-review` 活动用例为10项；所有 `stage: active` 套件合计112项。新增六题的题面与硬标准已由测试绑定冻结协议。
- Skill 仍为0.1.0、`experimental`、`evidence: null`；当前差异没有修改 Skill 包或 catalog。

### 4. 缺文件与编码事件

通过，且没有夸大。

`docs/quality-polish-round-18.md:43-49` 与机器报告 `review_artifact_note` 都明确记录：第一次计分因完成表缺失而在读取阶段失败、没有揭盲；既有匿名判断写入后才成功计分；揭盲后仅为UTF-8显示兼容重序列化理由；108个布尔、18个偏好和 reviewer 元数据未变；原始计分产物保留，正式报告使用另存的 encoding-fixed 结果。

修复前 Python UTF-8 读取已得到有效中文且没有 U+FFFD，因此文档谨慎写成“显示兼容”而没有断言源字节已经损坏。两个不同规范投影的口径现已解释，仓库侧投影也由测试重算。

### 5. `test_claim_evidence_round18.py` 的证据绑定

通过，审查中已加固。

测试现在覆盖：报告 scope；冻结提交；协议源哈希；具体 prepared/artifact 哈希；reviewer 暴露边界；18条非空中文理由；36个输出哈希；108个布尔；两臂总分、完整输出和偏好；六题逐题统计；成本增幅；包指纹；版本、状态和 evidence；10项目标用例、112项全仓用例；六题活动内容与冻结协议一致；编码修复前后不变的决策投影。

### 6. 第十七轮测试职责修正

通过。

`tests/test_relationship_nested_source_round17.py` 只删除了“当前全仓活动用例必须仍为106”的历史全局断言，保留第十七轮报告 scope 中历史值106、relationship 18项、包指纹和逐题统计等专属证据。当前全仓112项的责任由第十八轮测试承担。这样避免旧轮测试阻止后续合法新增用例，没有削弱第十七轮自身证据。

### 7. 偏好、token 与成本限制

通过。

README、评测说明、质量报告、机器报告和揭盲后独立决策都把7:3限定为描述性偏好，并明确硬分持平。总 token 增加29.4%没有遗漏；详细材料还明确 completion token、记录成本和延迟增幅。最终决定保持0.1.0，符合冻结前“跨题、跨重复的机制性失败后才设计候选”的门槛，未利用偏好结果强行升版。

## 残余限制

- `prepared_hashes` 对应的生成后 config/tests 文件没有保存在运行目录中，本次只能与 `frozen.json` 交叉核对并在回归测试中固定具体值，不能从原 prepared 文件再次计算。这一限制不影响已保留的冻结源、36个输出和正式盲评结果的重算。
- 显式臂没有 `skillCalls` 遥测；结果只能支持“显式项目条件下的输出差异”，不能证明每次实际读取了 Skill 正文。
- 单模型、单推理强度、每臂三次和模型辅助评审都限制外推；7:3偏好不构成统计优势。
- Windows 环境无法创建测试符号链接，相关用例按设计跳过；这是权限限制，不是功能失败。

## 验证

- `git diff --check`：通过，无输出；
- `python scripts/validate_collection.py`：通过；
- `python -m unittest discover -s tests -v`：68项，67项通过，1项因 Windows 缺少符号链接权限跳过；
- 聚焦 `python -m unittest tests.test_claim_evidence_round18 -v`：通过。

本审查没有修改 Skill 版本、status 或 evidence，没有提交或推送。
