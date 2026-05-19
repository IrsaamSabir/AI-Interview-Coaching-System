from pydantic import BaseModel, Field
from typing import Any
from datetime import datetime


# ── Sub-models ────────────────────────────────────────────────────────────────

class AnswerRecord(BaseModel):
    """A single Q&A entry inside a report transcript."""
    question_number: int
    question:        str
    answer:          str
    score:           float
    feedback:        str
    layer:           str | None = None
    face_metrics:    dict[str, Any] | None = None
    speech_emotions: dict[str, Any] | None = None


# ── Response ──────────────────────────────────────────────────────────────────

class ReportResponse(BaseModel):
    """Returned by GET /interview/report"""
    session_id:       str
    domain:           str
    stack:            str = ""
    total_questions:  int
    answered:         int
    overall_score:    float
    average_score:    float
    level:            str
    status:           str                        # completed | ended_early
    summary:          str
    strengths:        list[str]
    weaknesses:       list[str]
    skill_scores:     dict[str, float]
    recommendation:   str
    answers:          list[dict[str, Any]]       # full transcript
    scores:           list[float]
    coaching_metrics: dict[str, Any] = {}
    coaching_note:    str = "These are guidance indicators, not strict grading."


class ReportRecord(BaseModel):
    """Full DB record — used when fetching a saved report by session_id."""
    id:               int
    session_id:       str
    overall_score:    float | None
    level:            str | None
    summary:          str | None
    strengths:        list[str] | None
    weaknesses:       list[str] | None
    skill_scores:     dict[str, float] | None
    recommendation:   str | None
    coaching_metrics: dict[str, Any] | None
    report_data:      dict[str, Any] | None      # full raw report dict
    created_at:       datetime

    model_config = {"from_attributes": True}
