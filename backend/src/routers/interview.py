import uuid

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.schemas.interview_schemas import (
    InterviewStartRequest, InterviewStartResponse,
    InterviewAnswerRequest, AnswerResponse,
    QuestionResponse, StatusResponse,
)
from src.schemas.report_schemas import ReportResponse
from src.services.question_service   import generate_first_question, generate_next_question
from src.services.evaluation_service import evaluate_answer
from src.services.feedback_service   import generate_report
from src.services.interview_service  import InterviewSession, MAX_QUESTIONS
from src.services.session_store      import create_session, get_session
from src.database.session            import get_db
from src.database.crud               import (
    create_interview_session,
    save_interview_answer,
    save_interview_report,
    complete_interview_session,
    get_interview_report,
)

router = APIRouter()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _normalize_skill_list(values: list[str] | None) -> list[str]:
    normalized, seen = [], set()
    for value in values or []:
        skill = str(value).strip().lower()
        if skill and skill not in seen:
            normalized.append(skill)
            seen.add(skill)
    return normalized


def _merge_skills(base_skills: list[str], priority_skills: list[str]) -> list[str]:
    merged, seen = list(priority_skills), set(priority_skills)
    for skill in base_skills:
        if skill not in seen:
            merged.append(skill)
            seen.add(skill)
    return merged


def _build_experience_context(
    years_experience: str | None,
    total_months: int | None,
    jobs: list | None,
) -> str:
    lines: list[str] = []
    if total_months is not None and total_months >= 0:
        lines.append(f"Total paid experience: {total_months} months.")
    if years_experience and str(years_experience).strip():
        lines.append(f"Experience summary: {str(years_experience).strip()}.")
    if jobs:
        brief: list[str] = []
        for row in jobs[:8]:
            if not isinstance(row, dict):
                continue
            company = str(row.get("company", "")).strip()
            if not company:
                continue
            start = row.get("start")
            end   = row.get("end")
            brief.append(f"{company} ({start} – {'present' if end is None else end})")
        if brief:
            lines.append("Roles: " + "; ".join(brief) + ".")
    return "\n".join(lines)


def _get_or_404(session_id: str) -> InterviewSession:
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")
    return session


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("/start", response_model=InterviewStartResponse)
async def start_interview(
    request: InterviewStartRequest,
    db: AsyncSession = Depends(get_db),
):
    skills          = _normalize_skill_list(request.skills)
    priority_skills = _normalize_skill_list(request.priority_skills)
    merged_skills   = _merge_skills(skills, priority_skills)

    exp_ctx = _build_experience_context(
        request.years_experience,
        request.total_experience_months,
        request.jobs if isinstance(request.jobs, list) else None,
    )

    first_q = generate_first_question(
        request.domain,
        merged_skills,
        priority_skills,
        experience_context=exp_ctx,
    )

    session = InterviewSession(
        domain             = request.domain,
        skills             = merged_skills,
        priority_skills    = priority_skills,
        experience_context = exp_ctx,
    )
    session.set_question(first_q)

    session_id = str(uuid.uuid4())
    create_session(session_id, session)

    # Persist session to DB
    await create_interview_session(
        db         = db,
        session_id = session_id,
        domain     = request.domain,
        cv_upload_id = getattr(request, "cv_upload_id", None),
    )

    return InterviewStartResponse(
        session_id    = session_id,
        domain        = request.domain,
        max_questions = MAX_QUESTIONS,
        message       = "Interview started.",
    )


@router.get("/question", response_model=QuestionResponse)
def get_question(session_id: str):
    session = _get_or_404(session_id)
    if session.current_question is None:
        raise HTTPException(status_code=400, detail="No question available.")
    return QuestionResponse(
        session_id      = session_id,
        question_number = session.question_count,
        total_questions = MAX_QUESTIONS,
        question        = session.current_question["question"],
        layer           = session.current_question.get("layer", "basic"),
        is_last         = session.question_count >= MAX_QUESTIONS,
    )


