# Quick Start Guide

## 🚀 Getting Started in 5 Minutes

### 1. Setup Environment

```bash
# Clone the repository
git clone https://github.com/MuhammadEmmadSiddiqui/FitFindr.git
cd FitFindr

# Copy environment template
cp .env.example .env
```

### 2. Get API Keys

1. Visit [Groq Console](https://console.groq.com)
2. Sign up for a free account
3. Generate API key(s)
4. Add to `.env` file:

```bash
GROQ_API_KEYS=your_key_here
```

### 3. Choose Your Setup

#### Option A: Docker (Recommended)

```bash
docker-compose up -d

# Access at:
# Streamlit: http://localhost:8501
# API: http://localhost:8000/docs
```

#### Option B: Local Development

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run Streamlit
streamlit run streamlit_app.py

# Or run API
python -m uvicorn src.api.main:app --reload
```

## 📝 First Screening

1. **Open Streamlit** (http://localhost:8501)
2. **Upload Job Description** - Use the sidebar file uploader
3. **Upload Resumes** - Select one or multiple resume files
4. **View Results** - Get instant AI-powered rankings!

## 🔧 Configuration

### Database

Default: SQLite (no setup needed)

For PostgreSQL:
```bash
DATABASE_URL=postgresql://user:pass@localhost:5432/fitfindr
```

### Models

Change in `.env`:
```bash
BERT_MODEL=bert-base-uncased
LLM_MODEL=llama3-8b-8192
```

## 🧪 Testing

```bash
# Run tests
pytest

# With coverage
pytest --cov=src
```

## 📚 Next Steps

- Check out the [full README](README.md)
- Explore the [API documentation](http://localhost:8000/docs)
- Read [contributing guidelines](CONTRIBUTING.md)
- Review the architecture in [README](README.md#architecture)

## ❓ Troubleshooting

### API Key Issues
- Ensure `.env` file exists
- Check API key is valid on Groq console
- Try using multiple keys separated by commas

### Model Download Issues
- First run will download BERT model (~400MB)
- Ensure stable internet connection
- Check disk space

### Port Conflicts
Change ports in `.env`:
```bash
STREAMLIT_PORT=8502
API_PORT=8001
```

## 📞 Need Help?

- [Open an issue](https://github.com/MuhammadEmmadSiddiqui/FitFindr/issues)
- Check existing issues for solutions
- Review documentation

---

**You're all set! Start screening resumes with AI! 🎉**
