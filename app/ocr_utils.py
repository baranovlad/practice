"""Utility helpers for OCR‑processing PDF files.

Designed for a tiny CPU‑only server; keeps dependencies minimal:
* **EasyOCR** — text detection/recognition on raster pages.
* **PyPDF2**  — cheap check whether a PDF already contains selectable text.
* **pdf2image** — Poppler‑based rasterisation (needs `poppler-utils` on host).

The public interface is just two functions:

```
>>> from app import ocr_utils as ocr
>>> txt_path, json_path = ocr.run_ocr(Path("/path/to/file.pdf"), Path("results/123"))
```

— If the PDF is *textual* (copy‑paste works), we skip OCR and extract text via
  PyPDF2.
— Otherwise the file is rasterised page‑by‑page and passed to EasyOCR.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Dict, List, Tuple

import easyocr
from pdf2image import convert_from_path
from PyPDF2 import PdfReader
from PyPDF2.errors import PdfReadError


__all__ = [
    "is_pdf_textual",
    "extract_text_pdf",
    "convert_pdf_to_images",
    "ocr_images",
    "save_results",
    "run_ocr",
]

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────
# Global OCR reader (lazy‑loaded) — avoids model reload per page
# ──────────────────────────────────────────────────────────────
_GPU_ENV = os.getenv("EASYOCR_GPU", "0")
USE_GPU = _GPU_ENV in {"1", "true", "yes"}

logger.info("Initialising EasyOCR (GPU=%s)", USE_GPU)
reader = easyocr.Reader(["ru", "en"], gpu=USE_GPU)

# ──────────────────────────────────────────────────────────────
# Step 1: quick heuristic — is PDF already textual?
# ──────────────────────────────────────────────────────────────

def is_pdf_textual(pdf_path: Path, *, min_chars: int = 20) -> bool:
    """Return *True* if the first page appears to contain textual content.

    We attempt to read the first page and count how many non‑whitespace
    characters it has.  If the PDF is protected or malformed, we assume it is
    *not* textual to fall back to OCR.
    """
    try:
        reader_pdf = PdfReader(str(pdf_path))
        first_page = reader_pdf.pages[0]
        text = first_page.extract_text() or ""
        textual = len(text.strip()) >= min_chars
        logger.debug("Textual‑check: %s — %s chars found", pdf_path.name, len(text))
        return textual
    except (PdfReadError, IndexError, FileNotFoundError) as exc:
        logger.warning("Failed textual check for %s: %s — falling back to OCR", pdf_path.name, exc)
        return False


def extract_text_pdf(pdf_path: Path) -> str:
    """Extract *all* text with PyPDF2 (fast, no OCR)."""
    reader_pdf = PdfReader(str(pdf_path))
    all_pages = []
    for page in reader_pdf.pages:
        all_pages.append(page.extract_text() or "")
    return "\n\n".join(all_pages)

# ──────────────────────────────────────────────────────────────
# Step 2: rasterise pages → images
# ──────────────────────────────────────────────────────────────

def convert_pdf_to_images(pdf_path: Path, *, dpi: int = 300) -> List[Any]:  # Any = PIL.Image
    """Rasterise each PDF page to a PIL Image (RGB).

    The Poppler binary location can be overridden via `POPPLER_PATH` env var.
    """
    poppler_path = os.getenv("POPPLER_PATH")
    logger.debug("Rasterising %s (dpi=%s, poppler=%s)", pdf_path.name, dpi, poppler_path)
    images = convert_from_path(
        str(pdf_path), dpi=dpi, fmt="jpeg", poppler_path=poppler_path, thread_count=2
    )
    return images

# ──────────────────────────────────────────────────────────────
# Step 3: OCR on images
# ──────────────────────────────────────────────────────────────

def ocr_images(images: List[Any]) -> Tuple[str, List[List[Dict[str, Any]]]]:
    """Run EasyOCR on each image.

    Returns `(plain_text, per_page_json)` where `per_page_json` is suitable for
    dumping to *.json* to inspect bounding boxes.
    """
    page_texts: List[str] = []
    per_page_results: List[List[Dict[str, Any]]] = []

    for idx, img in enumerate(images, 1):
        logger.debug("OCR page %d/%d", idx, len(images))
        result = reader.readtext(img, detail=1)  # list[ [bbox, text, confidence], ... ]

        # Collect plain text in original reading order
        page_txt = "\n".join(r[1] for r in result)
        page_texts.append(page_txt)

        # Prepare JSON‑serialisable structure
        page_json = [
            {
                "bbox": r[0],
                "text": r[1],
                "confidence": float(r[2]),
            }
            for r in result
        ]
        per_page_results.append(page_json)

    return "\n\n".join(page_texts), per_page_results

# ──────────────────────────────────────────────────────────────
# Step 4: save
# ──────────────────────────────────────────────────────────────

def save_results(
    plain_text: str,
    page_json: List[List[Dict[str, Any]]],
    out_dir: Path,
) -> Tuple[Path, Path]:
    """Write *result.txt* and *result.json* into *out_dir*; return their paths."""
    out_dir.mkdir(parents=True, exist_ok=True)

    txt_path = out_dir / "result.txt"
    json_path = out_dir / "result.json"

    txt_path.write_text(plain_text, encoding="utf-8")
    json_path.write_text(json.dumps(page_json, ensure_ascii=False, indent=2), encoding="utf-8")

    logger.info("Saved %s and %s", txt_path, json_path)
    return txt_path, json_path

# ──────────────────────────────────────────────────────────────
# High‑level helper used by FastAPI background task
# ──────────────────────────────────────────────────────────────

def run_ocr(pdf_path: Path, out_dir: Path) -> Tuple[Path, Path]:
    """Full pipeline: decide, OCR if нужно, сохранить файлы, вернуть пути."""

    if is_pdf_textual(pdf_path):
        logger.info("%s detected as textual — extracting text via PyPDF2", pdf_path.name)
        text = extract_text_pdf(pdf_path)
        return save_results(text, [], out_dir)

    # else → rasterise + OCR
    images = convert_pdf_to_images(pdf_path)
    text, per_page = ocr_images(images)
    return save_results(text, per_page, out_dir)
