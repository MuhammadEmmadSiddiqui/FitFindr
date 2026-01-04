# 🎯 FitFindr - AI-Powered Resume Screening Platform

<div align="center">

![FitFindr Logo](https://img.shields.io/badge/FitFindr-AI%20Resume%20Screening-blue?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.10+-green?style=for-the-badge&logo=python)
![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)

**Streamline your hiring process with AI-powered resume analysis and candidate matching**

[Features](#features) • [Quick Start](#quick-start) • [Documentation](#documentation) • [Demo](#demo)

</div>

---

## 📋 Overview

FitFindr is an enterprise-grade resume screening application that leverages state-of-the-art AI models to automatically analyze, rank, and extract structured information from candidate resumes. Built with scalability and production-readiness in mind, it's perfect for showcasing in your resume and scaling for real-world use.

### 🎯 Key Highlights

- **AI-Powered Matching**: Uses BERT embeddings for semantic similarity scoring
- **Intelligent Extraction**: LLM-based structured data extraction from unstructured resumes
- **Dual Interface**: Modern Streamlit UI + RESTful FastAPI backend
- **Production Ready**: Dockerized, tested, and CI/CD enabled
- **Database Persistence**: SQLite/PostgreSQL support for historical tracking
- **Scalable Architecture**: Modular design with clear separation of concerns

---

## ✨ Features

### Core Capabilities

- 📊 **Semantic Similarity Matching**: Calculate job-resume fit using BERT embeddings
- 🤖 **Automated Data Extraction**: Extract contact info, skills, experience, education
- 📈 **Candidate Ranking**: Automatically rank candidates by relevance
- 🎨 **Interactive Dashboard**: Beautiful Streamlit interface with charts and filters
- 🔌 **REST API**: FastAPI endpoints for programmatic access
- 💾 **Persistent Storage**: Save and retrieve historical screening results
- 📊 **Advanced Analytics**: Visualize skills distribution, experience levels, universities

### Technical Features

- **Multi-file Processing**: Batch process dozens of resumes simultaneously
- **Multiple API Keys**: Built-in rotation for rate limit handling
- **Flexible File Formats**: Support for PDF and TXT files
- **Configurable Models**: Easy swap between different BERT and LLM models
- **Comprehensive Logging**: Track all operations for debugging and audit
- **Unit Tested**: Core functionality covered by pytest
- **Docker Ready**: Full containerization with docker-compose

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Docker & Docker Compose (optional)
- Groq API Key ([Get one free](https://console.groq.com))

### Installation

#### Option 1: Local Development

```bash
# Clone the repository
git clone https://github.com/MuhammadEmmadSiddiqui/FitFindr.git
cd FitFindr

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment variables
cp .env.example .env
# Edit .env and add your GROQ_API_KEYS

# Run Streamlit app
streamlit run streamlit_app.py

# Or run FastAPI backend
python -m uvicorn src.api.main:app --reload
```

#### Option 2: Docker

```bash
# Clone the repository
git clone https://github.com/MuhammadEmmadSiddiqui/FitFindr.git
cd FitFindr

# Setup environment
cp .env.example .env
# Edit .env and add your GROQ_API_KEYS

# Run with Docker Compose
docker-compose up -d

# Access applications
# Streamlit: http://localhost:8501
# FastAPI: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

---

## 📖 Usage

### Streamlit Web Interface

1. **Upload Job Description**: Drag and drop the JD file (PDF or TXT)
2. **Upload Resumes**: Select multiple resume files
3. **View Results**: Get instant rankings with similarity scores
4. **Explore Analytics**: Dive into skills distribution, universities, experience
5. **Filter Candidates**: Use interactive filters to find the best matches
6. **Export Results**: Download CSV for further analysis

### REST API

```python
import requests

# Upload files for screening
url = "http://localhost:8000/api/screen"
files = {
    'job_description': open('jd.pdf', 'rb'),
    'resumes': [
        open('resume1.pdf', 'rb'),
        open('resume2.pdf', 'rb'),
    ]
}

response = requests.post(url, files=files)
results = response.json()

# Get recent screening results
response = requests.get("http://localhost:8000/api/results?limit=50")
historical_data = response.json()
```

### Python Package

```python
from src.services import ScreeningService
from src.utils import preprocess_text

# Initialize service
service = ScreeningService()

# Screen resumes
results = service.screen_multiple_resumes(
    resume_files=[(file, filename, filetype), ...],
    jd_file=jd_file,
    jd_type="application/pdf"
)

# Access structured results
for result in results:
    print(f"{result.full_name}: {result.similarity_score:.2%}")
```

---

## 🏗️ Architecture

```
FitFindr/
├── src/
│   ├── api/              # FastAPI REST endpoints
│   ├── database/         # SQLAlchemy models & repository
│   ├── models/           # Pydantic data models
│   ├── services/         # Business logic (embedding, parsing, screening)
│   ├── utils/            # Helper functions
│   └── config.py         # Configuration management
├── tests/                # Unit tests
├── data/                 # Data storage
├── logs/                 # Application logs
├── streamlit_app.py      # Streamlit web UI
├── app.py                # Original prototype (legacy)
├── requirements.txt      # Python dependencies
├── Dockerfile            # Container definition
├── docker-compose.yml    # Multi-container setup
└── .env.example          # Environment template
```

### Technology Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | Streamlit 1.41+ |
| **Backend API** | FastAPI 0.115+ |
| **ML Models** | BERT (transformers), Groq Llama 3 |
| **Database** | SQLAlchemy (SQLite/PostgreSQL) |
| **ML Framework** | PyTorch, scikit-learn |
| **Visualization** | Matplotlib, Seaborn, Plotly, WordCloud |
| **Testing** | Pytest |
| **Containerization** | Docker, Docker Compose |

---

## 🔧 Configuration

### Environment Variables

Create a `.env` file from `.env.example`:

```bash
# Required
GROQ_API_KEYS=key1,key2,key3

# Optional (with defaults)
DEBUG=False
DATABASE_URL=sqlite:///./data/fitfindr.db
LOG_LEVEL=INFO

# Model Configuration
BERT_MODEL=bert-base-uncased
LLM_MODEL=llama3-8b-8192
```

### Database Options

**SQLite (Default)**
```
DATABASE_URL=sqlite:///./data/fitfindr.db
```

**PostgreSQL**
```
DATABASE_URL=postgresql://user:password@localhost:5432/fitfindr
```

---

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_utils.py -v
```

---

## 📊 API Documentation

Once the FastAPI server is running, visit:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Main Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check |
| `/api/screen` | POST | Screen resumes against JD |
| `/api/results` | GET | Get historical results |

---

## 🚢 Deployment

### Docker Production Build

```bash
# Build image
docker build -t fitfindr:latest .

# Run container
docker run -d \
  -p 8501:8501 \
  -p 8000:8000 \
  -e GROQ_API_KEYS=your_keys \
  -v $(pwd)/data:/app/data \
  fitfindr:latest
```

### Cloud Deployment

**Recommended Platforms:**
- **Streamlit Cloud**: For the web interface
- **AWS ECS/Fargate**: For containerized deployment
- **Google Cloud Run**: Serverless container platform
- **Azure Container Instances**: Quick container deployment
- **Heroku**: Easy deployment with Procfile

---

## 🎯 Resume & Portfolio

This project demonstrates:

✅ **Full-Stack Development**: Frontend (Streamlit) + Backend (FastAPI)  
✅ **Machine Learning**: BERT embeddings, NLP, similarity analysis  
✅ **Software Engineering**: Clean architecture, modular design, SOLID principles  
✅ **Database Design**: ORM usage, data persistence, migrations  
✅ **DevOps**: Docker, docker-compose, CI/CD pipelines  
✅ **Testing**: Unit tests, integration tests, test coverage  
✅ **API Design**: RESTful APIs, OpenAPI documentation  
✅ **Cloud Ready**: Environment configuration, logging, error handling  

---

## 🛣️ Roadmap

- [ ] Add user authentication and multi-tenancy
- [ ] Implement Redis caching for embeddings
- [ ] Add support for more document formats (DOCX, HTML)
- [ ] Build Chrome extension for LinkedIn integration
- [ ] Add real-time collaboration features
- [ ] Implement advanced filtering with boolean logic
- [ ] Create mobile-responsive PWA
- [ ] Add email integration for automated candidate outreach
- [ ] Implement A/B testing for different matching algorithms
- [ ] Add explainability features (why this match score?)

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👨‍💻 Author

**Muhammad Emmad Siddiqui**

- GitHub: [@MuhammadEmmadSiddiqui](https://github.com/MuhammadEmmadSiddiqui)
- LinkedIn: [Connect with me](https://linkedin.com/in/muhammad-emmad-siddiqui)

---

## 🙏 Acknowledgments

- BERT model by Google Research
- Groq for fast LLM inference
- Streamlit for the amazing web framework
- FastAPI for the high-performance backend framework

---

## 📞 Support

For questions or support, please:
- Open an issue on GitHub
- Contact via LinkedIn
- Email: [your-email@example.com]

---

<div align="center">

**Made with ❤️ for smarter hiring**

⭐ Star this repo if you find it helpful!

</div>
