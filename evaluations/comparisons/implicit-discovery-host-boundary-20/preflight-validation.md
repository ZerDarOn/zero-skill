# Round 27 冻结前预检

日期：2026-09-13

## 探索性链路

正式候选前的运行都位于被忽略的 `evaluations/runs/`，不进入正式统计。

最初直接把旧 `evaluations/promptfoo/implicit-discovery.json` 交给原生 runner：v1 因缺少 `native_resume` 配置在模型运行前被拒绝；v2 因旧 cases 没有 `turns` 被拒绝；v3 因旧 cases 只有一项 hard criterion 被拒绝。这三次证明 runner 没有静默补写旧规格。

补齐格式后的 v4 使用原生 runner 固定的只读命令。baseline 与项目 Skill 各一条轨迹，模型在项目 Skill 臂中选择 `discovery-token` 并连续尝试读取精确 `.agents/skills/discovery-token/SKILL.md`，但所有命令均被策略阻断，最终没有返回正文令牌。runner 基础标志显示 2/2 valid，是因为它只校验事件传输，不检查 stderr policy block；本轮专用 analyzer 因而必须单独分类策略阻断。

v5 在临时 spec 中写入 `workspace-write`，但进一步核对发现 runner 的实际 child command 仍硬编码为 `read-only`。该次不是有效的沙箱因果对照，原结果保留但不用于结论。v6 用只存在于忽略目录的 wrapper 实际生成 `workspace-write` child command，同时把 cwd 与隔离 HOME 放到仓库授权根内；精确 Skill 读取仍被宿主策略阻断。由于无沙箱运行会扩大不必要的文件访问范围，本轮到此停止，不尝试绕过宿主策略。

三次有真实轨迹的 exploratory raw 指纹如下：

| 运行 | frozen.json | run-meta.json | native-results.json | 结果边界 |
| --- | --- | --- | --- | --- |
| v4 read-only | `458152bdf867c4aefce0acc1f2e190573bea4ccb83f118d622e8fbdc3b9007ad` | `58d3433eda01ecc5dd904a4cb90c7bd3b0d35e65a8aee40881baa7370db1314d` | `7e4996a5d7cd6ebb2e793174f976b651a30faa618bd28bcaced29e0b95ca7386` | 精确路由尝试存在，正文未加载 |
| v5 无效沙箱对照 | `75ff2cc75a8588ca30ac86944901eeb046b98ebe7a7203284b696b3769432d1d` | `6c8efffe32c408f1eac5721edb8fef6450d8a723ebb53e8fe2cbbe8b971c1d5a` | `f81710164f022c73afb8bff25e1fccaeadec91ae1763b19c0647105e63ba6082` | spec 与实际命令不一致，不作因果证据 |
| v6 repository-root wrapper | `467b25c6ed504ffc0da9441d687ab8b2d7cf2fe89a04b3c68596d09172b39456` | `f4d4044b86b1c828adc6025719834bd95eb7a7654cdfd00f1bdd99181d7cbdaf` | `cd98c58280558f491a0040152d61db5f98b03f6e272e674b9687e01f197412d3` | 实际 workspace-write 仍被宿主策略阻断 |

## 当前候选预检

当前候选换用新的 `implicit-discovery-probe`，自然提示不含 Skill id、路径或令牌。预检目录为 `implicit-discovery-host-boundary-20-preflight-20260913-v1`，只执行冻结重复数的 `1/3`，共 4 条轨迹。

独立按当前 analyzer 分类：

| 臂 | 尝试 | route selected | body loaded | policy blocked | transport valid | operational success |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| baseline | 2 | 0 | 0 | 0 | 2 | 2 |
| probe | 2 | 2 | 0 | 2 | 0 | 0 |

两个 baseline 都严格返回 `ROUTE-NOT-AVAILABLE`。两个 probe 都尝试读取精确 `.agents/skills/implicit-discovery-probe/SKILL.md`，说明两个自然触发表面均选择了目标路由；读取随后被策略阻断，最终也返回备用值。每个 probe 还先输出一条加载过程消息，再输出最终备用值，所以单一消息和 output-last 绑定均失败。

预检 raw 指纹：

- `frozen.json`：`8c27c103c1d89d000d57d088d369e944d9959061f95c8b67fc6e16f8694b50d0`
- `run-meta.json`：`e0fd8fa841478b601cb838df1130cdf84a4df35fe14ed9ee8bb611890d3c4f48`
- `native-results.json`：`ee7cca9e48ddfae526c56cee9ed1d0621775d86185fd566adca8c19718eb5e61`
- prepared config：`904151fc5d58c7bdcd357467f2caee7778b790c7760b7a5f95d777def0fc20e3`
- prepared tests：`7536e6b6d6555351a4419c7f92bed4d2c6e60fcf2c9d1d37590e8eb0c493d584`
- probe package：`e45999851a3cf7d3dbb061b784c7a82bb5a9b7bfd6448751ecf2414ef8670887`
- job order：`3728cd1ad8af3ffdee0fe6467ae47d9c17a5ada804d64de4ff67bae1357684f0`

正式 analyzer 对这个目录返回 `ValueError: run does not contain every frozen repetition`，并且没有创建输出文件。预检不能与后续正式结果合并，也不能用 2 次路由选择代替正式的 6 次重复。

## 当前冻结字节

- protocol：`15c45a914b63ac76b25e373ec3245190512a5050aeca15399e3c06fa16e6be56`
- preparer：`4eca5a4c2caeffbeca6663ecf49ce8f9e293f86372593abfb3d794ea1d1b788b`
- runner：`cac3e238d717f7a268d9b6800bec11002eaa5d3e54ddf2458f65a2983e9912b5`
- normalizer：`91c336bc71b409adabe8c39668cbbb98b72fcb6bafcfc05c21faf899455daa9d`
- analyzer：`802d18bddd6142486ce2cf077043614c290ec998c7940b1573c244ffe9f8098e`
- spec：`369a5d85e1d8959a186e02ec734c2ee85ede9487f6e08bb0aab7df0e56be43b3`
- cases：`d22f5d4050155170d7990f479a6324754e311f82627a06b374082a59670547fd`
- probe package：`e45999851a3cf7d3dbb061b784c7a82bb5a9b7bfd6448751ecf2414ef8670887`

预检符合正式冻结条件：自然提示两臂相同，路由选择可以从精确路径重算，正文加载与策略阻断分开，失败没有被技术 valid 标志掩盖。预检也强烈预示正式门禁会失败，但正式结果仍应按冻结的三次重复完整运行并原样保留；任何失败都只关闭后续业务隐式比较，不触发业务 Skill 修改。
