import asyncio
import unittest
from memo import AsyncMemo


class PublicMemoTests(unittest.IsolatedAsyncioTestCase):
    async def test_success_is_cached(self):
        cache = AsyncMemo()
        calls = 0
        async def loader():
            nonlocal calls
            calls += 1
            return 42
        self.assertEqual(await cache.get("x", loader), 42)
        self.assertEqual(await cache.get("x", loader), 42)
        self.assertEqual(calls, 1)

    async def test_cancel_one_waiter_keeps_other_waiter(self):
        cache = AsyncMemo()
        started, release = asyncio.Event(), asyncio.Event()
        async def loader():
            started.set()
            await release.wait()
            return 42
        first = asyncio.create_task(cache.get("x", loader))
        await started.wait()
        second = asyncio.create_task(cache.get("x", loader))
        await asyncio.sleep(0)
        first.cancel()
        await asyncio.gather(first, return_exceptions=True)
        release.set()
        result = await asyncio.gather(second, return_exceptions=True)
        self.assertEqual(result, [42])

    async def test_failure_allows_later_retry(self):
        cache = AsyncMemo()
        calls = 0
        async def loader():
            nonlocal calls
            calls += 1
            if calls == 1:
                raise ValueError("transient")
            return 9
        with self.assertRaises(ValueError):
            await cache.get("x", loader)
        self.assertEqual(await cache.get("x", loader), 9)
