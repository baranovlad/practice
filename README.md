# OCR‑PDF

## Описание

Небольшой локальный сервис на FastAPI, который позволяет:

* Загружать PDF-документы
* Преобразовывать страницы в изображения
* Распознавать текст с помощью EasyOCR / PyMuPDF
* Выгружать результат в формате **TXT** и **JSON**

Проект готов к развёртыванию на Windows, Linux и macOS без дополнительных зависимостей помимо Python.

---

## Требования

* Python 3.9+
* Git

> Все зависимости указаны в `requirements.txt`.

---

## Установка

```bash
# Клонировать репозиторий
git clone https://github.com/<username>/practice-main.git
cd practice-main

# Создать виртуальное окружение
python -m venv venv

# Активировать окружение
# Windows:
venv\Scripts\activate.bat
# Linux/macOS:
source venv/bin/activate

# Установить зависимости
pip install --upgrade pip
pip install -r requirements.txt
```

---

## Конфигурация

Файл `.env` поддерживает две переменные:

```dotenv
# использовать GPU для EasyOCR (0 — CPU, 1 — GPU)
EASYOCR_GPU=0
```

---

## Запуск

```bash
uvicorn app.main:app --reload
```

Откройте в браузере [http://127.0.0.1:8000](http://127.0.0.1:8000).

---

## Использование

1. На главной странице выберите PDF.
2. Опционально выберите модель (локальная / серверная).
3. Нажмите **Отправить**.
4. Дождитесь обработки и перейдите на страницу результата.
5. Скачайте файлы:

   * `result.txt` – чистый текст
   * `result.json` – массив объектов `{ bbox, text, confidence }`

---

## Структура проекта

```
app/             # исходный код FastAPI
templates/       # Jinja2‑шаблоны (index.html, result.html, base.html)
static/          # CSS и JS
results/         # папка с результатами OCR
tools/           # вспомогательные скрипты и Poppler (опционально)
venv/            # виртуальное окружение (игнорируется)
requirements.txt # зафиксированные зависимости
Dockerfile       # конфигурация контейнера (если нужна)
README.md        # эта инструкция
```

---

## Тестирование

```bash
pytest -q
```

---

## Лицензия

MIT © Dmitriy Kuznetsov
