import asyncio
import unittest
from document import DocumentController


class PublicDocumentTests(unittest.IsolatedAsyncioTestCase):
    async def test_normal_open(self):
        state = DocumentController()
        async def loader(project):
            return project + " text"
        await state.open("A", loader)
        self.assertEqual((state.project, state.text, state.loading, state.error), ("A", "A text", False, None))

    async def test_slow_previous_project_cannot_overwrite_new_project(self):
        state = DocumentController()
        started, release = asyncio.Event(), asyncio.Event()
        async def loader(project):
            if project == "A":
                started.set()
                await release.wait()
            return project + " text"
        old = asyncio.create_task(state.open("A", loader))
        await started.wait()
        await state.open("B", loader)
        release.set()
        await old
        self.assertEqual((state.project, state.text), ("B", "B text"))

    async def test_user_edit_during_load_is_kept(self):
        state = DocumentController()
        started, release = asyncio.Event(), asyncio.Event()
        async def loader(project):
            started.set()
            await release.wait()
            return "disk text"
        task = asyncio.create_task(state.open("A", loader))
        await started.wait()
        state.edit("typed text")
        release.set()
        await task
        self.assertEqual(state.text, "typed text")
        self.assertFalse(state.loading)
