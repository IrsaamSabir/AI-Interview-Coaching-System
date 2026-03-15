# backend/app/api/v1/endpoints/interview_routes.py

from fastapi import APIRouter
from app.models.interview_models import InterviewStartRequest,InterviewAnswerRequest
from app.services.stack_service import detect_stack
from app.services.skill_scoring_service import score_skills
from app.services.question_service import generate_multi_layer_questions
from app.services.evaluation_service import evaluate_answer

router = APIRouter()

@router.post("/start")
def start_interview(request: InterviewStartRequest):

    domain = request.domain
    skills = request.skills

    stack = detect_stack(domain, skills)

    scored = score_skills(skills, domain)

    top_skills = [s["skill"] for s in scored[:3]]

    questions = generate_multi_layer_questions(stack, top_skills)

    return {
        "stack": stack,
        "questions": questions
    }
    

@router.post("/answer")
def submit_answer(request: InterviewAnswerRequest):

    question = request.question
    answer = request.answer

    evaluation = evaluate_answer(question, answer)

    return {
        "question": question,
        "answer": answer,
        "score": evaluation["score"],
        "feedback": evaluation["feedback"]
    }