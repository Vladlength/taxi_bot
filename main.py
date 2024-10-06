import telebot
# from notifications import notify_driver_found, notify_car_arrival, notify_trip_started, notify_trip_ended
import speech_recognition as sr
from pydub import AudioSegment
import os
import traceback
import requests
from gtts import gTTS
from google.cloud import speech
from pydub import AudioSegment

import address_dict
from test import find_closest_address as find_address
from config import *

API_TOKEN = TELEGRAM_API  # Замените на ваш токен
YANDEX_API_KEY = SECRET_KEY
YANDEX_MODEL_URI = f'gpt://{YANDEX_CATALOG}/yandexgpt-lite'
bot = telebot.TeleBot(TELEGRAM_API)

# Путь к файлу для хранения всех заказов
ORDER_FILE_PATH = 'orders.txt'

user_data = {}
user_confirmation = {}
user_preferences = {}  # Хранение настроек пользователя

# Словари для перевода фраз на разные языки
translations = {
    'ru': {
        'lang': "ru-RU",
        'confirmation_message': "Пожалуйста, подтвердите правильность данных:\nНачальный адрес: {start_address}\nКонечный адрес: {end_address}\nТип поездки: {trip_type}\n",
        'text_response': "Вы выбрали текстовые сообщения.",
        'audio_response': "Вы выбрали голосовые сообщения.",
        'language_response': "Вы выбрали язык: {language}.",
        'thank_you': "Все данные собраны и сохранены. Спасибо!",
        'start_message': ("Добро пожаловать! Для заказа такси, пожалуйста, укажите следующие данные:\n"
                          "1. Начальный адрес\n"
                          "2. Конечный адрес\n"
                          "3. Тип поездки (Эконом, Комфорт, Супер Комфорт)\n"
                          "Для выбора типа ответа и языка зайдите в настройки /settings"),
        'request_missing_data': "Пожалуйста, укажите {missing_data}.",
        'error': "Произошла ошибка при обработке голосового сообщения.",
        'confirm_data': "Пожалуйста, подтвердите правильность данных, нажав 'Да' или 'Нет'.",
        'start_over': "Пожалуйста, начните заново.",
        'voice_recognized': "Голос распознан",  # 1
        'gpt_text': "Разбери текст на Начальный адрес, Конечный адрес и Тип поездки. Только это, ничего дополнительного не надо",
        'start_address': "Начальный адрес",
        'end_address': "Конечный адрес",
        'trip_type': "Тип поездки"
        , 'trip': {
            'driver': "Водитель найден и направляется к вам.",
        }
    },
    'en': {
        'lang': "fr-FR",
        'confirmation_message': "Please confirm the correctness of the data:\nStart address: {start_address}\nEnd address: {end_address}\nTrip type: {trip_type}\n",
        'text_response': "You have selected text messages.",
        'audio_response': "You have selected audio messages.",
        'language_response': "You have selected language: {language}.",
        'thank_you': "All data collected and saved. Thank you!",
        'start_message': ("Welcome! To order a taxi, please provide the following details:\n"
                          "1. Start address\n"
                          "2. End address\n"
                          "3. Trip type (Economy, Comfort, Super Comfort)\n"
                          "To select response type and language, go to settings /settings"),
        'request_missing_data': "Please provide {missing_data}.",
        'error': "An error occurred while processing the voice message.",
        'confirm_data': "Please confirm the correctness of the data by pressing 'Yes' or 'No'.",
        'start_over': "Please start over.",
        'voice_recognized': "Voice recognized",  # 1
        'gpt_text': "Parse the text into start address, end address and trip type. That's all, nothing else needed.",
        'start_address': "Start address",
        'end_address': "End address",
        'trip_type': "Trip type"
        , 'trip': {
            'driver': "Driver found and heading to you.",
        }
    },
    'fr': {
        'lang': "fr-FR",
        'confirmation_message': "Veuillez confirmer l'exactitude des données :\nAdresse de départ : {start_address}\nAdresse de fin : {end_address}\nType de voyage : {trip_type}\n",
        'text_response': "Vous avez choisi les messages texte.",
        'audio_response': "Vous avez choisi les messages audio.",
        'language_response': "Vous avez sélectionné la langue : {language}.",
        'thank_you': "Toutes les données ont été collectées et enregistrées. Merci !",
        'start_message': ("Bienvenue ! Pour commander un taxi, veuillez fournir les informations suivantes :\n"
                          "1. Adresse de départ\n"
                          "2. Adresse de fin\n"
                          "3. Type de voyage (Économique, Confort, Super Confort)\n"
                          "Pour sélectionner le type de réponse et la langue, allez dans les paramètres /settings"),
        'request_missing_data': "Veuillez fournir {missing_data}.",
        'error': "Une erreur s'est produite lors du traitement du message vocal.",
        'confirm_data': "Veuillez confirmer l'exactitude des données en appuyant sur 'Oui' ou 'Non'.",
        'start_over': "Veuillez recommencer.",
        'voice_recognized': "Voix reconnue",  # 1
        'gpt_text': "Analysez le texte en adresse de départ, adresse de fin et type de voyage. Juste ça, rien de plus n'est nécessaire",
        'start_address': "Adresse de départ",
        'end_address': "Adresse de fin",
        'trip_type': "Type de voyage"
        , 'trip': {
            'driver': "Le chauffeur a été trouvé et se dirige vers vous.",
        }
    }
}


