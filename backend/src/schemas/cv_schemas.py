from pydantic import BaseModel, Field
from typing import Any
from datetime import datetime


# ── Sub-models ────────────────────────────────────────────────────────────────

class JobEntry(BaseModel):
    company: str
    start: str                          # MM/YYYY
    end: str | None = None              # MM/YYYY or null (ongoing)


# ── Request ───────────────────────────────────────────────────────────────────

# CV upload is multipart/form-data (UploadFile), no JSON request body needed.


# ── Responses ─────────────────────────────────────────────────────────────────

class CVAnalyzeResponse(BaseModel):
    """Returned after a successful CV upload and analysis."""
    cv_id:                   int
    filename:                str
    domain:                  str
    skills:                  list[str]
    education:               str | None
    years_experience:        str | None
    total_experience_months: int | None
    jobs:                    list[JobEntry] | None
    message:                 str

    model_config = {"from_attributes": True}


class CVUploadRecord(BaseModel):
    """Full DB record — used when fetching a saved CV by id."""
    id:                      int
    filename:                str
    domain:                  str
    skills:                  list[str]
    education:               str | None
    years_experience:        str | None
    total_experience_months: int | None
    jobs:                    list[dict[str, Any]] | None
    created_at:              datetime

    model_config = {"from_attributes": True}
