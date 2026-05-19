from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from src.database.connection import Base


class InterviewSessionDB(Base):
    __tablename__ = "interview_sessions"

    id            = Column(String(36), primary_key=True, index=True)   # UUID string
    cv_upload_id  = Column(Integer, ForeignKey("cv_uploads.id"), nullable=True)
    domain        = Column(String(255), nullable=False)
    started_at    = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    completed_at  = Column(DateTime(timezone=True), nullable=True)
    average_score = Column(Float, nullable=True)
    status        = Column(String(50), default="in_progress")          # in_progress | completed | ended_early

    cv_upload = relationship("CVUpload", back_populates="sessions")
    answers   = relationship("InterviewAnswer", back_populates="session", cascade="all, delete-orphan")
    report    = relationship("InterviewReport", back_populates="session", uselist=False, cascade="all, delete-orphan")
