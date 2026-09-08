# 新增或改进技能

1. 写出真实需求和一个不该触发的相近需求。先查登记表，避免同义技能重复建设。
2. 选择一个主分类和能力类型；用标签表达次要场景。
3. 将 `templates/SKILL.md.tmpl` 复制为 `skills/<category>/<id>/SKILL.md`，替换全部占位符。只有实际用到时才增加 `references/`、`scripts/`、`assets/`。
4. 按 `templates/skill-record.json` 在 `catalog/collection.json` 的 `skills` 数组登记。初始状态用 `draft`，版本从 `0.1.0` 开始；评测尚无时用 `null`。
5. 需要第三方内容时，先补上游条目并执行[来源审查](docs/skill-standard.md)。仅借鉴思想也用 `upstream_ids` 留下线索。
6. 用 `templates/evaluation-case.json` 建立对应合成用例文件。每个用例只测一个关键行为；加入误触发、信息不足或矛盾材料的情况。
7. 运行结构检查和校验器测试；完成人工阅读后可标记 `experimental`。
8. 按[评测规范](evaluations/README.md)运行有／无 skill 对照，保存脱敏报告，再考虑 `verified`。

模板不会自动发现或加载。尚未验证的上游项目保持在候选登记中，不伪装为本地可用技能。

## 修改和回退

指令、输入输出或触发范围发生变化时更新登记版本，状态退回 `experimental` 并重新评测。破坏性变化提升主版本；添加兼容能力提升次版本；措辞修正提升补丁版本。提交应让技能文件、登记表和配套用例一起接受审查。

本仓库没有自动安装器。以后增加安装功能时，需指定目标目录、检查重名、记录版本并提供回退；不得默认覆盖全局技能。
