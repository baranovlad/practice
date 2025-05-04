import os
import json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import warnings
import logging
from ocr_utils import convert_pdf_to_images, run_ocr_on_image
from main import upload_pdf

# Настройка логгеров для подавления предупреждений
pdfplumber_logger = logging.getLogger("pdfplumber")
pdfplumber_logger.setLevel(logging.ERROR)
warnings.filterwarnings("ignore")


def calculate_similarity(file1_path, file2_path):
    """
    Сравнивает два файла (TXT или JSON) и возвращает оценку их схожести (0-1)
    """
    try:
        # Проверка существования файлов
        if not os.path.exists(file1_path):
            raise FileNotFoundError(f"Файл {file1_path} не существует")
        if not os.path.exists(file2_path):
            raise FileNotFoundError(f"Файл {file2_path} не существует")

        # Проверка, что файлы не пустые
        if os.path.getsize(file1_path) == 0:
            raise ValueError(f"Файл {file1_path} пуст")
        if os.path.getsize(file2_path) == 0:
            raise ValueError(f"Файл {file2_path} пуст")

        # Определение типа файла
        def get_file_content(file_path):
            if file_path.lower().endswith('.json'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = json.load(f)
                return json.dumps(content, sort_keys=True)
            else:  # предполагаем, что это текстовый файл
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()

        # Получение содержимого файлов
        content1 = get_file_content(file1_path)
        content2 = get_file_content(file2_path)

        # Проверка, что содержимое не пустое
        if not content1:
            raise ValueError(f"Файл {file1_path} содержит только пустые символы")
        if not content2:
            raise ValueError(f"Файл {file2_path} содержит только пустые символы")

        # Векторизация текстов
        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform([content1, content2])

        # Расчет косинусного сходства
        similarity = cosine_similarity(tfidf_matrix[0], tfidf_matrix[1])

        similarity_score = similarity[0][0]
        if not (0 <= similarity_score <= 1):
            raise ValueError("Результат similarity должен быть в диапазоне [0, 1]")

        return similarity_score

    except Exception as e:
        print(f"Произошла ошибка: {e}")
        return None


def main():
    try:
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
        upload_pdf(PDFs)
        convert_pdf_to_images(PDFs)
        run_ocr_on_image(PDFs)

        # Пример сравнения текстов
        files_to_compare = [
            ("file1.txt", "file2.txt"),  # TXT файлы
            ("data1.json", "data2.json")  # JSON файлы
        ]

        for file1, file2 in files_to_compare:
            file1_path = os.path.join(current_dir, file1)
            file2_path = os.path.join(current_dir, file2)

            if not os.path.exists(file1_path) or not os.path.exists(file2_path):
                print(f"Один или оба файла ({file1}, {file2}) не существуют!")
                continue

            similarity_score = calculate_similarity(file1_path, file2_path)
            if similarity_score is not None:
                print(f"Уровень схожести между {file1} и {file2}: {similarity_score:.4f}")

    except Exception as e:
        print(f"Ошибка в main: {e}")


if __name__ == "__main__":
    try:
        main()
    except AssertionError as ae:
        print(f"Assertion Error: {ae}")
    except Exception as e:
        print(f"Critical error: {e}")