# Функция для получения перевода фразы
def get_translation(chat_id, key, **kwargs):
    language = user_preferences.get(chat_id, {}).get('language', 'ru')
    template = translations.get(language, translations['ru']).get(key, '')
    return template.format(**kwargs)


# Функция для сохранения данных в файл
def save_data_to_file(user_id, data):
    with open(ORDER_FILE_PATH, 'a', encoding='utf-8') as f:
        f.write(f"Заказ от пользователя {user_id}:\n")
        f.write(f"Начальный адрес: {data.get('start_address', 'Не указан')}\n")
        f.write(f"Конечный адрес: {data.get('end_address', 'Не указан')}\n")
        f.write(f"Тип поездки: {data.get('trip_type', 'Не указан')}\n")
        f.write("----------------------------------------------------\n")


# Функция для определения недостающих данных
def get_missing_data(user_id):
    data = user_data.get(user_id, {})
    missing_data = []

    if 'start_address' not in data:
        missing_data.append('начальный адрес')
    if 'end_address' not in data:
        missing_data.append('конечный адрес')
    if 'trip_type' not in data:
        missing_data.append('тип поездки')

    return missing_data


# Функция для анализа текста с помощью Yandex GPT
def analyze_text_with_gpt(text, language):
    headers = {
        'Authorization': f'Api-Key {YANDEX_API_KEY}',
        'Content-Type': 'application/json'
    }
    data = {
        "modelUri": YANDEX_MODEL_URI,
        "completionOptions": {
            "stream": False,
            "temperature": 0.1,
            "maxTokens": 2000
        },
        "messages": [
            {
                "role": "system",
                "text": translations[language]['gpt_text']
            },
            {
                "role": "user",
                "text": text
            }
        ],
        "language": language
    }
    try:
        response = requests.post('https://llm.api.cloud.yandex.net/foundationModels/v1/completion', headers=headers,
                                 json=data)
        response.raise_for_status()
        response_json = response.json()
        print(f"GPT Response: {response_json}")

        if 'result' in response_json and 'alternatives' in response_json['result']:
            alternatives = response_json['result']['alternatives']
            if alternatives:
                return alternatives[0]['message']['text']
            else:
                print("Нет альтернатив в ответе GPT.")
                return ''
        else:
            print("Некорректный ответ GPT:", response_json)
            return ''
    except Exception as e:
        print(f"Ошибка при обращении к GPT: {e}")
        return ''


# Функция для разбора ответа GPT
def parse_gpt_response(response, language):
    data = {}
    lines = response.split('\n')
    for line in lines:
        if translations[language]['start_address'] in line:
            data['start_address'] = line.split(translations[language]['start_address'])[1].strip().strip('.')
        elif translations[language]['end_address'] in line:
            data['end_address'] = line.split(translations[language]['end_address'])[1].strip().strip('.')
        elif translations[language]['trip_type'] in line:
            data['trip_type'] = line.split(translations[language]['trip_type'])[1].strip().strip('.')
    return data


# Функция для создания клавиатуры с кнопками подтверждения
def create_confirmation_keyboard():
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    yes_button = telebot.types.KeyboardButton('Да')
    no_button = telebot.types.KeyboardButton('Нет')
    keyboard.add(yes_button, no_button)
    return keyboard


# Функция для синтеза речи и отправки голосового сообщения
def send_audio_message(chat_id, text):
    language = user_preferences.get(chat_id, {}).get('language', 'ru')
    tts = gTTS(text, lang=language)
    tts.save('response.mp3')
    audio = AudioSegment.from_mp3('response.mp3')
    audio.export('response.ogg', format='ogg')
    with open('response.ogg', 'rb') as audio_file:
        bot.send_voice(chat_id, audio_file)
    os.remove('response.mp3')
    os.remove('response.ogg')


