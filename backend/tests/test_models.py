"""Tests for domain models (src/models.py)."""
import pytest
from src.models import ResumeData, EmploymentDetail, ScreeningResult


# ---------------------------------------------------------------------------
# EmploymentDetail
# ---------------------------------------------------------------------------

def test_employment_detail_creation():
    """EmploymentDetail stores basic fields correctly."""
    detail = EmploymentDetail(
        company="Tech Corp",
        position="Software Engineer",
        start_date="01/2020",
        end_date="12/2022",
        location="San Francisco",
        tags="industry",
    )
    assert detail.company == "Tech Corp"
    assert detail.position == "Software Engineer"
    assert detail.location == "San Francisco"
    assert detail.tags == "industry"


def test_employment_detail_duration_years():
    """duration_years is computed from start/end dates."""
    detail = EmploymentDetail(
        company="Acme",
        start_date="01/2020",
        end_date="01/2022",
    )
    # 2 full years ± rounding
    assert abs(detail.duration_years - 2.0) < 0.2


def test_employment_detail_present_end_date():
    """'Present' end date is treated as today — duration must be > 0."""
    detail = EmploymentDetail(
        company="CurrentJob",
        start_date="01/2023",
        end_date="Present",
    )
    assert detail.duration_years > 0


def test_employment_detail_defaults():
    """Fields default to N/A / industry when not supplied."""
    detail = EmploymentDetail()
    assert detail.company == "N/A"
    assert detail.position == "N/A"
    assert detail.tags == "industry"


# ---------------------------------------------------------------------------
# ResumeData
# ---------------------------------------------------------------------------

def test_resume_data_defaults():
    """ResumeData starts with safe N/A defaults and empty lists."""
    resume = ResumeData()
    assert resume.full_name == "N/A"
    assert resume.email_id == "N/A"
    assert resume.employment_details == []
    assert resume.technical_skills == []
    assert resume.soft_skills == []
    assert resume.phone_number == "N/A"


def test_resume_data_get_company_names():
    """get_company_names returns names from employment_details."""
    employment = [
        EmploymentDetail(company="Company A", position="Dev"),
        EmploymentDetail(company="Company B", position="Engineer"),
    ]
    resume = ResumeData(employment_details=employment)
    companies = resume.get_company_names()
    assert len(companies) == 2
    assert "Company A" in companies
    assert "Company B" in companies


def test_resume_data_empty_companies():
    """get_company_names returns an empty list when there's no employment."""
    resume = ResumeData()
    assert resume.get_company_names() == []


def test_resume_data_skips_na_company():
    """get_company_names excludes entries whose company is 'N/A'."""
    employment = [
        EmploymentDetail(company="RealCorp"),
        EmploymentDetail(company="N/A"),
    ]
    resume = ResumeData(employment_details=employment)
    assert resume.get_company_names() == ["RealCorp"]


def test_resume_data_total_professional_experience():
    """total_professional_experience sums only non-internship roles."""
    employment = [
        EmploymentDetail(company="Corp", start_date="01/2020", end_date="01/2022", tags="industry"),
        EmploymentDetail(company="Intern", start_date="06/2018", end_date="12/2018", tags="internship"),
    ]
    resume = ResumeData(employment_details=employment)
    exp = resume.total_professional_experience
    # Should be ~2 years (internship excluded)
    assert "yrs" in exp
    assert exp != "Fresh Graduate"


def test_resume_data_fresh_graduate():
    """total_professional_experience returns 'Fresh Graduate' with no industry roles."""
    resume = ResumeData(employment_details=[
        EmploymentDetail(company="Intern Co", start_date="06/2022", end_date="09/2022", tags="internship"),
    ])
    assert resume.total_professional_experience == "Fresh Graduate"


# ---------------------------------------------------------------------------
# ScreeningResult
# ---------------------------------------------------------------------------

def test_screening_result_creation():
    """ScreeningResult can be created with only the required fields."""
    result = ScreeningResult(
        resume_filename="john_doe_cv.pdf",
        similarity_score=0.82,
    )
    assert result.resume_filename == "john_doe_cv.pdf"
    assert result.similarity_score == 0.82
    assert result.full_name == "N/A"
    assert result.skill_gaps == []
    assert result.red_flags == []
    assert result.interview_questions == []


def test_screening_result_full_fields():
    """ScreeningResult stores all provided fields correctly."""
    result = ScreeningResult(
        resume_filename="alice_cv.pdf",
        similarity_score=0.91,
        full_name="Alice Smith",
        email_id="alice@example.com",
        technical_skills=["Python", "Docker"],
        total_experience="3.0 yrs",
        analysis_depth="deep",
        skill_gaps=["Kubernetes"],
    )
    assert result.full_name == "Alice Smith"
    assert "Python" in result.technical_skills
    assert result.analysis_depth == "deep"
    assert result.skill_gaps == ["Kubernetes"]

