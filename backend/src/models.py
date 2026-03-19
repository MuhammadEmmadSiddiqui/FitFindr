"""Pydantic domain models for FitFindr"""
from datetime import datetime
from typing import List, Optional
from dateutil import parser as dateparser
from dateutil.relativedelta import relativedelta
from pydantic import BaseModel, Field, computed_field


class EmploymentDetail(BaseModel):
    """Single employment record extracted from a resume"""
    company: str = Field(default="N/A", description="Company or organisation name")
    position: str = Field(default="N/A", description="Job title / role")
    start_date: str = Field(
        default="N/A",
        description="Start date of the role, e.g. '07/2023' or 'May 2024'"
    )
    end_date: str = Field(
        default="Present",
        description="End date of the role, e.g. '12/2024' or 'Present'"
    )
    location: str = Field(default="N/A", description="City / country of the role")
    tags: str = Field(
        default="industry",
        description="One of: teaching | industry | internship"
    )

    @computed_field
    @property
    def duration_years(self) -> float:
        """Programmatically calculate the duration of the role in years."""
        try:
            start = dateparser.parse(self.start_date, default=datetime(2000, 1, 1))
            end = (
                datetime.utcnow()
                if self.end_date.strip().lower() in ("present", "current", "now", "n/a", "")
                else dateparser.parse(self.end_date, default=datetime(2000, 1, 1))
            )
            delta = relativedelta(end, start)
            return round(delta.years + delta.months / 12, 1)
        except Exception:
            return 0.0

    @property
    def years_of_experience(self) -> str:
        """Human-readable duration string, e.g. '1.5 yrs  (07/2023 – 12/2024)'"""
        return f"{self.duration_years} yrs  ({self.start_date} – {self.end_date})"


class ResumeData(BaseModel):
    """Structured data extracted from a resume by the LLM"""
    full_name: str = Field(default="N/A", description="Candidate's full name")
    university_name: str = Field(
        default="N/A",
        description="Most recent degree university — short form preferred"
    )
    national_or_international: str = Field(
        default="N/A",
        alias="national_university/international_university",
        description="'National' if university is inside Pakistan, else 'International'"
    )
    email_id: str = Field(default="N/A", description="Email address or 'N/A'")
    github_link: str = Field(default="N/A", description="GitHub profile URL or 'N/A'")
    phone_number: str = Field(default="N/A", description="Phone or mobile number or 'N/A'")
    employment_details: List[EmploymentDetail] = Field(
        default_factory=list,
        description="List of employment / internship records"
    )
    technical_skills: List[str] = Field(
        default_factory=list, description="List of technical skills"
    )
    soft_skills: List[str] = Field(
        default_factory=list, description="List of soft skills"
    )
    location: str = Field(default="N/A", description="Current location of the candidate")

    model_config = {"populate_by_name": True}

    @computed_field
    @property
    def total_professional_experience(self) -> str:
        """
        Sum duration_years for all roles where tags != 'internship'.
        Returns a human-readable string, e.g. '1.4 yrs' or 'Fresh Graduate'.
        """
        total = sum(
            emp.duration_years
            for emp in self.employment_details
            if emp.tags.strip().lower() != "internship"
        )
        if total == 0.0:
            return "Fresh Graduate"
        return f"{round(total, 1)} yrs"

    def get_company_names(self) -> List[str]:
        """Return a flat list of company names from employment details"""
        return [e.company for e in self.employment_details if e.company != "N/A"]


class ScreeningResult(BaseModel):
    """Final result for a single resume after screening"""
    resume_filename: str
    similarity_score: float
    full_name: str = "N/A"
    university_name: str = "N/A"
    national_or_international: str = "N/A"
    email_id: str = "N/A"
    github_link: str = "N/A"
    phone_number: str = "N/A"
    company_names: List[str] = []
    technical_skills: List[str] = []
    soft_skills: List[str] = []
    total_experience: str = "N/A"
    location: str = "N/A"
    # ── LangGraph pipeline fields ──────────────────────────────────────────────
    analysis_depth: str = "standard"          # "skip" | "standard" | "deep"
    jd_domain: str = "N/A"                    # from JD analysis (feature 3)
    jd_seniority: str = "N/A"                 # from JD analysis (feature 3)
    skill_gaps: List[str] = []                # from deep analysis (feature 1)
    red_flags: List[str] = []                 # from deep analysis (feature 1)
    interview_questions: List[str] = []       # from deep analysis (feature 1)
    overall_recommendation: str = "N/A"       # from deep analysis (feature 1)
