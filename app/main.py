"""FastAPI entry‑point for the OCR‑PDF demo.

Highlights
──────────
* Minimal background‑task workflow (no Celery):
  uploads go to a temp file → background coroutine `process_pdf()`
  runs OCR and writes results into `results/<task_id>/`.
* Jinja2 templates served from *templates/*, static files from *static/*.
* Endpoints
    GET  /               — форма загрузки
    POST /upload         — принимает PDF, возвращает JSON с `task_id`
    GET  /result/{id}    — HTML‑страница: «обрабатывается» или ссылки на файлы
    GET  /download/{id}/{filename} — отдаёт TXT/JSON
"""

from __future__ import annotations

import shutil
import uuid
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Annotated

from fastapi import (
    BackgroundTasks,
    FastAPI,
    HTTPException,
    Request,
    UploadFile,
)
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from . import ocr_utils

# ──────────────────────────────────────────────────────────────
# Paths & constants
# ──────────────────────────────────────────────────────────────
ROOT_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = ROOT_DIR / "templates"
STATIC_DIR = ROOT_DIR / "static"
RESULTS_DIR = ROOT_DIR / "results"
RESULTS_DIR.mkdir(exist_ok=True)

# ──────────────────────────────────────────────────────────────
# FastAPI app
# ──────────────────────────────────────────────────────────────
app = FastAPI(title="OCR‑PDF Demo", version="0.1.0")

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# ──────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────

def _save_upload_temp(upload: UploadFile) -> Path:
    """Write an `UploadFile` to a NamedTemporaryFile on disk and return path."""
    suffix = Path(upload.filename or "upload.pdf").suffix or ".pdf"
    tmp = NamedTemporaryFile(delete=False, suffix=suffix)
    with tmp:  # keep file handle open for writting
        shutil.copyfileobj(upload.file, tmp)
    return Path(tmp.name)


def _result_paths(task_id: str) -> dict[str, Path]:
    folder = RESULTS_DIR / task_id
    return {
        "folder": folder,
        "txt": folder / "result.txt",
        "json": folder / "result.json",
    }


async def process_pdf(temp_pdf: Path, task_id: str) -> None:
    """Background coroutine: run OCR and store output under `results/<id>/`."""
    out_dir = RESULTS_DIR / task_id
    try:
        ocr_utils.run_ocr(temp_pdf, out_dir)
    finally:
        # clean the uploaded tmp‑file whatever happens
        temp_pdf.unlink(missing_ok=True)

# ──────────────────────────────────────────────────────────────
# Routes
# ──────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Render upload form."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/upload")
async def upload_pdf(
    request: Request,
    file: Annotated[UploadFile, "PDF file to process"],
    bg: BackgroundTasks,
):
    if file.content_type not in {"application/pdf", "application/x-pdf"}:
        raise HTTPException(415, "File must be PDF")

    task_id = uuid.uuid4().hex
    temp_pdf = _save_upload_temp(file)
    bg.add_task(process_pdf, temp_pdf, task_id)

    # Front‑end будет опрашивать /result/{task_id}
    return JSONResponse({"task_id": task_id})


@app.get("/result/{task_id}", response_class=HTMLResponse)
async def result_page(request: Request, task_id: str):
    paths = _result_paths(task_id)

    if paths["txt"].exists() and paths["json"].exists():
        context = {
            "request": request,
            "processing": False,
            "error": None,
            "txt_filename": f"download/{task_id}/result.txt",
            "json_filename": f"download/{task_id}/result.json",
        }
        return templates.TemplateResponse("result.html", context)

    folder_exists = paths["folder"].exists()

    if folder_exists:
        # Файл ещё обрабатывается
        context = {"request": request, "processing": True, "error": None}
        return templates.TemplateResponse("result.html", context, status_code=202)

    # неизвестный task_id
    context = {"request": request, "processing": False, "error": "Задача не найдена"}
    return templates.TemplateResponse("result.html", context, status_code=404)


@app.get("/download/{task_id}/{filename}")
async def download_file(task_id: str, filename: str):
    paths = _result_paths(task_id)
    file_map = {"result.txt": paths["txt"], "result.json": paths["json"]}
    target = file_map.get(filename)

    if not target or not target.exists():
        raise HTTPException(404, "File not found")

    return FileResponse(target, media_type="application/octet-stream", filename=filename)


# ──────────────────────────────────────────────────────────────
# Dev helper (optional)
# ──────────────────────────────────────────────────────────────
if __name__ == "__main__":  # pragma: no cover
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
