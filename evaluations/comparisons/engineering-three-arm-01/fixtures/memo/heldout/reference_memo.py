import asyncio


class AsyncMemo:
    def __init__(self):
        self._tasks = {}

    async def get(self, key, loader):
        task = self._tasks.get(key)
        if task is None:
            task = asyncio.create_task(loader())
            self._tasks[key] = task
            def completed(done):
                failed = done.cancelled() or done.exception() is not None
                if failed and self._tasks.get(key) is task:
                    self._tasks.pop(key, None)
            task.add_done_callback(completed)
        return await asyncio.shield(task)

    def invalidate(self, key):
        self._tasks.pop(key, None)
