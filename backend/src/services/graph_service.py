"""LangGraph-powered agentic screening pipeline.

Features
────────
1. Tiered analysis   – deep LLM analysis for high-scoring candidates (≥ 0.70),
                       standard parse for mid-range (0.40–0.70),
                       skip the LLM entirely for weak matches (< 0.40).

2. Self-healing parse – if the parsed ResumeData is sparse (≥ SPARSE_THRESHOLD
                        key fields returned as "N/A"), automatically retries
                        with a more explicit, field-by-field prompt (max 2 attempts).

3. JD analysis       – the job description is analysed *once* before all resumes
                       to extract must-have / nice-to-have skills, seniority level,
                       and domain.  These feed into the deep-analysis prompt so
                       skill-gap detection is grounded in actual JD requirements.
"""

from __future__ import annotations

import os
import traceback
from typing import Any, List, Optional, TypedDict

import instructor
from groq import Groq
from langgraph.graph import END, StateGraph
from langsmith import traceable
from pydantic import BaseModel, Field

from ..config import settings
from ..models import ResumeData, ScreeningResult
from ..utils import decode_file, extract_text_from_pdf, get_logger, preprocess_text
from .resume_parser import ResumeParserService


logger = get_logger(__name__)


def _configure_langsmith() -> None:
    """Push LangSmith env-vars from settings into os.environ so the SDK picks them up."""
    if settings.LANGCHAIN_API_KEY:
        # Always force these — setdefault would silently keep stale values
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_API_KEY"]     = settings.LANGCHAIN_API_KEY
        os.environ["LANGCHAIN_PROJECT"]     = settings.LANGCHAIN_PROJECT
        logger.info(
            f"LangSmith tracing enabled — project: {settings.LANGCHAIN_PROJECT}"
        )
    else:
        os.environ["LANGCHAIN_TRACING_V2"] = "false"
        logger.info("LangSmith tracing disabled (LANGCHAIN_API_KEY not set)")


# Configure at module load time so env-vars are in place before any @traceable call
_configure_langsmith()

# ── Thresholds ─────────────────────────────────────────────────────────────────
DEEP_THRESHOLD = 0.70       # score ≥ this → deep analysis
SKIP_THRESHOLD = 0.40       # score < this → skip LLM parse entirely
SPARSE_THRESHOLD = 4        # number of key "N/A" fields that triggers a retry
MAX_PARSE_ATTEMPTS = 2      # parse + at most one retry


# ── LLM output schemas ──────────────────────────────────────────────────────────

class JdRequirements(BaseModel):
    """Structured requirements extracted from a job description."""
    must_have_skills: List[str] = Field(
        default_factory=list,
        description="Skills or qualifications explicitly required by the JD",
    )
    nice_to_have_skills: List[str] = Field(
        default_factory=list,
        description="Skills mentioned as preferred, bonus, or nice-to-have",
    )
    seniority_level: str = Field(
        default="N/A",
        description="One of: junior | mid | senior | lead | N/A",
    )
    domain: str = Field(
        default="N/A",
        description="Primary domain, e.g. Software Engineering, Data Science, DevOps",
    )
    min_years_experience: float = Field(
        default=0.0,
        description="Minimum years of relevant experience required; 0 if not stated",
    )


class DeepAnalysisResult(BaseModel):
    """Detailed candidate assessment produced during deep analysis."""
    skill_gaps: List[str] = Field(
        default_factory=list,
        description="Must-have skills from the JD that the candidate appears to lack",
    )
    red_flags: List[str] = Field(
        default_factory=list,
        description="Potential concerns: unexplained employment gaps, mismatches, etc.",
    )
    interview_questions: List[str] = Field(
        default_factory=list,
        description="3–5 targeted interview questions tailored to this candidate and JD",
    )
    overall_recommendation: str = Field(
        default="N/A",
        description="One of: Strong Recommend | Recommend | Maybe | Pass",
    )


# ── Graph state ─────────────────────────────────────────────────────────────────

class ScreeningState(TypedDict):
    # inputs
    jd_text: str
    jd_requirements: Optional[dict]     # serialised JdRequirements
    resume_text: str
    resume_filename: str
    # embedding stage
    jd_embedding: Any                   # numpy array — not serialised; in-memory only
    similarity_score: float
    analysis_depth: str                 # "skip" | "standard" | "deep"
    # parse stage
    parsed_data: Optional[dict]         # serialised ResumeData
    parse_attempts: int
    # deep-analysis stage
    deep_analysis: Optional[dict]       # serialised DeepAnalysisResult
    # output
    final_result: Optional[ScreeningResult]


# ── Helpers ─────────────────────────────────────────────────────────────────────

