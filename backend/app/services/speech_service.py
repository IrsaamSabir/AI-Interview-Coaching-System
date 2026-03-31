import os
import httpx
from dotenv import load_dotenv

load_dotenv()

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")  # Rachel
ELEVENLABS_TTS_URL = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"
ELEVENLABS_STT_URL = "https://api.elevenlabs.io/v1/speech-to-text"


# -------------------------------------------------
# TTS - convert question text - audio bytes (MP3)
# -------------------------------------------------
def text_to_speech(text: str) -> bytes:
    if not ELEVENLABS_API_KEY:
        raise ValueError("ELEVENLABS_API_KEY is not set in your .env file.")

    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json",
    }

    payload = {
        "text": text,
        "model_id": "eleven_monolingual_v1",
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


# -------------------------------------------------
# STT - convert audio file bytes - transcript text
# -------------------------------------------------
def speech_to_text(audio_bytes: bytes, filename: str = "answer.mp3") -> str:
    if not ELEVENLABS_API_KEY:
        raise ValueError("ELEVENLABS_API_KEY is not set in your .env file.")

    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
    }

    files = {
        "file": (filename, audio_bytes, "audio/mpeg"),
        "model_id": (None, "scribe_v1"),
    }

    response = httpx.post(
        ELEVENLABS_STT_URL,
        headers=headers,
        files=files,
        timeout=60.0
    )

    if response.status_code != 200:
        raise RuntimeError(
            f"ElevenLabs STT failed: {response.status_code} - {response.text}"
        )

    data = response.json()
    return data.get("text", "").strip()