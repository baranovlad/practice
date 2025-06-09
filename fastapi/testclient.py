"""Minimal TestClient for offline tests."""

from .responses import RedirectResponse
import asyncio

__all__ = ["TestClient", "Response"]
__test__ = False

class Response:
    def __init__(self, status_code=200, headers=None, json_data=None):
        self.status_code = status_code
        self.headers = headers or {}
        self._json = json_data
    def json(self):
        return self._json

class TestClient:
    __test__ = False
    def __init__(self, app):
        self.app = app

    def _run(self, result):
        if asyncio.iscoroutine(result):
            result = asyncio.run(result)
        if isinstance(result, Response):
            return result
        if isinstance(result, RedirectResponse):
            return Response(status_code=result.status_code, headers=result.headers)
        return Response(status_code=200, json_data=result)

    def post(self, path, data=None, files=None, allow_redirects=True):
        func = self.app.routes.get(("POST", path))
        if not func:
            raise ValueError("Route not found")
        if files:
            name, file_obj, ctype = next(iter(files.values()))
            class UploadFile:
                def __init__(self, filename, file, content_type):
                    self.filename = filename
                    self.file = file
                    self.content_type = content_type
                async def read(self):
                    return self.file.read()
            upload = UploadFile(name, file_obj, ctype)
        else:
            upload = None
        class BG:
            def add_task(self, fn, *a, **k):
                res = fn(*a, **k)
                if asyncio.iscoroutine(res):
                    asyncio.get_event_loop().create_task(res)
        bg = BG()
        if path == "/upload":
            result = func(request=None, bg=bg, file=upload, model=data.get("model") if data else None)
        else:
            result = func(file=upload, model=data.get("model") if data else None)
        return self._run(result)

    def get(self, path):
        func = self.app.routes.get(("GET", path))
        if not func:
            raise ValueError("Route not found")
        return self._run(func(request=None))

