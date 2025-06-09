class HTTPException(Exception):
    def __init__(self, status_code: int, detail: str | None = None):
        self.status_code = status_code
        self.detail = detail

class UploadFile:
    def __init__(self, file, filename: str | None = None, content_type: str | None = None):
        self.file = file
        self.filename = filename
        self.content_type = content_type

class BackgroundTasks:
    def __init__(self):
        self.tasks = []
    def add_task(self, func, *args, **kwargs):
        self.tasks.append((func, args, kwargs))
    def run(self):
        for func, args, kwargs in self.tasks:
            func(*args, **kwargs)


def File(default=None):
    return default

def Form(default=None):
    return default

class FastAPI:
    def __init__(self, *_, **__):
        self.routes = {}
    def mount(self, *_, **__):
        pass
    def get(self, path, **__):
        def decorator(func):
            self.routes[("GET", path)] = func
            return func
        return decorator
    def post(self, path, **__):
        def decorator(func):
            self.routes[("POST", path)] = func
            return func
        return decorator

def Request():
    pass

from .testclient import TestClient
from .responses import RedirectResponse, FileResponse, HTMLResponse
from .staticfiles import StaticFiles
from .templating import Jinja2Templates

