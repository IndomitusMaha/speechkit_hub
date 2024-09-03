import os
import yaml


def load_creds():
    try:
        STT_API_KEY = os.environ['STT_API_KEY']
        STT_URL = os.environ['STT_URL']
        TTS_API_KEY = os.environ['TTS_API_KEY']
        TTS_URL = os.environ['TTS_URL']
    except:
        print('LOADING FROM YAML')
        with open(f'speechkit_config.yml') as file:
            speechkit_config = yaml.full_load(file)

        STT_API_KEY = speechkit_config['STT_API_KEY']
        STT_URL = speechkit_config['STT_URL']
        TTS_API_KEY = speechkit_config['TTS_API_KEY']
        TTS_URL = speechkit_config['TTS_URL']

    return STT_API_KEY, STT_URL, TTS_API_KEY, TTS_URL