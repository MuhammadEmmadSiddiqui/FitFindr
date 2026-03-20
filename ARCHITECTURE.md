# Architecture

## System Overview

```
+----------------------------------------------------------------------------+
|                    FRONTEND  (Next.js 15, port 3000)                       |
|                                                                            |
|  app/login          app/register        app/dashboard                     |
|  components/CandidateCard               components/ResultsTable           |
|  components/Analytics                   components/FilterPanel            |
|                                                                            |
|  lib/api.ts  →  JWT Bearer fetch  →  FastAPI backend                      |
+------------------------------+---------------------------------------------+
                               |  HTTP / REST
+------------------------------v---------------------------------------------+
|                    BACKEND  (FastAPI 0.115, port 8000)                     |
|                                                                            |
|  POST /api/screen          GET /api/results                               |
|  POST /auth/register       POST /auth/login                               |
|  GET  /health                                                              |
+------------------------------+---------------------------------------------+
                               |
+------------------------------v---------------------------------------------+
|                 LANGGRAPH AGENTIC PIPELINE  (graph_service.py)            |
|                                                                            |
|  GraphScreeningService.analyze_jd()  ←  runs once per batch              |
|    extracts: must_have_skills, nice_to_have_skills,                       |
|              seniority_level, domain, min_years_experience                |
|                                                                            |
|  Per-resume StateGraph:                                                    |
|                                                                            |
|  START                                                                     |
|   └─► embed_and_score                                                     |
|            │  score < 0.40  ──────────────────────────────► build_result  |
|            │  score 0.40-0.70 (standard)                                  |
|            │  score >= 0.70  (deep)     ──► parse_resume                  |
|                                               │                           |
|                                    sparse parse (>=4 N/A)?                |
|                                      yes → retry_parse                    |
|                                      no  → (continue)                     |
|                                               │                           |
|                                    depth = deep?                          |
|                                      yes → deep_analysis                  |
|                                      no  → build_result                   |
|                                               │                           |
|                                    deep_analysis → build_result → END     |
+-------------------+------------------+--------------------------------------+
                    |                  |
       +------------v------+  +--------v---------+  +----------------------+
       | EmbeddingService  |  |  Groq LLM        |  | SQLAlchemy ORM      |
       | bert-base-uncased |  |  instructor      |  | ScreeningResultDB   |
       | cosine similarity |  |  ResumeData      |  | UserDB              |
       |                   |  |  DeepAnalysis    |  | JobDescriptionDB    |
       +-------------------+  +------------------+  +----------------------+
```

---

## LangGraph Node Descriptions

| Node | Purpose | LLM Call |
|------|---------|----------|
| `embed_and_score` | Compute BERT cosine similarity; decide `skip/standard/deep` | No |
| `parse_resume` | First-pass structured extraction with `instructor` + Groq | Yes |
| `retry_parse` | Self-healing re-extraction with an enhanced system prompt | Yes |
| `deep_analysis` | Skill gaps, red flags, interview questions, recommendation | Yes |
| `build_result` | Assemble `ScreeningResult` from accumulated state | No |

---

## Data Models

### Pydantic Domain (`backend/src/models.py`)

```
EmploymentDetail
  company, position, start_date, end_date, location, tags
  computed: duration_years, years_of_experience

ResumeData
  full_name, university_name, national_or_international
  email_id, phone_number, github_link, location
  employment_details: List[EmploymentDetail]
  technical_skills: List[str]
  soft_skills: List[str]
  computed: total_professional_experience

ScreeningResult
  resume_filename, similarity_score
  (all ResumeData fields flattened)
  analysis_depth, jd_domain, jd_seniority
  skill_gaps, red_flags, interview_questions
  overall_recommendation
```

### SQLAlchemy ORM (`backend/src/database/models.py`)

```
UserDB            — id, username, email, hashed_password, created_at
ScreeningResultDB — id, jd_id (FK), resume_filename, similarity_score,
                    candidate_data (JSON), screening_date
JobDescriptionDB  — id, title, content, hash, created_at
```

---

## API Request/Response Flow

```
Client                 FastAPI               LangGraph             DB
  |                       |                      |                  |
  |-- POST /api/screen --> |                      |                  |
  |   (JWT + multipart)    |                      |                  |
  |                        |-- analyze_jd() ----> |                  |
  |                        |                      |-- Groq API call  |
  |                        |                      |<- JdRequirements |
  |                        |                      |                  |
  |                        |  for each resume:    |                  |
  |                        |-- graph.invoke() ---> |                  |
  |                        |                      |-- BERT embed     |
  |                        |                      |-- [Groq parse]   |
  |                        |                      |-- [Groq deep]    |
  |                        |                      |-- ScreeningResult|
  |                        |<- List[result] ------ |                  |
  |                        |-- save results ------> |                 |
  |<- ScreeningBatch ------ |                                         |
```

---

## Technology Stack

| Component | Library / Version |
|-----------|------------------|
| Frontend framework | Next.js 15.5 (App Router) |
| UI library | React 19 |
| Styling | Tailwind CSS 3.4 |
| Charts | Recharts 2.12 |
| Backend framework | FastAPI 0.115 |
| ASGI server | uvicorn |
| Agentic pipeline | LangGraph |
| Observability | LangSmith (`@traceable`) |
| LLM inference | Groq (`llama-3.3-70b-versatile`) |
| Structured LLM output | instructor 1.7 |
| Embeddings | bert-base-uncased (HuggingFace transformers) |
| ML utilities | PyTorch, scikit-learn |
| ORM | SQLAlchemy 2.0 |
| Auth | JWT (python-jose), bcrypt |
| File parsing | pypdfium2 |
| Testing | pytest, pytest-cov, httpx |
| Containerisation | Docker, Docker Compose |

---

## Deployment Scenarios

### Development

```bash
# Backend
.venv\Scripts\python.exe -m uvicorn --app-dir backend src.api.main:app \
    --reload --reload-dir backend/src --port 8000

# Frontend
cd frontend && npm run dev   # port 3000
```

### Docker Compose

```bash
docker-compose up -d   # backend :8000, frontend :3000
```

### Cloud (separate services)

- **Backend**: Deploy `Dockerfile` to Railway / Fly.io / Render. Set `GROQ_API_KEYS`, `SECRET_KEY`, `DATABASE_URL`.
- **Frontend**: Deploy `frontend/` to Vercel. Set `NEXT_PUBLIC_API_URL=https://your-backend-url`.

---

## Security Considerations

- Passwords hashed with bcrypt (work factor 12)
- JWT tokens signed with `SECRET_KEY`; expire in `ACCESS_TOKEN_EXPIRE_MINUTES`
- File uploads stored in `data/uploads/` (not served publicly)
- CORS restricted to explicit origins (localhost:3000, localhost:8501)
- No raw SQL — all DB access via SQLAlchemy ORM
- Environment secrets loaded from `.env` (never committed)
