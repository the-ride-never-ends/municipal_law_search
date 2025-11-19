"""
Error Simulation Fixtures for upload_document testing.

This module provides fixtures for simulating various error conditions
and exceptions that can occur during file upload processing.
"""
from unittest.mock import Mock
from typing import Dict, Any, Callable
import pytest
from fastapi import HTTPException


def _create_io_error_mock() -> Mock:
    """
    Create a mock that raises IOError when called.
    
    Returns:
        Mock: Mock object that raises IOError
    """
    mock = Mock()
    mock.side_effect = IOError("File operation failed")
    return mock


def _create_value_error_mock() -> Mock:
    """
    Create a mock that raises ValueError when called.
    
    Returns:
        Mock: Mock object that raises ValueError
    """
    mock = Mock()
    mock.side_effect = ValueError("Content extraction failed")
    return mock


def _create_type_error_mock() -> Mock:
    """
    Create a mock that raises TypeError when called.
    
    Returns:
        Mock: Mock object that raises TypeError
    """
    mock = Mock()
    mock.side_effect = TypeError("Invalid parameter type")
    return mock


def _create_http_exception_mock(status_code: int, detail: str) -> Mock:
    """
    Create a mock that raises HTTPException when called.
    
    Args:
        status_code: HTTP status code
        detail: Error detail message
        
    Returns:
        Mock: Mock object that raises HTTPException
    """
    mock = Mock()
    mock.side_effect = HTTPException(status_code=status_code, detail=detail)
    return mock


# ============================================================================
# Error Simulation Fixtures
# ============================================================================

@pytest.fixture
def io_error_simulation():
    """
    Fixture that simulates IO errors during file operations.
    
    Returns:
        Mock: Mock object that raises IOError when called
    """
    return _create_io_error_mock()


@pytest.fixture
def value_error_simulation():
    """
    Fixture that simulates content extraction failures.
    
    Returns:
        Mock: Mock object that raises ValueError when called
    """
    return _create_value_error_mock()


@pytest.fixture
def type_error_simulation():
    """
    Fixture that simulates parameter type errors.
    
    Returns:
        Mock: Mock object that raises TypeError when called
    """
    return _create_type_error_mock()


@pytest.fixture
def http_exception_simulation():
    """
    Fixture that simulates various HTTP exceptions.
    
    Returns:
        Dict[int, Mock]: Mock objects for different HTTP status codes
    """
    return {
        400: _create_http_exception_mock(400, "Bad Request - Invalid file"),
        413: _create_http_exception_mock(413, "Payload Too Large - File exceeds size limit"),
        415: _create_http_exception_mock(415, "Unsupported Media Type - Invalid file format"),
        500: _create_http_exception_mock(500, "Internal Server Error - Processing failed")
    }


@pytest.fixture
def file_read_error_simulation():
    """
    Simulates file read errors during upload processing.
    
    Returns:
        Mock: Mock that raises IOError on file read attempts
    """
    mock = Mock()
    mock.read.side_effect = IOError("Cannot read file")
    mock.seek.side_effect = IOError("Cannot seek in file")
    return mock


@pytest.fixture
def content_extraction_error_simulation():
    """
    Simulates content extraction failures for various file types.
    
    Returns:
        Dict[str, Mock]: File type to error mock mappings
    """
    return {
        'pdf': Mock(side_effect=ValueError("PDF extraction failed")),
        'docx': Mock(side_effect=ValueError("DOCX extraction failed")),
        'doc': Mock(side_effect=ValueError("DOC extraction failed")),
        'txt': Mock(side_effect=ValueError("TXT extraction failed"))
    }


@pytest.fixture
def cid_generation_error_simulation():
    """
    Simulates CID generation failures.
    
    Returns:
        Mock: Mock that raises exception during CID generation
    """
    mock = Mock()
    mock.side_effect = Exception("CID generation failed")
    return mock


@pytest.fixture
def database_error_simulations():
    """
    Simulates various database error conditions.
    
    Returns:
        Dict[str, Mock]: Error type to mock mappings
    """
    return {
        'connection_error': Mock(side_effect=ConnectionError("Database connection failed")),
        'timeout_error': Mock(side_effect=TimeoutError("Database operation timed out")),
        'constraint_error': Mock(side_effect=Exception("UNIQUE constraint failed")),
        'permission_error': Mock(side_effect=PermissionError("Database access denied")),
        'disk_full_error': Mock(side_effect=OSError("No space left on device"))
    }


