# Quick Start Guide

## Getting Started in 5 Minutes

### 1. Clone and Configure

```bash
git clone https://github.com/MuhammadEmmadSiddiqui/FitFindr.git
cd FitFindr
cp .env.example .env
```

Edit `.env` and add at minimum:

```bash
GROQ_API_KEYS=your_groq_key_here
SECRET_KEY=any-long-random-string
```

Get a free Groq API key at <https://console.groq.com>.

---

### 2. Choose Your Setup

#### Option A: Docker (Recommended)

```bash
docker-compose up -d
```

| Service | URL |
|---------|-----|
| Frontend (Next.js) | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |

#### Option B: Local Development

**Backend**

```bash
pip install uv
uv venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate      # macOS / Linux

uv pip install -r requirements.txt

.venv\Scripts\python.exe -m uvicorn --app-dir backend src.api.main:app \
    --reload --reload-dir backend/src --port 8000
```

**Frontend** (second terminal)

```bash
cd frontend
npm install
npm run dev   # http://localhost:3000
```

> The first backend start downloads the BERT model (~440 MB) and caches it.

---

### 3. First Screening

1. Open **http://localhost:3000**
2. **Register** an account and log in
3. On the **Dashboard**, upload a Job Description (PDF or TXT)
4. Upload one or more resumes (PDF or TXT)
5. Click **Screen Resumes**
6. Toggle between **Cards** / **Table** view, use **Filters**, download **CSV**

The LangGraph pipeline routes each resume automatically:

| Score | Action |
|-------|--------|
| >= 70% | Deep LLM analysis (skill gaps, red flags, interview questions, recommendation) |
| 40–70% | Standard parse only |
| < 40% | Skipped — no LLM call |

---

## Optional: LangSmith Tracing

Add to `.env` to see every LLM call traced in LangSmith:

```bash
LANGCHAIN_API_KEY=lsv2_your_key_here
LANGCHAIN_PROJECT=fitfindr
```

Get a free key at <https://smith.langchain.com>. **Restart the backend** after adding the key.

---

## Database

SQLite is the default — no setup needed. For PostgreSQL:

```bash
DATABASE_URL=postgresql://user:pass@localhost:5432/fitfindr
```

---

## Testing

```bash
# Backend tests
.venv\Scripts\python.exe -m pytest backend/tests -v
.venv\Scripts\python.exe -m pytest backend/tests --cov=backend/src --cov-report=html

# Frontend TypeScript type check
cd frontend && npx tsc --noEmit
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `GROQ_API_KEYS` missing | Ensure key is in `.env`, not `.env.example` |
| Slow first backend start | BERT model (~440 MB) downloading — only once |
| Port conflict | Update `API_PORT` in `.env` or edit `docker-compose.yml` |
| CORS error in browser | Backend allows `localhost:3000` by default; check you're not using a different port |
| LangSmith shows 0 traces | Verify `LANGCHAIN_API_KEY` is set and backend was restarted |

---

## Next Steps

- Full documentation: [Readme.md](Readme.md)
- Live API explorer: http://localhost:8000/docs
- LangGraph traces: https://smith.langchain.com
- Contribution guide: [CONTRIBUTING.md](CONTRIBUTING.md)
