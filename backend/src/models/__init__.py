# Re-export all ORM models so that:
#   - `from src.models import CVUpload` works anywhere
#   - Alembic autogenerate discovers every table via Base.metadata

from src.models.cv_upload import CVUpload
from src.models.interview_session import InterviewSessionDB
from src.models.interview_answer import InterviewAnswer
from src.models.interview_report import InterviewReport

__all__ = [
    "CVUpload",
    "InterviewSessionDB",
    "InterviewAnswer",
    "InterviewReport",
]
