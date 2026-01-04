"""Resume parsing service using Groq API"""
import json
from typing import List, Optional
from groq import Groq
from ..config import settings
from ..models import ResumeData, EmploymentDetail
from ..utils import get_logger


logger = get_logger(__name__)


class ResumeParserService:
    """Service for parsing resumes using LLM"""
    
    INSTRUCTION = """
You are an AI bot designed to parse resumes and extract the following details in below JSON:
1. full_name: 
2. university_name: of most recent degree (return the short form of the university name else return full name) 
3. national_university/international_university: "return National if inside Pak else return International" 
4. email_id: if available else return "N/A"
5. github_link: if available else return "N/A"
6. employment_details: (company, position, years_of_experience, location, tags: teaching/industry/internship)
7. total_professional_experience: total experience in years excluding internships (return Fresh Graduate if not available)
8. technical_skills:
9. soft_skills: 
10. location: 

Return all information in JSON format.
"""
    
    def __init__(self):
        """Initialize Groq API clients"""
        api_keys = settings.get_api_keys()
        
        if not api_keys:
            logger.warning("No API keys found in configuration")
            self.clients = []
        else:
            self.clients = [Groq(api_key=key) for key in api_keys]
            logger.info(f"Initialized {len(self.clients)} Groq API clients")
    
    def parse_resume(self, resume_text: str) -> Optional[ResumeData]:
        """
        Parse resume text and extract structured information
        
        Args:
            resume_text: Preprocessed resume text
            
        Returns:
            ResumeData object or None if parsing fails
        """
        if not self.clients:
            logger.error("No API clients available")
            return None
        
        completion = None
        used_client_idx = None
        
        for idx, client in enumerate(self.clients):
            try:
                completion = client.chat.completions.create(
                    model=settings.LLM_MODEL,
                    messages=[{
                        "role": "user", 
                        "content": self.INSTRUCTION + resume_text
                    }],
                    temperature=settings.LLM_TEMPERATURE,
                    max_tokens=settings.LLM_MAX_TOKENS,
                    top_p=settings.LLM_TOP_P,
                    response_format={"type": "json_object"}
                )
                used_client_idx = idx + 1
                logger.info(f"Successfully used API client {used_client_idx}")
                break
            
            except Exception as e:
                error_msg = str(e).lower()
                if "rate limit" in error_msg or "quota" in error_msg:
                    logger.warning(f"Client {idx + 1} limit exceeded, trying next...")
                    continue
                else:
                    logger.error(f"Error with client {idx + 1}: {str(e)}")
                    break
        
        if not completion:
            logger.error("All API clients failed")
            return None
        
        try:
            result = json.loads(completion.choices[0].message.content)
            
            # Parse employment details
            employment_details = []
            for detail in result.get("employment_details", []):
                employment_details.append(EmploymentDetail(**detail))
            
            # Create ResumeData object
            resume_data = ResumeData(
                full_name=result.get("full_name", "N/A"),
                university_name=result.get("university_name", "N/A"),
                national_or_international=result.get("national_university/international_university", "N/A"),
                email_id=result.get("email_id", "N/A"),
                github_link=result.get("github_link", "N/A"),
                employment_details=employment_details,
                total_professional_experience=result.get("total_professional_experience", "N/A"),
                technical_skills=result.get("technical_skills", []),
                soft_skills=result.get("soft_skills", []),
                location=result.get("location", "N/A")
            )
            
            return resume_data
        
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error creating ResumeData: {str(e)}")
            return None
