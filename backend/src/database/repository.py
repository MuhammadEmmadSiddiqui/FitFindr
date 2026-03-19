"""Repository for database operations"""
import hashlib
from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime
from .models import ScreeningResultDB, JobDescriptionDB, LLMResponseLogDB, UserDB
from ..models import ScreeningResult
from ..utils import get_logger


logger = get_logger(__name__)


class ScreeningRepository:
    """Repository for screening results operations"""
    
    @staticmethod
    def create_or_get_job_description(
        db: Session, 
        title: str, 
        content: str
    ) -> JobDescriptionDB:
        """
        Create or retrieve existing job description
        
        Args:
            db: Database session
            title: Job title
            content: Job description content
            
        Returns:
            JobDescriptionDB object
        """
        # Create hash of content
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        
        # Check if exists
        jd = db.query(JobDescriptionDB).filter(
            JobDescriptionDB.content_hash == content_hash
        ).first()
        
        if jd:
            logger.info(f"Found existing job description: {jd.id}")
            return jd
        
        # Create new
        jd = JobDescriptionDB(
            title=title,
            content=content,
            content_hash=content_hash
        )
        db.add(jd)
        db.commit()
        db.refresh(jd)
        
        logger.info(f"Created new job description: {jd.id}")
        return jd
    
    @staticmethod
    def save_screening_result(
        db: Session,
        result: ScreeningResult,
        job_description_id: int
    ) -> ScreeningResultDB:
        """
        Save screening result to database
        
        Args:
            db: Database session
            result: ScreeningResult object
            job_description_id: Foreign key to job description
            
        Returns:
            Saved ScreeningResultDB object
        """
        db_result = ScreeningResultDB(
            job_description_id=job_description_id,
            resume_filename=result.resume_filename,
            similarity_score=result.similarity_score,
            full_name=result.full_name,
            university_name=result.university_name,
            national_or_international=result.national_or_international,
            email_id=result.email_id,
            github_link=result.github_link,
            company_names=result.company_names,
            technical_skills=result.technical_skills,
            soft_skills=result.soft_skills,
            total_experience=result.total_experience,
            location=result.location
        )
        
        db.add(db_result)
        db.commit()
        db.refresh(db_result)
        
        return db_result
    
    @staticmethod
    def get_screening_results(
        db: Session,
        job_description_id: Optional[int] = None,
        limit: int = 100
    ) -> List[ScreeningResultDB]:
        """
        Retrieve screening results
        
        Args:
            db: Database session
            job_description_id: Filter by job description
            limit: Maximum results to return
            
        Returns:
            List of ScreeningResultDB objects
        """
        query = db.query(ScreeningResultDB)
        
        if job_description_id:
            query = query.filter(
                ScreeningResultDB.job_description_id == job_description_id
            )
        
        results = query.order_by(
            ScreeningResultDB.similarity_score.desc()
        ).limit(limit).all()
        
        return results
    
    @staticmethod
    def get_recent_screenings(
        db: Session,
        days: int = 7,
        limit: int = 50
    ) -> List[ScreeningResultDB]:
        """
        Get recent screening results
        
        Args:
            db: Database session
            days: Number of days to look back
            limit: Maximum results
            
        Returns:
            List of recent screening results
        """
        from datetime import timedelta
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        results = db.query(ScreeningResultDB).filter(
            ScreeningResultDB.screening_date >= cutoff_date
        ).order_by(
            ScreeningResultDB.screening_date.desc()
        ).limit(limit).all()
        
        return results


class LLMLogRepository:
    """Repository for LLM response log operations"""

    @staticmethod
    def log_response(
        db: Session,
        model_used: str,
        api_client_index: int,
        raw_response: str,
        prompt_tokens: Optional[int],
        completion_tokens: Optional[int],
        parse_success: bool
    ) -> LLMResponseLogDB:
        """
        Persist a raw LLM response for traceability.

        Args:
            db: Database session
            model_used: Name of the LLM model
            api_client_index: 1-based index of the Groq client used
            raw_response: Raw JSON string returned by the model
            prompt_tokens: Token count for the prompt (may be None)
            completion_tokens: Token count for the completion (may be None)
            parse_success: Whether the response was successfully parsed

        Returns:
            Saved LLMResponseLogDB object
        """
        log_entry = LLMResponseLogDB(
            model_used=model_used,
            api_client_index=api_client_index,
            raw_response=raw_response,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            parse_success=parse_success
        )
        db.add(log_entry)
        db.commit()
        db.refresh(log_entry)

        logger.info(
            f"LLM response logged [id={log_entry.id}, client={api_client_index}, "
            f"parse_success={parse_success}, tokens={prompt_tokens}+{completion_tokens}]"
        )
        return log_entry


class UserRepository:
    """Repository for user account operations"""

    @staticmethod
    def create_user(db: Session, username: str, email: str, hashed_password: str) -> UserDB:
        """Create a new user account."""
        user = UserDB(username=username, email=email, hashed_password=hashed_password)
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info(f"Created user: {username}")
        return user

    @staticmethod
    def get_by_username(db: Session, username: str) -> Optional[UserDB]:
        """Retrieve a user by username."""
        return db.query(UserDB).filter(UserDB.username == username).first()

    @staticmethod
    def get_by_email(db: Session, email: str) -> Optional[UserDB]:
        """Retrieve a user by email address."""
        return db.query(UserDB).filter(UserDB.email == email).first()
