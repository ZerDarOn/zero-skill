class DocumentController:
    def __init__(self):
        self.project = None
        self.text = ""
        self.loading = False
        self.error = None

    async def open(self, project, loader):
        self.project = project
        self.text = ""
        self.loading = True
        self.error = None
        try:
            self.text = await loader(project)
        except Exception as exc:
            self.error = str(exc)
        finally:
            self.loading = False

    def edit(self, text):
        self.text = text

    def close(self):
        self.project = None
        self.text = ""
        self.loading = False
        self.error = None
