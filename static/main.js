// Получаем элементы DOM (объектной модели документа)
const dropArea = document.getElementById('dropArea'); // Область для перетаскивания файлов
const fileInput = document.getElementById('fileInput'); // Поле ввода файла
const browseBtn = document.querySelector('.browse-btn'); // Кнопка выбора файлов
const fileInfo = document.getElementById('fileInfo'); // Блок с информацией о файле
const fileName = document.getElementById('fileName'); // Элемент для отображения имени файла
const fileSize = document.getElementById('fileSize'); // Элемент для отображения размера файла
const downloadBtn = document.getElementById('download'); // Кнопка скачивания
const serverSelect = document.getElementById('serverSelect'); // Выпадающий список серверов
const statusDiv = document.getElementById('status'); // Блок для отображения статуса

// Текущий выбранный файл
let selectedFile = null;

// Инициализация обработчиков событий
function init() {
    // Обработчик изменения выбранного файла
    fileInput.addEventListener('change', handleFileSelect);
    
    // Обработчик клика по кнопке выбора файла
    browseBtn.addEventListener('click', () => fileInput.click());
    
    // Добавляем обработчики для drag and drop
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, preventDefaults, false);
    });
    
    // Подсветка области при наведении файла
    ['dragenter', 'dragover'].forEach(eventName => {
        dropArea.addEventListener(eventName, highlight, false);
    });
    
    // Убираем подсветку когда файл убрали
    ['dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, unhighlight, false);
    });
    
    // Обработчик сброса файла в область
    dropArea.addEventListener('drop', handleDrop);
    
    // Обработчик клика по кнопке скачивания
    downloadBtn.addEventListener('click', handleDownload);
    
    // Обработчик выбора сервера
    serverSelect.addEventListener('change', handleServerSelect);
}

// Отменяем стандартное поведение браузера для drag and drop
function preventDefaults(e) {
    e.preventDefault(); // Отменяем действие по умолчанию
    e.stopPropagation(); // Останавливаем всплытие события
}

// Подсвечиваем область для drop
function highlight() {
    dropArea.classList.add('highlight'); // Добавляем класс highlight
}

// Убираем подсветку области
function unhighlight() {
    dropArea.classList.remove('highlight'); // Удаляем класс highlight
}

// Обработка сброшенных файлов
function handleDrop(e) {
    const dt = e.dataTransfer; // Получаем данные о перетаскивании
    const files = dt.files; // Получаем список файлов
    
    if (files.length > 0) {
        fileInput.files = files; // Устанавливаем файлы в input
        handleFileSelect({ target: fileInput }); // Обрабатываем выбор файла
    }
}

// Обработка выбора файла
function handleFileSelect(event) {
    const files = event.target.files; // Получаем выбранные файлы
    
    if (files.length === 0) return; // Если файлов нет - выходим
    
    const file = files[0]; // Берем первый файл
    
    // Проверяем что файл PDF (по типу или расширению)
    if (!file.type.includes('pdf') && !file.name.toLowerCase().endsWith('.pdf')) {
        showStatus('Пожалуйста, выберите PDF файл', 'error');
        return;
    }
    
    selectedFile = file; // Сохраняем выбранный файл
    
    // Отображаем информацию о файле
    fileName.textContent = file.name; // Имя файла
    fileSize.textContent = formatFileSize(file.size); // Размер файла
    fileInfo.style.display = 'block'; // Показываем блок информации
    
    showStatus('PDF файл выбран и готов к обработке', 'success');
}

// Обработка скачивания текстового файла
function handleDownload() {
    if (!selectedFile) {
        showStatus('Сначала выберите PDF файл', 'error');
        return;
    }
    
    
    // Для примера создаем тестовый текстовый файл
    const textContent = "Это был бы извлеченный текст из PDF.\n\n" +
                      `Оригинальный PDF: ${selectedFile.name}\n` +
                      `Размер: ${formatFileSize(selectedFile.size)}\n` +
                      "Здесь происходил бы парсинг PDF в реальном приложении.";
    
    downloadTextFile(textContent, selectedFile.name.replace('.pdf', '') + '.txt');
}

// Функция скачивания текстового файла
function downloadTextFile(content, filename) {
    const blob = new Blob([content], { type: 'text/plain' }); // Создаем Blob с текстом
    const url = URL.createObjectURL(blob); // Создаем URL для Blob
    
    const a = document.createElement('a'); // Создаем ссылку
    a.href = url; // Устанавливаем URL
    a.download = filename; // Устанавливаем имя файла
    document.body.appendChild(a); // Добавляем ссылку в DOM
    a.click(); // Эмулируем клик для скачивания
    
    // Чистим за собой
    setTimeout(() => {
        document.body.removeChild(a); // Удаляем ссылку
        URL.revokeObjectURL(url); // Освобождаем URL
    }, 100);
    
    showStatus('Текстовый файл успешно скачан', 'success');
}

// Переключение видимости выбора сервера
function toggleServerSelect() {
    if (serverSelect.style.display === 'none' || !serverSelect.style.display) {
        serverSelect.style.display = 'inline-block'; // Показываем список
        serverSelect.focus(); // Фокусируемся на списке
    } else {
        serverSelect.style.display = 'none'; // Скрываем список
    }
}

// Обработка выбора сервера
function handleServerSelect(event) {
    const selectedServer = event.target.value; // Получаем выбранный сервер
    if (selectedServer) {
        showStatus(`Выбран сервер: ${selectedServer}`, 'success');
        console.log(`Выбран сервер: ${selectedServer}`);
    }
}

// Форматирование размера файла в читаемый вид
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Байт';
    const k = 1024;
    const sizes = ['Байт', 'КБ', 'МБ', 'ГБ'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Отображение статусного сообщения
function showStatus(message, type) {
    statusDiv.textContent = message; // Устанавливаем текст
    statusDiv.className = type; // Устанавливаем класс (success/error)
}

// Инициализация приложения
init();

// Альтернативная версия toggleServerSelect 
function toggleServerSelect() {
    const serverSelect = document.getElementById('serverSelect');
    if (serverSelect.style.display === 'none') {
        serverSelect.style.display = 'block';
        serverSelect.focus(); 
    } else {
        serverSelect.style.display = 'none';
    }
}

// Альтернативный обработчик выбора сервера 
document.getElementById('serverSelect').addEventListener('change', function(event) {
    const selectedServer = event.target.value;
    if (selectedServer) {
        console.log(`выбран сервер: ${selectedServer}`);
    }
});
