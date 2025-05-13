from __future__ import annotations

"""Light‑weight OCR utilities (lazy‑loading heavy models).

* EasyOCR initialises instantly and is the default.
* RolmOCR (≈12 GB) загружается ТОЛЬКО при первом запросе **и** без
  `device_map`, чтобы избежать ошибки *offload the whole model to disk*.
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
import easyocr
import fitz
from PIL import Image
from PyPDF2 import PdfReader
from PyPDF2.errors import PdfReadError

__all__ = [
    "run_ocr",
]

logger = logging.getLogger(__name__)
DEFAULT_MODEL = os.getenv("MODEL_NAME", "EasyOCR")

# ------------------------------------------------------------------
# EasyOCR (fast, small)
# ------------------------------------------------------------------
reader_easy = easyocr.Reader(["ru", "en"], gpu=os.getenv("EASYOCR_GPU", "0") in {"1", "true", "yes"})
logger.info("EasyOCR initialised")

# ------------------------------------------------------------------
# RolmOCR — lazy load, no device_map
# ------------------------------------------------------------------
_rolm_model = None
_rolm_processor = None


def _load_rolm():
    global _rolm_model, _rolm_processor  # pylint: disable=global-statement
    if _rolm_model is not None:
        return _rolm_model, _rolm_processor

    import torch  # heavy only if really needed
    from transformers import AutoProcessor, AutoModelForImageTextToText

    logger.info("Loading RolmOCR (CPU mode)")
    _rolm_model = AutoModelForImageTextToText.from_pretrained(
        "reducto/RolmOCR",
        torch_dtype="auto",
        trust_remote_code=True,
        low_cpu_mem_usage=True,
    ).to("cpu")

    _rolm_processor = AutoProcessor.from_pretrained(
        "reducto/RolmOCR", trust_remote_code=True, use_fast=False
    )
    return _rolm_model, _rolm_processor

# ------------------------------------------------------------------
# OCR pipeline helpers
# ------------------------------------------------------------------

def _is_pdf_textual(pdf_path: Path, *, min_chars: int = 20) -> bool:
    try:
        reader = PdfReader(str(pdf_path))
        return len((reader.pages[0].extract_text() or "").strip()) >= min_chars
    except Exception:  # pylint: disable=broad-except
        return False


def _pdf_to_images(pdf_path: Path, dpi: int = 200) -> list[Image.Image]:
    zoom = dpi / 72
    mat = fitz.Matrix(zoom, zoom)
    with fitz.open(str(pdf_path)) as doc:
        return [
            Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            for page in doc
            for pix in [page.get_pixmap(matrix=mat, alpha=False)]
        ]


def _ocr_images(images: list[Any], model_name: str) -> Tuple[str, List[List[Dict[str, Any]]]]:
    texts, pages_json = [], []
    for img in images:
        if model_name == "EasyOCR":
            result = reader_easy.readtext(np.array(img), detail=1)
            texts.append("\n".join(r[1] for r in result))
            pages_json.append([
                {"bbox": np.array(r[0]).flatten().tolist(), "text": r[1], "conf": float(r[2])}
                for r in result
            ])
        else:  # RolmOCR
            model, processor = _load_rolm()
            from qwen_vl_utils import process_vision_info

            messages = [{
                "role": "user",
                "content": [
                    {"type": "image", "image": img},
                    {"type": "text", "text": "Extract the text from this image"},
                ],
            }]
            prompt = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            imgs, vids = process_vision_info(messages)
            batch = processor(text=[prompt], images=imgs, videos=vids, padding=True, return_tensors="pt")
            out = model.generate(**batch, max_new_tokens=128)
            text = processor.batch_decode(out[:, batch.input_ids.shape[1]:], skip_special_tokens=True)[0]
            texts.append(text)
            pages_json.append([{"text": text}])
    return "\n\n".join(texts), pages_json


def _save(text: str, page_json: list[list[dict[str, Any]]], out: Path):
    out.mkdir(parents=True, exist_ok=True)
    (out / "result.txt").write_text(text, "utf-8")
    (out / "result.json").write_text(json.dumps(page_json, ensure_ascii=False, indent=2), "utf-8")


# ------------------------------------------------------------------
# Public API
# ------------------------------------------------------------------

def run_ocr(pdf_path: Path, out_dir: Path, *, model_name: str = DEFAULT_MODEL):
    if _is_pdf_textual(pdf_path):
        from PyPDF2 import PdfReader
        txt = "\n\n".join(p.extract_text() or "" for p in PdfReader(str(pdf_path)).pages)
        _save(txt, [], out_dir)
        return

    imgs = _pdf_to_images(pdf_path)
    text, pages = _ocr_images(imgs, model_name)
    _save(text, pages, out_dir)
