# 第十九轮待提交改动最终工程审查

日期：2026-09-11
审查基准：当前工作区相对 `HEAD`，以及冻结提交 `704855f73c8b57ab595ebe1d89f54d09697f6e4e`

## Findings

### [Low，已修复] 跨轮 `4 对 2` 原先固定数值并绑定旧报告哈希，但没有从两轮统计重算

位置：`tests/test_claim_quantitative_preservation_round19.py`

原测试确认第十八轮报告文件哈希、`exploratory: true` 及遗漏计数为 baseline 2、0.1.0 为4，但若机器报告中的累计数字与两轮逐题统计脱节，测试仍可能通过。

已修复：测试现在读取已由 SHA-256 锁定的第十八轮报告，从其 `numeric_fidelity_observation` 计算旧轮遗漏，再与第十九轮四题的实际缺失标准数相加；同时重算5个相关拓扑和每臂15个输出。聚焦测试及全量测试均通过。

**没有剩余阻塞性或非阻塞性发现。**

## 逐项核对

### 文档与机器数字

通过。`README.md`、`evaluations/README.md`、`docs/quality-polish-round-19.md` 和机器报告一致记录：baseline `35/36`、`11/12` 完整、2次偏好；0.1.0 为 `34/36`、`10/12` 完整、2次偏好；另有8次持平。总 token 为117,890对130,302，0.1.0多12,412、约10.5%；详细文档还保留 completion token约多26.1%、成本约多38.7%、中位延迟约低5.3%。

所有文字都把一分差限定为小样本观察，明确“不能改写成稳定退化”；没有改变 Skill 版本、status 或 evidence，也没有把2比2偏好写成质量提升。

### 自包含机器报告

通过。独立脚本将 `evaluations/reports/claim-quantitative-preservation-round-19-diagnostic.json` 与盲包、揭盲键和正式 review-result 对齐，结果无差异：

- 12个 review item、24个候选输出、72个布尔判断；
- task、hard criteria、候选输出、匿名映射、评分、偏好及理由一致；
- 24个 `output_sha256` 全部由内嵌正文重算通过；
- overall 与四组 by-case 统计均能从内嵌 items 重算；
- 8个 artifact 哈希均从保留的运行产物重算通过。

### 冻结协议、包指纹和活动用例

通过。冻结提交为 `704855f73c8b57ab595ebe1d89f54d09697f6e4e`；协议源哈希同时匹配当前文件和冻结提交。当前包指纹重算为 `bfda03a341b9d1b62f2004b7854fca0d4e7712a730a95274e3f9a4b43f7d8e29`，与报告一致。

`claim-evidence-review` 当前活动用例为14项，全仓活动用例为116项。第十九轮测试固定冻结提交、prepared 哈希、8个 artifact 哈希，并把四个活动题的 `prompt` 与 `must_include` 分别绑定冻结 `prompt` 与 `hard_criteria`。

### 跨轮探索性信号

通过。机器报告通过具体路径及 SHA-256 绑定第十八轮报告，并明确 `exploratory: true`；现由测试从两轮数据重算 baseline 2次、0.1.0 4次遗漏、5个相关拓扑、每臂15个输出。README 和两份说明都声明该汇总发生在揭盲后，只能触发下一组确认性复测，不能替代第十九轮预注册升版门槛。

### 第十八轮测试职责调整

通过。`tests/test_claim_evidence_round18.py` 只移除了“当前全仓必须仍为112项”和“claim套件必须仍为10项”的历史当前状态断言，并把第十八轮 comparison ID 集合从等于改为子集。它仍保留：第十八轮报告 scope 中历史112/10、冻结提交与关键哈希、36输出/108布尔、包指纹、六题 ID，以及六题 `prompt`/`must_include` 与冻结协议逐项一致。

当前116/14及新增四题内容由第十九轮测试接管。该调整允许后续合法增加活动用例，没有削弱第十八轮历史报告或六题绑定。

### 版本与结论边界

通过。catalog 中 `claim-evidence-review` 仍为0.1.0、`experimental`、`evidence: null`，Skill 包没有待提交修改。报告明确0.1.0的两次失败分散在两个题型、各一次，且 baseline 在地区题也有同类失败，因此未达到“至少两个题型各自重复且 baseline 明显更少”的门槛。

## 残余限制

- 单模型、单推理强度、每臂三次和模型辅助盲评限制外推；一分差、2比2偏好和跨轮4比2均不具统计显著含义。
- 显式臂没有 `skillCalls` 遥测，不能证明每次实际读取 Skill 正文。
- prepared config/tests 原文件未随运行目录保留；其哈希能与 frozen 元数据交叉核对并由测试固定，但不能从原 prepared 文件再次计算。
- Windows 无符号链接权限导致1项测试按设计跳过；这是环境限制，不是功能失败。

## 验证

- `git diff --check`：通过，无输出；
- `python scripts/validate_collection.py`：通过；
- `python -m unittest discover -s tests -v`：69项，68项通过，1项因 Windows 符号链接权限跳过；
- `python -m unittest tests.test_claim_quantitative_preservation_round19 -v`：通过。

本审查没有修改 Skill 版本、status 或 evidence，没有提交或推送。
