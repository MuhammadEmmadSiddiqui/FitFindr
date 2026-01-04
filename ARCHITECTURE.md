# 🏗️ FitFindr Architecture

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────┐              ┌──────────────────┐        │
│  │   Streamlit UI   │              │   REST API       │        │
│  │  streamlit_app   │              │   /api/screen    │        │
│  │                  │              │   /api/results   │        │
│  │  • File Upload   │              │   /health        │        │
│  │  • Dashboard     │              │                  │        │
│  │  • Analytics     │              │  (FastAPI)       │        │
│  │  • Filtering     │              │                  │        │
│  └────────┬─────────┘              └────────┬─────────┘        │
│           │                                 │                  │
└───────────┼─────────────────────────────────┼──────────────────┘
            │                                 │
            └────────────┬────────────────────┘
                         │
┌────────────────────────┴─────────────────────────────────────────┐
│                    SERVICE LAYER                                 │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │            ScreeningService                              │    │
│  │  • Orchestrates complete workflow                        │    │
│  │  • Processes multiple resumes                            │    │
│  │  • Coordinates services                                  │    │
│  └────────┬──────────────────┬──────────────────┬───────────┘    │
│           │                  │                  │                │
│  ┌────────▼────────┐  ┌─────▼──────────┐  ┌───▼────────────┐   │
│  │ EmbeddingService│  │ ResumeParser   │  │ Database Repo  │   │
│  │                 │  │ Service        │  │                │   │
│  │ • BERT Model    │  │                │  │ • Save results │   │
│  │ • Tokenizer     │  │ • Groq API     │  │ • Retrieve     │   │
│  │ • Similarity    │  │ • LLM Parsing  │  │ • Query        │   │
│  │   Calculation   │  │ • Data Extract │  │                │   │
│  └─────────────────┘  └────────────────┘  └───┬────────────┘   │
│                                               │                │
└───────────────────────────────────────────────┼────────────────┘
                                                │
┌───────────────────────────────────────────────┴────────────────┐
│                    DATA MODELS                                 │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌─────────────────┐  ┌──────────────────┐  ┌──────────────┐ │
│  │   ResumeData    │  │ ScreeningResult  │  │ Employment   │ │
│  │   (Pydantic)    │  │   (Pydantic)     │  │   Detail     │ │
│  │                 │  │                  │  │              │ │
│  │ • full_name     │  │ • resume_file    │  │ • company    │ │
│  │ • university    │  │ • similarity     │  │ • position   │ │
│  │ • skills        │  │ • candidate_data │  │ • years      │ │
│  │ • experience    │  │ • timestamp      │  │              │ │
│  └─────────────────┘  └──────────────────┘  └──────────────┘ │
│                                                                │
└───────────────────────────────────────┬────────────────────────┘
                                        │
┌───────────────────────────────────────┴────────────────────────┐
│                    DATABASE LAYER                              │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │              SQLAlchemy ORM                               │ │
│  │                                                           │ │
│  │  ┌─────────────────────┐  ┌─────────────────────┐       │ │
│  │  │ ScreeningResultDB   │  │ JobDescriptionDB    │       │ │
│  │  │                     │  │                     │       │ │
│  │  │ • id (PK)           │  │ • id (PK)           │       │ │
│  │  │ • jd_id (FK)        │  │ • title             │       │ │
│  │  │ • resume_filename   │  │ • content           │       │ │
│  │  │ • similarity_score  │  │ • hash              │       │ │
│  │  │ • candidate_data    │  │ • created_at        │       │ │
│  │  │ • screening_date    │  │                     │       │ │
│  │  └─────────────────────┘  └─────────────────────┘       │ │
│  │                                                           │ │
│  └──────────────────────────────────────────────────────────┘ │
│                              │                                 │
│                    ┌─────────▼──────────┐                     │
│                    │   SQLite / PG      │                     │
│                    │   Database         │                     │
│                    └────────────────────┘                     │
│                                                                │
└────────────────────────────────────────────────────────────────┘


┌────────────────────────────────────────────────────────────────┐
│                    EXTERNAL SERVICES                           │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌──────────────┐    ┌──────────────┐    ┌────────────────┐  │
│  │   Groq API   │    │ Hugging Face │    │   File System  │  │
│  │   (Llama 3)  │    │   (BERT)     │    │   (Storage)    │  │
│  │              │    │              │    │                │  │
│  │ • Parse      │    │ • Embeddings │    │ • Uploads      │  │
│  │ • Extract    │    │ • Similarity │    │ • Logs         │  │
│  └──────────────┘    └──────────────┘    └────────────────┘  │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

---

## Data Flow Diagram

