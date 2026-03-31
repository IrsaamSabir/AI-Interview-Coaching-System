from fastapi import APIRouter, UploadFile, File
import shutil
import traceback
from app.services.cv_service import analyze_cv
router = APIRouter()

@router.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    path = f"uploads/{file.filename}"
    with open(path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return analyze_cv(path)
