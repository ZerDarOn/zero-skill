# Round 26 真实预检

日期：2026-09-13

在当前未提交候选字节上，各取两个队列的全部两题、两臂和 1 次重复，共执行 8 条真实单轮轨迹。预检目录受 Git 忽略，不进入正式统计：

- `evaluations/runs/explicit-invocation-canary-preflight-20260913-v1`
- `evaluations/runs/conversation-explicit-operational-preflight-20260913-v1`

两个队列均为 4/4 技术有效、4/4 operational success。探针臂分别精确返回 `EMBER-QUARTZ-260913` 与 `TIDAL-COPPER-260913`，baseline 均未命中令牌。业务队列的 baseline 与 ours 各 2/2：每条只有一个 agent message，与 output-last 绑定；没有工具项、策略阻断、过程播报、超时、非零退出或损坏 JSONL。该结果只说明协议可运行，不是正式可靠性结论。

## Canary 预检绑定

- frozen：`5b53ebb014a9d1a2616b702add88efbd3394a99f1babcf82f26c368531f45f20`
- run metadata：`97730d333bff2746796a43a156a4cff3c423ecca82b8c76a01fff3882e3789f0`
- native results：`58825e9dcf89aa1d6b61b8e27e32ad5c7a1fef8d43e5b55f693322787337e70d`
- prepared config：`4d27d37d0183bba5fbf2398e199dff68bcc652148218197194acf9bffda4c7a3`
- prepared tests：`e025cb0ab3564571b47ccc86f6aa16cf75eaa207d72875173164d8216eecee8f`
- job order：`08a7cce1edbda5c5f311e9a02f4b2a0a7d62188355bb9904056044d0ab875da1`
- probe package：`0d77227b068fd544342082d48d852a7549252058cf2c266ebce61c43e95aeb06`

## Business 预检绑定

- frozen：`6a4269b4907b23d29265ffbb0da711f0d6cffb4b7dc9b44408b90db487ec7c60`
- run metadata：`8f5d5932dc831aa31a02fd55137baf5bc6c3872cdf395d5903098be0e04802e7`
- native results：`455879c75bef1cf5ad763f37c0065455ac9987e494305913a84e5ead34c66b29`
- prepared config：`d7520846a3f60321ee357aa466f6ea7b0c04ce1a4d5159c56e9ff4b7e84f5828`
- prepared tests：`85a814f1da659a9a5146dc92c77f8d9c297564a7e618eebec83163e19ad26d25`
- job order：`2021408dbb41d2828b3b7cafb187a0013bbb2cf686cb6e8463fbe1e2c80da2d3`
- `conversation-rehearsal` package：`b09fcd8955cce840d3ab9fb9acc19f29d6bff371d66b4b7ccfabb3d9f53e3ff9`

正式运行仍须从冻结提交重新准备两个全量目录，执行各 10 次重复，并由绑定的 analyzer 对完整 80 条轨迹统一判断。预检成功不得替换正式失败，也不得与正式结果拼接。