def _make_clients() -> list:
    """Build instructor-patched Groq clients from settings."""
    return [
        instructor.from_groq(Groq(api_key=key), mode=instructor.Mode.JSON)
        for key in settings.get_api_keys()
    ]


@traceable(name="llm_structured_call", run_type="llm")
def _llm_structured(clients: list, response_model, messages: list):
    """Try each client in turn; return the structured model instance or None."""
    for idx, client in enumerate(clients):
        try:
            return client.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=messages,
                response_model=response_model,
                temperature=settings.LLM_TEMPERATURE,
                max_tokens=settings.LLM_MAX_TOKENS,
                top_p=settings.LLM_TOP_P,
            )
        except Exception as exc:
            err = str(exc).lower()
            if "rate limit" in err or "quota" in err:
                logger.warning(f"Graph: client {idx + 1} rate-limited, trying next…")
                continue
            logger.error(f"Graph: LLM call failed on client {idx + 1}: {exc}")
            break
    return None


def _count_na_fields(data: dict) -> int:
    """Count how many key ResumeData fields are absent / empty / 'N/A'."""
    key_fields = [
        "full_name", "university_name", "email_id",
        "location", "technical_skills", "employment_details",
    ]
    count = 0
    for field in key_fields:
        val = data.get(field)
        if val in (None, "N/A", "", []):
            count += 1
    return count


# ── Graph service ────────────────────────────────────────────────────────────────

