import os
import subprocess
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
    language: str
    sample_rate: Optional[int] = 16000
    speed: Optional[float] = 1.0


def speechkit_tts(syntez_config):
    url = TTS_URL

    headers = {'Authorization': f'Api-Key {TTS_API_KEY}'}
    data = {
        'text': syntez_config['text'],
        'lang': syntez_config['lang'],
        'voice': syntez_config['voice_model'],
        'format': 'lpcm',
        'speed': syntez_config['speed'],
        'sampleRateHertz': syntez_config['sample_rate'],
    }

    with requests.post(url, headers=headers, data=data, stream=True) as resp:
        if resp.status_code != 200:
            raise RuntimeError("Invalid response received: code: %d, message: %s" % (resp.status_code, resp.text))

        for chunk in resp.iter_content(chunk_size=None):
            yield chunk


def get_synthesized_audio(syntez_config, audio_path):
    with open(f'{audio_path}', "wb") as f:
        for audio_content in speechkit_tts(syntez_config):
            f.write(audio_content)


def convert_raw_to_wav(input_path, output_path, raw_sample_rate, wav_sample_rate):
    command = f"ffmpeg -f s16le -ar {raw_sample_rate} -i \"{input_path}\" -ar {wav_sample_rate} \"{output_path}\" "
    # print(command)
    with open(os.devnull, 'w') as devnull:
        # Saying yes to replace audio by default
        subprocess.call(command + '-y', stdout=devnull, stderr=subprocess.STDOUT, shell=True)
        devnull.close()


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
        synthesis_request: Annotated[Synthesis_Task, Depends()],
) -> dict:
    UUID = str(uuid.uuid4())

    syntez_config = {
        'text': synthesis_request.text,
        'lang': synthesis_request.language,
        'voice_model': synthesis_request.voice_model,
        'speed': synthesis_request.speed,
        'sample_rate': synthesis_request.sample_rate,
    }

    raw_audio_path = f"/tmp/raw/{UUID}.raw"
    wav_audio_path = f"/tmp/wav/{UUID}.wav"
    print('synthesis!')
    get_synthesized_audio(syntez_config, raw_audio_path)
    convert_raw_to_wav(raw_audio_path, wav_audio_path, raw_sample_rate=synthesis_request.sample_rate,
                       desired_sample_rate=synthesis_request.sample_rate)

    return {"ok": True, "audio": open(wav_audio_path, 'rb')}

