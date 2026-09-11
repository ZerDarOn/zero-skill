# 第十一轮质量打磨：React 浏览器运行验收

日期：2026-09-11。

## 结论

本轮没有修改 `react-performance-review` 的指令，也没有升版。当前 0.1.3 技能包 SHA-256 仍为 `66411b82b4075b8ad839cb75fce155ead7beff2170816591a6dab642116e05c6`。

新增了一个 React 19.2、Vite 和 Playwright 的合成运行夹具，把第十轮模型回答中的三个关键边界落到真实浏览器行为：

- 迟到的旧请求不能覆盖最新结果；
- 虚拟窗口跨界后，键盘焦点必须转移到新挂载的目标，并保留完整集合位置语义；
- 筛选值在渲染阶段派生时，结果和必要的 analytics 外部同步保持正确，同时由 React Profiler 记录实际提交。

本地 Edge 验收最终为 3 个场景各重复 3 次，`9/9` 通过；远端 Ubuntu Playwright Chromium job 也通过了类型检查与 `3/3` 浏览器验收。collection 结构检查和原有 Python 回归同样通过。技能仍为 `experimental`，catalog 的 `evidence` 仍为 `null`，因为这份夹具只验证实现边界，不能证明模型总会给出正确建议，也没有完成隐式路由和真实读屏验收。

## 夹具与冻结边界

运行夹具位于 `evaluations/runtime/react-performance-review/`，依赖由 `package-lock.json` 固定。公开材料全部是合成数据，没有真实项目代码、聊天或账户信息。

三个 Playwright 用例在实现前建立。修正浏览器环境后，未实现页面在三个用例上均因缺少目标控件而失败；实现后才转绿。第一次运行默认 Chromium 时因本机浏览器版本不匹配而失败，那是基础设施失败，不计作行为红灯。

| 场景 | 浏览器断言 |
| --- | --- |
| 迟到响应 | 先启动 old 和 new，先完成 new、后完成 old，最终仍显示 new |
| 虚拟焦点 | Item 5 按 ArrowDown 后 Item 6 被挂载并取得真实 DOM 焦点，同时带有 `aria-posinset=6`、`aria-setsize=100` |
| Profiler 与派生值 | 输入 alp 后结果顺序为 Alpha、Alpine，Beta 消失，Profiler 提交数递增，analytics 同步数从 1 变为 2 |

Profiler 的 `actualDuration` 只证明回调真实执行，不设性能阈值，也不据此宣称优化收益。

## 运行证据

本地环境：

- Windows，Microsoft Edge `152.0.4191.66`
- Node.js `24.19.0`
- React / React DOM `19.2.0`
- Playwright `1.63.0`

最终检查：

- `npm run typecheck`：通过；
- `npm test -- --repeat-each=3 --workers=3`：`9/9` 通过；
- `python scripts/validate_collection.py`：通过；
- `python -m unittest discover -s tests -v`：54 通过，1 个既有 Windows 符号链接权限用例跳过；`15e5c7c` 的 Ubuntu 首跑随后暴露了工程夹具树指纹的平台排序问题，该问题由独立回归测试覆盖并修正。
- [GitHub Actions React runtime job](https://github.com/ZerDarOn/zero-skill/actions/runs/34558034912/job/103134805400)：Ubuntu Playwright Chromium 类型检查与 `3/3` 浏览器验收通过。

机器可读记录见 `evaluations/reports/react-performance-runtime-round-11-diagnostic.json`。

## 压力复跑中的一次失败

第一次六工作进程、每题重复三次的压力运行得到 `8/9`：一个焦点用例没有找到整个列表；当时还没有显式页面就绪断言。后续同环境运行：

- 焦点用例单工作进程重复 10 次：`10/10`；
- 焦点用例六工作进程重复 10 次：`10/10`；
- 全套六工作进程重复 10 次：`30/30`；
- 加入首页响应和主标题就绪断言后，以三工作进程完成最终 `9/9`。

现有证据没有稳定复现该失败，不能确认应用逻辑或并行资源是根因。因此没有用本地 retry 隐藏它，也不写成“已修复”。新增的页面就绪断言会让再次发生时先区分服务响应、应用挂载和场景断言。

## 持续检查

`.github/workflows/validate.yml` 的独立 `react-runtime` job 已在 Ubuntu 上安装锁定依赖和 Playwright Chromium，并通过类型检查与三项浏览器验收。对应运行是 [GitHub Actions run 34558034912](https://github.com/ZerDarOn/zero-skill/actions/runs/34558034912)，React job 成功。该次工作流整体为失败，是同一提交中另一项 Ubuntu Python 测试暴露了工程夹具树指纹按宿主 `Path` 语义排序的问题；这不改变 React job 的通过结论。

## 尚未覆盖

本轮没有验证：

- 自然提示是否隐式路由到该 Skill；
- 六个模型评测题的所有建议能否生成正确补丁；
- 真实业务应用、生产数据或性能收益；
- NVDA、JAWS、VoiceOver 等真实读屏器；
- Firefox、WebKit、移动设备和 React 19.3；

这些边界决定了当前状态继续保持 `experimental`。
