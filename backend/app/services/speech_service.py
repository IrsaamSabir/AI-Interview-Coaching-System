import os
import httpx
from openai import OpenAI
from dotenv import load_dotenv
import io

load_dotenv()

ELEVENLABS_API_KEY  = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "pNInz6obpgDQGcFmaJgB")
ELEVENLABS_TTS_URL  = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"

_openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def text_to_speech(text: str) -> bytes:
    if not ELEVENLABS_API_KEY:
        raise ValueError("ELEVENLABS_API_KEY is not set in your .env file.")

    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json",
    }

    payload = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75
        }
    }

    response = httpx.post(
        ELEVENLABS_TTS_URL,
        headers=headers,
        json=payload,
        timeout=30.0
    )

    if response.status_code != 200:
        raise RuntimeError(
            f"ElevenLabs TTS failed: {response.status_code} - {response.text}"
        )

    return response.content   # raw MP3 bytes

def speech_to_text(audio_bytes: bytes, filename: str = "answer.webm") -> str:
    print(f"[STT] filename={filename}, size={len(audio_bytes)} bytes")

    audio_file = io.BytesIO(audio_bytes)
    audio_file.name = filename

    response = _openai.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file,
        language="en"
    )

    transcript = response.text.strip()
    print(f"[STT] transcript: {transcript}")

    if not transcript:
        raise RuntimeError("No speech detected. Please speak clearly and try again.")

    return transcript