"""FastAPI application for REST API"""
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
import io

from ..config import settings
from ..utils import setup_logging, get_logger
from ..database import get_db, init_db
from ..database.repository import ScreeningRepository
from ..services import ScreeningService
from .schemas import (
    ScreeningResultResponse,
    ScreeningBatchResponse,
    HealthResponse
)


# Setup logging
setup_logging(settings.LOG_LEVEL, settings.LOG_FILE, settings.LOGS_DIR)
logger = get_logger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-Powered Resume Screening API"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    init_db()
    logger.info("Application started successfully")


@app.get("/", response_model=HealthResponse)
async def root():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        version=settings.APP_VERSION,
        message=f"Welcome to {settings.APP_NAME} API"
    )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Detailed health check"""
    return HealthResponse(
        status="healthy",
        version=settings.APP_VERSION,
        message="All systems operational"
    )


@app.post("/api/screen", response_model=ScreeningBatchResponse)
async def screen_resumes(
    job_description: UploadFile = File(...),
    resumes: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    """
    Screen multiple resumes against a job description
    
    Args:
        job_description: Job description file (PDF or TXT)
        resumes: List of resume files (PDF or TXT)
        db: Database session
        
    Returns:
        Screening results with similarity scores
    """
    try:
        logger.info(f"Screening {len(resumes)} resumes")
        
        # Initialize screening service
        screening_service = ScreeningService()
        
        # Prepare resume files
        resume_data = []
        for resume in resumes:
            content = await resume.read()
            resume_data.append((
                io.BytesIO(content),
                resume.filename,
                resume.content_type
            ))
            await resume.seek(0)
        
        # Read JD
        jd_content = await job_description.read()
        jd_file = io.BytesIO(jd_content)
        
        # Process screening
        results = screening_service.screen_multiple_resumes(
            resume_data,
            jd_file,
            job_description.content_type
        )
        
        # Save to database
        jd_db = ScreeningRepository.create_or_get_job_description(
            db,
            title=job_description.filename,
            content=jd_content.decode('utf-8', errors='ignore')
        )
        
        for result in results:
            ScreeningRepository.save_screening_result(db, result, jd_db.id)
        
        # Convert to response format
        response_results = [
            ScreeningResultResponse(**result.dict())
            for result in results
        ]
        
        return ScreeningBatchResponse(
            total_resumes=len(results),
            results=response_results,
            message="Screening completed successfully"
        )
    
    except Exception as e:
        logger.error(f"Error in screening: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/results", response_model=List[ScreeningResultResponse])
async def get_results(
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Get recent screening results
    
    Args:
        limit: Maximum number of results to return
        db: Database session
        
    Returns:
        List of screening results
    """
    try:
        results = ScreeningRepository.get_recent_screenings(db, limit=limit)
        
        return [
            ScreeningResultResponse(
                id=r.id,
                resume_filename=r.resume_filename,
                similarity_score=r.similarity_score,
                full_name=r.full_name,
                university_name=r.university_name,
                national_or_international=r.national_or_international,
                email_id=r.email_id,
                github_link=r.github_link,
                company_names=r.company_names,
                technical_skills=r.technical_skills,
                soft_skills=r.soft_skills,
                total_experience=r.total_experience,
                location=r.location,
                screening_date=r.screening_date
            )
            for r in results
        ]
    
    except Exception as e:
        logger.error(f"Error fetching results: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.api.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG
    )
