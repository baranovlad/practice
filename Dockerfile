# ---- Базовый образ --------------------------------------------------
FROM python:3.12-slim

# ---- Системные пакеты ----------------------------------------------
# poppler-utils   — backend для pdf2image
# tesseract-ocr   — не обязателен для EasyOCR, но пригодится для future features
RUN apt-get update && \
    apt-get install -y --no-install-recommends poppler-utils tesseract-ocr && \
    rm -rf /var/lib/apt/lists/*

# ---- Копируем код ---------------------------------------------------
WORKDIR /app
COPY . /app
RUN rm -rf fastapi_stub

# ---- Устанавливаем Python‑зависимости -------------------------------
RUN pip install --no-cache-dir -r requirements.txt

# ---- Переменные окружения (CPU‑режим) -------------------------------
ENV PYTHONUNBUFFERED=1 \
    POPPLER_PATH=/usr/bin

# ---- Старт приложения ----------------------------------------------
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
