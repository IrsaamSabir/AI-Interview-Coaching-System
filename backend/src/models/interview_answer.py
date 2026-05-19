from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from src.database.connection import Base


class InterviewAnswer(Base):
    __tablename__ = "interview_answers"

    id              = Column(Integer, primary_key=True, index=True)
    session_id      = Column(String(36), ForeignKey("interview_sessions.id"), nullable=False)
    question_number = Column(Integer, nullable=False)
    question_text   = Column(Text, nullable=False)
    answer_text     = Column(Text, nullable=False)
    score           = Column(Float, nullable=False)
    feedback        = Column(Text, nullable=True)
    layer           = Column(String(50), nullable=True)
    face_metrics    = Column(JSON, nullable=True)
    speech_emotions = Column(JSON, nullable=True)
    answered_at     = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    session = relationship("InterviewSessionDB", back_populates="answers")
