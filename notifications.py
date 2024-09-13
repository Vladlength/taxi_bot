import telebot
from gtts import gTTS
from pydub import AudioSegment
import os
from config import *
# from main import translations


# Путь к токену и создание бота
# API_TOKEN = 'ВашApi'  # Замените на ваш токен
bot = telebot.TeleBot(TELEGRAM_API)

# Функция для синтеза речи и отправки голосового сообщения
def send_audio_message(chat_id, text):
    tts = gTTS(text, lang='ru')
    tts.save('response.mp3')
    audio = AudioSegment.from_mp3('response.mp3')
    audio.export('response.ogg', format='ogg')
    with open('response.ogg', 'rb') as audio_file:
        bot.send_voice(chat_id, audio_file)
    os.remove('response.mp3')
    os.remove('response.ogg')

# Функция для отправки сообщения в зависимости от предпочтений пользователя
def send_message(chat_id, text, preference):
    if preference == 'audio':
        send_audio_message(chat_id, text)
    else:
        bot.send_message(chat_id, text)

# Функция для уведомления о том, что водитель найден
def notify_driver_found(chat_id, user_preferences):
    text = "Водитель найден и направляется к вам."
    send_message(chat_id, text, user_preferences.get(chat_id, 'text'))

# Функция для уведомления о прибытии машины через указанное время
def notify_car_arrival(chat_id, minutes, user_preferences):
    text = f"Ваша машина прибудет через {minutes} минут."
    send_message(chat_id, text, user_preferences.get(chat_id, 'text'))

# Функция для уведомления о начале поездки
def notify_trip_started(chat_id, user_preferences):
    text = "Поездка началась. Приятного пути!"
    send_message(chat_id, text, user_preferences.get(chat_id, 'text'))

# Функция для уведомления о завершении поездки
def notify_trip_ended(chat_id, user_preferences):
    text = "Поездка завершена. Спасибо за использование нашего сервиса!"
    send_message(chat_id, text, user_preferences.get(chat_id, 'text'))
