"""Tests for API endpoints."""
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from src.api.main import app
from src.models import ScreeningResult
from tests.conftest import SAMPLE_DATA_DIR


# ---------------------------------------------------------------------------
# Health endpoints (no auth required)
# ---------------------------------------------------------------------------

def test_root_endpoint(client):
    """GET / returns 200 with healthy status."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_health_check(client):
    """GET /health returns 200 with healthy status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


# ---------------------------------------------------------------------------
# Auth — /auth/register
# ---------------------------------------------------------------------------

def test_register_new_user(client):
    """POST /auth/register creates a new user and returns 201."""
    resp = client.post("/auth/register", json={
        "username": "alice",
        "email": "alice@example.com",
        "password": "secret123",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["username"] == "alice"
    assert data["email"] == "alice@example.com"
    assert "id" in data
    assert "hashed_password" not in data  # password must NOT be exposed


def test_register_duplicate_username(client):
    """POST /auth/register with an existing username returns 409."""
    payload = {"username": "bob", "email": "bob@example.com", "password": "pass"}
    client.post("/auth/register", json=payload)
    resp = client.post("/auth/register", json={**payload, "email": "bob2@example.com"})
    assert resp.status_code == 409


def test_register_duplicate_email(client):
    """POST /auth/register with an existing email returns 409."""
    payload = {"username": "carol", "email": "carol@example.com", "password": "pass"}
    client.post("/auth/register", json=payload)
    resp = client.post("/auth/register", json={**payload, "username": "carol2"})
    assert resp.status_code == 409


# ---------------------------------------------------------------------------
# Auth — /auth/login
# ---------------------------------------------------------------------------

def test_login_success(client, registered_user):
    """POST /auth/login returns a bearer token for valid credentials."""
    resp = client.post("/auth/login", data={
        "username": "testuser",
        "password": "testpass123",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client, registered_user):
    """POST /auth/login returns 401 for a wrong password."""
    resp = client.post("/auth/login", data={
        "username": "testuser",
        "password": "wrongpassword",
    })
    assert resp.status_code == 401


def test_login_unknown_user(client):
    """POST /auth/login returns 401 for a non-existent username."""
    resp = client.post("/auth/login", data={
        "username": "nobody",
        "password": "pass",
    })
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Auth — /auth/me
# ---------------------------------------------------------------------------

def test_get_me_requires_auth(client):
    """GET /auth/me without a token returns 401."""
    resp = client.get("/auth/me")
    assert resp.status_code == 401


def test_get_me_with_token(client, auth_headers):
    """GET /auth/me returns the current user's profile."""
    resp = client.get("/auth/me", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"
    assert data["is_active"] is True


# ---------------------------------------------------------------------------
# /api/screen
# ---------------------------------------------------------------------------

def test_screen_requires_auth(client):
    """POST /api/screen without a token returns 401."""
    resp = client.post("/api/screen", files=[
        ("job_description", ("jd.txt", b"some JD", "text/plain")),
        ("resumes", ("cv.pdf", b"some resume", "application/pdf")),
    ])
    assert resp.status_code == 401


def test_screen_resumes_mocked(client, auth_headers):
    """POST /api/screen returns screening results (LLM mocked)."""
    mock_result = ScreeningResult(
        resume_filename="candidate_cv.pdf",
        similarity_score=0.85,
        full_name="Jane Candidate",
        email_id="jane@example.com",
        technical_skills=["Python", "FastAPI"],
        total_experience="2.0 yrs",
    )

    with patch("src.api.main.GraphScreeningService") as MockSvc:
        MockSvc.return_value.screen_multiple_resumes.return_value = [mock_result]

        resp = client.post(
            "/api/screen",
            files=[
                ("job_description", ("jd.txt", b"Looking for a Python developer", "text/plain")),
                ("resumes", ("candidate_cv.pdf", b"Jane Candidate, Python developer", "application/pdf")),
            ],
            headers=auth_headers,
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["total_resumes"] == 1
    assert data["results"][0]["full_name"] == "Jane Candidate"
    assert data["results"][0]["similarity_score"] == 0.85
    assert "Python" in data["results"][0]["technical_skills"]


def test_screen_multiple_resumes_mocked(client, auth_headers):
    """POST /api/screen handles multiple resume files."""
    mock_results = [
        ScreeningResult(resume_filename="cv1.pdf", similarity_score=0.90, full_name="Alice"),
        ScreeningResult(resume_filename="cv2.pdf", similarity_score=0.65, full_name="Bob"),
    ]

    with patch("src.api.main.GraphScreeningService") as MockSvc:
        MockSvc.return_value.screen_multiple_resumes.return_value = mock_results

        resp = client.post(
            "/api/screen",
            files=[
                ("job_description", ("jd.txt", b"Senior Python dev needed", "text/plain")),
                ("resumes", ("cv1.pdf", b"Alice resume", "application/pdf")),
                ("resumes", ("cv2.pdf", b"Bob resume", "application/pdf")),
            ],
            headers=auth_headers,
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["total_resumes"] == 2
    names = [r["full_name"] for r in data["results"]]
    assert "Alice" in names
    assert "Bob" in names


def test_screen_with_sample_data_files(client, auth_headers):
    """POST /api/screen works with real PDF + TXT files from Sample_data (LLM mocked)."""
    jd_path = SAMPLE_DATA_DIR / "JD-Instructors.txt"
    cv_path = SAMPLE_DATA_DIR / "Muhammad Emmad Siddiqui CV.pdf"

    if not jd_path.exists() or not cv_path.exists():
        pytest.skip("Sample_data files not present — skipping")

    mock_result = ScreeningResult(
        resume_filename="Muhammad Emmad Siddiqui CV.pdf",
        similarity_score=0.78,
        full_name="Muhammad Emmad Siddiqui",
    )

    with patch("src.api.main.GraphScreeningService") as MockSvc:
        MockSvc.return_value.screen_multiple_resumes.return_value = [mock_result]

        with open(jd_path, "rb") as jd_f, open(cv_path, "rb") as cv_f:
            resp = client.post(
                "/api/screen",
                files=[
                    ("job_description", ("JD-Instructors.txt", jd_f, "text/plain")),
                    ("resumes", ("Muhammad Emmad Siddiqui CV.pdf", cv_f, "application/pdf")),
                ],
                headers=auth_headers,
            )

    assert resp.status_code == 200
    assert resp.json()["total_resumes"] == 1


# ---------------------------------------------------------------------------
# /api/results
# ---------------------------------------------------------------------------

def test_get_results_requires_auth(client):
    """GET /api/results without a token returns 401."""
    resp = client.get("/api/results")
    assert resp.status_code == 401


def test_get_results_empty(client, auth_headers):
    """GET /api/results returns an empty list when no screenings exist."""
    resp = client.get("/api/results", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json() == []


def test_get_results_after_screening(client, auth_headers):
    """GET /api/results reflects previously screened resumes."""
    mock_result = ScreeningResult(
        resume_filename="stored_cv.pdf",
        similarity_score=0.70,
        full_name="Stored Candidate",
    )

    with patch("src.api.main.GraphScreeningService") as MockSvc:
        MockSvc.return_value.screen_multiple_resumes.return_value = [mock_result]
        client.post(
            "/api/screen",
            files=[
                ("job_description", ("jd.txt", b"We need a developer", "text/plain")),
                ("resumes", ("stored_cv.pdf", b"Stored Candidate resume", "application/pdf")),
            ],
            headers=auth_headers,
        )

    resp = client.get("/api/results", headers=auth_headers)
    assert resp.status_code == 200
    results = resp.json()
    assert len(results) >= 1
    assert results[0]["resume_filename"] == "stored_cv.pdf"


def test_get_results_limit(client, auth_headers):
    """GET /api/results?limit=1 returns at most 1 result."""
    mock_results = [
        ScreeningResult(resume_filename=f"cv{i}.pdf", similarity_score=0.5)
        for i in range(3)
    ]

    with patch("src.api.main.GraphScreeningService") as MockSvc:
        MockSvc.return_value.screen_multiple_resumes.return_value = mock_results
        client.post(
            "/api/screen",
            files=[
                ("job_description", ("jd.txt", b"JD text", "text/plain")),
                ("resumes", ("cv0.pdf", b"r0", "application/pdf")),
                ("resumes", ("cv1.pdf", b"r1", "application/pdf")),
                ("resumes", ("cv2.pdf", b"r2", "application/pdf")),
            ],
            headers=auth_headers,
        )

    resp = client.get("/api/results?limit=1", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1

