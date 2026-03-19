"""Tests for data models"""
import pytest
from src.models.resume import ResumeData, EmploymentDetail


def test_employment_detail_creation():
    """Test EmploymentDetail model"""
    detail = EmploymentDetail(
        company="Tech Corp",
        position="Software Engineer",
        years_of_experience=3.0,
        location="San Francisco",
        tags="industry"
    )
    
    assert detail.company == "Tech Corp"
    assert detail.position == "Software Engineer"
    assert detail.years_of_experience == 3.0


def test_resume_data_defaults():
    """Test ResumeData with default values"""
    resume = ResumeData()
    
    assert resume.full_name == "N/A"
    assert resume.email_id == "N/A"
    assert resume.employment_details == []
    assert resume.technical_skills == []


def test_resume_data_get_company_names():
    """Test extracting company names"""
    employment = [
        EmploymentDetail(company="Company A", position="Dev"),
        EmploymentDetail(company="Company B", position="Engineer")
    ]
    
    resume = ResumeData(employment_details=employment)
    companies = resume.get_company_names()
    
    assert len(companies) == 2
    assert "Company A" in companies
    assert "Company B" in companies


def test_resume_data_empty_companies():
    """Test company names with no employment"""
    resume = ResumeData()
    companies = resume.get_company_names()
    
    assert companies == ["N/A"]
