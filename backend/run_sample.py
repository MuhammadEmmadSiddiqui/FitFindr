"""
Quick runner to test resume parsing against Sample_data/ PDFs.
Usage:
    python run_sample.py
"""
import sys
from pathlib import Path

# ── make src importable when running from project root ──────────────────────
sys.path.insert(0, str(Path(__file__).parent))

# ── import config first so LOGS_DIR is resolved before setup_logging ────────
from src.config import settings
from src.utils.logging_config import setup_logging

# Writes to stdout AND logs/YYYYMMDD_fitfindr.log
setup_logging(
    log_level=settings.LOG_LEVEL,
    log_file=settings.LOG_FILE,
    log_dir=settings.LOGS_DIR,
)

import logging
logger = logging.getLogger("run_sample")

# ── lazy imports after path + logging are set ────────────────────────────────
from src.database.database import init_db
from src.services.resume_parser import ResumeParserService
from src.utils.text_processing import extract_text_from_pdf, preprocess_text


def parse_pdf(path: Path, parser: ResumeParserService):
    logger.info("=" * 60)
    logger.info(f"Processing: {path.name}")
    logger.info("=" * 60)

    with open(path, "rb") as fh:
        raw_text = extract_text_from_pdf(fh)

    logger.info(f"Extracted {len(raw_text)} characters from PDF")

    processed = preprocess_text(raw_text)
    logger.info(f"Pre-processed text length: {len(processed)} chars")

    resume_data = parser.parse_resume(processed)

    if resume_data is None:
        logger.error("Parsing returned None — check API keys in .env")
        return

    logger.info("── Parsed Resume Data ──────────────────────────────")
    logger.info(f"  Name           : {resume_data.full_name}")
    logger.info(f"  Email          : {resume_data.email_id}")
    logger.info(f"  GitHub         : {resume_data.github_link}")
    logger.info(f"  University     : {resume_data.university_name}")
    logger.info(f"  Nat/Intl       : {resume_data.national_or_international}")
    logger.info(f"  Location       : {resume_data.location}")
    logger.info(f"  Total Exp.     : {resume_data.total_professional_experience}")
    logger.info(f"  Technical      : {', '.join(resume_data.technical_skills[:8])}")
    logger.info(f"  Soft Skills    : {', '.join(resume_data.soft_skills[:5])}")
    logger.info(f"  Companies      : {resume_data.get_company_names()}")
    logger.info(f"  Employment ({len(resume_data.employment_details)} roles):")
    for emp in resume_data.employment_details:
        logger.info(
            f"    [{emp.tags}] {emp.position} @ {emp.company} "
            f"({emp.start_date} – {emp.end_date} = {emp.duration_years} yrs) — {emp.location}"
        )


def main():
    logger.info("Initialising database …")
    init_db()

    sample_dir = Path(__file__).parent / "Sample_data"
    pdfs = sorted(sample_dir.glob("*.pdf"))

    if not pdfs:
        logger.error(f"No PDF files found in {sample_dir}")
        sys.exit(1)

    logger.info(f"Found {len(pdfs)} PDF(s): {[p.name for p in pdfs]}")

    parser = ResumeParserService()

    for pdf_path in pdfs:
        try:
            parse_pdf(pdf_path, parser)
        except Exception as exc:
            logger.exception(f"Failed to process {pdf_path.name}: {exc}")

    logger.info("Done.")


if __name__ == "__main__":
    main()
