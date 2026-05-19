from fastapi import APIRouter, UploadFile, File
from fastapi.responses import Response
from pydantic import BaseModel

from src.services.speech_service import text_to_speech, speech_to_text

router = APIRouter()


class TTSRequest(BaseModel):
    text: str


@router.post("/tts")
def tts(request: TTSRequest):
    """Convert question text to MP3 audio."""
    audio = text_to_speech(request.text)
    return Response(content=audio, media_type="audio/mpeg")


@router.post("/stt")
async def stt(file: UploadFile = File(...)):
    """Convert candidate mic recording to text transcript."""
    audio_bytes = await file.read()
    transcript  = speech_to_text(audio_bytes, filename=file.filename)
    return {"transcript": transcript}
