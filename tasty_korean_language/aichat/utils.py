# aichat/utils.py
import os
import logging
from pathlib import Path
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from openai import OpenAI
from google.cloud import translate_v2, speech
from pydub import AudioSegment

logger = logging.getLogger(__name__)

class ApiClientManager:
    _instances = {}
    @classmethod
    def get_client(cls, service_name):
        if service_name not in cls._instances:
            if service_name == 'openai':
                cls._instances[service_name] = OpenAI(api_key=settings.CHATGPT_API_KEY)
            elif service_name == 'translate':
                cred_path = os.getenv('GOOGLE_CREDENTIALS_PATH', 'credentials.json')
                cls._instances[service_name] = translate_v2.Client.from_service_account_json(cred_path)
            elif service_name == 'speech':
                cls._instances[service_name] = speech.SpeechClient()
        return cls._instances[service_name]

class FileHandler:
    @staticmethod
    def save_audio_file(user, file_obj, ext='webm'):
        filename = f"{user.username}/audio_{os.urandom(4).hex()}.{ext}"
        path = default_storage.save(filename, ContentFile(file_obj.read()))
        return Path(default_storage.path(path))

    @staticmethod
    def convert_audio_format(input_path, output_ext='wav'):
        audio = AudioSegment.from_file(input_path)
        output_path = input_path.with_suffix(f'.{output_ext}')
        audio.export(output_path, format=output_ext)
        return output_path

class AIChatProcessor:
    @staticmethod
    def generate_gpt_response(message, lang):
        client = ApiClientManager.get_client('openai')
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": settings.GPT_SYSTEM_PROMPT},
                {"role": "user", "content": f"{message} (Response Language: {lang})"}
            ]
        )
        return response.choices[0].message.content

    @staticmethod
    def translate_message(text, target_lang):
        client = ApiClientManager.get_client('translate')
        return client.translate(text, target_language=target_lang)['translatedText']

    @staticmethod
    def process_feedback(feedback):
        if not feedback.feedback:
            return []
        parts = feedback.feedback.split(', ')
        return list(zip(parts[::2], parts[1::2]))