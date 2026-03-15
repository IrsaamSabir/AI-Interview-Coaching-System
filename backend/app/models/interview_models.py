# backend/app/models/interview_models.py

from pydantic import BaseModel
from typing import List

class InterviewStartRequest(BaseModel):
    domain: str
    skills: List[str]

class InterviewAnswerRequest(BaseModel):
    question: str
    answer: str

class InterviewScore(BaseModel):
    technical: float
    depth: float
    clarity: float
    overall: float

class InterviewReport(BaseModel):
    summary: str
    strengths: str
    weaknesses: str
    recommendation: str 