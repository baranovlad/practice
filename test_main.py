import os
import requests
from colpali_engine.models.qwen2_5.biqwen2_5.processing_biqwen2_5 import BiQwen2_5_Processor
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pdfplumber
import warnings
import logging

import extract_text_from_pdf from ocr_utils

# Настройка логгеров для подавления предупреждений
pdfplumber_logger = logging.getLogger("pdfplumber")
pdfplumber_logger.setLevel(logging.ERROR)
warnings.filterwarnings("ignore")


def download_pdfs(pdf_list, output_dir):
    """Скачивает PDF-файлы из списка в указанную директорию"""
    assert isinstance(pdf_list, list), "pdf_list должен быть списком"
    assert os.path.isdir(output_dir), "Указанная директория не существует"

    for pdf in pdf_list:
        assert 'title' in pdf and 'file' in pdf, "Каждый элемент pdf_list должен содержать 'title' и 'file'"

        pdf_path = os.path.join(output_dir, f"{pdf['title']}.pdf")
        try:
            response = requests.get(pdf['file'], verify=False)
            assert response.status_code == 200, f"Ошибка HTTP {response.status_code}"

            with open(pdf_path, 'wb') as f:
                f.write(response.content)
            print(f"Успешно скачан: {pdf['title']}")

            assert os.path.exists(pdf_path), f"Файл {pdf_path} не был создан"
        except Exception as e:
            print(f"Ошибка при скачивании {pdf['title']}: {e}")


def pdf_to_text(pdf_list, output_dir):
    """Конвертирует PDF-файлы в текстовые файлы с помощью pdfplumber"""
    assert isinstance(pdf_list, list), "pdf_list должен быть списком"
    assert os.path.isdir(output_dir), "Указанная директория не существует"

    for pdf in pdf_list:
        assert 'title' in pdf, "Каждый элемент pdf_list должен содержать 'title'"

        pdf_path = os.path.join(output_dir, f"{pdf['title']}.pdf")
        txt_path = os.path.join(output_dir, f"{pdf['title']}.txt")

        if not os.path.exists(pdf_path):
            print(f"Файл {pdf_path} не существует, пропускаем")
            continue

        try:
            text = ""
            with pdfplumber.open(pdf_path) as pdf_file:
                for page in pdf_file.pages:
                    page_text = page.extract_text()
                    assert page_text is not None, f"Не удалось извлечь текст со страницы {page.page_number}"
                    text += page_text + "\n"

            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(text)
            print(f"Успешно конвертировано: {pdf['title']}.pdf -> {pdf['title']}.txt")

            assert os.path.exists(txt_path), f"Текстовый файл {txt_path} не был создан"
            assert os.path.getsize(txt_path) > 0, f"Текстовый файл {txt_path} пуст"
        except Exception as e:
            print(f"Ошибка при конвертации {pdf['title']}: {e}")


def pdf_to_images(pdf_list, output_dir, dpi=200):
    """Конвертирует PDF-файлы в изображения без лишних предупреждений"""
    assert isinstance(pdf_list, list), "pdf_list должен быть списком"
    assert os.path.isdir(output_dir), "Указанная директория не существует"
    assert isinstance(dpi, int) and dpi > 0, "DPI должен быть положительным целым числом"

    for pdf in pdf_list:
        assert 'title' in pdf, "Каждый элемент pdf_list должен содержать 'title'"

        pdf_path = os.path.join(output_dir, f"{pdf['title']}.pdf")

        if not os.path.exists(pdf_path):
            print(f"Файл {pdf_path} не существует, пропускаем")
            continue

        try:
            image_count = 0
            with pdfplumber.open(pdf_path) as pdf_file:
                for i, page in enumerate(pdf_file.pages):
                    img = page.to_image(resolution=dpi).original
                    img_path = os.path.join(output_dir, f"{pdf['title']}_{i}.jpg")
                    img.save(img_path, "JPEG", quality=95)
                    image_count += 1

                    assert os.path.exists(img_path), f"Изображение {img_path} не было создано"
                    assert os.path.getsize(img_path) > 0, f"Изображение {img_path} пустое"

            print(f"Успешно созданы изображения для: {pdf['title']}")
            assert image_count > 0, f"Не было создано ни одного изображения для {pdf['title']}"
        except Exception as e:
            print(f"Ошибка при создании изображений для {pdf['title']}: {e}")


