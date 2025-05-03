import easyocr
from pdf2image import convert_from_path
import numpy as np
import json
import os
import PyPDF2
import asyncio
import urllib3
import requests
import tempfile


class ChangeDir:
    def __init__(self, path):
        self.original_path = os.getcwd()
        self.path = path

    def __enter__(self):
        os.chdir(self.path)
        return self

    def __exit__(self, exp_type, exp_value, traceback):
        os.chdir(self.original_path)
        return True


urllib3.disable_warnings()
reader = easyocr.Reader(['en', 'ru'], gpu=True)


async def upload_file(url, out_dir):
    with ChangeDir(out_dir):
        with open(f"pdf_for_ocr.pdf", 'wb') as f:
            try:
                f.write(requests.get(str(url), verify=False).content)
            except Exception as e:
                print(f"Error downloading PDF: {e}")


def is_pdf_textual(pdf_path):
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        if reader.pages[1].extract_text() is not None:
            return True
        else:
            return False


def convert_pdf_to_images(pdf_path, dpi=300):
    """Извлекает изображения из PDF."""
    try:
        images = convert_from_path(pdf_path, dpi=dpi, poppler_path=r"C:\Users\dimaw_1l7qj73\OneDrive\Рабочий стол\политех\practice\poppler-24.08.0\Library\bin")
        return images

    except Exception as e:
        print(f"Ошибка при конвертации PDF: {e}")


def run_ocr_on_image(img, reader):
    """Распознаёт текст с помощью EasyOCR."""
    try:
        image_np = np.array(img)
        text_blocks = reader.readtext(image_np, detail=0)  # Только текст
        page_text = "\n".join(text_blocks)  # Объединяем все блоки в одну строку
        return page_text

    except Exception as e:
        print(f"Ошибка при распознавании текста: {e}")
        return ""


def collect_results(pages, out_dir):
    """Сохраняет текст в файл."""
    try:
        formatted_json = json.dumps(pages, indent=4, ensure_ascii=False)

        with open(out_dir, 'w', encoding='utf-8') as file:
            file.write(formatted_json)
            return out_dir
    except Exception as e:
        print(f"Ошибка при сохранении файла: {e}")


def main():
    pdf_path = input("Введите путь к PDF: ").strip()
    if not os.path.exists(pdf_path):
        print("Указанный файл PDF не существует!")
        return

    output_path = input("Куда сохранить текст (например, output.txt): ").strip()

    with tempfile.TemporaryDirectory() as temp_dir:
        print("Извлекаем изображения из PDF...")
        images = convert_pdf_to_images(pdf_path, dpi=300)

        if not images:
            print("Не удалось извлечь изображения из PDF.")
            return

        print("Распознаём текст с помощью EasyOCR...")
        page_text = ""

        result = {
            "source_pdf": pdf_path,
            "pages": []
        }

        for page_num, img in enumerate(images, start=1):
            page_text = ""
            text = run_ocr_on_image(img, reader)
            page_text += text + "\n\n"

            result["pages"].append({
                "page_number": page_num,
                "text": page_text.strip()
            })

        print("Сохраняем результат...")
        collect_results(result, output_path)

    print(f"Готово! Текст сохранён в {output_path}")

if __name__ == "__main__":
    main()