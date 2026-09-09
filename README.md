# Skill 集合

把可复用的方法做成清晰、可组合、可验证的技能。覆盖开发、研究、创作、办公、人物、关系和生活。

当前阶段：**第五次吸收 v0.1**。已有十二个可试用的 `experimental` 技能。第五次吸收新增 `react-performance-review` 0.1.0 与 `meeting-communication-review` 0.1.0；单次合成对照按全部冻结约束分别为 3/4→4/4 和 3/4→3/4，后者同时有一项改善与一项退化。这仍未达到 `verified`，也未完成自动发现路由或独立人工评审。上游项目是固定来源参考，不代表已引入代码。

## 从这里开始

- [本地试用与导出指南](docs/trying-skills.md)
- [本地 ZIP 导出验证报告](docs/local-skill-distribution-report.md)
- [第二次吸收实施与诊断](docs/second-absorption-report.md)
- [第二次吸收完整诊断证据](evaluations/reports/second-absorption-0.1.0-diagnostic.json)
- [第三次吸收实施与诊断](docs/third-absorption-report.md)
- [第三次吸收完整诊断证据](evaluations/reports/third-absorption-0.1.0-diagnostic.json)
- [第四次吸收实施与诊断](docs/fourth-absorption-report.md)
- [第四次吸收完整诊断证据](evaluations/reports/fourth-absorption-0.1.0-diagnostic.json)
- [第五次吸收实施与诊断](docs/fifth-absorption-report.md)
- [第五次吸收完整诊断证据](evaluations/reports/fifth-absorption-0.1.0-diagnostic.json)

- [第一次吸收：新对话执行说明](docs/first-absorption-handoff.md)
- [第一次吸收报告](docs/first-absorption-report.md)
- [首批行为评测与复核](docs/first-behavior-evaluation-report.md)
- [关系复盘 0.1.1 归因修订评测计划](docs/relationship-review-attribution-evaluation-plan.md)
- [P3 公众人物观点设计](docs/public-person-perspective-design.md)
- [P3 0.1.0 运行与 0.1.1 复核修订](docs/public-person-perspective-implementation-report.md)
- [P3 0.1.0 精确诊断证据](evaluations/reports/public-person-perspective-0.1.0-diagnostic.json)
- [P3 0.1.2 版本对照报告](docs/public-person-perspective-0.1.2-comparison-report.md)
- [P4 沟通演练 0.1.0 实施与诊断](docs/conversation-rehearsal-0.1.0-report.md)
- [第二轮高星项目研究](docs/research-round-02.md)
- [整体方案与建设顺序](docs/architecture.md)
- [上游设计取舍](docs/upstream-design-review.md)
- [收录与编写规范](docs/skill-standard.md)
- [新增技能流程](CONTRIBUTING.md)
- [评测方法](evaluations/README.md)
- [机器可读分类与本地技能登记](catalog/collection.json)
- [上游候选登记](catalog/upstreams.json)

## 分类

| 目录 | 场景 |
| --- | --- |
| `skills/engineering/` | 开发与工程 |
| `skills/research/` | 研究与分析 |
| `skills/creation/` | 写作与创作 |
| `skills/productivity/` | 办公与效率 |
| `skills/people/` | 人物与思维 |
| `skills/relationships/` | 关系与沟通 |
| `skills/life/` | 生活与娱乐 |

每项技能有一个主分类；跨场景用标签关联。另有独立的能力类型：`analysis`、`perspective`、`simulation`、`workflow`、`tool`。分类定义以登记表为准。

## 本地检查

需要 Python 3.11 或更新版本，使用标准库，无第三方安装步骤。在仓库根目录运行：

```sh
python scripts/validate_collection.py
python -m unittest discover -s tests -v
```

校验只读取仓库；不联网、不安装技能、不读取聊天软件。通过结构校验不等于通过行为评测。

## 目录职责

```text
catalog/       分类、本地技能元数据、上游来源
skills/        自包含的技能包，按场景分类
templates/     编写技能和登记评测的起点，不作为技能加载
evaluations/   合成用例、评测方法；真实运行记录另行生成
scripts/       本地结构校验
tests/         校验工具的回归测试
docs/          架构、规范、调研取舍
```

真实人物资料、聊天记录和私人运行产物放在被忽略的 `private/` 中。公开示例只用合成或已确认可发布的资料。`.gitignore` 不是完整的隐私保护工具，提交前仍需检查文件内容。

## 来源与授权

本阶段使用原创说明和链接进行设计研究，没有复制上游技能、脚本或素材。上游声明的许可证记录在候选表，正式引入时需针对具体提交核对许可证、素材权利及署名。此仓库自身的公开发布许可尚未选定，不应假定仓库已按 MIT 或其他许可证授权。
