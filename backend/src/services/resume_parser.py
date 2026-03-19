"""Resume parsing service using Groq API + instructor for structured output"""
import json
from datetime import datetime
from pathlib import Path
from typing import Optional
import instructor
from groq import Groq
from ..config import settings
from ..database import SessionLocal, LLMLogRepository
from ..models import ResumeData
from ..utils import get_logger


logger = get_logger(__name__)


class ResumeParserService:
    """Service for parsing resumes using LLM"""

    # System prompt — field descriptions come from ResumeData's Field(description=...) automatically
    SYSTEM_PROMPT = (
        "You are an expert resume parser. "
        "Extract all available information from the resume as accurately as possible. "
        "If a field is genuinely absent, return 'N/A' or an empty list as appropriate."
    )
    
    def __init__(self):
        """Initialize instructor-patched Groq clients"""
        api_keys = settings.get_api_keys()

        if not api_keys:
            logger.warning("No API keys found in configuration")
            self.clients = []
        else:
            # instructor.from_groq patches each Groq client so that
            # response_model=<PydanticModel> is enforced automatically.
            self.clients = [
                instructor.from_groq(Groq(api_key=key), mode=instructor.Mode.JSON)
                for key in api_keys
            ]
            logger.info(f"Initialized {len(self.clients)} instructor-patched Groq clients")
    
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
        raw_content = None
        usage = None
        parse_success = False
        resume_data = None

        for idx, client in enumerate(self.clients):
            try:
                # instructor enforces the schema — returns a ResumeData directly
                resume_data, completion = client.chat.completions.create_with_completion(
                    model=settings.LLM_MODEL,
                    messages=[
                        {"role": "system", "content": self.SYSTEM_PROMPT},
                        {"role": "user",   "content": resume_text},
                    ],
                    response_model=ResumeData,
                    temperature=settings.LLM_TEMPERATURE,
                    max_tokens=settings.LLM_MAX_TOKENS,
                    top_p=settings.LLM_TOP_P,
                )
                used_client_idx = idx + 1
                raw_content = completion.choices[0].message.content
                usage = completion.usage
                parse_success = True
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

        self._log_llm_response(raw_content or "", used_client_idx or 0, usage, parse_success)

        if not parse_success:
            logger.error("All API clients failed or structured parsing failed")

        return resume_data

    def _log_llm_response(
        self,
        raw_response: str,
        client_index: int,
        usage,
        parse_success: bool
    ) -> None:
        """Persist the raw LLM response to the database AND to a JSON file for traceability."""
        # ── 1. Database log ────────────────────────────────────────────────
        try:
            db = SessionLocal()
            LLMLogRepository.log_response(
                db=db,
                model_used=settings.LLM_MODEL,
                api_client_index=client_index,
                raw_response=raw_response,
                prompt_tokens=usage.prompt_tokens if usage else None,
                completion_tokens=usage.completion_tokens if usage else None,
                parse_success=parse_success
            )
        except Exception as e:
            logger.error(f"Failed to log LLM response to database: {str(e)}")
        finally:
            db.close()

        # ── 2. JSON file log ───────────────────────────────────────────────
        # Saved to  logs/llm_responses/YYYYMMDD_HHMMSS_<ok|fail>.json
        # One file per call — always written, even on parse failures.
        try:
            response_log_dir = settings.LOGS_DIR / "llm_responses"
            response_log_dir.mkdir(parents=True, exist_ok=True)

            ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
            status = "ok" if parse_success else "fail"
            log_path = response_log_dir / f"{ts}_{status}.json"

            payload = {
                "timestamp": datetime.utcnow().isoformat(),
                "model": settings.LLM_MODEL,
                "api_client_index": client_index,
                "parse_success": parse_success,
                "prompt_tokens": usage.prompt_tokens if usage else None,
                "completion_tokens": usage.completion_tokens if usage else None,
                "raw_response": raw_response,
            }

            log_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
            logger.info(f"LLM response saved to {log_path}")
        except Exception as e:
            logger.error(f"Failed to write LLM response file: {str(e)}")
