# 第四轮研究：同事的 Witchcat 技能

查看日期：2026-09-09。入口来自用户提供的 [witchscottishfoldcat](https://github.com/witchscottishfoldcat)。本轮只研究公开仓库，没有访问私人资料或联系作者。

## 找到什么

主要仓库是 [witchcat-skills](https://github.com/witchscottishfoldcat/witchcat-skills/tree/fa3d57ee21c549383e0835ada65098366fd8f458)，固定提交为 `fa3d57ee21c549383e0835ada65098366fd8f458`。GitHub API 查询时为 2 stars；递归目录中有 50 个 `SKILL.md`，包含工程流程和单独引入的工具技能，不代表 50 个全为作者原创。该仓库不是 fork；同账号下的 `skills` 和 `everything-claude-code` 则是 fork，不能将其上游内容或星数算成同事原创项目的成绩。

它偏向工程开发、排障与交付治理，与我们的人物和关系技能不是同一类产品。选择它是因为用户提供了直接参考和方法契合度，不是因为高星。此前高星来源继续见[第三轮研究](research-round-03.md)。

## 具体取舍

以下链接均指向本次查看的固定提交。阅读范围为选定入口，不是整个仓库的全面审计。

| 来源 | 阅读范围 | 本地吸收与限制 |
| --- | --- | --- |
| [task-levels](https://github.com/witchscottishfoldcat/witchcat-skills/blob/fa3d57ee21c549383e0835ada65098366fd8f458/common/task-levels/SKILL.md) | 完整入口 | 按任务大小控制流程；简短请求直接回答，不给本地技能新增强制分级表或路由链 |
| [decision-records](https://github.com/witchscottishfoldcat/witchcat-skills/blob/fa3d57ee21c549383e0835ada65098366fd8f458/common/decision-records/SKILL.md) | 完整入口 | 决策编号、原批准与当时依据保留；新事实可触发复议，但不替用户宣布改选；不强制创建 ADR 文件 |
| [requirements-clarification](https://github.com/witchscottishfoldcat/witchcat-skills/blob/fa3d57ee21c549383e0835ada65098366fd8f458/common/requirements-clarification/SKILL.md) | 完整入口 | 只追问会改变方案的未知条件，尊重直接交稿与等待回复的不同请求，不启动固定问卷 |
| [root-cause-debugging](https://github.com/witchscottishfoldcat/witchcat-skills/blob/fa3d57ee21c549383e0835ada65098366fd8f458/debug/root-cause-debugging/SKILL.md) | 前部及验证、交付段；未完整精读中间所有阶段 | 区分本地源码、构建产物和线上版本；原条件复验。结合本仓库边界，补充隔离环境与合成写入数据；不引入自动部署、生产重放或记忆写入 |
| [engineering-baseline](https://github.com/witchscottishfoldcat/witchcat-skills/blob/fa3d57ee21c549383e0835ada65098366fd8f458/common/engineering-baseline/SKILL.md) | 选读，含完整输出约束段 | 输出服从任务范围；会议一句话改写保留事实和条件，不扩成额外清单 |
| [skill-governance](https://github.com/witchscottishfoldcat/witchcat-skills/blob/fa3d57ee21c549383e0835ada65098366fd8f458/tools/skill-governance/SKILL.md) | 完整入口 | 修改后核对版本、引用与行为证据；继续区分结构检查、显式加载诊断和宿主路由 |

“文字明确阻止发言”与“实际声音重叠”的区分来自对本地会议技能的复核；隔离写入和有界改写也是结合本地失败与任务要求形成的修订，不把所有变化都归功于上游。

## 许可证和材料处理

该提交未发现仓库根级统一许可证，GitHub license 元数据为空。目录内存在 `licenses/taste-skill-MIT.txt`，以及部分工具技能自己的 `LICENSE.txt`；这些局部许可证不能自动覆盖选读的全部工程入口。

本轮没有复制第三方技能正文、脚本或素材，也没有安装或运行上游代码。使用本仓库自己的表述实现方法，来源登记为 `imported: false`。未来若要引入原文件，应先核对该文件适用许可证并保留作者、许可与修改记录。

## 落地

本轮只修改故障证据排查、决策简报起草、会议沟通复盘三个现有技能。版本、真实输出、通过与未通过项见[第二轮质量打磨](quality-polish-round-02.md)。没有将工程流程套入人物分析或扩充新技能数量。

后续同事链接或视频线索仍按“找到具体入口 → 核对版本与许可 → 提取适用方法 → 在本地用例验证”接入。视频中的演示可以帮助发现任务，不直接作为技能有效性证据。
