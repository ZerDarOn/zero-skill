# 第三次吸收：故障证据排查与论断证据审查

日期：2026-09-08。起始提交：`a58be07d7c83a35ba583c0883aea87d30f9822b6`。

## 来源与取舍

| 上游固定来源 | 采用 | 舍弃 | 本地规则与可观察用例 |
| --- | --- | --- | --- |
| Superpowers `b36e0829c6d0140e93cfef2ca599b1b07d4a7797` 的 `systematic-debugging/SKILL.md`；仓库 MIT 许可 | 组件边界追踪、最小假设检验、按原条件核对结果 | 强制完整四阶段、自动调用其他技能、广泛打印环境或敏感数据 | 同请求标识追踪、只选一项区分检查、恢复不等于验证；四个 debug 用例 |
| Scientific Agent Skills `9cf7d9aea7d84754db4c167ab04b299d33c444bc` 的 `scientific-critical-thinking/SKILL.md`；该技能元数据和仓库 `LICENSE.md` 均为 MIT | 观察与解释分离、识别混杂、按证据强度调整结论 | GRADE/Cochrane 整套框架、完整科研流程、外部图像生成与 API | 追溯共同来源、保留分母与更正、给范围化结论；四个 claim 用例 |

两个包及合成示例均为本仓库原创措辞，没有复制第三方文件、执行上游脚本或调用其外部服务；`catalog/upstreams.json` 继续保持 `imported: false`。Scientific Agent Skills 已指向对应固定入口；Superpowers 更新为本轮实际采用的 `systematic-debugging` 入口，同时保留同提交下既有验证方法的采用说明。两者均为 `entrypoint-reviewed`，没有改写历史 Star 快照。

## 实现

- `debug-evidence-triage` 0.1.0：`engineering / analysis`。区分观察、用户猜测与模型假设，沿同一请求缩小边界，给一项带分支判断的检查，并区分恢复、缓解、待验证修复与已验证解决。
- `claim-evidence-review` 0.1.0：`research / analysis`。拆解论断、追溯转述依赖，保留分母、时间、比较条件、反证与更正，输出材料实际支持的范围化表述。

两者均为 `experimental`，登记 `evidence: null`。单次合成诊断及执行模型评分不能支持 `verified`。

| 技能 | 包 SHA-256 | active 用例 SHA-256 |
| --- | --- | --- |
| `debug-evidence-triage` | `2fe35079629562ba83b4cbaf492d2f0398a41832390ab276dcbf7ac97ac86bb2` | `29cdf87df547a5d85964adf5fcfde7e27d87547f37e6b1c1c6e9ca29b5d99bd5` |
| `claim-evidence-review` | `bfda03a341b9d1b62f2004b7854fca0d4e7712a730a95274e3f9a4b43f7d8e29` | `9df9896edc65bf50f4383705edb9a4576e8df79c0e4785d0c20eba0b57233682` |

## 对照运行

先在技能文件不存在时运行 8 个 `planned` 合成用例，再实现、登记并只把 `stage` 改为 `active`，随后用相同 8 个用户请求显式加载各自完整包。模型为 `gpt-5.6-sol`、`medium`。共 16 次有效单轮生成，模型启动 16 次、启动失败 0、重试 0；每次使用独立临时目录、`--ephemeral --ignore-user-config`、只读沙箱且无工具。

| 技能 | Baseline | Skill | 严格改善 | 退化 |
| --- | --- | --- | --- | --- |
| `debug-evidence-triage` | 1/4 | 2/4 | 1 | 0 |
| `claim-evidence-review` | 4/4 | 4/4 | 0 | 0 |

debug 的改善来自 `decisive-reproduction`：两组都定位了假值判断误伤零值，但 baseline 没有建议覆盖零值与 null 的回归验证，skill 明确补上。两组都未通过 `correlation-is-not-root-cause`：虽然排除了部署是必要原因并缩小边界，但下一项检查只看网关出站，没有把同一请求的网关出站与队列入站摘要放在一次对照中。两组也都未通过 `recovery-is-not-verification`：虽然正确区分恢复与验证、保留原触发条件并拒绝删除命令，但都没有明确要求只在安全隔离环境复验。

claim 四例两组均通过。`bounded-supported-conclusion` 中 baseline 写“30条（75%）”，skill 写“30/40”；后者在一句话限制下表达相同分母与比例，按语义而非关键词判定通过。

baseline 总观察时长 116,744 ms，输入／缓存输入／输出 token 为 122,306／88,064／1,836；skill 为 106,478 ms 和 129,276／92,160／1,412。时长是本地编排观察区间，不是服务端延迟。

完整包和前后用例快照、精确提示、原始输出、事件、stderr、哈希、时长、用量及逐例理由见[诊断证据](../evaluations/reports/third-absorption-0.1.0-diagnostic.json)。

## 本地导出

两个 ZIP 均只包含 `bundle-manifest.json`、对应技能入口和合成示例；manifest 包指纹与实现表一致。

| 归档 | ZIP SHA-256 |
| --- | --- |
| `dist/debug-evidence-triage-0.1.0.zip` | `23ccad1cdb9c30b7f059758b3553482c3535f87b0eead82bbb8ba3e43439ff7b` |
| `dist/claim-evidence-review-0.1.0.zip` | `d2f29d62f18cc2605cc1aecb1b832eecc0e64d9ba57872d204cfd6c8ca374e1c` |

## 限制

每例只运行一次，初评由本次执行任务中的 Codex 模型完成，后由同项目 Astra 只读复核并修正一项漏判；这仍不是独立人工评审或重复采样。显式加载不测试自动发现与路由；无工具隔离 CLI 不代表真实故障诊断、联网核验或开放工具环境安全。强 baseline 已通过 5/8，用例中观察到的一项改善不证明稳定或聚合收益。
