"""Text processing utilities"""
import re
import fitz
from typing import BinaryIO


def preprocess_text(text: str) -> str:
    """
    Preprocess text by removing special characters and normalizing whitespace
    
    Args:
        text: Input text to preprocess
        
    Returns:
        Preprocessed lowercase text
    """
    text = re.sub(r'\W', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.lower()


def decode_file(file: BinaryIO) -> str:
    """
    Decode file content with fallback encoding
    
    Args:
        file: Binary file object
        
    Returns:
        Decoded text content
    """
    try:
        return file.getvalue().decode("utf-8")
    except UnicodeDecodeError:
        return file.getvalue().decode("ISO-8859-1")


def extract_text_from_pdf(pdf_file: BinaryIO) -> str:
    """
    Extract text content from PDF file
    
    Args:
        pdf_file: PDF file object
        
    Returns:
        Extracted text content
    """
    pdf_bytes = pdf_file.read()
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text("text")
    return text
