"""
UploadFile Mock Fixtures for upload_document testing.

This module provides mock UploadFile objects that simulate FastAPI's
UploadFile behavior for testing purposes.
"""
import io
from unittest.mock import Mock, AsyncMock
from typing import Optional
import pytest
from fastapi import UploadFile


def _create_upload_file_mock(
    content: bytes, 
    filename: str = "test.pdf",
    content_type: str = "application/pdf",
    size: Optional[int] = None
) -> Mock:
    """
    Create a mock UploadFile object with specified content and metadata.
    
    Args:
        content: File content as bytes
        filename: Filename for the mock file
        content_type: MIME type of the file
        size: File size in bytes (calculated if None)
        
    Returns:
        Mock: UploadFile mock object
    """
    if size is None:
        size = len(content)
    
    # Create BytesIO stream from content
    file_stream = io.BytesIO(content)
    
    # Create mock UploadFile
    mock_file = Mock(spec=UploadFile)
    mock_file.filename = filename
    mock_file.content_type = content_type
    mock_file.size = size
    
    # Mock the file operations
    async def mock_read(size: int = -1) -> bytes:
        if size == -1:
            file_stream.seek(0)
            return file_stream.read()
        return file_stream.read(size)
    
    def mock_seek(offset: int, whence: int = 0) -> int:
        return file_stream.seek(offset, whence)
    
    mock_file.read = AsyncMock(side_effect=mock_read)
    mock_file.seek = mock_seek
    mock_file.file = file_stream
    
    return mock_file


# ============================================================================
# UploadFile Mock Fixtures
# ============================================================================

@pytest.fixture
def mock_upload_file(valid_pdf_file):
    """
    A mock UploadFile object for valid PDF testing.
    
    Args:
        valid_pdf_file: PDF file content from fixture
        
    Returns:
        Mock: UploadFile mock object with PDF content
    """
    return _create_upload_file_mock(
        content=valid_pdf_file,
        filename="test_document.pdf",
        content_type="application/pdf"
    )


@pytest.fixture
def mock_upload_file_docx(valid_docx_file):
    """
    A mock UploadFile object for DOCX testing.
    
    Args:
        valid_docx_file: DOCX file content from fixture
        
    Returns:
        Mock: UploadFile mock object with DOCX content
    """
    return _create_upload_file_mock(
        content=valid_docx_file,
        filename="test_document.docx",
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )


@pytest.fixture
def mock_upload_file_doc(valid_doc_file):
    """
    A mock UploadFile object for DOC testing.
    
    Args:
        valid_doc_file: DOC file content from fixture
        
    Returns:
        Mock: UploadFile mock object with DOC content
    """
    return _create_upload_file_mock(
        content=valid_doc_file,
        filename="test_document.doc",
        content_type="application/msword"
    )


@pytest.fixture
def mock_upload_file_txt(valid_txt_file):
    """
    A mock UploadFile object for TXT testing.
    
    Args:
        valid_txt_file: TXT file content from fixture
        
    Returns:
        Mock: UploadFile mock object with TXT content
    """
    return _create_upload_file_mock(
        content=valid_txt_file,
        filename="test_document.txt",
        content_type="text/plain"
    )


@pytest.fixture
def mock_upload_file_empty(empty_file):
    """
    A mock UploadFile object for empty file testing.
    
    Args:
        empty_file: Empty file content from fixture
        
    Returns:
        Mock: UploadFile mock object with empty content
    """
    return _create_upload_file_mock(
        content=empty_file,
        filename="empty_file.txt",
        content_type="text/plain"
    )


@pytest.fixture
def mock_upload_file_oversized(oversized_file):
    """
    A mock UploadFile object for oversized file testing.
    
    Args:
        oversized_file: Oversized file content from fixture
        
    Returns:
        Mock: UploadFile mock object with oversized content
    """
    return _create_upload_file_mock(
        content=oversized_file,
        filename="huge_file.pdf",
        content_type="application/pdf"
    )


@pytest.fixture
def mock_upload_file_corrupted(corrupted_pdf_file):
    """
    A mock UploadFile object for corrupted file testing.
    
    Args:
        corrupted_pdf_file: Corrupted PDF content from fixture
        
    Returns:
        Mock: UploadFile mock object with corrupted content
    """
    return _create_upload_file_mock(
        content=corrupted_pdf_file,
        filename="corrupted_document.pdf",
        content_type="application/pdf"
    )


@pytest.fixture
def mock_upload_file_unsupported(unsupported_file_jpg):
    """
    A mock UploadFile object for unsupported file type testing.
    
    Args:
        unsupported_file_jpg: JPG file content from fixture
        
    Returns:
        Mock: UploadFile mock object with JPG content
    """
    return _create_upload_file_mock(
        content=unsupported_file_jpg,
        filename="image.jpg",
        content_type="image/jpeg"
    )


@pytest.fixture
def mock_upload_file_unicode_name(unicode_filename_file):
    """
    A mock UploadFile object with Unicode filename.
    
    Args:
        unicode_filename_file: File content and Unicode filename from fixture
        
    Returns:
        Mock: UploadFile mock object with Unicode filename
    """
    content, filename = unicode_filename_file
    return _create_upload_file_mock(
        content=content,
        filename=filename,
        content_type="text/plain"
    )


@pytest.fixture
def mock_upload_file_special_chars(special_chars_filename_file):
    """
    A mock UploadFile object with special characters in filename.
    
    Args:
        special_chars_filename_file: File content and special filename from fixture
        
    Returns:
        Mock: UploadFile mock object with special characters in filename
    """
    content, filename = special_chars_filename_file
    return _create_upload_file_mock(
        content=content,
        filename=filename,
        content_type="text/plain"
    )
