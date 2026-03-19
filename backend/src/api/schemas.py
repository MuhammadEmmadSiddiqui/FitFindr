"""Pydantic schemas for API requests/responses"""
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    message: str


class ScreeningResultResponse(BaseModel):
    """Screening result response"""
    id: Optional[int] = None
    resume_filename: str
    similarity_score: float
    full_name: Optional[str] = "N/A"
    university_name: Optional[str] = "N/A"
    national_or_international: Optional[str] = "N/A"
    email_id: Optional[str] = "N/A"
    github_link: Optional[str] = "N/A"
    phone_number: Optional[str] = "N/A"
    company_names: List[str] = []
    technical_skills: List[str] = []
    soft_skills: List[str] = []
    total_experience: Optional[str] = "N/A"
    location: Optional[str] = "N/A"
    screening_date: Optional[datetime] = None
    # ── LangGraph pipeline fields ──────────────────────────────────────────────
    analysis_depth: str = "standard"
    jd_domain: str = "N/A"
    jd_seniority: str = "N/A"
    skill_gaps: List[str] = []
    red_flags: List[str] = []
    interview_questions: List[str] = []
    overall_recommendation: str = "N/A"

    class Config:
        from_attributes = True


class ScreeningBatchResponse(BaseModel):
    """Batch screening response"""
    total_resumes: int
    results: List[ScreeningResultResponse]
    message: str
