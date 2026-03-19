"""Unit tests for FitFindr"""
import pytest
from src.utils.text_processing import preprocess_text


def test_preprocess_text():
    """Test text preprocessing"""
    text = "Hello, World! This is a TEST."
    result = preprocess_text(text)
    
    assert result == "hello world this is a test"
    assert " " in result
    assert "," not in result
    assert "!" not in result


def test_preprocess_text_empty():
    """Test preprocessing empty text"""
    result = preprocess_text("")
    assert result == ""


def test_preprocess_text_whitespace():
    """Test preprocessing multiple whitespaces"""
    text = "Multiple    spaces   here"
    result = preprocess_text(text)
    assert result == "multiple spaces here"
