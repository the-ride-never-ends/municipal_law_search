"""
File and Upload Fixtures for upload_document testing.

This module provides fixtures for creating various file types and content
used in testing the upload_document method functionality.
"""
import io
import tempfile
from pathlib import Path
from typing import Tuple
import pytest


# ============================================================================
# File Content Creation Helpers
# ============================================================================

def _create_pdf_content(text_content: str = "Sample PDF content for testing") -> bytes:
    """
    Create a minimal valid PDF with extractable text.
    
    Args:
        text_content: Text to embed in the PDF
        
    Returns:
        bytes: Valid PDF file content
    """
    # Minimal PDF structure with text content
    pdf_content = f"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/Resources <<
/Font <<
/F1 4 0 R
>>
>>
/MediaBox [0 0 612 792]
/Contents 5 0 R
>>
endobj

4 0 obj
<<
/Type /Font
/Subtype /Type1
/BaseFont /Times-Roman
>>
endobj

5 0 obj
<<
/Length {len(text_content) + 50}
>>
stream
BT
/F1 12 Tf
72 720 Td
({text_content}) Tj
ET
endstream
endobj

xref
0 6
0000000000 65535 f 
0000000010 00000 n 
0000000079 00000 n 
0000000173 00000 n 
0000000301 00000 n 
0000000380 00000 n 
trailer
<<
/Size 6
/Root 1 0 R
>>
startxref
{450 + len(text_content)}
%%EOF"""
    return pdf_content.encode('utf-8')


def _create_docx_content(text_content: str = "Sample DOCX content for testing") -> bytes:
    """
    Create a minimal valid DOCX file with text content.
    
    Args:
        text_content: Text to embed in the DOCX
        
    Returns:
        bytes: Valid DOCX file content
    """
    import zipfile
    
    # Create DOCX structure
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as docx:
        # Content Types
        docx.writestr('[Content_Types].xml', 
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
            '</Types>')
        
        # Main relationships
        docx.writestr('_rels/.rels',
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
            '</Relationships>')
        
        # Document content
        docx.writestr('word/document.xml',
            f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            f'<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
            f'<w:body>'
            f'<w:p><w:r><w:t>{text_content}</w:t></w:r></w:p>'
            f'</w:body>'
            f'</w:document>')
    
    buffer.seek(0)
    return buffer.getvalue()


def _create_doc_content(text_content: str = "Sample DOC content for testing") -> bytes:
    """
    Create a minimal valid DOC file with text content.
    
    Args:
        text_content: Text to embed in the DOC
        
    Returns:
        bytes: Valid DOC file content (simplified binary format)
    """
    # Simplified DOC header + text content
    # This is a very basic DOC structure for testing purposes
    doc_header = b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1'  # OLE signature
    doc_body = text_content.encode('utf-8')
    padding = b'\x00' * (512 - len(doc_body) % 512) if len(doc_body) % 512 else b''
    return doc_header + doc_body + padding


def _create_oversized_content(target_size_mb: int = 100) -> bytes:
    """
    Create file content that exceeds size limits.
    
    Args:
        target_size_mb: Target size in megabytes
        
    Returns:
        bytes: Content exceeding size limits
    """
    target_size_bytes = target_size_mb * 1024 * 1024
    chunk_size = 1024 * 1024  # 1MB chunks
    content = b'X' * chunk_size
    
    full_chunks = target_size_bytes // chunk_size
    remainder = target_size_bytes % chunk_size
    
    result = content * full_chunks
    if remainder:
        result += b'Y' * remainder
    
    return result


# ============================================================================
# File and Upload Fixtures
# ============================================================================

@pytest.fixture
def valid_pdf_file():
    """
    A valid PDF file with extractable text content.

    Returns:
        bytes: PDF file content as bytes
    """
    return _create_pdf_content("This is a test PDF document with extractable text content.")


@pytest.fixture
def valid_docx_file():
    """
    A valid DOCX file with text content.
    
    Returns:
        bytes: DOCX file content as bytes
    """
    return _create_docx_content("This is a test DOCX document with text content.")


@pytest.fixture
def valid_doc_file():
    """
    A valid DOC file with text content.
    
    Returns:
        bytes: DOC file content as bytes
    """
    return _create_doc_content("This is a test DOC document with text content.")


@pytest.fixture
def valid_txt_file():
    """
    A plain text file with known content.
    
    Returns:
        bytes: TXT file content as bytes
    """
    content = "This is a plain text file for testing.\nIt contains multiple lines.\nAnd various characters: !@#$%^&*()"
    return content.encode('utf-8')


@pytest.fixture
def empty_file():
    """
    A zero-byte file for testing empty file handling.
    
    Returns:
        bytes: Empty file content (zero bytes)
    """
    return b''


@pytest.fixture
def oversized_file():
    """
    A file that exceeds maximum size limits.
    
    Returns:
        bytes: File content exceeding size limits
    """
    return _create_oversized_content(100)  # 100MB file


@pytest.fixture
def corrupted_pdf_file():
    """
    A corrupted PDF file that cannot be processed.
    
    Returns:
        bytes: Corrupted PDF file content
    """
    # Invalid PDF header and random bytes
    return b'%PDF-1.4\nCorrupted content that is not a valid PDF\x00\xFF\xFE\xFD'


@pytest.fixture
def unsupported_file_jpg():
    """
    An unsupported JPG file for testing file type validation.
    
    Returns:
        bytes: JPG file content
    """
    # Minimal JPEG header
    return b'\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xFF\xDB'


@pytest.fixture
def unicode_filename_file():
    """
    A file with Unicode characters in the filename.
    
    Returns:
        tuple[bytes, str]: File content and Unicode filename
    """
    content = "Test content with unicode filename".encode('utf-8')
    filename = "测试文档_ñáéíóú_файл.txt"
    return content, filename


@pytest.fixture
def special_chars_filename_file():
    """
    A file with special characters and spaces in filename.
    
    Returns:
        tuple[bytes, str]: File content and filename with special characters
    """
    content = "Test content with special characters in filename".encode('utf-8')
    filename = "test file & document (copy) [1] - final.txt"
    return content, filename