def calculate_text_similarity(file1_path, file2_path):
    """
    Сравнивает два текстовых файла и возвращает оценку их схожести (0-1)
    """
    try:
        # Проверка существования файлов
        assert os.path.exists(file1_path), f"Файл {file1_path} не существует"
        assert os.path.exists(file2_path), f"Файл {file2_path} не существует"

        # Проверка что файлы не пустые
        assert os.path.getsize(file1_path) > 0, f"Файл {file1_path} пуст"
        assert os.path.getsize(file2_path) > 0, f"Файл {file2_path} пуст"

        # Чтение файлов
        with open(file1_path, 'r', encoding='utf-8') as f1, \
                open(file2_path, 'r', encoding='utf-8') as f2:
            doc1 = f1.read()
            doc2 = f2.read()

            assert len(doc1) > 0, f"Файл {file1_path} содержит только пустые символы"
            assert len(doc2) > 0, f"Файл {file2_path} содержит только пустые символы"

        # Векторизация текстов
        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform([doc1, doc2])

        # Расчет косинусного сходства
        similarity = cosine_similarity(tfidf_matrix[0], tfidf_matrix[1])

        similarity_score = similarity[0][0]
        assert 0 <= similarity_score <= 1, "Результат similarity должен быть в диапазоне [0, 1]"

        return similarity_score

    except Exception as e:
        print(f"Произошла ошибка: {e}")
        return None


def main():
    try:
        # Инициализация модели
        nomic_processor = BiQwen2_5_Processor.from_pretrained("nomic-ai/nomic-embed-multimodal-3b", use_fast=True)
        assert nomic_processor is not None, "Не удалось инициализировать модель"

        # Определяем рабочую директорию
        current_dir = os.getcwd()
        assert os.path.isdir(current_dir), "Текущая директория не существует"

        # Список PDF-файлов для обработки
        PDFs = [
            {'title': "Attention Is All You Need", 'file': "https://arxiv.org/pdf/1706.03762"},
            {'title': "Deep Residual Learning", 'file': "https://arxiv.org/pdf/1512.03385"},
            {'title': "BERT", 'file': "https://arxiv.org/pdf/1810.04805"},
            {'title': "GPT-3", 'file': "https://arxiv.org/pdf/2005.14165"},
            {'title': "Adam Optimizer", 'file': "https://arxiv.org/pdf/1412.6980"},
            {'title': "GANs", 'file': "https://arxiv.org/pdf/1406.2661"},
            {'title': "U-Net", 'file': "https://arxiv.org/pdf/1505.04597"},
            {'title': "DALL-E 2", 'file': "https://arxiv.org/pdf/2204.06125"},
            {'title': "Stable Diffusion", 'file': "https://arxiv.org/pdf/2112.10752"}
        ]

        assert len(PDFs) > 0, "Список PDFs не должен быть пустым"

        # Выполняем все этапы обработки
        download_pdfs(PDFs, current_dir)
        pdf_to_text(PDFs, current_dir)
        pdf_to_images(PDFs, current_dir)

        # Пример сравнения текстов
        file1 = os.path.join(current_dir, "Attention Is All You Need.txt")
        file2 = os.path.join(current_dir, "BERT.txt")

        if not os.path.exists(file1) or not os.path.exists(file2):
            print("Один или оба файла не существуют!")
        else:
            similarity_score = calculate_text_similarity(file1, file2)
            if similarity_score is not None:
                print(f"Уровень схожести между файлами: {similarity_score:.4f}")
                assert isinstance(similarity_score, float), "Результат должен быть float"

    except Exception as e:
        print(f"Ошибка в main: {e}")


if __name__ == "__main__":
    try:
        main()
    except AssertionError as ae:
        print(f"Assertion Error: {ae}")
    except Exception as e:
        print(f"Critical error: {e}")
