from fastapi import APIRouter, UploadFile, File, HTTPException
import shutil
import traceback
from app.services.cv_service import analyze_cv

router = APIRouter()

@router.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    path = f"uploads/{file.filename}"
    with open(path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        return analyze_cv(path)
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="An unexpected error occurred while processing the document.")
