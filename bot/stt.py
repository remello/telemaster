import requests
import tempfile
import os
from bot.config import ELEVENLABS_API_KEY

def transcribe_voice(ogg_file):
    url = "https://api.elevenlabs.io/v1/speech-to-text/convert"
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY
    }

    with tempfile.NamedTemporaryFile(delete=False, suffix=".ogg") as temp_file:
        temp_file.write(ogg_file)
        temp_filename = temp_file.name

    try:
        with open(temp_filename, 'rb') as f:
            files = {'file': (os.path.basename(temp_filename), f, 'audio/ogg')}
            data = {
                'model_id': 'scribe_v1',
                'language_code': 'ru',
                'tag_audio_events': 'true',
                'diarize': 'false',
                'timestamps_granularity': 'word'
            }
            response = requests.post(url, headers=headers, files=files, data=data)
            response.raise_for_status()
            return response.json().get('text', '')
    finally:
        os.remove(temp_filename)
