"""Screening service combining all components"""
from typing import List, BinaryIO
from ..models import ScreeningResult, ResumeData
from ..utils import preprocess_text, extract_text_from_pdf, decode_file, get_logger
from .embedding_service import EmbeddingService
from .resume_parser import ResumeParserService


logger = get_logger(__name__)


class ScreeningService:
    """Main service for resume screening"""
    
    def __init__(self):
        """Initialize screening service with required components"""
        self.embedding_service = EmbeddingService()
        self.parser_service = ResumeParserService()
        logger.info("ScreeningService initialized")
    
    def process_document(self, file: BinaryIO, file_type: str) -> str:
        """
        Process uploaded document and extract text
        
        Args:
            file: File object
            file_type: MIME type of the file
            
        Returns:
            Extracted text content
        """
        if file_type == "application/pdf":
            return extract_text_from_pdf(file)
        else:
            return decode_file(file)
    
    def screen_resume(
        self, 
        resume_file: BinaryIO,
        resume_filename: str,
        resume_type: str,
        jd_text: str,
        jd_embedding
    ) -> ScreeningResult:
        """
        Screen a single resume against job description
        
        Args:
            resume_file: Resume file object
            resume_filename: Name of the resume file
            resume_type: MIME type of resume
            jd_text: Preprocessed job description text
            jd_embedding: Precomputed JD embedding
            
        Returns:
            ScreeningResult object
        """
        # Extract and preprocess resume text
        resume_text = self.process_document(resume_file, resume_type)
        processed_resume = preprocess_text(resume_text)
        
        # Calculate similarity
        resume_embedding = self.embedding_service.get_embeddings(processed_resume)
        similarity_score = self.embedding_service.calculate_similarity(
            jd_embedding, 
            resume_embedding
        )
        
        # Parse resume
        resume_data = self.parser_service.parse_resume(processed_resume)
        
        if not resume_data:
            logger.warning(f"Failed to parse resume: {resume_filename}")
            resume_data = ResumeData()  # Use default values
        
        # Create screening result
        result = ScreeningResult(
            resume_filename=resume_filename,
            similarity_score=similarity_score,
            full_name=resume_data.full_name,
            university_name=resume_data.university_name,
            national_or_international=resume_data.national_or_international,
            email_id=resume_data.email_id,
            github_link=resume_data.github_link,
            company_names=resume_data.get_company_names(),
            technical_skills=resume_data.technical_skills,
            soft_skills=resume_data.soft_skills,
            total_experience=resume_data.total_professional_experience,
            location=resume_data.location
        )
        
        logger.info(f"Screened resume: {resume_filename} - Score: {similarity_score:.4f}")
        return result
    
    def screen_multiple_resumes(
        self,
        resume_files: List[tuple],
        jd_file: BinaryIO,
        jd_type: str
    ) -> List[ScreeningResult]:
        """
        Screen multiple resumes against a job description
        
        Args:
            resume_files: List of (file, filename, type) tuples
            jd_file: Job description file
            jd_type: MIME type of JD
            
        Returns:
            List of ScreeningResult objects sorted by similarity
        """
        # Process job description
        jd_text = self.process_document(jd_file, jd_type)
        processed_jd = preprocess_text(jd_text)
        jd_embedding = self.embedding_service.get_embeddings(processed_jd)
        
        logger.info(f"Screening {len(resume_files)} resumes")
        
        # Process each resume
        results = []
        for resume_file, filename, file_type in resume_files:
            try:
                result = self.screen_resume(
                    resume_file, 
                    filename, 
                    file_type,
                    processed_jd,
                    jd_embedding
                )
                results.append(result)
            except Exception as e:
                logger.error(f"Error screening {filename}: {str(e)}")
                continue
        
        # Sort by similarity score
        results.sort(key=lambda x: x.similarity_score, reverse=True)
        
        logger.info(f"Successfully screened {len(results)} resumes")
        return results
