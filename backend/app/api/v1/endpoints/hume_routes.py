import os
import httpx
from fastapi import APIRouter, UploadFile, File, HTTPException
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

HUME_API_KEY    = os.getenv("HUME_API_KEY", "")
HUME_SECRET_KEY = os.getenv("HUME_SECRET_KEY", "")
HUME_BASE_URL   = "https://api.hume.ai/v0/batch"


def _auth_header() -> dict:
    """Bearer token using API key directly."""
    return {"X-Hume-Api-Key": HUME_API_KEY}


@router.post("/analyze-prosody")
async def analyze_prosody(file: UploadFile = File(...)):
    """
    Receive an audio file, submit to Hume batch API for speech prosody analysis,
    poll until complete, and return top emotions.
    """
    if not HUME_API_KEY or not HUME_SECRET_KEY:
        raise HTTPException(status_code=500, detail="Hume credentials not configured.")

    audio_bytes = await file.read()

    async with httpx.AsyncClient(timeout=60) as client:
        # 1. Submit job
        submit_resp = await client.post(
            f"{HUME_BASE_URL}/jobs",
            headers=_auth_header(),
            files={"file": (file.filename or "audio.webm", audio_bytes, file.content_type or "audio/webm")},
            data={"json": '{"models": {"prosody": {}}}'},
        )
        if submit_resp.status_code not in (200, 201):
            raise HTTPException(status_code=502, detail=f"Hume submit failed: {submit_resp.text}")

        job_id = submit_resp.json().get("job_id")
        if not job_id:
            raise HTTPException(status_code=502, detail="No job_id returned from Hume.")

        # 2. Poll for completion (max ~30s)
        import asyncio
        for _ in range(15):
            await asyncio.sleep(2)
            status_resp = await client.get(
                f"{HUME_BASE_URL}/jobs/{job_id}",
                headers=_auth_header(),
            )
            if status_resp.status_code != 200:
                continue
            state = status_resp.json().get("state", {}).get("status", "")
            if state == "COMPLETED":
                break
            if state == "FAILED":
                raise HTTPException(status_code=502, detail="Hume job failed.")

        # 3. Fetch predictions
        pred_resp = await client.get(
            f"{HUME_BASE_URL}/jobs/{job_id}/predictions",
            headers=_auth_header(),
        )
        if pred_resp.status_code != 200:
            raise HTTPException(status_code=502, detail="Failed to fetch Hume predictions.")

        predictions = pred_resp.json()

    # 4. Parse prosody emotions
    emotions: list = []
    try:
        for item in predictions:
            results = item.get("results", {})
            for pred in results.get("predictions", []):
                for model_pred in pred.get("models", {}).get("prosody", {}).get("grouped_predictions", []):
                    for segment in model_pred.get("predictions", []):
                        emotions = segment.get("emotions", [])
                        if emotions:
                            break
                    if emotions:
                        break
                if emotions:
                    break
    except Exception:
        pass

    top_emotions = sorted(emotions, key=lambda e: e.get("score", 0), reverse=True)[:10]
    return {"prosody": top_emotions}
