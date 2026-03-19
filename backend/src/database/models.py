"""Database models using SQLAlchemy"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from .database import Base


class JobDescriptionDB(Base):
    """Job description table"""
    __tablename__ = "job_descriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255))
    content = Column(Text)
    content_hash = Column(String(64), unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    screening_results = relationship("ScreeningResultDB", back_populates="job_description")


class ScreeningResultDB(Base):
    """Screening result table"""
    __tablename__ = "screening_results"
    
    id = Column(Integer, primary_key=True, index=True)
    job_description_id = Column(Integer, ForeignKey("job_descriptions.id"))
    
    # Resume information
    resume_filename = Column(String(255))
    similarity_score = Column(Float)
    
    # Candidate information
    full_name = Column(String(255))
    university_name = Column(String(255))
    national_or_international = Column(String(50))
    email_id = Column(String(255))
    github_link = Column(String(500))
    company_names = Column(JSON)  # Stored as JSON array
    technical_skills = Column(JSON)
    soft_skills = Column(JSON)
    total_experience = Column(String(100))
    location = Column(String(255))
    
    # Metadata
    screening_date = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationship
    job_description = relationship("JobDescriptionDB", back_populates="screening_results")


class UserDB(Base):
    """User accounts table for authentication"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class LLMResponseLogDB(Base):
    """Log table for raw LLM responses — traceability of every parse attempt"""
    __tablename__ = "llm_response_logs"

    id = Column(Integer, primary_key=True, index=True)
    model_used = Column(String(100))
    api_client_index = Column(Integer)
    raw_response = Column(Text)
    prompt_tokens = Column(Integer, nullable=True)
    completion_tokens = Column(Integer, nullable=True)
    parse_success = Column(Boolean, default=False)
    logged_at = Column(DateTime, default=datetime.utcnow, index=True)
