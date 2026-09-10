import asyncio
import unittest
from memo import AsyncMemo


class AcceptanceMemoTests(unittest.IsolatedAsyncioTestCase):
    async def test_invalidated_old_failure_cannot_remove_replacement(self):
        cache = AsyncMemo()
        old_started, old_release, new_started, new_release = [asyncio.Event() for _ in range(4)]
        new_calls = 0
        async def old_loader():
            old_started.set()
            await old_release.wait()
            raise ValueError("old")
        async def new_loader():
            nonlocal new_calls
            new_calls += 1
            new_started.set()
            await new_release.wait()
            return "new"
        old = asyncio.create_task(cache.get("x", old_loader))
        await old_started.wait()
        cache.invalidate("x")
        new = asyncio.create_task(cache.get("x", new_loader))
        await new_started.wait()
        old_release.set()
        with self.assertRaises(ValueError):
            await old
        another = asyncio.create_task(cache.get("x", new_loader))
        await asyncio.sleep(0)
        new_release.set()
        self.assertEqual(await asyncio.gather(new, another), ["new", "new"])
        self.assertEqual(new_calls, 1)

    async def test_underlying_cancellation_is_retryable(self):
        cache = AsyncMemo()
        calls = 0
        async def loader():
            nonlocal calls
            calls += 1
            if calls == 1:
                raise asyncio.CancelledError()
            return 7
        with self.assertRaises(asyncio.CancelledError):
            await cache.get("x", loader)
        self.assertEqual(await cache.get("x", loader), 7)

    async def test_last_waiter_cancellation_does_not_cancel_work(self):
        cache = AsyncMemo()
        started, release = asyncio.Event(), asyncio.Event()
        calls = 0
        async def loader():
            nonlocal calls
            calls += 1
            started.set()
            await release.wait()
            return "kept"
        waiter = asyncio.create_task(cache.get("x", loader))
        await started.wait()
        waiter.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await waiter
        release.set()
        self.assertEqual(await cache.get("x", loader), "kept")
        self.assertEqual(calls, 1)

    async def test_success_cache_and_different_keys(self):
        cache = AsyncMemo()
        calls = []
        async def left():
            calls.append("left")
            return 0
        async def right():
            calls.append("right")
            return None
        self.assertEqual(await cache.get("left", left), 0)
        self.assertIsNone(await cache.get("right", right))
        self.assertEqual(await cache.get("left", left), 0)
        self.assertIsNone(await cache.get("right", right))
        self.assertEqual(calls, ["left", "right"])

    async def test_old_success_after_invalidate_does_not_replace_new_success(self):
        cache = AsyncMemo()
        started, release = asyncio.Event(), asyncio.Event()
        async def old_loader():
            started.set()
            await release.wait()
            return "old"
        async def new_loader():
            return "new"
        old = asyncio.create_task(cache.get("x", old_loader))
        await started.wait()
        cache.invalidate("x")
        self.assertEqual(await cache.get("x", new_loader), "new")
        release.set()
        self.assertEqual(await old, "old")
        self.assertEqual(await cache.get("x", new_loader), "new")
