import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from google.oauth2.service_account import Credentials
import gspread
from datetime import datetime
import os
import json

# Токен вашего бота
TOKEN = '7220815906:AAFw_nacPxVipWdsMC9H3nJ7r_ZEvMYjjwo'  # Ваш токен бота
bot = telebot.TeleBot(TOKEN)


# Подключаемся к Google Sheets API
CREDS_FILE = '/Users/ali/Downloads/credentials.json'
creds = Credentials.from_service_account_file(CREDS_FILE, scopes=[
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
])

gc = gspread.authorize(creds)

# ID существующей Google Таблицы
SPREADSHEET_ID = '1WRNI1BHueREap2EILOIqyzpVq0PStQ3TSJRoZAOdVg0'
# Открываем листы
sheet_ldsp = gc.open_by_key(SPREADSHEET_ID).worksheet('ЛДСП')
sheet_korobka = gc.open_by_key(SPREADSHEET_ID).worksheet('Коробка')
sheet_metal = gc.open_by_key(SPREADSHEET_ID).worksheet('Металл')

# Функция для поиска первой пустой строки в столбце A
def find_next_available_row(sheet):
    col_values = sheet.col_values(1)  # Получаем все значения из колонки A
    return len(col_values) + 1  # Первая пустая строка после заполненных

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def start(message):
    # Основное меню с кнопками "Добавить"
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    button_add = KeyboardButton("Добавить")
    markup.add(button_add)
    bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)

# Обработчик нажатия на кнопку "Добавить"
@bot.message_handler(func=lambda message: message.text == "Добавить")
def handle_buttons(message):
    # Кнопки для добавления: ЛДСП, Коробка, Метал
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("ЛДСП"), KeyboardButton("Коробка"), KeyboardButton("Метал"), KeyboardButton("Назад"))
    bot.send_message(message.chat.id, "Что вы хотите добавить?", reply_markup=markup)

# Функция для обработки пар "название - количество"
def process_multiple_entries(sheet, message):
    try:
        entries = message.text.strip().split("\n")  # Разделяем строки по переносам
        for entry in entries:
            parts = entry.rsplit(' ', 1)  # Разделяем строку по последнему пробелу
            if len(parts) != 2:
                bot.send_message(message.chat.id, f"Ошибка в строке: {entry}. Убедитесь, что количество указано числом.")
                continue
            
            name = parts[0].strip()  # Все, кроме последнего слова — это название
            quantity = parts[1].strip()  # Последнее слово — это количество

            if not quantity.isdigit():
                bot.send_message(message.chat.id, f"Ошибка в строке: {entry}. Количество должно быть числом.")
                continue
            
            date = datetime.now().strftime('%d-%m-%Y')
            next_row = find_next_available_row(sheet)  # Находим следующую доступную строку
            sheet.update(f'A{next_row}:C{next_row}', [[date, name, int(quantity)]])  # Обновляем только столбцы A, B и C

        bot.send_message(message.chat.id, f"Данные успешно добавлены.")
    except Exception as e:
        bot.send_message(message.chat.id, f"Ошибка: {e}")

# Обработчик добавления данных на ЛДСП
@bot.message_handler(func=lambda message: message.text == "ЛДСП")
def request_ldsp_data(message):
    bot.send_message(message.chat.id, "Введите данные в формате: Название Количество.")
    bot.register_next_step_handler(message, lambda msg: process_multiple_entries(sheet_ldsp, msg))

# Обработчик добавления данных на Коробка
@bot.message_handler(func=lambda message: message.text == "Коробка")
def request_korobka_data(message):
    bot.send_message(message.chat.id, "Введите данные в формате: Название Количество.")
    bot.register_next_step_handler(message, lambda msg: process_multiple_entries(sheet_korobka, msg))

# Обработчик добавления данных на Метал
@bot.message_handler(func=lambda message: message.text == "Метал")
def request_metal_data(message):
    bot.send_message(message.chat.id, "Введите данные в формате: Название Количество.")
    bot.register_next_step_handler(message, lambda msg: process_multiple_entries(sheet_metal, msg))

# Обработчик нажатия на кнопку "Назад"
@bot.message_handler(func=lambda message: message.text == "Назад")
def back_to_main_menu(message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("Добавить"))
    bot.send_message(message.chat.id, "Вы вернулись в главное меню. Выберите действие:", reply_markup=markup)

if __name__ == '__main__':
    bot.polling(none_stop=True)
