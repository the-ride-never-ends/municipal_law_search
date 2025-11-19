"""
Content and Text Fixtures for upload_document testing.

This module provides fixtures for text content validation,
extraction testing, and various content scenarios.
"""
from typing import Tuple
import pytest


# ============================================================================
# Content Constants
# ============================================================================

KNOWN_TEXT_CONTENT = """This is a comprehensive test document for content extraction testing.

It contains multiple paragraphs with various formatting and special characters.

Special characters: !@#$%^&*()_+-=[]{}|;:'"<>?,.

Numbers: 1234567890

Mixed content: The year 2025 marks significant progress in AI technology.

Unicode content: This document tests unicode handling: café, naïve, résumé.

Legal-style content: Whereas the party of the first part agrees to the terms
and conditions set forth herein, the party of the second part shall comply
with all applicable regulations and statutes.

End of test document."""

UNICODE_TEXT_CONTENT = """Unicode Test Document

This document contains various Unicode characters for testing:

Accented characters: café, naïve, résumé, jalapeño, piñata
Greek letters: α, β, γ, δ, ε, Ω, Φ, Ψ
Mathematical symbols: ∑, ∏, ∫, √, ∞, ≤, ≥, ≠
Currency symbols: $, €, £, ¥, ₹
Chinese characters: 你好世界 (Hello World)
Japanese characters: こんにちは (Hello)
Arabic characters: مرحبا (Hello)
Russian characters: Привет (Hello)

Emoji (if supported): 😀 🌟 🚀 📄 ✅

This tests the system's ability to handle international text."""

LARGE_TEXT_CONTENT = """Large Content Test Document

""" + "This is line {} with repeated content for testing large file processing.\n" * 1000

MINIMAL_TEXT_CONTENT = "Minimal content."

EMPTY_TEXT_CONTENT = ""

WHITESPACE_TEXT_CONTENT = """   

\t\t\t

   \n\n\n   

"""

LEGAL_DOCUMENT_SAMPLE = """UNITED STATES CONSTITUTION

We the People of the United States, in Order to form a more perfect Union,
establish Justice, insure domestic Tranquility, provide for the common defence,
promote the general Welfare, and secure the Blessings of Liberty to ourselves
and our Posterity, do ordain and establish this Constitution for the United
States of America.

ARTICLE I
Section 1. All legislative Powers herein granted shall be vested in a Congress
of the United States, which shall consist of a Senate and House of Representatives.

Section 2. The House of Representatives shall be composed of Members chosen
every second Year by the People of the several States, and the Electors in
each State shall have the Qualifications requisite for Electors of the most
numerous Branch of the State Legislature."""


# ============================================================================
# Content and Text Fixtures
# ============================================================================

@pytest.fixture
def known_text_content():
    """
    Known text content for content extraction testing.
    
    Returns:
        str: Known text content for validation
    """
    return KNOWN_TEXT_CONTENT


@pytest.fixture
def unicode_text_content():
    """
    Text content with Unicode characters.
    
    Returns:
        str: Text content containing Unicode characters
    """
    return UNICODE_TEXT_CONTENT


@pytest.fixture
def large_text_content():
    """
    Large text content for testing content processing limits.
    
    Returns:
        str: Large text content for limit testing
    """
    return LARGE_TEXT_CONTENT


@pytest.fixture
def minimal_text_content():
    """
    Minimal text content for boundary testing.
    
    Returns:
        str: Minimal text content
    """
    return MINIMAL_TEXT_CONTENT


@pytest.fixture
def empty_text_content():
    """
    Empty text content for edge case testing.
    
    Returns:
        str: Empty text content
    """
    return EMPTY_TEXT_CONTENT


@pytest.fixture
def whitespace_text_content():
    """
    Text content with only whitespace characters.
    
    Returns:
        str: Whitespace-only text content
    """
    return WHITESPACE_TEXT_CONTENT


@pytest.fixture
def legal_document_sample():
    """
    Sample legal document text for realistic testing.
    
    Returns:
        str: Legal document sample text
    """
    return LEGAL_DOCUMENT_SAMPLE


