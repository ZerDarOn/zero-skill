import asyncio
import unittest
from document import DocumentController


class AcceptanceDocumentTests(unittest.IsolatedAsyncioTestCase):
    async def test_same_project_aba_needs_request_identity(self):
        state = DocumentController()
        started, release = asyncio.Event(), asyncio.Event()
        async def slow(project):
            started.set()
            await release.wait()
            return "old A"
        async def quick(project):
            return "fresh " + project
        old = asyncio.create_task(state.open("A", slow))
        await started.wait()
        await state.open("B", quick)
        await state.open("A", quick)
        release.set()
        await old
        self.assertEqual((state.project, state.text), ("A", "fresh A"))

    async def test_stale_failure_cannot_clear_current_loading_or_set_error(self):
        state = DocumentController()
        old_started, old_release, new_started, new_release = [asyncio.Event() for _ in range(4)]
        async def old_loader(project):
            old_started.set()
            await old_release.wait()
            raise ValueError("stale")
        async def new_loader(project):
            new_started.set()
            await new_release.wait()
            return "new"
        old = asyncio.create_task(state.open("A", old_loader))
        await old_started.wait()
        new = asyncio.create_task(state.open("B", new_loader))
        await new_started.wait()
        old_release.set()
        await old
        observed = (state.loading, state.error)
        new_release.set()
        await new
        self.assertEqual(observed, (True, None))

    async def test_close_prevents_late_result(self):
        state = DocumentController()
        started, release = asyncio.Event(), asyncio.Event()
        async def loader(project):
            started.set()
            await release.wait()
            return "late"
        old = asyncio.create_task(state.open("A", loader))
        await started.wait()
        state.close()
        release.set()
        await old
        self.assertEqual((state.project, state.text, state.loading, state.error), (None, "", False, None))

    async def test_current_error_keeps_edit_and_finishes_loading(self):
        state = DocumentController()
        started, release = asyncio.Event(), asyncio.Event()
        async def loader(project):
            started.set()
            await release.wait()
            raise ValueError("offline")
        task = asyncio.create_task(state.open("A", loader))
        await started.wait()
        state.edit("mine")
        release.set()
        await task
        self.assertEqual((state.text, state.loading, state.error), ("mine", False, "offline"))

    async def test_cancelling_stale_request_keeps_current_loading(self):
        state = DocumentController()
        old_started, old_release, new_started, new_release = [asyncio.Event() for _ in range(4)]
        async def old_loader(project):
            old_started.set()
            await old_release.wait()
        async def new_loader(project):
            new_started.set()
            await new_release.wait()
            return "B"
        old = asyncio.create_task(state.open("A", old_loader))
        await old_started.wait()
        new = asyncio.create_task(state.open("B", new_loader))
        await new_started.wait()
        old.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await old
        observed = state.loading
        new_release.set()
        await new
        self.assertTrue(observed)

    async def test_current_cancellation_ends_loading_and_propagates(self):
        state = DocumentController()
        started = asyncio.Event()
        async def loader(project):
            started.set()
            await asyncio.Event().wait()
        task = asyncio.create_task(state.open("A", loader))
        await started.wait()
        state.edit("mine")
        task.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await task
        self.assertEqual((state.project, state.text, state.loading, state.error), ("A", "mine", False, None))
