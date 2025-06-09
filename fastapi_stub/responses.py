class RedirectResponse:
    def __init__(self, url, status_code=307):
        self.status_code = status_code
        self.headers = {"location": url}

class FileResponse:
    def __init__(self, path, filename=None, media_type=None):
        self.status_code = 200
        self.path = path
        self.filename = filename
        self.media_type = media_type

class HTMLResponse:
    def __init__(self, content='', status_code=200):
        self.status_code = status_code
        self.content = content

