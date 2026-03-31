from pydantic import BaseModel
from typing import List, Optional, Dict


# -- Requests -------------------------------------------

class InterviewStartRequest(BaseModel):
    domain: str
    skills: List[str]


class InterviewAnswerRequest(BaseModel):
    session_id: str
    answer: str


# -- Responses ------------------------------------------

class InterviewStartResponse(BaseModel):
    session_id: str
    domain: str
    stack: str
    total_questions: int
    message: str


class QuestionResponse(BaseModel):
    session_id: str
    question_number: int
    total_questions: int
    question: str
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
    stack: str
    total_questions: int
    answered: int
    remaining: int
    average_score: float
    status: str                  # "in_progress" | "completed"


# -- Rich final report ----------------------------------

class ReportResponse(BaseModel):
    session_id:     str
    domain:         str
    stack:          str
    total_questions: int
    answered:       int
    average_score:  float
    level:          str          # Beginner | Intermediate | Advanced | Expert
    status:         str
    # LLM-generated fields
    summary:        str
    strengths:      List[str]
    weaknesses:     List[str]
    skill_scores:   Dict[str, float]
    recommendation: str
    # Full transcript
    answers:        List[dict]
    scores:         List[float]