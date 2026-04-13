import uuid
from fastapi import APIRouter, HTTPException

from app.models.interview_models     import (
    InterviewStartRequest, InterviewStartResponse,
    InterviewAnswerRequest, AnswerResponse,
    QuestionResponse, StatusResponse, ReportResponse,
)
from app.services.question_service   import generate_first_question, generate_next_question
from app.services.evaluation_service import evaluate_answer
from app.services.feedback_service   import generate_report
from app.services.interview_service  import InterviewSession, MAX_QUESTIONS
from app.core.session_store          import create_session, get_session

router = APIRouter()


@router.post("/start", response_model=InterviewStartResponse)
def start_interview(request: InterviewStartRequest):
    first_q    = generate_first_question(request.domain, request.skills)
    session    = InterviewSession(domain=request.domain, skills=request.skills)
    session.set_question(first_q)
    session_id = str(uuid.uuid4())
    create_session(session_id, session)
    return InterviewStartResponse(
        session_id    = session_id,
        domain        = request.domain,
        max_questions = MAX_QUESTIONS,
        message       = "Interview started."
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
        is_last         = session.question_count >= MAX_QUESTIONS
    )


@router.post("/answer", response_model=AnswerResponse)
def submit_answer(request: InterviewAnswerRequest):
    session    = _get_or_404(request.session_id)
    if session.current_question is None:
        raise HTTPException(status_code=400, detail="No active question.")
    question   = session.current_question["question"]
    evaluation = evaluate_answer(question, request.answer)
    score      = float(evaluation.get("score", 5))
    feedback   = evaluation.get("feedback", "No feedback available.")

    session.save_answer(answer=request.answer, score=score, feedback=feedback)

    interview_complete = session.is_completed()
    if not interview_complete:
        next_q = generate_next_question(
            domain         = session.domain,
            skills         = session.skills,
            prev_question  = question,
            prev_answer    = request.answer,
            score          = score,
            question_count = session.question_count
        )
        session.set_question(next_q)
    else:
        session.current_question = None

    return AnswerResponse(
        session_id         = request.session_id,
        question           = question,
        answer             = request.answer,
        score              = score,
        feedback           = feedback,
        question_number    = session.answered_count(),
        total_questions    = MAX_QUESTIONS,
        interview_complete = interview_complete
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
        status          = "completed" if session.is_completed() else "in_progress"
    )


@router.get("/report", response_model=ReportResponse)
def get_report(session_id: str):
    session = _get_or_404(session_id)
    if session.answered_count() == 0:
        raise HTTPException(status_code=400, detail="No answers recorded yet.")
    if session.report is None:
        session.report = generate_report(
            domain        = session.domain,
            skills        = session.skills,
            answers       = session.get_transcript(),
            average_score = session.average_score()
        )
    r = session.report
    avg = session.average_score()
    return ReportResponse(
        session_id      = session_id,
        domain          = session.domain,
        stack           = ", ".join(session.skills[:3]) if session.skills else "",
        total_questions = session.answered_count(),
        answered        = session.answered_count(),
        overall_score   = r.get("overall_score", avg),
        average_score   = avg,
        level           = r.get("level", session.level()),
        status          = "completed" if session.is_completed() else "ended_early",
        summary         = r.get("summary", ""),
        strengths       = r.get("strengths", []),
        weaknesses      = r.get("weaknesses", []),
        skill_scores    = r.get("skill_scores", {}),
        recommendation  = r.get("recommendation", ""),
        answers         = session.get_transcript(),
        scores          = session.scores
    )


def _get_or_404(session_id: str) -> InterviewSession:
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")
    return session
