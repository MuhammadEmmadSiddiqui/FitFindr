"""Configuration for pytest"""
import pytest
import sys
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

# Add backend/ to Python path so `from src.xxx import yyy` works
sys.path.insert(0, str(Path(__file__).parent.parent))

# Path to Sample_data at project root (backend/tests/ -> backend/ -> FitFindr/)
SAMPLE_DATA_DIR = Path(__file__).parent.parent.parent / "Sample_data"

from src.database.database import Base, get_db  # noqa: E402
from src.api.main import app  # noqa: E402


# ---------------------------------------------------------------------------
# Database fixtures — fresh in-memory SQLite per test function
# ---------------------------------------------------------------------------

@pytest.fixture
def db_session():
    """Provide a clean in-memory SQLite session for each test.

    StaticPool forces all SQLAlchemy operations to reuse the same underlying
    connection, so tables created at setup time are visible to every query.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(bind=engine)
    session = TestSession()
    yield session
    session.close()
    engine.dispose()


@pytest.fixture
def client(db_session):
    """TestClient with the production get_db dependency replaced by the test session."""
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Auth fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def registered_user(client):
    """Register a test user and return the response body."""
    resp = client.post("/auth/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpass123",
    })
    assert resp.status_code == 201, resp.text
    return resp.json()


@pytest.fixture
def auth_headers(client, registered_user):
    """Return Authorization headers for the registered test user."""
    resp = client.post("/auth/login", data={
        "username": "testuser",
        "password": "testpass123",
    })
    assert resp.status_code == 200, resp.text
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Text fixtures (kept for backward compatibility)
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_resume_text():
    """Sample resume text for testing."""
    return """
    John Doe
    Software Engineer
    Email: john.doe@example.com

    Experience:
    - Tech Corp (2020-2023): Senior Developer
    - StartupXYZ (2018-2020): Junior Developer

    Skills: Python, JavaScript, React, Docker
    """


@pytest.fixture
def sample_jd_text():
    """Sample job description text for testing."""
    return """
    Looking for a Senior Software Engineer with experience in:
    - Python and web frameworks
    - Cloud technologies (AWS, Docker)
    - Frontend development (React, Vue)
    - 3+ years of experience
    """
