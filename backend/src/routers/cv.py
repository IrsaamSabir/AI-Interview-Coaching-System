import os
import shutil
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.cv_service import analyze_cv
from src.database.session import get_db
from src.models.cv_upload import CVUpload
from src.schemas.cv_schemas import CVAnalyzeResponse

router = APIRouter()

_UPLOADS_DIR = Path("uploads")


@router.post("/analyze", response_model=CVAnalyzeResponse)
async def analyze(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    _UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    path = _UPLOADS_DIR / file.filename

    with open(path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        result = analyze_cv(str(path))

        # Save CV record to database
        cv_record = CVUpload(
            filename=file.filename,
            domain=result["domain"],
            skills=result["skills"],
            education=result.get("education"),
            years_experience=result.get("years_experience"),
            total_experience_months=result.get("total_experience_months"),
            jobs=result.get("jobs"),
        )
        db.add(cv_record)
        await db.flush()  # get the generated id before commit

        return CVAnalyzeResponse(
            cv_id=cv_record.id,
            filename=file.filename,
            domain=result["domain"],
            skills=result["skills"],
            education=result.get("education"),
            years_experience=result.get("years_experience"),
            total_experience_months=result.get("total_experience_months"),
            jobs=result.get("jobs"),
            message=result["message"],
        )

    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="An unexpected error occurred while processing the document.")
    finally:
        if path.exists():
            os.remove(path)