```
┌──────────┐
│  User    │
└────┬─────┘
     │
     │ 1. Upload JD + Resumes
     │
     ▼
┌────────────────┐
│  Streamlit/    │
│  FastAPI       │
└────┬───────────┘
     │
     │ 2. Create request
     │
     ▼
┌──────────────────────┐
│  ScreeningService    │
│  • Process JD        │
│  • Loop resumes      │
└────┬─────────────────┘
     │
     │ 3. For each resume
     │
     ├─────────────┬────────────────┐
     │             │                │
     ▼             ▼                ▼
┌─────────┐  ┌───────────┐  ┌────────────┐
│ Extract │  │ Calculate │  │   Parse    │
│  Text   │  │ Embedding │  │  with LLM  │
└────┬────┘  └─────┬─────┘  └─────┬──────┘
     │             │                │
     │             ▼                │
     │      ┌──────────────┐       │
     │      │  Similarity  │       │
     │      │  Calculation │       │
     │      └──────┬───────┘       │
     │             │                │
     └─────────────┴────────────────┘
                   │
                   │ 4. Combine results
                   │
                   ▼
         ┌──────────────────┐
         │ ScreeningResult  │
         │  • Score         │
         │  • Data          │
         └────┬─────────────┘
              │
              │ 5. Save to DB
              │
              ▼
         ┌──────────────┐
         │   Database   │
         └────┬─────────┘
              │
              │ 6. Return results
              │
              ▼
         ┌──────────────┐
         │  Display to  │
         │     User     │
         └──────────────┘
```

---

## Component Interaction

```
┌─────────────────────────────────────────────────────────────┐
│                    Request Flow                             │
└─────────────────────────────────────────────────────────────┘

HTTP Request → FastAPI Router → Endpoint Handler
                                      │
                                      ▼
                                Service Layer
                                      │
                    ┌─────────────────┼─────────────────┐
                    │                 │                 │
                    ▼                 ▼                 ▼
              EmbeddingService  ParserService  DatabaseRepo
                    │                 │                 │
                    ▼                 ▼                 ▼
               BERT Model        Groq API         SQLAlchemy
                    │                 │                 │
                    └─────────────────┴─────────────────┘
                                      │
                                      ▼
                              Response Object
                                      │
                                      ▼
                                 JSON Response


┌─────────────────────────────────────────────────────────────┐
│                Configuration Management                      │
└─────────────────────────────────────────────────────────────┘

.env file → settings.py (Pydantic) → Components
                │
                ├→ API Keys
                ├→ Model Names
                ├→ Database URL
                ├→ Ports
                └→ Logging Config
```

---

## Deployment Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                     Development                              │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Python Virtual Environment                                  │
│  • Local SQLite                                             │
│  • streamlit run streamlit_app.py                          │
│  • python -m uvicorn src.api.main:app --reload             │
│                                                              │
└──────────────────────────────────────────────────────────────┘


┌──────────────────────────────────────────────────────────────┐
│                     Docker Compose                           │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────┐        ┌──────────────────┐          │
│  │  streamlit       │        │      api         │          │
│  │  Container       │        │   Container      │          │
│  │  Port: 8501      │        │   Port: 8000     │          │
│  └────────┬─────────┘        └────────┬─────────┘          │
│           │                           │                     │
│           └───────────┬───────────────┘                     │
│                       │                                     │
│                  ┌────▼─────┐                              │
│                  │  Shared  │                              │
│                  │  Volume  │                              │
│                  │  (data)  │                              │
│                  └──────────┘                              │
│                                                              │
└──────────────────────────────────────────────────────────────┘


┌──────────────────────────────────────────────────────────────┐
│                     Cloud Production                         │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────────────────────────────────────┐       │
│  │                Load Balancer                      │       │
│  └────────┬──────────────────────────┬───────────────┘       │
│           │                          │                       │
│  ┌────────▼─────────┐      ┌────────▼─────────┐            │
│  │  App Instance 1  │      │  App Instance 2  │            │
│  │  (Container)     │      │  (Container)     │            │
│  └────────┬─────────┘      └────────┬─────────┘            │
│           │                          │                       │
│           └──────────┬───────────────┘                       │
│                      │                                       │
│              ┌───────▼────────┐                             │
│              │   PostgreSQL    │                             │
│              │    Database     │                             │
│              │   (RDS/Cloud)   │                             │
│              └─────────────────┘                             │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## Technology Stack Layers

