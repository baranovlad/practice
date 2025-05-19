from __future__ import annotations

"""FastAPI entry‑point for the OCR‑PDF demo (model switch‑ready)."""

import shutil
import uuid
from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import (
    BackgroundTasks,
    FastAPI,
    HTTPException,
    Request,
    UploadFile,
    File,
    Form,
)
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .ocr_utils import run_ocr

# ------------------------------------------------------------------
# Paths
# ------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = ROOT / "templates"
STATIC_DIR = ROOT / "static"
RESULTS_DIR = ROOT / "results"
RESULTS_DIR.mkdir(exist_ok=True)

# ------------------------------------------------------------------
# App
# ------------------------------------------------------------------
app = FastAPI(title="OCR‑PDF Demo", version="0.3.0")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _save_upload(upload: UploadFile) -> Path:
    suffix = Path(upload.filename or "upload.pdf").suffix or ".pdf"
    tmp = NamedTemporaryFile(delete=False, suffix=suffix)
    with tmp:
        shutil.copyfileobj(upload.file, tmp)
    return Path(tmp.name)


class Results:
    """Wraps result file paths for a given task ID."""

    def __init__(self, task_id: str):
        self.folder = RESULTS_DIR / task_id
        self.txt = self.folder / "result.txt"
        self.json = self.folder / "result.json"


async def _process_pdf(src: Path, task_id: str, model_name: str) -> None:
    try:
        run_ocr(src, RESULTS_DIR / task_id, model_name=model_name)
    finally:
        src.unlink(missing_ok=True)

# ------------------------------------------------------------------
# Routes
# ------------------------------------------------------------------


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/upload")
async def upload_pdf(
    request: Request,  # keeps client IP etc. for logs if needed
    bg: BackgroundTasks,
    file: UploadFile = File(...),
    model: str = Form("EasyOCR"),
):
    """Receive PDF and chosen model, spawn background OCR job."""
    if file.content_type not in {"application/pdf", "application/x-pdf"}:
        raise HTTPException(415, "Only PDF files are accepted")

    task_id = uuid.uuid4().hex
    tmp_pdf = _save_upload(file)

    Results(task_id).folder.mkdir(parents=True, exist_ok=True)  # flag as processing
    bg.add_task(_process_pdf, tmp_pdf, task_id, model)

    return RedirectResponse(url=f"/result/{task_id}", status_code=303)


@app.get("/result/{task_id}", response_class=HTMLResponse)
async def result_page(request: Request, task_id: str):
    res = Results(task_id)

    if res.txt.exists() and res.json.exists():
        return templates.TemplateResponse(
            "result.html",
            {
                "request": request,
                "processing": False,
                "task_id": task_id,
                "txt_url": app.url_path_for("download_file", task_id=task_id, filename="result.txt"),
                "json_url": app.url_path_for("download_file", task_id=task_id, filename="result.json"),
            },
        )

    if res.folder.exists():
        return templates.TemplateResponse(
            "result.html", {"request": request, "processing": True}, status_code=202
        )

    return templates.TemplateResponse(
        "result.html",
        {"request": request, "processing": False, "error": "Task not found"},
        status_code=404,
    )


@app.get("/download/{task_id}/{filename}")
async def download_file(task_id: str, filename: str):
    res = Results(task_id)
    target = {"result.txt": res.txt, "result.json": res.json}.get(filename)

    if not (target and target.exists()):
        raise HTTPException(404, "File not found")

    return FileResponse(target, filename=filename, media_type="application/octet-stream")


@app.post("/api/ocr")
async def api_ocr(
    file: UploadFile = File(...),
    model: str = Form("EasyOCR"),
):
    """
    Возвращает распознанный текст без сохранения файлов на диск клиента.
    """
    if file.content_type not in {"application/pdf", "application/x-pdf"}:
        raise HTTPException(415, "Only PDF files are accepted")

    # сохраняем во временный файл
    tmp = _save_upload(file)
    try:
        out_dir = RESULTS_DIR / "tmp"
        run_ocr(tmp, out_dir, model_name=model)
        text = (out_dir / "result.txt").read_text("utf-8")
    finally:
        # чистим всё лишнее
        tmp.unlink(missing_ok=True)
        (out_dir / "result.txt").unlink(missing_ok=True)
        (out_dir / "result.json").unlink(missing_ok=True)
        out_dir.rmdir()

    return {"text": text}

# ------------------------------------------------------------------
# Dev helper
# ------------------------------------------------------------------
if __name__ == "__main__":  # pragma: no cover
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