@pytest.fixture
def pdf_with_known_text(known_text_content):
    """
    PDF file containing specific known text for extraction testing.
    
    Args:
        known_text_content: Known text content from fixture
        
    Returns:
        tuple[bytes, str]: PDF content and expected extracted text
    """
    from .archived_fixtures.file_upload_fixtures import _create_pdf_content
    pdf_content = _create_pdf_content(known_text_content)
    return pdf_content, known_text_content


@pytest.fixture
def docx_with_unicode_text(unicode_text_content):
    """
    DOCX file containing Unicode text for extraction testing.
    
    Args:
        unicode_text_content: Unicode text content from fixture
        
    Returns:
        tuple[bytes, str]: DOCX content and expected extracted text
    """
    from .archived_fixtures.file_upload_fixtures import _create_docx_content
    docx_content = _create_docx_content(unicode_text_content)
    return docx_content, unicode_text_content


@pytest.fixture
def txt_with_legal_content(legal_document_sample):
    """
    TXT file containing legal document sample.
    
    Args:
        legal_document_sample: Legal document text from fixture
        
    Returns:
        tuple[bytes, str]: TXT content and expected text
    """
    txt_content = legal_document_sample.encode('utf-8')
    return txt_content, legal_document_sample


@pytest.fixture
def files_with_identical_content(known_text_content):
    """
    Multiple files with identical content for CID consistency testing.
    
    Args:
        known_text_content: Known text content from fixture
        
    Returns:
        list[tuple[bytes, str, str]]: List of (content, filename, expected_text) tuples
    """
    from .archived_fixtures.file_upload_fixtures import _create_pdf_content, _create_docx_content
    
    pdf_content = _create_pdf_content(known_text_content)
    txt_content = known_text_content.encode('utf-8')
    
    return [
        (pdf_content, "document1.pdf", known_text_content),
        (txt_content, "document1.txt", known_text_content),
        (pdf_content, "document2.pdf", known_text_content),
        (txt_content, "document2.txt", known_text_content)
    ]


@pytest.fixture
def content_extraction_test_cases():
    """
    Various content types for comprehensive extraction testing.
    
    Returns:
        dict: Dictionary of content type to (content, expected_text) mappings
    """
    return {
        "minimal": (MINIMAL_TEXT_CONTENT.encode('utf-8'), MINIMAL_TEXT_CONTENT),
        "unicode": (UNICODE_TEXT_CONTENT.encode('utf-8'), UNICODE_TEXT_CONTENT),
        "large": (LARGE_TEXT_CONTENT.encode('utf-8'), LARGE_TEXT_CONTENT),
        "legal": (LEGAL_DOCUMENT_SAMPLE.encode('utf-8'), LEGAL_DOCUMENT_SAMPLE),
        "empty": (EMPTY_TEXT_CONTENT.encode('utf-8'), EMPTY_TEXT_CONTENT),
        "whitespace": (WHITESPACE_TEXT_CONTENT.encode('utf-8'), WHITESPACE_TEXT_CONTENT)
    }


@pytest.fixture
def text_processing_edge_cases():
    """
    Edge cases for text processing validation.
    
    Returns:
        dict: Dictionary of edge case scenarios
    """
    return {
        "null_bytes": b"Content with \x00 null bytes",
        "mixed_encoding": "Mixed encoding: café".encode('utf-8') + b'\xff\xfe',
        "very_long_line": ("A" * 10000).encode('utf-8'),
        "control_characters": "Content with \t tabs \r carriage returns \n newlines".encode('utf-8'),
        "binary_content": b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR',  # PNG header
        "partial_utf8": b'\xc3\xa9\xc3',  # Incomplete UTF-8 sequence
    }


@pytest.fixture
def expected_content_lengths():
    """
    Expected content lengths for validation testing.
    
    Returns:
        dict: Content type to expected length mappings
    """
    return {
        "minimal": len(MINIMAL_TEXT_CONTENT),
        "unicode": len(UNICODE_TEXT_CONTENT),
        "large": len(LARGE_TEXT_CONTENT),
        "legal": len(LEGAL_DOCUMENT_SAMPLE),
        "empty": 0,
        "whitespace": len(WHITESPACE_TEXT_CONTENT)
    }
