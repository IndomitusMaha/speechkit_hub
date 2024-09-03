import uuid
import json
from typing import Annotated, Optional

from fastapi import FastAPI, Depends
from pydantic import BaseModel
import aiohttp

from load_config import load_creds


app = FastAPI()
STT_API_KEY, STT_URL, TTS_API_KEY, TTS_URL = load_creds()


class Recognize_Task(BaseModel):
    audio_name: str
    audio_data: bytes
    language: str
    sample_rate: int
    audio_format: Optional[str] = 'lpcm'


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

