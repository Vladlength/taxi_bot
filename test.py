from google.cloud import speech
from pydub import AudioSegment
import difflib

def find_closest_address(input_address, address_list):
    # Находим наиболее похожий адрес с помощью difflib
    closest_match = difflib.get_close_matches(input_address, address_list, n=1)
    return closest_match[0] if closest_match else None
def run_quickstart() -> speech.RecognizeResponse:
    # Instantiates a client
    client = speech.SpeechClient()
    # Загрузка файла
    audio = AudioSegment.from_ogg("voice.ogg")
    # Изменение частоты дискретизации на 16000 Гц и битности на 16 бит
    audio = audio.set_frame_rate(16000).set_sample_width(2)  # 2 байта = 16 бит
    # Сохранение нового файла
    audio.export("voice_16bit_16000.wav", format="wav")
    with open('voice_16bit_16000.wav', 'rb') as audio_file:
        content = audio_file.read()
    audio = speech.RecognitionAudio(content=content)

    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,  # 16000
        # language_code="en-US",
        language_code="ru-RU"
    )

    # Detects speech in the audio file
    response = client.recognize(config=config, audio=audio)


    for result in response.results:
        print(f"Transcript: {result.alternatives[0].transcript}")
    print(response)


if __name__ == "__main__":
    run_quickstart()
