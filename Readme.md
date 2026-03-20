# 🎯 FitFindr — AI-Powered Resume Screening Platform

<div align="center">

![FitFindr](https://img.shields.io/badge/FitFindr-AI%20Resume%20Screening-blue?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.10+-green?style=for-the-badge&logo=python)
![Next.js](https://img.shields.io/badge/Next.js-15-black?style=for-the-badge&logo=next.js)
![LangGraph](https://img.shields.io/badge/LangGraph-Agentic%20Pipeline-orange?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)

**Streamline hiring with an agentic AI screening pipeline, a modern Next.js dashboard, and full observability via LangSmith.**

[Features](#-features) - [Architecture](#-architecture) - [Quick Start](#-quick-start) - [API](#-api-reference) - [Configuration](#-configuration)

</div>

---

## Overview

FitFindr combines **BERT semantic embeddings**, a **LangGraph agentic pipeline**, and **Groq LLM inference** to automatically score, parse, and deeply analyse candidates against a job description.

Two independent services:
- **Backend** — FastAPI + LangGraph + SQLAlchemy (`backend/`)
- **Frontend** — Next.js 15 + React 19 + Tailwind CSS (`frontend/`)

---

## Features

### Agentic Screening Pipeline (LangGraph)

| Feature | Description |
|---------|-------------|
| **Tiered Analysis** | Routes each resume: deep LLM analysis for score >= 70%, standard parse 40-70%, skips LLM < 40% |
| **Self-Healing Parse** | Detects sparse extractions (>=4 N/A fields) and retries with an enhanced prompt (max 2 attempts) |
| **JD Analysis** | Analyses the job description once per batch extracting must-have skills, seniority, domain |
| **Deep Analysis** | For high-scoring candidates: skill gaps, red flags, tailored interview questions, recommendation |

### Platform

- JWT Authentication — register/login with secure token-based auth
- Analytics Dashboard — score distribution, top universities, top skills (Recharts)
- Smart Filtering — filter by min score slider, university tags, skill tags
- Dual View — expandable candidate cards or sortable table
- CSV Export — one-click download of all screening results
- Persistent History — SQLite/PostgreSQL via SQLAlchemy ORM
- LangSmith Tracing — optional full observability on every LLM call
- API Key Rotation — automatic fallback across multiple Groq keys

---

## Architecture

```
+--------------------------------------------------------------------------+
|                  FRONTEND  (Next.js 15, port 3000)                       |
|  Login  Register  Dashboard  CandidateCards  ResultsTable  Analytics     |
|  FilterPanel      lib/api.ts -> JWT-authenticated fetch to backend        |
+------------------------------+-------------------------------------------+
                               | HTTP / REST  (port 8000)
+------------------------------v-------------------------------------------+
|                  BACKEND  (FastAPI, port 8000)                           |
|   POST /api/screen   GET /api/results   /auth/login   /auth/register     |
+------------------------------+-------------------------------------------+
                               |
+------------------------------v-------------------------------------------+
|               LANGGRAPH AGENTIC PIPELINE                                 |
|                                                                          |
|  analyze_jd() --(once per batch)--> JdRequirements                      |
|                                                                          |
|  embed_and_score                                                         |
|       +- score < 0.40 ----------------------------------------> build_result |
|       +- score >= 0.40 --> parse_resume                                  |
|                               +- sparse (>=4 N/A) --> retry_parse       |
|                               +- depth=deep --------> deep_analysis     |
|                                                           +-> build_result|
+-------------------+------------------+-----------------------------------+
                    |                  |
       +------------v------+  +--------v---------+  +------------------+
       | EmbeddingService  |  |  Groq LLM        |  | SQLAlchemy ORM   |
       | bert-base-uncased |  |  instructor      |  | SQLite/Postgres  |
       +-------------------+  +------------------+  +------------------+
```

### Technology Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | Next.js 15.5, React 19, TypeScript, Tailwind CSS 3, Recharts |
| **Backend API** | FastAPI 0.115, uvicorn |
| **Agentic Pipeline** | LangGraph, LangSmith (@traceable) |
| **LLM** | Groq llama-3.3-70b-versatile via instructor |
| **Embeddings** | bert-base-uncased (transformers + PyTorch) |
| **Database** | SQLAlchemy 2.0 — SQLite (default) / PostgreSQL |
| **Auth** | JWT (python-jose), bcrypt |
| **Testing** | pytest, pytest-cov, httpx |
| **Containers** | Docker, Docker Compose |

### Project Structure

```
FitFindr/
├── backend/
│   ├── src/
│   │   ├── api/              # FastAPI app, routes, response schemas
│   │   ├── auth/             # JWT auth router and service
│   │   ├── database/         # SQLAlchemy models, repository
│   │   ├── services/
│   │   │   ├── graph_service.py      # LangGraph pipeline (core)
│   │   │   ├── embedding_service.py  # BERT embeddings and similarity
│   │   │   └── resume_parser.py      # Groq LLM structured extraction
│   │   ├── utils/            # Text processing, logging config
│   │   ├── models.py         # Pydantic domain models
│   │   └── config.py         # Pydantic Settings (reads .env)
│   └── tests/                # pytest unit + integration tests
├── frontend/
│   ├── app/
│   │   ├── dashboard/        # Main screening dashboard
│   │   ├── login/            # Login page
│   │   └── register/         # Registration page
│   ├── components/           # CandidateCard, ResultsTable, Analytics, FilterPanel
│   ├── lib/api.ts            # Typed JWT fetch client
│   └── types/index.ts        # Shared TypeScript interfaces
├── data/                     # SQLite DB and uploaded files
├── requirements.txt          # Python dependencies
├── docker-compose.yml        # Multi-container: backend + frontend
├── Dockerfile                # Backend (Python) image
├── Dockerfile.frontend       # Frontend (Node.js) image
└── .env.example              # Environment variable template
```

---

## Quick Start

See [QUICKSTART.md](QUICKSTART.md) for the full walkthrough.

```bash
git clone https://github.com/MuhammadEmmadSiddiqui/FitFindr.git
cd FitFindr
cp .env.example .env        # add GROQ_API_KEYS (required)
docker-compose up -d
```

Open http://localhost:3000, register, and start screening.

---

## Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GROQ_API_KEYS` | Yes | — | Comma-separated Groq API key(s) |
| `SECRET_KEY` | Yes | — | JWT signing secret |
| `DATABASE_URL` | No | `sqlite:///./data/fitfindr.db` | SQLAlchemy connection string |
| `BERT_MODEL` | No | `bert-base-uncased` | HuggingFace model ID |
| `LLM_MODEL` | No | `llama-3.3-70b-versatile` | Groq model name |
| `LANGCHAIN_API_KEY` | No | `""` | LangSmith key; tracing disabled when empty |
| `LANGCHAIN_PROJECT` | No | `fitfindr` | LangSmith project name |

---

## API Reference

Interactive docs: http://localhost:8000/docs

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/auth/register` | POST | — | `{username, email, password}` |
| `/auth/login` | POST | — | form username/password -> JWT |
| `/api/screen` | POST | Bearer | Multipart: `job_description` + `resumes[]` |
| `/api/results` | GET | Bearer | Last 50 results |
| `/health` | GET | — | Health check |

---

## Testing

```bash
.venv\Scripts\python.exe -m pytest backend/tests -v
.venv\Scripts\python.exe -m pytest backend/tests --cov=backend/src --cov-report=html
```

---

## Deployment

```bash
# Docker (recommended)
docker-compose up -d          # backend :8000, frontend :3000

# Manual
.venv\Scripts\python.exe -m uvicorn --app-dir backend src.api.main:app --reload --reload-dir backend/src --port 8000

cd frontend && npm run dev    # http://localhost:3000
```

For cloud deployment, set `NEXT_PUBLIC_API_URL` in `frontend/.env.local` to your backend URL.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) — fork, branch, PR against `main`. Run `pytest` and `npx tsc --noEmit` before submitting.

---

## License

MIT — see [LICENSE](LICENSE).

---

## Author

**Muhammad Emmad Siddiqui** — [GitHub](https://github.com/MuhammadEmmadSiddiqui) — [LinkedIn](https://linkedin.com/in/muhammad-emmad-siddiqui)

<div align="center">Made with love for smarter hiring — Star this repo if you find it helpful!</div>
