import os
from colpali_engine.models.qwen2_5.biqwen2_5.processing_biqwen2_5 import BiQwen2_5_Processor
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import warnings
import logging
from ocr_utils import convert_pdf_to_images,  run_ocr_on_image
from main import upload_pdf

# Настройка логгеров для подавления предупреждений
pdfplumber_logger = logging.getLogger("pdfplumber")
pdfplumber_logger.setLevel(logging.ERROR)
warnings.filterwarnings("ignore")


def calculate_text_similarity(file1_path, file2_path):
    """
    Сравнивает два текстовых файла и возвращает оценку их схожести (0-1)
    """
    try:
        # Проверка существования файлов
        assert os.path.exists(file1_path), f"Файл {file1_path} не существует"
        assert os.path.exists(file2_path), f"Файл {file2_path} не существует"

        # Проверка, что файлы не пустые
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
