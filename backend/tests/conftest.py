"""Configuration for pytest"""
import pytest
import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def sample_resume_text():
    """Sample resume text for testing"""
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
    """Sample job description for testing"""
    return """
    Looking for a Senior Software Engineer with experience in:
    - Python and web frameworks
    - Cloud technologies (AWS, Docker)
    - Frontend development (React, Vue)
    - 3+ years of experience
    """