```
┌─────────────────────────────────────────────────────────┐
│  Layer 1: Presentation / UI                             │
├─────────────────────────────────────────────────────────┤
│  • Streamlit (Web UI)                                   │
│  • HTML/CSS (Styling)                                   │
│  • Plotly, Matplotlib (Charts)                          │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  Layer 2: API / Interface                               │
├─────────────────────────────────────────────────────────┤
│  • FastAPI (REST Endpoints)                             │
│  • Pydantic (Validation)                                │
│  • OpenAPI/Swagger (Documentation)                      │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  Layer 3: Business Logic                                │
├─────────────────────────────────────────────────────────┤
│  • ScreeningService (Orchestration)                     │
│  • EmbeddingService (BERT)                              │
│  • ResumeParserService (LLM)                            │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  Layer 4: Data Access                                   │
├─────────────────────────────────────────────────────────┤
│  • Repository Pattern                                   │
│  • SQLAlchemy ORM                                       │
│  • Database Models                                      │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  Layer 5: Data Storage                                  │
├─────────────────────────────────────────────────────────┤
│  • SQLite (Development)                                 │
│  • PostgreSQL (Production)                              │
│  • File System (Uploads, Logs)                          │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  Layer 6: External Services                             │
├─────────────────────────────────────────────────────────┤
│  • Groq API (LLM)                                       │
│  • Hugging Face (BERT Models)                           │
│  • PyTorch (ML Framework)                               │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  Layer 7: Infrastructure                                │
├─────────────────────────────────────────────────────────┤
│  • Docker (Containerization)                            │
│  • Docker Compose (Orchestration)                       │
│  • GitHub Actions (CI/CD)                               │
└─────────────────────────────────────────────────────────┘
```

---

## Security Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Security Layers                                        │
└─────────────────────────────────────────────────────────┘

┌──────────────────┐
│  Environment     │  ← API Keys stored securely
│  Variables       │  ← Not in code repository
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Input           │  ← File type validation
│  Validation      │  ← Size limits
└────────┬─────────┘  ← Content sanitization
         │
         ▼
┌──────────────────┐
│  API Layer       │  ← Rate limiting (via Groq)
│                  │  ← Error handling
└────────┬─────────┘  ← Request validation
         │
         ▼
┌──────────────────┐
│  Data Layer      │  ← SQL injection prevention (ORM)
│                  │  ← Data sanitization
└────────┬─────────┘  ← Access control ready
         │
         ▼
┌──────────────────┐
│  Storage         │  ← File permissions
│                  │  ← Database security
└──────────────────┘
```

---

## Scalability Design

```
Current (Single Instance)
┌──────────────────┐
│   Application    │
│   • Streamlit    │
│   • API          │
│   • Database     │
└──────────────────┘

Future (Scaled)
┌──────────────────────────────────────────┐
│          Load Balancer                   │
└────┬──────────┬──────────┬───────────────┘
     │          │          │
┌────▼────┐ ┌──▼──────┐ ┌─▼─────────┐
│  App 1  │ │  App 2  │ │  App N    │
└────┬────┘ └──┬──────┘ └─┬─────────┘
     │         │           │
     └─────────┴───────────┴──┐
                               │
                        ┌──────▼───────┐
                        │   Redis      │
                        │   (Cache)    │
                        └──────┬───────┘
                               │
                        ┌──────▼───────┐
                        │  PostgreSQL  │
                        │  (Database)  │
                        └──────────────┘
```

---

## CI/CD Pipeline

```
┌──────────────────────────────────────────────────────────┐
│                     Git Push                             │
└───────────────────┬──────────────────────────────────────┘
                    │
                    ▼
           ┌────────────────┐
           │  GitHub Action │
           │    Triggered   │
           └────────┬───────┘
                    │
        ┌───────────┴───────────┐
        │                       │
        ▼                       ▼
┌───────────────┐      ┌───────────────┐
│  Run Tests    │      │  Lint Code    │
│  (pytest)     │      │  (flake8)     │
└───────┬───────┘      └───────┬───────┘
        │                       │
        └───────────┬───────────┘
                    │
                    ▼
            ┌───────────────┐
            │  Build Docker │
            │     Image     │
            └───────┬───────┘
                    │
                    ▼
            ┌───────────────┐
            │  Push to      │
            │  Registry     │
            └───────┬───────┘
                    │
                    ▼
            ┌───────────────┐
            │    Deploy     │
            │  to Cloud     │
            └───────────────┘
```

---

This architecture ensures:

✅ **Separation of Concerns**: Each layer has a specific responsibility  
✅ **Scalability**: Can grow from single instance to distributed system  
✅ **Maintainability**: Clear structure makes changes easier  
✅ **Testability**: Each component can be tested independently  
✅ **Security**: Multiple layers of protection  
✅ **Flexibility**: Easy to swap components (e.g., database, LLM provider)  