# Функция для отправки сообщения в зависимости от предпочтений пользователя
def send_message(chat_id, key, **kwargs):
    user_prefs = user_preferences.get(chat_id, {'response_type': 'text'})
    text = get_translation(chat_id, key, **kwargs)
    if user_prefs.get('response_type') == 'audio':
        send_audio_message(chat_id, text)
    else:
        bot.send_message(chat_id, text)


# Обработчик команды /settings
@bot.message_handler(commands=['settings'])
def send_settings(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    text_button = telebot.types.KeyboardButton('Текстовые сообщения')
    audio_button = telebot.types.KeyboardButton('Голосовые сообщения')
    lang_buttons = [
        telebot.types.KeyboardButton('Русский'),
        telebot.types.KeyboardButton('Английский'),
        telebot.types.KeyboardButton('Французский')
    ]
    keyboard.add(text_button, audio_button)
    keyboard.add(*lang_buttons)
    bot.reply_to(message, get_translation(chat_id, 'start_message'), reply_markup=keyboard)


# Обработчик команды /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, get_translation(message.chat.id, 'start_message'))


# Обработчик голосовых сообщений
# @bot.message_handler(content_types=['voice'])
# def handle_voice(message):
#     user_id = message.from_user.id
#     language = user_preferences.get(user_id, {}).get('language', 'ru')
#
#     try:
#         file_info = bot.get_file(message.voice.file_id)
#         file = bot.download_file(file_info.file_path)
#
#         with open("voice.ogg", 'wb') as f:
#             f.write(file)
#         # Конвертируем .ogg в .wav
#         audio = AudioSegment.from_ogg("voice.ogg")
#         audio.export("voice.wav", format="wav")
#         # Распознаем речь из .wav файла
#         recognizer = sr.Recognizer()
#
#         with sr.AudioFile("voice.wav") as source:
#             audio_data = recognizer.record(source)
#             text = recognizer.recognize_google(audio_data, language=f"{language}-RU")
#
#         send_message(message.chat.id, 'voice_recognized', text=text)
#
#         if user_id not in user_data:
#             user_data[user_id] = {}
#
#         # Анализ текста с помощью Yandex GPT
#         gpt_response = analyze_text_with_gpt(text, language)
#
#
#         # Разбор ответа GPT
#         if gpt_response:
#             data = parse_gpt_response(gpt_response, language)
#             print("------------------")
#             print(data)
#             print("------------------")
#
#             user_data[user_id].update(data)
#         else:
#             send_message(message.chat.id, 'error')
#
#         # Проверка на наличие всех данных
#         missing_data = get_missing_data(user_id)
#
#         if missing_data:
#             send_message(message.chat.id, 'request_missing_data', missing_data=', '.join(missing_data))
#         else:
#             user_confirmation[user_id] = user_data[user_id]
#             confirmation_message = get_translation(message.chat.id, 'confirmation_message',
#                                                    start_address=user_data[user_id].get('start_address', 'Не указан'),
#                                                    end_address=user_data[user_id].get('end_address', 'Не указан'),
#                                                    trip_type=user_data[user_id].get('trip_type', 'Не указан'))
#             keyboard = create_confirmation_keyboard()
#             # send_message(message.chat.id, 'confirmation_message',
#             #              start_address=user_data[user_id].get('start_address', 'Не указан'),
#             #              end_address=user_data[user_id].get('end_address', 'Не указан'),
#             #              trip_type=user_data[user_id].get('trip_type', 'Не указан'))
#             bot.send_message(message.chat.id, confirmation_message, reply_markup=keyboard)
#
#         # Удаляем временные файлы
#         os.remove("voice.ogg")
#         os.remove("voice.wav")
#
#     except Exception as e:
#         send_message(message.chat.id, 'error')
#         print(f"Ошибка: {e}")

@bot.message_handler(content_types=['voice'])
def google_handle_voice(message):
    user_id = message.from_user.id
    language = user_preferences.get(user_id, {}).get('language', 'ru')

    try:
        file_info = bot.get_file(message.voice.file_id)
        file = bot.download_file(file_info.file_path)

        with open("voice.ogg", 'wb') as f:
            f.write(file)
        audio = AudioSegment.from_ogg("voice.ogg")
        # Изменение частоты дискретизации на 16000 Гц и битности на 16 бит
        audio = audio.set_frame_rate(16000).set_sample_width(2)  # 2 байта = 16 бит
        # Сохранение нового файла
        audio.export("voice_16bit_16000.wav", format="wav")
        with open('voice_16bit_16000.wav', 'rb') as audio_file:
            content = audio_file.read()
        audio = speech.RecognitionAudio(content=content)

        client = speech.SpeechClient()

        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000,  # 16000
            # language_code="en-US",
            language_code=translations[language]['lang']
        )

        # Detects speech in the audio file
        response = client.recognize(config=config, audio=audio)

        text = response.results[0].alternatives[0].transcript

        send_message(message.chat.id, 'voice_recognized', text=text)

        if user_id not in user_data:
            user_data[user_id] = {}

        # Анализ текста с помощью Yandex GPT
        gpt_response = analyze_text_with_gpt(text, language)

        # Разбор ответа GPT
        if gpt_response:
            data = parse_gpt_response(gpt_response, language)
            print("------------------")
            print(data)
            print("------------------")

            user_data[user_id].update(data)
        else:
            send_message(message.chat.id, 'error')

        # Проверка на наличие всех данных
        missing_data = get_missing_data(user_id)

        if missing_data:
            send_message(message.chat.id, 'request_missing_data', missing_data=', '.join(missing_data))
        else:
            user_confirmation[user_id] = user_data[user_id]
            confirmation_message = get_translation(message.chat.id, 'confirmation_message',
                                                   start_address=user_data[user_id].get('start_address', 'Не указан'),
                                                   end_address=user_data[user_id].get('end_address', 'Не указан'),
                                                   trip_type=user_data[user_id].get('trip_type', 'Не указан'))
            keyboard = create_confirmation_keyboard()

            bot.send_message(message.chat.id, confirmation_message, reply_markup=keyboard)

            bot.send_message(message.chat.id, 'address_dict: ')
            bot.send_message(message.chat.id,
                             find_address(input_address=user_data[user_id].get('start_address', 'Не указан'),
                                          address_list=address_dict.addresses))
            bot.send_message(message.chat.id,
                             find_address(input_address=user_data[user_id].get('end_address', 'Не указан'),
                                          address_list=address_dict.addresses))

            # print(find_address(input_address=user_data[user_id].get('start_address', 'Не указан'),
            #                    address_list=address_dict.addresses))

        # Удаляем временные файлы
        os.remove("voice.ogg")
        os.remove("voice_16bit_16000.wav")

    except Exception as e:
        send_message(message.chat.id, 'error')
        print(f"Ошибка: {e}")
    # except Exception as e:
    #     error_message = str(e)
    #     error_traceback = traceback.format_exc()
    #     send_message(message.chat.id, 'error')
    #     print(f"Ошибка: {error_message}")
    #     print(f"Трассировка:\n{error_traceback}")


