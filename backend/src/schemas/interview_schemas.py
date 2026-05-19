from pydantic import BaseModel
from typing import List, Dict, Any, Optional


class InterviewStartRequest(BaseModel):
    domain: str
    skills: List[str]
    priority_skills: List[str] = []
    years_experience: Optional[str] = None
    total_experience_months: Optional[int] = None
    jobs: Optional[List[Dict[str, Any]]] = None
    cv_upload_id: Optional[int] = None          # links session to a saved CV


class InterviewAnswerRequest(BaseModel):
    session_id: str
    answer: str
    coaching_metrics: Dict[str, Any] | None = None


class InterviewStartResponse(BaseModel):
    session_id: str
    domain: str
    max_questions: int
    message: str


class QuestionResponse(BaseModel):
    session_id: str
    question_number: int
    total_questions: int
    question: str
    layer: str
    is_last: bool


class AnswerResponse(BaseModel):
    session_id: str
    question: str
    answer: str
    score: float
    feedback: str
    question_number: int
    total_questions: int
    interview_complete: bool


class StatusResponse(BaseModel):
    session_id: str
    domain: str
    total_questions: int
    answered: int
    remaining: int
    average_score: float
    status: str
