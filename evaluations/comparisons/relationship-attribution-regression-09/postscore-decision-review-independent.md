# Independent post-score decision review

- reviewer: `gpt-5.6-sol` medium
- date: 2026-09-11
- decision: **既定升版门槛满足，建议登记 `relationship-review` 0.1.4，状态继续保持 `experimental`。**

## Run validity

- 三臂各27个输出，共81个输出；planned 与 executed repetitions 均为3。
- 三臂 `promptfoo_passed_rows` 均为27，provider errors 与 forbidden tool rows 均为0。
- 运行基础设施标记为有效；该协议是项目级显式Skill质量对照，不构成隐式路由或真实关系场景验证。

## Three new cases

| case | baseline | 0.1.3 | 0.1.4 candidate | preference baseline / 0.1.3 / candidate |
| --- | ---: | ---: | ---: | ---: |
| `nested-handoff-report-chain` | 6/9，0/3完整 | 3/9，0/3完整 | 7/9，1/3完整 | 1 / 0 / 2 |
| `partial-system-record-invitation` | 6/9，0/3完整 | 5/9，0/3完整 | 8/9，2/3完整 | 0 / 0 / 3 |
| `corrected-draft-not-sent` | 9/9，3/3完整 | 9/9，3/3完整 | 9/9，3/3完整 | 1 / 0 / 2 |
| **new-case total** | **21/27，3/9完整** | **17/27，3/9完整** | **24/27，6/9完整** | **2 / 0 / 7** |

判断：候选在有提升空间的嵌套转述和有限系统记录两题均提高硬标准及完整输出；更正题三臂已经满分，候选没有可提升空间且未退化，并获得2次偏好。三个新题合计相对0.1.3提高7项硬标准和3个完整输出。

## Six reused cases

| case | baseline | 0.1.3 | 0.1.4 candidate | candidate vs 0.1.3 |
| --- | ---: | ---: | ---: | --- |
| `clear-labeled-return-date-one-line` | 9/9，3/3 | 9/9，3/3 | 9/9，3/3 | 持平 |
| `explicit-numbered-speaker-mapping` | 9/9，3/3 | 9/9，3/3 | 9/9，3/3 | 持平 |
| `conditional-options-without-clarification` | 9/9，3/3 | 9/9，3/3 | 9/9，3/3 | 持平 |
| `disputed-access-card-handoff` | 6/9，0/3 | 7/9，1/3 | 9/9，3/3 | 改善2项、2个完整输出 |
| `mutual-specific-invitation` | 9/9，3/3 | 9/9，3/3 | 9/9，3/3 | 持平 |
| `decline-with-concrete-alternative` | 9/9，3/3 | 9/9，3/3 | 9/9，3/3 | 持平 |
| **reuse total** | **51/54，15/18完整** | **52/54，16/18完整** | **54/54，18/18完整** | **无退化，净改善2项、2个完整输出** |

复用题偏好总计为 baseline 3、0.1.3 2、candidate 5。baseline的3次偏好全部来自三组均满分的明确编号映射题，不构成候选硬标准退化。

## Attribution-related criteria

采用预先可解释的口径：三个新题各自前两项为来源、证据层级或当前有效状态标准，共18项；门禁卡复用题第一项为直接来源保留标准，再增加3项。

| scope | baseline | 0.1.3 | 0.1.4 candidate |
| --- | ---: | ---: | ---: |
| three new cases, first two criteria | 12/18 | 8/18 | 15/18 |
| above plus access-card attribution criterion | 12/21 | 9/21 | 18/21 |

候选相对0.1.3在新证据拓扑上净增7项来源相关判断；加上原门禁卡缺口后净增9项。行动、合作语气和反过度纠正标准没有为此退化。

## Nested-report residual

`nested-handoff-report-chain` 的候选在前两次重复中都把“B转述C说D可能取走”压平为类似“C说D可能取走”，因此第二项来源链标准仅1/3通过。这是实际残留，不能在报告中写成“嵌套转述已经解决”或“一般来源链处理已验证”。

该残留不阻断本次升版，理由是：

1. 既定门槛要求稳定改善而非所有新题满分；候选在该题三次分别为2/3、2/3、3/3，0.1.3三次均为1/3，逐次都改善。
2. 本次修订的原始稳定缺口是长短输出中的双方来源保留；门禁卡复用题从0.1.3的7/9、1/3完整提高到候选9/9、3/3完整，三次均修复。
3. 有限系统记录题也从5/9、0/3完整提高到8/9、2/3完整；更正题保持9/9、3/3完整。
4. 六个复用题没有任何逐题退化，候选反而达到54/54、18/18完整。
5. 目录仍为experimental，允许把边界明确、证据充分的窄改善登记为小版本，同时保留未解决缺口。

后续应新增与当前钥匙题表面不同的嵌套转述前向任务，专门检查“说话者—转述者—原始来源—不确定程度”四层关系；在该任务通过前，不应继续为嵌套来源压平问题升版，也不应扩大0.1.4的结论。

## Gate decision

既定门槛解释为：候选在三个新题的来源相关标准上总体且在有提升空间的题目中稳定改善，同时六个复用题相对0.1.3不退化。按此冻结前定义：

- 新题：24/27、6/9完整，高于0.1.3的17/27、3/9完整；
- 来源相关标准：15/18，高于0.1.3的8/18；
- 复用题：54/54、18/18完整，不低于0.1.3的52/54、16/18；
- 总体：candidate 78/81、24/27完整、12次偏好；0.1.3为69/81、19/27完整、2次偏好。

因此门槛满足，建议把冻结候选包登记为0.1.4并继续保持experimental。发布说明必须同时记录：该结论来自合成材料、显式加载和模型盲评；嵌套B到C转述仍有2/3压平失败，属于后续缺口而非已解决能力。
