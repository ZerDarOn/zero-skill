class DocumentController:
    def __init__(self):
        self.project = None
        self.text = ""
        self.loading = False
        self.error = None
        self._request = None
        self._edit_version = 0

    async def open(self, project, loader):
        request = object()
        self._request = request
        edit_version = self._edit_version
        self.project = project
        self.text = ""
        self.loading = True
        self.error = None
        try:
            text = await loader(project)
            if self._request is request and self._edit_version == edit_version:
                self.text = text
        except Exception as exc:
            if self._request is request:
                self.error = str(exc)
        finally:
            if self._request is request:
                self.loading = False

    def edit(self, text):
        self._edit_version += 1
        self.text = text

    def close(self):
        self._request = None
        self.project = None
        self.text = ""
        self.loading = False
        self.error = None
