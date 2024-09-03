import uuid
import json
from typing import Annotated, Optional

from fastapi import FastAPI, Depends
from pydantic import BaseModel
import aiohttp
import requests

from load_config import load_creds


app = FastAPI()
STT_API_KEY, STT_URL, TTS_API_KEY, TTS_URL = load_creds()


class Recognize_Task(BaseModel):
    audio_name: str
    audio_data: bytes
    language: str
    sample_rate: int
    audio_format: Optional[str] = 'lpcm'


class Synthesis_Task(BaseModel):
    text: str
    voice_model: str
    sample_rate: Optional[int] = 16000
    speed: Optional[float] = 1.0


def speechkit_tts(text, sampleRateHertz, data_dict, syntez_config):
    url = 'https://tts.api.cloud.yandex.net/speech/v1/tts:synthesize'

    API_KEY_SYNTEZ = data_dict['API_KEY_SYNTEZ']

    headers = {'Authorization': f'Api-Key {API_KEY_SYNTEZ}'}
    data = {
        'text': text,
        'lang': syntez_config['lang'],
        'voice': syntez_config['voice_model'],
        'format': 'lpcm',
        'speed': syntez_config['speed'],
        'sampleRateHertz': sampleRateHertz,
    }

    with requests.post(url, headers=headers, data=data, stream=True) as resp:
        if resp.status_code != 200:
            raise RuntimeError("Invalid response received: code: %d, message: %s" % (resp.status_code, resp.text))

        for chunk in resp.iter_content(chunk_size=None):
            yield chunk


def get_synthesized_audio(text, raw_audio_path, data_dict, syntez_config):
    sample_rate = data_dict['sample_rate']

    with open(f'{raw_audio_path}', "wb") as f:
        for audio_content in speechkit_tts(text, sample_rate, data_dict, syntez_config):
            f.write(audio_content)


@app.post("/stt")
async def stt(
        stt_request: Annotated[Recognize_Task, Depends()],
) -> dict:
    UUID = str(uuid.uuid4())

    headers = {
        'Authorization': f'Api-key {STT_API_KEY}',
        "x-client-request-id": UUID,
    }

    params = {
        'lang': stt_request.language,
        'sampleRateHertz': stt_request.sample_rate,
        'format': stt_request.audio_format,
    }

    async with aiohttp.ClientSession() as session:
        response = await session.post(STT_URL, params=params, headers=headers, data=stt_request.audio_data)
        # response_text = await response.text()
        response_text = (await response.json())['result']
        print(response_text)

    return {"ok": True, "text": response_text}


@app.post("/synthesis")
async def synthesis(
        stt_request: Annotated[Recognize_Task, Depends()],
) -> dict:
    UUID = str(uuid.uuid4())

    print('synthesis!')

    return {"ok": True, "audio": 'audio'}

