# 第三十一轮质量打磨：当前文稿润色与 Humanizer 前向盲测

日期：2026-09-14

## 本轮问题

`prose-polish` 早期做过三方对照，但当时评测的是 0.1.1；当前 0.1.3 只有局部长度与保真回归，旧结果不能证明当前包。本轮重新比较无 Skill、当前 `prose-polish` 0.1.3 与固定的 Humanizer 3.0.0，重点检查严格压缩、修订历史和作者声音克制。

Humanizer 是更广的英文 AI 写作模式清理技能。本轮只比较三者共同覆盖的中文文本润色切片，没有测试它的全部规则，也不把 Star 数或项目知名度当作质量证据。

## 固定设计

协议、六题、完整运行配置与两个 Skill 包在提交 `5fb4a1ca09a7a17059b41a372daf1c06e0927fa0` 冻结并推送。三臂使用同一个 `gpt-5.6-sol`、medium、公共提示和只读隔离配置；每题每臂重复三次，共 `6 × 3 × 3 = 54` 份输出、18 个匿名评阅项和 216 个布尔判断。失败保留且不重试。

六题按三个机制各两题组织：

- `bounded-condition-preservation`：在 85 字内保留迁移范围、条件纳入、明确排除和未知状态；在 90 字内保留三项合取资格与四类例外。
- `revision-history-control`：审计作废旧指标但保留主观引语；局部撤回人数更正时保留仍有效的条件性日程修订。
- `author-voice-restraint`：删除或收敛原稿中的成功与全员赞扬夸大；对明确声明为刻意的短句与重复原样返回。

候选门槛在运行前写定：同一机制的两题中，当前 Skill 必须每题至少 `2/3` 次出现核心失败，同时 baseline 每题最多 `1/3` 次核心失败，且 54 份输出全部有效，才允许打开最小候选设计。Humanizer 只作设计参照，不参与本地改版门槛。

冻结前独立复核发现两项 P2。第一版迁移题与已有改期题过于相似，随后换成地区范围、条件纳入与上线状态的新表面；测试最初也没有锁定生成后的完整配置和题目，随后加入确定性哈希、三臂完整 provider 配置与实际 Skill 副本校验。修订后复核无 P0–P3，才冻结并运行。

## 正式结果

预检 3/3 完成且只验证基础设施，不计分。正式运行 54/54 完成，三个臂各 18 行；provider error、禁止工具轨迹和 Promptfoo 失败均为 0。

| arm | 完整通过 | 标准通过 | 唯一偏好 |
| --- | ---: | ---: | ---: |
| 无 Skill | 17/18 | 71/72 | 1 |
| `prose-polish` 0.1.3 | 16/18 | 70/72 | 0 |
| Humanizer 3.0.0 | 15/18 | 69/72 | 0 |

六个 `false` 全部来自 `restrained-voice-with-fixed-closing` 的同一核心标准。该题要求保留事实和固定末句，同时删除或实质收敛“圆满成功”与“每个人都高度赞扬”。三次重复中，baseline 失败 `1/3`、当前包 `2/3`、Humanizer `3/3`；唯一偏好来自第三次重复的 baseline，因为另两组仍保留明显夸大。

评审保留这六个失败：相关输出仍写“很成功”“顺顺利利”“圆满结束”或“每个人都赞许/夸修得好”等表达。原稿本身含有成功和全员赞扬，所以它们没有被重复扣为“新增事实”；扣分只落在专门要求收敛夸大的标准上。

另外五题三臂均无核心失败。尤其是同属 `author-voice-restraint` 的原样保持控制题，三臂都是 `0/3`：当前包没有普遍改坏刻意短句，只在一个夸大收敛表面出现重复遗漏。

## 门槛与决定

| 机制 | 当前包核心失败 | baseline 核心失败 | 触发 |
| --- | --- | --- | --- |
| bounded-condition-preservation | `0/3`、`0/3` | `0/3`、`0/3` | 否 |
| revision-history-control | `0/3`、`0/3` | `0/3`、`0/3` | 否 |
| author-voice-restraint | `2/3`、`0/3` | `1/3`、`0/3` | 否 |

作者声音机制只有一题达到当前包的单题失败阈值，配对控制题没有失败，因此不能后验把单题差异升级为机制级问题。三个机制均未触发预注册门槛，不打开候选设计。

`prose-polish` 正文、版本和 catalog 均不变，继续是 0.1.3、`experimental`、`evidence: null`，包指纹仍为 `85460012946903fe6401f8df5f6b284497103606fbeaed86eda963d92a103047`。六个冻结题加入活动回归，该 Skill 从 9 例增至 15 例，全仓从 160 例增至 166 例。

这次结果不证明当前包优于无 Skill 或 Humanizer。相反，在这组六题里 baseline 多通过一个标准，Humanizer又比当前包少通过一个标准；差异全部集中于一道题和三次重复，不能据此形成一般排名。该局部信号保留给未来不同表面的前向验证，不能据此修改现有 Skill。

## 运行成本

当前 Skill 相对 baseline 的总 token 多 `13.9%`、记录成本多 `49.7%`，中位延迟多 `7.4%`。Humanizer 相对 baseline 的总 token 多 `68.1%`、记录成本多 `191.4%`，中位延迟多 `11.2%`。当前 Skill 相对 Humanizer 少 `32.3%` token、少 `48.6%` 记录成本，中位延迟少 `3.4%`。

这些数字只描述本次 Promptfoo 记录，会受输出长度、缓存、定价和调度影响，不是稳定性能基准。更长的上游指令也不等同于更差的完整产品设计。

## 评审与外推边界

匿名评审由模型辅助的独立任务完成，评分时只读取匿名包与表单，对三臂随机映射保持盲态。揭盲后的决策复核由同一评审任务完成，因此它校验了评分一致性和门槛计算，但不是第二位独立评分者。

本轮只覆盖六个合成、单轮、中文、显式项目级调用任务。它没有验证隐式发现、真实作者满意度、多轮编辑、文件读写、发布、其他语言或其他模型。原始 Promptfoo 产物仍被 Git 忽略；公开机器报告嵌入合成输出、评分投影和哈希，新克隆可检查已提交证据，但不能独立重建 provider 事件。

## 下一步

当前 `prose-polish` 已补上当前版本的三方前向证据，继续追加相近短文题的收益有限。下一轮应转向尚缺严格前向证据的技能；修伞题保留在活动回归，等出现新的作者声音表面后再检验它是否构成跨题机制，而不是围绕已经揭示的题目调规则。

## 对应证据

- [机器报告](../evaluations/reports/prose-polish-current-humanizer-round-31-diagnostic.json)
- [冻结协议](../evaluations/comparisons/prose-polish-current-humanizer-24/README.md)
- [冻结前独立复核](../evaluations/comparisons/prose-polish-current-humanizer-24/prefreeze-review-independent.md)
- [揭盲后独立复核](../evaluations/comparisons/prose-polish-current-humanizer-24/postscore-decision-review-independent.md)
- [最终工程复核](../evaluations/comparisons/prose-polish-current-humanizer-24/final-engineering-review-independent.md)
- [固定 Humanizer 来源](../evaluations/fixtures/upstreams/humanizer/9862685f575c65a8247f90369951df1b3416e3d6/provenance.json)