class GraphScreeningService:
    """
    Agentic resume screening pipeline powered by LangGraph.

    Graph topology
    ──────────────
    embed_and_score
        │
        ├─(skip)──────────────────────────── build_result → END
        │
        └─(standard | deep)─► parse_resume
                                    │
                                    ├─(retry)──────────► retry_parse
                                    │                        │
                                    │                        ├─(deep)──► deep_analysis ─► build_result → END
                                    │                        └─(standard)────────────────► build_result → END
                                    │
                                    ├─(deep)──────────► deep_analysis ─► build_result → END
                                    └─(standard)──────────────────────► build_result → END
    """

    def __init__(self) -> None:
        from .embedding_service import EmbeddingService  # lazy to avoid heavy import at module load

        self.embedding_service = EmbeddingService()
        self._clients = _make_clients()
        self._graph = self._build_graph()
        logger.info("GraphScreeningService initialised")

    # ── JD analysis (runs once per batch, before any per-resume graph runs) ─────

    @traceable(name="analyze_jd", run_type="chain")
    def analyze_jd(self, jd_text: str) -> dict:
        """
        Feature 3 – analyse the job description and return a JdRequirements dict.
        Called once per screening batch; result is shared across all resume runs.
        """
        prompt = (
            "Analyse the following job description and extract structured requirements "
            "including must-have skills, nice-to-have skills, seniority level, domain, "
            "and minimum years of experience.\n\n"
            f"JOB DESCRIPTION:\n{jd_text}"
        )
        result = _llm_structured(
            self._clients,
            JdRequirements,
            [{"role": "user", "content": prompt}],
        )
        if result:
            logger.info(
                f"JD analysis: domain={result.domain}, "
                f"seniority={result.seniority_level}, "
                f"must_have={len(result.must_have_skills)} skills"
            )
            return result.model_dump()
        logger.warning("JD analysis failed – proceeding without structured requirements")
        return JdRequirements().model_dump()

    # ── Graph builder ─────────────────────────────────────────────────────────────

    def _build_graph(self) -> Any:
        embedding_service = self.embedding_service
        clients = self._clients

        # ── Node: embed_and_score ────────────────────────────────────────────────
        def embed_and_score(state: ScreeningState) -> dict:
            """Compute BERT cosine-similarity and decide analysis depth."""
            resume_emb = embedding_service.get_embeddings(state["resume_text"])
            score = embedding_service.calculate_similarity(state["jd_embedding"], resume_emb)

            if score >= DEEP_THRESHOLD:
                depth = "deep"
            elif score >= SKIP_THRESHOLD:
                depth = "standard"
            else:
                depth = "skip"

            logger.info(
                f"[{state['resume_filename']}] similarity={score:.4f} → depth={depth}"
            )
            return {
                "similarity_score": score,
                "analysis_depth": depth,
                "parse_attempts": 0,
                "parsed_data": None,
                "deep_analysis": None,
            }

        # ── Node: parse_resume ───────────────────────────────────────────────────
        def parse_resume(state: ScreeningState) -> dict:
            """First-pass parse with the standard instructor prompt."""
            result: Optional[ResumeData] = _llm_structured(
                clients,
                ResumeData,
                [
                    {"role": "system", "content": ResumeParserService.SYSTEM_PROMPT},
                    {"role": "user",   "content": state["resume_text"]},
                ],
            )
            attempts = state["parse_attempts"] + 1
            parsed = result.model_dump(by_alias=False) if result else None
            logger.info(
                f"[{state['resume_filename']}] parse attempt {attempts}: "
                f"{'ok' if parsed else 'failed'}"
            )
            return {"parsed_data": parsed, "parse_attempts": attempts}

        # ── Node: retry_parse (feature 2) ────────────────────────────────────────
        def retry_parse(state: ScreeningState) -> dict:
            """
            Feature 2 – self-healing parse.
            Called when the first parse returned a sparse result.
            Uses a more emphatic system prompt to recover more data.
            """
            na_count = _count_na_fields(state.get("parsed_data") or {})
            logger.info(
                f"[{state['resume_filename']}] sparse parse ({na_count} N/A fields) "
                f"— retrying with enhanced prompt"
            )
            enhanced_system = (
                "You are an expert resume parser. "
                "The previous extraction was incomplete. "
                "Re-read the resume very carefully and extract EVERY available field. "
                "Do not leave any field as N/A unless the information is genuinely absent."
            )
            result: Optional[ResumeData] = _llm_structured(
                clients,
                ResumeData,
                [
                    {"role": "system", "content": enhanced_system},
                    {"role": "user",   "content": state["resume_text"]},
                ],
            )
            attempts = state["parse_attempts"] + 1
            parsed = (
                result.model_dump(by_alias=False) if result else state.get("parsed_data")
            )
            logger.info(
                f"[{state['resume_filename']}] retry parse attempt {attempts}: "
                f"{'ok' if result else 'failed — keeping previous result'}"
            )
            return {"parsed_data": parsed, "parse_attempts": attempts}

        # ── Node: deep_analysis (feature 1) ──────────────────────────────────────
        def deep_analysis(state: ScreeningState) -> dict:
            """
            Feature 1 – deep analysis for high-scoring candidates.
            Uses JD requirements (feature 3) + parsed resume to produce:
              • skill gaps, • red flags, • tailored interview questions,
              • overall recommendation.
            """
            jd_req = state.get("jd_requirements") or {}
            parsed = state.get("parsed_data") or {}
            prompt = (
                "You are a senior technical recruiter. "
                "Analyse the candidate profile against the job requirements below.\n\n"
                f"JOB REQUIREMENTS (structured):\n{jd_req}\n\n"
                f"JD TEXT:\n{state['jd_text']}\n\n"
                f"CANDIDATE PROFILE (parsed resume):\n{parsed}\n\n"
                "Provide:\n"
                "  1. skill_gaps – must-have JD skills the candidate is missing\n"
                "  2. red_flags  – concerns (gaps, mismatches, inconsistencies)\n"
                "  3. interview_questions – 3 to 5 targeted questions\n"
                "  4. overall_recommendation – one of: "
                "Strong Recommend | Recommend | Maybe | Pass"
            )
            result: Optional[DeepAnalysisResult] = _llm_structured(
                clients,
                DeepAnalysisResult,
                [{"role": "user", "content": prompt}],
            )
            analysis = result.model_dump() if result else DeepAnalysisResult().model_dump()
            logger.info(
                f"[{state['resume_filename']}] deep analysis: "
                f"recommendation={analysis.get('overall_recommendation')}, "
                f"gaps={len(analysis.get('skill_gaps', []))}"
            )
            return {"deep_analysis": analysis}

        # ── Node: build_result ────────────────────────────────────────────────────
        def build_result(state: ScreeningState) -> dict:
            """Assemble the final ScreeningResult from accumulated state."""
            parsed = state.get("parsed_data") or {}
            analysis = state.get("deep_analysis") or {}
            jd_req = state.get("jd_requirements") or {}

            try:
                resume_data = ResumeData.model_validate(parsed) if parsed else ResumeData()
            except Exception:
                resume_data = ResumeData()

            result = ScreeningResult(
                resume_filename=state["resume_filename"],
                similarity_score=state.get("similarity_score", 0.0),
                full_name=resume_data.full_name,
                university_name=resume_data.university_name,
                national_or_international=resume_data.national_or_international,
                email_id=resume_data.email_id,
                github_link=resume_data.github_link,
                phone_number=resume_data.phone_number,
                company_names=resume_data.get_company_names(),
                technical_skills=resume_data.technical_skills,
                soft_skills=resume_data.soft_skills,
                total_experience=resume_data.total_professional_experience,
                location=resume_data.location,
                # ── new fields ──────────────────────────────────────────────────
                analysis_depth=state.get("analysis_depth", "standard"),
                jd_domain=jd_req.get("domain", "N/A"),
                jd_seniority=jd_req.get("seniority_level", "N/A"),
                skill_gaps=analysis.get("skill_gaps", []),
                red_flags=analysis.get("red_flags", []),
                interview_questions=analysis.get("interview_questions", []),
                overall_recommendation=analysis.get("overall_recommendation", "N/A"),
            )
            return {"final_result": result}

        # ── Routing functions ─────────────────────────────────────────────────────

        def route_after_embed(state: ScreeningState) -> str:
            """Skip straight to result assembly when the score is too low."""
            return "build_result" if state["analysis_depth"] == "skip" else "parse_resume"

        def route_after_parse(state: ScreeningState) -> str:
            """
            Feature 2 routing: retry if parse is sparse.
            Otherwise advance based on analysis depth.
            """
            parsed = state.get("parsed_data")
            attempts = state.get("parse_attempts", 0)
            if parsed and _count_na_fields(parsed) >= SPARSE_THRESHOLD and attempts < MAX_PARSE_ATTEMPTS:
                return "retry_parse"
            return "deep_analysis" if state["analysis_depth"] == "deep" else "build_result"

        def route_after_retry(state: ScreeningState) -> str:
            """After the retry, advance to deep analysis or result depending on depth."""
            return "deep_analysis" if state["analysis_depth"] == "deep" else "build_result"

        # ── Assemble the graph ────────────────────────────────────────────────────
        g = StateGraph(ScreeningState)

        g.add_node("embed_and_score", embed_and_score)
        g.add_node("parse_resume",    parse_resume)
        g.add_node("retry_parse",     retry_parse)
        g.add_node("deep_analysis",   deep_analysis)
        g.add_node("build_result",    build_result)

        g.set_entry_point("embed_and_score")

        g.add_conditional_edges(
            "embed_and_score",
            route_after_embed,
            {"parse_resume": "parse_resume", "build_result": "build_result"},
        )
        g.add_conditional_edges(
            "parse_resume",
            route_after_parse,
            {
                "retry_parse":    "retry_parse",
                "deep_analysis":  "deep_analysis",
                "build_result":   "build_result",
            },
        )
        g.add_conditional_edges(
            "retry_parse",
            route_after_retry,
            {"deep_analysis": "deep_analysis", "build_result": "build_result"},
        )
        g.add_edge("deep_analysis", "build_result")
        g.add_edge("build_result",  END)

        return g.compile()

    # ── Public interface (same signature as the original ScreeningService) ─────────

    def screen_multiple_resumes(
        self,
        resume_files: list,
        jd_file: Any,
        jd_type: str,
    ) -> List[ScreeningResult]:
        """
        Screen a batch of resumes against a job description.

        Args:
            resume_files: List of (file, filename, mime_type) tuples.
            jd_file:      Job-description file-like object.
            jd_type:      MIME type of the JD file.

        Returns:
            List of ScreeningResult objects sorted by similarity score (descending).
        """
        # 1. Extract and preprocess JD
        if jd_type == "application/pdf":
            jd_raw = extract_text_from_pdf(jd_file)
        else:
            jd_raw = decode_file(jd_file)
        jd_text = preprocess_text(jd_raw)

        # 2. Feature 3 – analyse JD once for the whole batch
        jd_requirements = self.analyze_jd(jd_text)

        # 3. Pre-compute JD embedding (shared across all resumes)
        jd_embedding = self.embedding_service.get_embeddings(jd_text)

        logger.info(
            f"Graph: screening {len(resume_files)} resumes | "
            f"domain={jd_requirements.get('domain')} | "
            f"seniority={jd_requirements.get('seniority_level')}"
        )

        # 4. Run the graph for every resume
        results: List[ScreeningResult] = []
        for resume_file, filename, file_type in resume_files:
            try:
                if file_type == "application/pdf":
                    raw_text = extract_text_from_pdf(resume_file)
                else:
                    raw_text = decode_file(resume_file)
                resume_text = preprocess_text(raw_text)

                initial_state: ScreeningState = {
                    "jd_text":          jd_text,
                    "jd_requirements":  jd_requirements,
                    "resume_text":      resume_text,
                    "resume_filename":  filename,
                    "jd_embedding":     jd_embedding,
                    "similarity_score": 0.0,
                    "analysis_depth":   "standard",
                    "parsed_data":      None,
                    "parse_attempts":   0,
                    "deep_analysis":    None,
                    "final_result":     None,
                }

                final_state = self._graph.invoke(initial_state)
                result: ScreeningResult = final_state["final_result"]
                if result:
                    results.append(result)

            except Exception as exc:
                logger.error(
                    f"Graph error processing {filename}: {exc}\n"
                    f"{traceback.format_exc()}"
                )
                continue

        results.sort(key=lambda r: r.similarity_score, reverse=True)
        logger.info(f"Graph: completed {len(results)}/{len(resume_files)} resumes")
        return results
