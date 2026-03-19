"""Text processing utilities"""
import re
from typing import BinaryIO
import pypdfium2 as pdfium


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
    Extract text content from a PDF file using pypdfium2.

    Uses the PDF's embedded text layer directly — no ML models required.

    Args:
        pdf_file: PDF file object (BytesIO or any readable binary stream)

    Returns:
        Extracted text content
    """
    pdf_bytes = pdf_file.read()
    doc = pdfium.PdfDocument(pdf_bytes)
    pages = []
    for page in doc:
        textpage = page.get_textpage()
        pages.append(textpage.get_text_range())
    doc.close()
    return "\n".join(pages)
