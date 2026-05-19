from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from src.database.connection import Base


class InterviewReport(Base):
    __tablename__ = "interview_reports"

    id               = Column(Integer, primary_key=True, index=True)
    session_id       = Column(String(36), ForeignKey("interview_sessions.id"), nullable=False, unique=True)
    overall_score    = Column(Float, nullable=True)
    level            = Column(String(50), nullable=True)
    summary          = Column(Text, nullable=True)
    strengths        = Column(JSON, nullable=True)                       # list[str]
    weaknesses       = Column(JSON, nullable=True)                       # list[str]
    skill_scores     = Column(JSON, nullable=True)                       # dict[str, float]
    recommendation   = Column(Text, nullable=True)
    coaching_metrics = Column(JSON, nullable=True)
    report_data      = Column(JSON, nullable=True)                       # full raw report dict
    created_at       = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    session = relationship("InterviewSessionDB", back_populates="report")
