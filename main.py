# main.py
from fastapi import FastAPI, Request, Form, UploadFile, HTTPException, status
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
from typing import Optional
import ocr_utils
import os
import uuid  # имен файлов
import asyncio  # асинхрон
from fastapi.middleware.cors import CORSMiddleware
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

app = FastAPI()

# # Конфигурация CORS (настройте нужные вам домены)
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  # Разрешите все источники (только для разработки!)
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# Настройка статических файлов (CSS, JavaScript)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Настройка шаблонов Jinja2
templates = Jinja2Templates(directory="templates")

# Путь для сохранения загруженных файлов (Раздел "Хранение данных")
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)  # Создаем директорию, если ее нет

# Путь для сохранения результатов (Раздел "Формат выдачи результатов")
OUT_DIR = Path("results")
OUT_DIR.mkdir(exist_ok=True)  # Создаем директорию, если ее нет

# Временное хранилище для прогресса обработки (можно заменить на базу данных, если нужно хранить прогресс между сессиями)
# processing_progress = {}  # file_id: progress (0-100)


# Функция для обработки PDF (Раздел "Блок-схема процесса")
async def process_pdf(file_path: Path, file_id: str):
    """
    Асинхронная функция для обработки PDF в фоне.
    """
    try:
        logging.info(f"Начало обработки PDF: {file_path}")
        # processing_progress[file_id] = 5  # Начало обработки

        # Проверяем, содержит ли PDF встроенный текст (Раздел "Обработка PDF с текстом")
        if ocr_utils.is_pdf_textual(file_path):
            logging.info("PDF содержит текстовый слой, извлекаем текст напрямую.")
            # processing_progress[file_id] = 30
            pages = ocr_utils.extract_text_from_pdf(file_path)
        else:
            logging.info("PDF не содержит текстовый слой, запускаем OCR.")
            # processing_progress[file_id] = 20
            # Конвертируем PDF в изображения (Раздел "Обработка сканированного PDF")
            images = ocr_utils.convert_pdf_to_images(file_path)
            # processing_progress[file_id] = 40
            pages = []
            total_pages = len(images)

            # Распознаем текст на каждом изображении (Раздел "Обработка сканированного PDF" и код, который вы предоставили)
            for i, img in enumerate(images):
                # processing_progress[file_id] = 40 + int(
                #     (i / total_pages) * 50
                #  )  # Обновляем прогресс
                logging.info(f"Обработка страницы {i + 1}/{total_pages}")
                text = await asyncio.to_thread(
                    ocr_utils.recognize_text_with_qwen, img
                )  # Используем Qwen/Qwen2.5-Omni-7B
                pages.append({"page": i + 1, "text": text})

        # Собираем результаты и сохраняем в файлы (Раздел "Формат выдачи результатов")
        # processing_progress[file_id] = 90
        txt_path, json_path = ocr_utils.collect_results(
            pages, OUT_DIR, file_id
        )  # Передаем file_id

        # processing_progress[file_id] = 95
        logging.info(f"Результаты сохранены в: TXT - {txt_path}, JSON - {json_path}")

        # Удаляем временные файлы (Раздел "Хранение данных")
        ocr_utils.cleanup_files(file_path)
        # processing_progress[file_id] = 100  # Обработка завершена
        logging.info(f"Обработка PDF завершена: {file_path}")

        return txt_path, json_path

    except Exception as e:
        logging.exception(f"Ошибка при обработке PDF: {e}")
        # processing_progress[file_id] = -1  # Ошибка
        return None, None


# Маршруты (Раздел "FastAPI-маршруты")
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """
    Отображает страницу с формой загрузки.
    """
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/upload")
async def upload_pdf(request: Request, file: UploadFile):
    """
    Принимает PDF-файл, сохраняет его и запускает обработку в фоновом режиме.
    """
    try:
        logging.info(f"Загрузка файла: {file.filename}")

        # Проверка типа файла (Раздел "Загрузка PDF")
        if file.content_type != "application/pdf":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Недопустимый тип файла. Разрешены только PDF-файлы.",
            )

        # Проверка размера файла (Раздел "Загрузка PDF")
        if file.size > 50 * 1024 * 1024:  # 50MB limit
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Размер файла превышает ограничение в 50МБ.",
            )

        # Генерируем уникальный ID для файла (Раздел "Хранение данных")
        file_id = str(uuid.uuid4())
        file_path = UPLOAD_DIR / f"{file_id}_{file.filename}"

        # Сохраняем файл (Раздел "Хранение данных")
        with open(file_path, "wb") as f:
            f.write(await file.read())
        logging.info(f"Файл сохранен во временную папку: {file_path}")

        # Запускаем обработку в фоновом режиме (Раздел "Блок-схема процесса")
        asyncio.create_task(process_pdf(file_path, file_id))
        # processing_progress[file_id] = 0  # Инициализация прогресса
        logging.info(f"Обработка файла запущена в фоновом режиме. File ID: {file_id}")

        # Редирект на страницу ожидания/прогресса (Раздел "Интерфейс пользователя")
        return RedirectResponse(
            url=f"/result?file_id={file_id}", status_code=status.HTTP_303_SEE_OTHER
        )

    except HTTPException as e:
        logging.warning(f"Ошибка при загрузке файла: {e.detail}")
        raise e  # Передаем исключение дальше, чтобы FastAPI обработал его
    except Exception as e:
        logging.exception(f"Непредвиденная ошибка при загрузке файла: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Произошла ошибка при загрузке файла.",
        )


# @app.get("/progress")
# async def get_progress(file_id: str):
#     """
#     Возвращает текущий прогресс обработки для прогресс-бара.
#     """
#     progress = processing_progress.get(file_id, None)
#     if progress is None:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND, detail="File ID не найден"
#         )
#     return {"progress": progress}


@app.get("/result", response_class=HTMLResponse)
async def get_result(request: Request, file_id: str):
    """
    Отображает страницу со ссылками на готовые файлы, когда обработка завершена.
    """
    # progress = processing_progress.get(file_id, None)

    # if progress == -1:
    #     return templates.TemplateResponse(
    #         "result.html",
    #         {"request": request, "error": "Произошла ошибка во время обработки файла."},
    #     )  # Сообщение об ошибке

    # if progress != 100:
    #     return templates.TemplateResponse(
    #         "result.html", {"request": request, "processing": True, "file_id": file_id}
    #     )  # Ждем

    # Получаем пути к файлам
    txt_filename = f"{file_id}_result.txt"
    json_filename = f"{file_id}_result.json"

    txt_path = OUT_DIR / txt_filename
    json_path = OUT_DIR / json_filename

    if not txt_path.exists() or not json_path.exists():
        return templates.TemplateResponse(
            "result.html",
            {"request": request, "error": "Файлы результатов не найдены."},
        )

    return templates.TemplateResponse(
        "result.html",
        {
            "request": request,
            "txt_filename": txt_filename,
            "json_filename": json_filename,
            "file_id": file_id,
        },
    )


@app.get("/download/{fname}")
async def download_file(fname: str):
    """
    Отдает TXT или JSON-файл для скачивания.
    """
    file_path = OUT_DIR / fname
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Файл не найден"
        )
    return FileResponse(
        file_path, filename=fname, media_type="application/octet-stream"
    )


# Запуск Uvicorn (Раздел "FastAPI-маршруты")
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app, host="0.0.0.0", port=8000, reload=True
    )  # reload=True для разработки
