import sys
import types
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

for name in ["numpy", "easyocr", "fitz", "PIL", "PyPDF2", "PyPDF2.errors"]:
    sys.modules.setdefault(name, types.ModuleType(name))
sys.modules["easyocr"].Reader = type("Reader", (), {"__init__": lambda *a, **k: None, "readtext": lambda *a, **k: []})
sys.modules["PIL"].Image = type("Image", (), {})
sys.modules["PyPDF2"].PdfReader = lambda *a, **k: None
sys.modules["PyPDF2.errors"].PdfReadError = Exception

from fastapi.testclient import TestClient

from app.main import app


PDF_PATH = Path("pdf/BERT.pdf")


def _setup_dummy_ocr(monkeypatch):
    def dummy_run_ocr(pdf_path, out_dir, *, model_name="easyocr_cpu"):
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "result.txt").write_text("dummy text", encoding="utf-8")
        (out_dir / "result.json").write_text("[]", encoding="utf-8")

    monkeypatch.setattr("app.main.run_ocr", dummy_run_ocr)

    def dummy_process_pdf(src, task_id, model_name):
        dummy_run_ocr(src, Path("results") / task_id, model_name=model_name)

    monkeypatch.setattr("app.main._process_pdf", dummy_process_pdf, raising=False)
    import uuid
    monkeypatch.setattr("app.main.uuid4", uuid.uuid4, raising=False)


def test_upload_endpoint(monkeypatch):
    _setup_dummy_ocr(monkeypatch)
    client = TestClient(app)

    with PDF_PATH.open("rb") as f:
        response = client.post(
            "/upload",
            data={"model": "easyocr_cpu"},
            files={"file": ("test.pdf", f, "application/pdf")},
            allow_redirects=False,
        )

    assert response.status_code == 303
    assert response.headers["location"].startswith("/result/")

    task_id = response.headers["location"].split("/result/")[-1]
    res_dir = Path("results") / task_id
    assert (res_dir / "result.txt").read_text(encoding="utf-8") == "dummy text"


def test_api_ocr_endpoint(monkeypatch):
    _setup_dummy_ocr(monkeypatch)
    client = TestClient(app)

    with PDF_PATH.open("rb") as f:
        response = client.post(
            "/api/ocr",
            data={"model": "easyocr_cpu"},
            files={"file": ("test.pdf", f, "application/pdf")},
        )

    assert response.status_code == 200
    assert response.json() == {"text": "dummy text"}