@router.post("/answer", response_model=AnswerResponse)
async def submit_answer(
    request: InterviewAnswerRequest,
    db: AsyncSession = Depends(get_db),
):
    session = _get_or_404(request.session_id)
    if session.current_question is None:
        raise HTTPException(status_code=400, detail="No active question.")

    question   = session.current_question["question"]
    layer      = session.current_question.get("layer", "basic")
    evaluation = evaluate_answer(question, request.answer)
    score      = float(evaluation.get("score", 5))
    feedback   = evaluation.get("feedback", "No feedback available.")

    coaching   = request.coaching_metrics or {}
    session.save_answer(
        answer           = request.answer,
        score            = score,
        feedback         = feedback,
        coaching_metrics = coaching,
    )

    # Persist answer to DB
    await save_interview_answer(
        db              = db,
        session_id      = request.session_id,
        question_number = session.answered_count(),
        question_text   = question,
        answer_text     = request.answer,
        score           = score,
        feedback        = feedback,
        layer           = layer,
        face_metrics    = coaching.get("face"),
        speech_emotions = coaching.get("speech"),
    )

    interview_complete = session.is_completed()

    if interview_complete:
        session.current_question = None
        # Mark session complete in DB
        await complete_interview_session(
            db            = db,
            session_id    = request.session_id,
            average_score = session.average_score(),
            status        = "completed",
        )
    else:
        next_q = generate_next_question(
            domain             = session.domain,
            skills             = session.skills,
            priority_skills    = session.priority_skills,
            prev_question      = question,
            prev_answer        = request.answer,
            score              = score,
            question_count     = session.question_count,
            experience_context = session.experience_context,
        )
        session.set_question(next_q)

    return AnswerResponse(
        session_id         = request.session_id,
        question           = question,
        answer             = request.answer,
        score              = score,
        feedback           = feedback,
        question_number    = session.answered_count(),
        total_questions    = MAX_QUESTIONS,
        interview_complete = interview_complete,
    )


@router.get("/status", response_model=StatusResponse)
def get_status(session_id: str):
    session = _get_or_404(session_id)
    return StatusResponse(
        session_id      = session_id,
        domain          = session.domain,
        total_questions = MAX_QUESTIONS,
        answered        = session.answered_count(),
        remaining       = session.remaining_count(),
        average_score   = session.average_score(),
        status          = "completed" if session.is_completed() else "in_progress",
    )


@router.get("/report", response_model=ReportResponse)
async def get_report(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    session = _get_or_404(session_id)
    if session.answered_count() == 0:
        raise HTTPException(status_code=400, detail="No answers recorded yet.")

    # Generate report if not already done
    if session.report is None:
        session.report = generate_report(
            domain        = session.domain,
            skills        = session.skills,
            answers       = session.get_transcript(),
            average_score = session.average_score(),
        )
        # Persist report to DB (only once)
        existing = await get_interview_report(db, session_id)
        if not existing:
            await save_interview_report(
                db         = db,
                session_id = session_id,
                report     = session.report,
            )

    r   = session.report
    avg = session.average_score()

    return ReportResponse(
        session_id       = session_id,
        domain           = session.domain,
        stack            = ", ".join(session.skills[:3]) if session.skills else "",
        total_questions  = session.answered_count(),
        answered         = session.answered_count(),
        overall_score    = r.get("overall_score", avg),
        average_score    = avg,
        level            = r.get("level", session.level()),
        status           = "completed" if session.is_completed() else "ended_early",
        summary          = r.get("summary", ""),
        strengths        = r.get("strengths", []),
        weaknesses       = r.get("weaknesses", []),
        skill_scores     = r.get("skill_scores", {}),
        recommendation   = r.get("recommendation", ""),
        answers          = session.get_transcript(),
        scores           = session.scores,
        coaching_metrics = r.get("coaching_metrics", {}),
        coaching_note    = r.get("coaching_note", "These are guidance indicators, not strict grading."),
    )