# Обработчик текстовых сообщений
@bot.message_handler(content_types=['text'])
def handle_text(message):
    user_id = message.from_user.id
    text = message.text.lower()

    if user_id not in user_preferences:
        user_preferences[user_id] = {'response_type': 'text', 'language': 'ru'}

    if text == 'текстовые сообщения':
        user_preferences[user_id]['response_type'] = 'text'
        send_message(message.chat.id, 'text_response')

    elif text == 'голосовые сообщения':
        user_preferences[user_id]['response_type'] = 'audio'
        send_message(message.chat.id, 'audio_response')

    elif text in ['русский', 'английский', 'французский']:
        lang_map = {
            'русский': 'ru',
            'английский': 'en',
            'французский': 'fr'
        }
        user_preferences[user_id]['language'] = lang_map[text]
        send_message(message.chat.id, 'language_response', language=text.capitalize())

    elif text == 'да' and user_id in user_confirmation:
        save_data_to_file(user_id, user_confirmation[user_id])
        send_message(message.chat.id, 'thank_you')
        send_audio_message(message.chat.id, translations[user_preferences[user_id]['language']]['trip']['driver'])
        # notify_driver_found(message.chat.id, user_preferences)
        # send_message(message.chat.id, translations[user_preferences[user_id]['language']]['trip']['driver'], user_preferences.get(message.chat.id, 'text'))
        user_data.pop(user_id, None)
        user_confirmation.pop(user_id, None)

    elif text == 'нет' and user_id in user_confirmation:
        user_data.pop(user_id, None)
        user_confirmation.pop(user_id, None)
        send_message(message.chat.id, 'start_over')

    else:
        # Если пользователь отправил текст до подтверждения данных, сообщаем о необходимости подтверждения
        if user_id in user_confirmation:
            send_message(message.chat.id, 'confirm_data')
        else:
            send_message(message.chat.id, 'start_message')


bot.polling(none_stop=True)
