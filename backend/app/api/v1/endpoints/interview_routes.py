import uuid
from fastapi import APIRouter, HTTPException

from app.models.interview_models import (
    InterviewStartRequest,
    InterviewStartResponse,
    InterviewAnswerRequest,
    AnswerResponse,
    QuestionResponse,
    StatusResponse,
    ReportResponse,
)
from app.services.stack_service          import detect_stack
from app.services.skill_scoring_service  import score_skills
from app.services.question_service       import generate_multi_layer_questions
from app.services.evaluation_service     import evaluate_answer
from app.services.feedback_service       import generate_report
from app.services.interview_service      import InterviewSession
from app.core.session_store              import create_session, get_session

router = APIRouter()


# ------------------------------------------------------
# 1. START  -  create a new interview session
# POST /interview/start
# Body   : { domain, skills }
# Returns: session_id, stack, total_questions
# ------------------------------------------------------
@router.post("/start", response_model=InterviewStartResponse)
def start_interview(request: InterviewStartRequest):

    domain = request.domain
    skills = request.skills

    stack      = detect_stack(domain, skills)
    scored     = score_skills(skills, domain)
    top_skills = [s["skill"] for s in scored[:3]]

    questions = generate_multi_layer_questions(stack, top_skills)

    if not questions:
        raise HTTPException(
            status_code=500,
            detail="Failed to generate questions. Make sure Ollama is running."
        )

    session_id = str(uuid.uuid4())
    # Pass skills so report can reference them later
    session    = InterviewSession(
        questions = questions,
        domain    = domain,
        stack     = stack,
        skills    = skills
    )
    create_session(session_id, session)

    return InterviewStartResponse(
        session_id      = session_id,
        domain          = domain,
        stack           = stack,
        total_questions = len(questions),
        message         = f"Interview started. {len(questions)} questions ready."
    )


# ------------------------------------------------------
# 2. QUESTION  -  get the current question
# GET /interview/question?session_id=...
# ------------------------------------------------------
@router.get("/question", response_model=QuestionResponse)
def get_question(session_id: str):

    session = _get_or_404(session_id)

    if session.is_completed():
        raise HTTPException(
            status_code=400,
            detail="Interview complete. Call GET /report to see your results."
        )

    q_obj = session.current_question()
    if not q_obj:
        raise HTTPException(status_code=400, detail="No more questions available.")

    number = session.answered_count() + 1
    total  = len(session.questions)

    return QuestionResponse(
        session_id      = session_id,
        question_number = number,
        total_questions = total,
        question        = q_obj["question"],
        is_last         = (number == total)
    )


# ------------------------------------------------------
# 3. ANSWER  -  submit answer for current question
# POST /interview/answer
# Body: { session_id, answer }
# ------------------------------------------------------
@router.post("/answer", response_model=AnswerResponse)
def submit_answer(request: InterviewAnswerRequest):

    session = _get_or_404(request.session_id)

    if session.is_completed():
        raise HTTPException(status_code=400, detail="Interview already completed.")

    q_obj    = session.current_question()
    question = q_obj["question"]

    evaluation = evaluate_answer(question, request.answer)
    score      = float(evaluation.get("score", 5))
    feedback   = evaluation.get("feedback", "No feedback available.")

    session.save_answer(
        question = question,
        answer   = request.answer,
        score    = score,
        feedback = feedback
    )
    session.advance()

    number = session.answered_count()
    total  = len(session.questions)

    return AnswerResponse(
        session_id         = request.session_id,
        question           = question,
        answer             = request.answer,
        score              = score,
        feedback           = feedback,
        question_number    = number,
        total_questions    = total,
        interview_complete = session.is_completed()
    )


# ------------------------------------------------------
# 4. STATUS  -  check progress mid-interview
# GET /interview/status?session_id=...
# ------------------------------------------------------
@router.get("/status", response_model=StatusResponse)
def get_status(session_id: str):

    session = _get_or_404(session_id)

    return StatusResponse(
        session_id      = session_id,
        domain          = session.domain,
        stack           = session.stack,
        total_questions = len(session.questions),
        answered        = session.answered_count(),
        remaining       = session.remaining_count(),
        average_score   = session.average_score(),
        status          = "completed" if session.is_completed() else "in_progress"
    )


# ------------------------------------------------------
# 5. REPORT  -  full LLM-generated report after completion
# GET /interview/report?session_id=...
# ------------------------------------------------------
@router.get("/report", response_model=ReportResponse)
def get_report(session_id: str):

    session = _get_or_404(session_id)

    if not session.is_completed():
        answered  = session.answered_count()
        total     = len(session.questions)
        raise HTTPException(
            status_code=400,
            detail=f"Interview not yet complete - {answered}/{total} questions answered."
        )

    # Use cached report if already generated (avoid calling phi3 twice)
    if session.report is None:
        session.report = generate_report(
            domain        = session.domain,
            stack         = session.stack,
            skills        = session.skills,
            answers       = session.get_transcript(),
            average_score = session.average_score()
        )

    r = session.report

    return ReportResponse(
        session_id      = session_id,
        domain          = session.domain,
        stack           = session.stack,
        total_questions = len(session.questions),
        answered        = session.answered_count(),
        average_score   = session.average_score(),
        level           = r.get("level", session.level()),
        status          = "completed",
        summary         = r.get("summary", ""),
        strengths       = r.get("strengths", []),
        weaknesses      = r.get("weaknesses", []),
        skill_scores    = r.get("skill_scores", {}),
        recommendation  = r.get("recommendation", ""),
        answers         = session.get_transcript(),
        scores          = session.scores
    )


# ------------------------------------------------------
# Helper  -  get session or raise 404
# ------------------------------------------------------
def _get_or_404(session_id: str) -> InterviewSession:
    session = get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=404,
            detail=f"Session '{session_id}' not found. Start a new interview first."
        )
    return session