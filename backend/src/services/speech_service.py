import io
import httpx
from openai import OpenAI

from src.config import settings

_ELEVENLABS_TTS_URL = f"https://api.elevenlabs.io/v1/text-to-speech/{settings.elevenlabs_voice_id}"
_openai             = OpenAI(api_key=settings.openai_api_key)


def text_to_speech(text: str) -> bytes:
    if not settings.elevenlabs_api_key:
        raise ValueError("ELEVENLABS_API_KEY is not set in your .env file.")

    headers = {
        "xi-api-key":   settings.elevenlabs_api_key,
        "Content-Type": "application/json",
    }
    payload = {
        "text":     text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability":        0.5,
            "similarity_boost": 0.75,
        },
    }

    response = httpx.post(_ELEVENLABS_TTS_URL, headers=headers, json=payload, timeout=30.0)

    if response.status_code != 200:
        raise RuntimeError(
            f"ElevenLabs TTS failed: {response.status_code} - {response.text}"
        )

    return response.content   # raw MP3 bytes


def speech_to_text(audio_bytes: bytes, filename: str = "answer.webm") -> str:
    print(f"[STT] filename={filename}, size={len(audio_bytes)} bytes")

    audio_file      = io.BytesIO(audio_bytes)
    audio_file.name = filename

    response   = _openai.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file,
        language="en",
    )
    transcript = response.text.strip()
    print(f"[STT] transcript: {transcript}")

    if not transcript:
        raise RuntimeError("No speech detected. Please speak clearly and try again.")

    return transcript
