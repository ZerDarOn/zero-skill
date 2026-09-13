# Round 30 冻结前独立复核

复核对象为 `article-visual-plan-discriminative-23` 的 `README.md`、`promptfoo.json`、`cases.json` 与 `tests/test_article_visual_discriminative_comparison.py`，并按需只读核对已提交的 `article-visual-plan`、Round 29 active cases、Promptfoo prepare/summarize 实现及固定 Baoyu 上游夹具和 provenance。本复核不读取未来运行结果或臂映射，也未修改 Skill、catalog、协议或题目。

## 初审发现与修正

初审发现两项 P2：

1. `unequal-cohort-observed-rates` 的第一项硬标准曾强制“比较段后”和“同一尺度的并排结构”，但题面没有唯一要求这两点。该项已放宽为要求明确插入位置、理解目的，以及能公平呈现两次观察的并排、等权卡片或等价结构。修正后仍可客观判断，同时不排除其他忠实编码。
2. 原测试只锁定部分协议字段和少量题面事实，隐藏标准检查也只能发现完整标准逐字进入 prompt，不能充分阻止协议、题目或释义式 rubric 注入回归。测试现以固定 SHA-256 锁定完整 `promptfoo.json` 与 `cases.json`，逐字段锁定 `common_prompt` 和三臂的 source、install mode、invocation，并逐条断言 prepared metadata 及模型 prompt 精确由显式调用前缀、公共提示和原题面组成。baseline 不带显式调用前缀。

复核修正后，无开放 P0、P1、P2 或 P3，可以冻结。

## 已核验项目

- 六题均为未进入 Round 29 active cases 的新 ID 和新任务表面；三个机制各两题。
- 每题四项硬标准均可从题面材料判断，核心标准索引唯一且有效；未再发现会把可选审美或题面外位置要求强加为唯一答案的标准。
- 三臂使用同一模型、推理等级、公共任务边界和题面；baseline 不加载 Skill，ours 与 upstream 均为项目级显式调用。
- 规模为 `6 × 3 × 3 = 54` 份输出、18 个匿名三候选评阅项和 216 个布尔判断。
- 沙箱为只读；公共提示禁止工具、文件读写、生图、网页搜索、澄清和执行完成声称。可观察到的命令、文件、MCP、搜索或 Codex app 调用会使运行无效。
- 冻结门槛方向正确：只在同一机制两题上 ours 每题至少 `2/3` 次核心失败、baseline 每题至多 `1/3` 次核心失败且 54 份输出全部有效时，打开最小候选设计；upstream 仅作设计上下文。
- prepare 产物保留题目和臂隔离，模型 prompt 不含隐藏硬标准；固定上游包携带 MIT 许可证，来源提交与自包含夹具边界保持不变。

## 验证

```sh
python -m unittest tests.test_article_visual_discriminative_comparison -v
git diff --check
```

定向测试共 5 项，全部通过；`git diff --check` 通过。

## 限制

本结论只覆盖冻结前协议、题面、准备逻辑和静态边界，不证明未来正式运行基础设施有效，也不评价尚未生成的模型输出。比较只覆盖一次性文本配图规划，不能外推到隐式路由、实际图片质量、文字渲染、文件回填、编辑器集成或完整 Baoyu 工作流。模型辅助盲评仍不等于独立人工视觉设计评审。
