"""
CRUD helpers — all raw DB operations live here.
Routers and services stay free of SQLAlchemy imports.
"""
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.interview_session import InterviewSessionDB
from src.models.interview_answer  import InterviewAnswer
from src.models.interview_report  import InterviewReport


# ── Session ───────────────────────────────────────────────────────────────────

async def create_interview_session(
    db:           AsyncSession,
    session_id:   str,
    domain:       str,
    cv_upload_id: int | None = None,
) -> InterviewSessionDB:
    record = InterviewSessionDB(
        id           = session_id,
        domain       = domain,
        cv_upload_id = cv_upload_id,
        status       = "in_progress",
    )
    db.add(record)
    await db.flush()
    return record


async def get_interview_session(
    db: AsyncSession, session_id: str
) -> InterviewSessionDB | None:
    result = await db.execute(
        select(InterviewSessionDB).where(InterviewSessionDB.id == session_id)
    )
    return result.scalar_one_or_none()


async def complete_interview_session(
    db:            AsyncSession,
    session_id:    str,
    average_score: float,
    status:        str = "completed",
) -> None:
    record = await get_interview_session(db, session_id)
    if record:
        record.average_score = average_score
        record.completed_at  = datetime.now(timezone.utc)
        record.status        = status
        await db.flush()


# ── Answer ────────────────────────────────────────────────────────────────────

async def save_interview_answer(
    db:              AsyncSession,
    session_id:      str,
    question_number: int,
    question_text:   str,
    answer_text:     str,
    score:           float,
    feedback:        str,
    layer:           str | None        = None,
    face_metrics:    dict | None       = None,
    speech_emotions: dict | None       = None,
) -> InterviewAnswer:
    record = InterviewAnswer(
        session_id      = session_id,
        question_number = question_number,
        question_text   = question_text,
        answer_text     = answer_text,
        score           = score,
        feedback        = feedback,
        layer           = layer,
        face_metrics    = face_metrics,
        speech_emotions = speech_emotions,
    )
    db.add(record)
    await db.flush()
    return record


# ── Report ────────────────────────────────────────────────────────────────────

async def save_interview_report(
    db:         AsyncSession,
    session_id: str,
    report:     dict,
) -> InterviewReport:
    record = InterviewReport(
        session_id       = session_id,
        overall_score    = report.get("overall_score"),
        level            = report.get("level"),
        summary          = report.get("summary"),
        strengths        = report.get("strengths"),
        weaknesses       = report.get("weaknesses"),
        skill_scores     = report.get("skill_scores"),
        recommendation   = report.get("recommendation"),
        coaching_metrics = report.get("coaching_metrics"),
        report_data      = report,                          # full raw dict
    )
    db.add(record)
    await db.flush()
    return record


async def get_interview_report(
    db: AsyncSession, session_id: str
) -> InterviewReport | None:
    result = await db.execute(
        select(InterviewReport).where(InterviewReport.session_id == session_id)
    )
    return result.scalar_one_or_none()
