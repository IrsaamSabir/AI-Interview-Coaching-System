from pydantic import BaseModel
from typing import List, Dict


class InterviewStartRequest(BaseModel):
    domain: str
    skills: List[str]


class InterviewAnswerRequest(BaseModel):
    session_id: str
    answer: str


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


class ReportResponse(BaseModel):
    session_id: str
    domain: str
    stack: str = ""
    total_questions: int
    answered: int
    overall_score: float
    average_score: float
    level: str
    status: str
    summary: str
    strengths: List[str]
    weaknesses: List[str]
    skill_scores: Dict[str, float]
    recommendation: str
    answers: List[dict]
    scores: List[float]