@pytest.fixture
def network_error_simulation():
    """
    Simulates network-related errors during upload.
    
    Returns:
        Mock: Mock that raises network-related exceptions
    """
    mock = Mock()
    mock.side_effect = ConnectionError("Network connection lost")
    return mock


@pytest.fixture
def memory_error_simulation():
    """
    Simulates memory errors during large file processing.
    
    Returns:
        Mock: Mock that raises MemoryError
    """
    mock = Mock()
    mock.side_effect = MemoryError("Insufficient memory to process file")
    return mock


@pytest.fixture
def permission_error_simulation():
    """
    Simulates permission errors during file operations.
    
    Returns:
        Mock: Mock that raises PermissionError
    """
    mock = Mock()
    mock.side_effect = PermissionError("Permission denied")
    return mock


@pytest.fixture
def timeout_error_simulation():
    """
    Simulates timeout errors during processing.
    
    Returns:
        Mock: Mock that raises TimeoutError
    """
    mock = Mock()
    mock.side_effect = TimeoutError("Operation timed out")
    return mock


@pytest.fixture
def encoding_error_simulation():
    """
    Simulates text encoding/decoding errors.
    
    Returns:
        Mock: Mock that raises UnicodeDecodeError
    """
    mock = Mock()
    mock.side_effect = UnicodeDecodeError('utf-8', b'\xff\xfe', 0, 1, 'invalid start byte')
    return mock


@pytest.fixture
def file_corruption_simulation():
    """
    Simulates various file corruption scenarios.
    
    Returns:
        Dict[str, Mock]: Corruption type to mock mappings
    """
    return {
        'header_corruption': Mock(side_effect=ValueError("Invalid file header")),
        'structure_corruption': Mock(side_effect=ValueError("Corrupted file structure")),
        'encoding_corruption': Mock(side_effect=UnicodeDecodeError('utf-8', b'\xff', 0, 1, 'invalid')),
        'truncated_file': Mock(side_effect=EOFError("Unexpected end of file")),
        'binary_corruption': Mock(side_effect=ValueError("Binary data corruption detected"))
    }


@pytest.fixture
def cascading_error_simulation():
    """
    Simulates cascading errors where multiple systems fail.
    
    Returns:
        Callable: Function that simulates multiple consecutive failures
    """
    def simulate_cascading_errors():
        errors = [
            IOError("File read failed"),
            ValueError("Content extraction failed"),
            Exception("Database save failed"),
            HTTPException(status_code=500, detail="Multiple system failures")
        ]
        for error in errors:
            yield error
    
    return simulate_cascading_errors


@pytest.fixture
def intermittent_error_simulation():
    """
    Simulates intermittent errors that sometimes succeed.
    
    Returns:
        Mock: Mock that fails on some calls but succeeds on others
    """
    call_count = 0
    
    def side_effect_func(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count % 3 == 0:  # Fail every third call
            raise ConnectionError("Intermittent connection failure")
        return "Success"
    
    mock = Mock()
    mock.side_effect = side_effect_func
    return mock


@pytest.fixture
def resource_exhaustion_simulation():
    """
    Simulates resource exhaustion scenarios.
    
    Returns:
        Dict[str, Mock]: Resource type to exhaustion mock mappings
    """
    return {
        'memory': Mock(side_effect=MemoryError("Out of memory")),
        'disk_space': Mock(side_effect=OSError("No space left on device")),
        'file_handles': Mock(side_effect=OSError("Too many open files")),
        'cpu_timeout': Mock(side_effect=TimeoutError("CPU time limit exceeded")),
        'connection_pool': Mock(side_effect=ConnectionError("Connection pool exhausted"))
    }


@pytest.fixture
def error_recovery_test_scenarios():
    """
    Scenarios for testing error recovery and cleanup.
    
    Returns:
        Dict[str, Dict]: Error scenarios with recovery expectations
    """
    return {
        'partial_upload_failure': {
            'error': IOError("Upload interrupted"),
            'expected_cleanup': ['temp_files', 'partial_database_entries'],
            'expected_response': 'error_with_cleanup_confirmation'
        },
        'database_rollback_needed': {
            'error': Exception("Transaction failed"),
            'expected_cleanup': ['database_transaction_rollback'],
            'expected_response': 'error_with_rollback_confirmation'
        },
        'resource_cleanup_failure': {
            'error': OSError("Cleanup failed"),
            'expected_cleanup': ['manual_intervention_required'],
            'expected_response': 'error_with_cleanup_warning'
        }
    }
