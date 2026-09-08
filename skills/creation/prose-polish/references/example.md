# 合成示例：保留限定与受保护片段

用户：只润色第一段，返回完整 Markdown。命令和链接目标原样保留。

```markdown
我们在12人的内部试用里看到，这个提醒可能让等待时间略微下降，但还不能说明对所有人有效。

运行 `demo --mode cautious`。详见 [说明](https://example.test/guide?mode=cautious)。
```

助手：

```markdown
在12人的内部试用中，我们观察到这个提醒可能略微缩短等待时间，但这还不足以说明它对所有人都有效。

运行 `demo --mode cautious`。详见 [说明](https://example.test/guide?mode=cautious)。
```

改写没有扩大样本、效果或适用范围，命令和链接目标也保持不变。
