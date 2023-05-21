import pip
pip.main(['install', 'pytelegrambotapi'])

import json
import logging
import os
from telegram import Bot, Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

import json
import time

# Устанавливаем настройки логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Инициализируем Telegram Bot API
bot_token = "6151384984:AAEM7zZIC2yEEnbTHVNz0JaP11NKg2x9TMo"  # Замените на ваш API-токен
bot = Bot(token=bot_token)

# Определяем обработчик команды /start
def start(update: Update, context) -> None:
    # Отправляем ответное сообщение
    update.message.reply_text("Я весь в ожидании. Введите не менее 5 слов.")

# Определяем обработчик текстовых сообщений
def handle_text(update: Update, context) -> None:
    user_id = update.message.from_user.id
    text = update.message.text

    # Проверяем количество слов в тексте
    word_count = len(text.split())
    if word_count < 5:
        # Отправляем сообщение о минимальном количестве слов
        update.message.reply_text("Введите не менее 5 слов.")
        return

    # Создаем название папки в формате user_id__requests
    requests_folder = f"{user_id}__requests"
    os.makedirs(requests_folder, exist_ok=True)

    # Создаем название файла в формате user_id__text.json
    filename = f"{user_id}__text.json"

    # Путь к файлу в текущей директории
    filepath = os.path.join(requests_folder, filename)

    # Создаем новый файл json и сохраняем в него текст пользователя
    with open(filepath, 'w', encoding='utf-8') as file:
        json.dump({'text': text}, file, ensure_ascii=False, indent=4)

    # Отправляем ответное сообщение
    update.message.reply_text("Анализирую...")

    # Открываем файл с текстом для анализа
    with open(filepath, 'r', encoding='utf-8') as file:
        text_data = json.load(file)

    # Инициализируем параметры безголового режима Chrome
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Включаем безголовый режим Chrome

    # Запускаем веб-драйвер (здесь используется Chrome)
    driver = webdriver.Chrome(options=chrome_options)

    # Переходим на сайт с полем для ввода текста
    driver.get('https://textometr.ru/')  # Замените на фактический URL сайта

    # Находим текстовое поле и вводим текст из файла
    text_field = driver.find_element(By.CLASS_NAME, "textarea.textarea")  # Замените на фактический идентификатор текстового поля
    text_field.send_keys(text_data['text'])

    # Нажимаем кнопку "Определить" (замените на фактический идентификатор кнопки)
    button = driver.find_element('xpath', '//a[contains(@class, "button") and contains(@class, "is-primary") and contains(@class, "is-rounded") and contains(@class, "is-medium") and contains(@class, "is-primary")]')

    button.click()

    # Ждем некоторое время для получения результата (здесь задержка составляет 15 секунд)
    time.sleep(5)

    # Получаем результат анализа (замените на фактический идентификатор элемента с результатом)
    result_table = driver.find_element('xpath', '//*[@id="result"]/div[1]/table/tbody')

    # Инициализируем переменные для хранения результата
    result = {}

    # Извлекаем текст из указанного элемента
    level_element = driver.find_element('xpath', '//*[@id="result"]/div[1]/table/tbody/tr[1]')
    level_value = level_element.text

    # Заменяем символы \n на пробелы
    level_value = level_value.replace('\n', ' ')

    # Добавляем значение в начало результата с ключом "Уровень"
    result['Уровень'] = level_value

    # Обрабатываем каждую строку <tr> в таблице
    rows = result_table.find_elements('xpath', './/tr')

    for row in rows:
        # Проверяем, что строка содержит как <th>, так и <td>
        if row.find_elements('xpath', './/th') and row.find_elements('xpath', './/td'):
            # Проверяем, что в строке нет строки 'Частотный словарь по тексту' в <th>
            if 'Частотный словарь по тексту' not in row.find_element('xpath', './/th').text:
                # Извлекаем данные из <th> и <td>
                key = row.find_element('xpath', './/th').text
                value = row.find_element('xpath', './/td').text

                # Добавляем данные в результат
                result[key] = value

    # Закрываем веб-драйвер
    driver.quit()

    # Сохраняем результат в файл result.json
    #result_data = {'result': result}
    result_filepath = os.path.join(requests_folder, f"{user_id}__result.json")
    
    # Открываем файл с результатом
    with open(result_filepath, 'r', encoding='utf-8') as file:
        response_data = json.load(file)

        # Определение ключей для форматирования
    formatting_keys = [
        'Ключевые слова',
        'Самые полезные слова',
        'Не входит в лексический список А2',
        'Не входит в лексический список B1',
        'Не входит в лексический список B2',
        'Не входит в лексический список C1',
        'Редкие слова',
        'Не входит в список РКИ-дети 1000',
        'Не входит в список РКИ-дети 2000',
        'Не входит в список РКИ-дети 5000']

    # Форматирование значений соответствующих ключам
    for key in formatting_keys:
        if key in response_data['result']:
            value = response_data['result'][key]
            value_list = value.split('\n')
            formatted_value = ', '.join(word for word in value_list[:-1]) + ', ' + value_list[-1]
            response_data['result'][key] = formatted_value

    if "Возможные грамматические темы" in result:
        value = result["Возможные грамматические темы"]
        value_lines = value.split("\n")
        formatted_value = "\n".join([line.strip() for line in value_lines if line.strip()])
        response_data["Возможные грамматические темы"] = formatted_value
        

    # Форматируем содержимое файла в ответ
    response = ""
    for key, value in response_data['result'].items():
        response += f"<b>{key}:</b> {value}\n\n"
    
    # Отправляем ответ пользователю
    bot.send_message(chat_id=user_id, text=response, parse_mode='HTML')


# Определяем обработчик ошибок
def error(update: Update, context) -> None:
    logging.error(f"Update {update} caused error {context.error}")

# Определяем функцию для запуска бота
def run_bot():
    # Создаем экземпляр Updater и регистрируем обработчики
    updater = Updater(bot_token, use_context=True)
    dispatcher = updater.dispatcher

    # Регистрируем обработчик команды /start
    dispatcher.add_handler(CommandHandler("start", start))

    # Регистрируем обработчик текстовых сообщений
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_text))

    # Регистрируем обработчик ошибок
    dispatcher.add_error_handler(error)

    # Запускаем бота
    updater.start_polling()

run_bot()
