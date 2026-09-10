import asyncio


class AsyncMemo:
    def __init__(self):
        self._tasks = {}

    async def get(self, key, loader):
        if key not in self._tasks:
            self._tasks[key] = asyncio.create_task(loader())
        return await self._tasks[key]

    def invalidate(self, key):
        self._tasks.pop(key, None)
