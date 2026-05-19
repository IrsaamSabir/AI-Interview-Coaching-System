from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from src.database.connection import Base


class CVUpload(Base):
    __tablename__ = "cv_uploads"

    id                      = Column(Integer, primary_key=True, index=True)
    filename                = Column(String(255), nullable=False)
    domain                  = Column(String(255), nullable=False)
    skills                  = Column(JSON, nullable=False, default=list)   # list[str]
    education               = Column(Text, nullable=True)
    years_experience        = Column(String(100), nullable=True)
    total_experience_months = Column(Integer, nullable=True)
    jobs                    = Column(JSON, nullable=True)                   # list[dict]
    created_at              = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # one CV → many interview sessions
    sessions = relationship("InterviewSessionDB", back_populates="cv_upload")
