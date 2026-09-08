# 本地技能导出验证

日期：2026-09-08。起始提交：`45ce7b5e38ab39398278f5e18f7699d94851cd46`。

## 实现与命令

`scripts/export_skills.py` 只使用 Python 标准库，从 `catalog/collection.json` 读取 ID、版本、状态和路径，不硬编码技能清单。

```sh
python scripts/export_skills.py --list
python scripts/export_skills.py --skill conversation-rehearsal
python scripts/export_skills.py --all
```

输出固定在被忽略的 `dist/`。导出前批量检查所有选择、路径与同名碰撞；已有 ZIP 不覆盖。技能目录中的脚本只作为普通文件读取，不导入、不执行。归档通过同文件系统临时文件构建，再以不覆盖的硬链接发布。

复核后补强三项边界：在解析前逐级拒绝源路径与输出路径中的 junction／reparse point；每个包只读取一次形成冻结字节快照，manifest、包指纹与 ZIP 共用该快照；批量运行期失败携带并由 CLI 输出已经成功的文件，再以失败状态退出。

## 实际产物

| ZIP | 字节 | 源包指纹 | ZIP SHA-256 |
| --- | ---: | --- | --- |
| `conversation-rehearsal-0.1.0.zip` | 2806 | `7845404ab95596792479d0586b0376ef40100510a5281888f7b59052cb0cae22` | `1f185d87b955db9a8aa89cf9a1ed089dab45c6d55276c6f6a9b31c8a7211b337` |
| `person-evidence-analysis-0.1.0.zip` | 3630 | `8bc1ee388800742488c8ba19af5312fcfb489173b75374cc1c098e3932071ad8` | `472e298e6899a28fb731a353dcf9192fc2a5a2cde37a86ce6c95f69a3c80a9ec` |
| `public-person-perspective-0.1.2.zip` | 3530 | `14e7a02453a4b462c745d970c7510be9e6c46729ae0fd68a1e42825f4c72d3d8` | `fbbcf01efcdd96d02169f248b9801702529ecd32fe5bb059e40e61b648a4f50c` |
| `relationship-review-0.1.1.zip` | 3997 | `63f896e2da16d50ea870c5dbcf24e3e178494931a4bac4d6f31c4749dd7284b0` | `e5cb95a826473c97941764b94dee2df96aca7333a4c4a54643a8f458fd56fefc` |

每个 ZIP 均逐一打开核对：顶层只有 `bundle-manifest.json` 和 `<skill-id>/`；成员没有绝对路径、盘符或 `..`；manifest 文件清单与 SHA-256 匹配；归档文件与源包逐字节一致；解压到临时目录重新计算的包指纹与源包及 manifest 一致。未执行任何包内脚本。

## 测试

专用导出测试共 10 项：9 项通过，1 项跳过。覆盖未知 ID、`draft`／`archived`、路径穿越、junction／reparse point、源文件竞态、部分成功报告、意外或凭据形态文件、批量碰撞预检、已有输出不变、引用资源完整、外置 manifest、文件哈希和确定性 ZIP 字节。符号链接测试在本机因 Windows 缺少创建符号链接权限而跳过；Windows junction 拒绝测试实际通过。

README 规定的结构检查通过；完整测试共 27 项，26 项通过、1 项因 Windows 当前权限无法创建符号链接而跳过。重复执行真实 `--all` 按预期退出 1，四个既有 ZIP 的字节均未改变。

## 边界

这是本地结构分发验证，不是正式发布、用户安装、自动发现、自动路由、模型行为或跨宿主兼容验证。仓库许可证仍未指定，manifest 记录为 `unspecified`。四个技能包及其 `experimental` 成熟度没有改变；ZIP 位于被忽略的 `dist/`，不纳入提交。
