import os

from google.cloud import speech
from pydub import AudioSegment

def run_quickstart() -> speech.RecognizeResponse:
    # Instantiates a client
    client = speech.SpeechClient()
    # Загрузка файла
    audio = AudioSegment.from_wav("voice.wav")
    # Изменение частоты дискретизации на 16000 Гц и битности на 16 бит
    audio = audio.set_frame_rate(16000).set_sample_width(2)  # 2 байта = 16 бит
    # Сохранение нового файла
    audio.export("voice_16bit_16000.wav", format="wav")
    with open('voice.wav', 'rb') as audio_file:
        content = audio_file.read()
    audio = speech.RecognitionAudio(content=content)

    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,  # 16000
        language_code="ru-RU"
    )

    # Detects speech in the audio file
    response = client.recognize(config=config, audio=audio)
    os.remove("voice_16bit_16000.wav")
    return response




