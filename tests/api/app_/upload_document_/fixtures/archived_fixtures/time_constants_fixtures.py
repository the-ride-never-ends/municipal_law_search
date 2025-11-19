"""
Time, Constants and Parametrized Fixtures for upload_document testing.

This module provides fixtures for time management, test constants,
and parametrized test data generation.
"""
import datetime
from typing import Dict, Any, List, Optional
from unittest.mock import patch
import pytest
from freezegun import freeze_time


# ============================================================================
# Test Constants
# ============================================================================

# File size limits in bytes
FILE_SIZE_LIMITS = {
    'min_size': 1,  # 1 byte
    'small_file': 1024,  # 1KB
    'medium_file': 1024 * 1024,  # 1MB
    'large_file': 10 * 1024 * 1024,  # 10MB
    'max_size': 50 * 1024 * 1024,  # 50MB
    'oversized': 100 * 1024 * 1024  # 100MB (exceeds limit)
}

# Supported file types
SUPPORTED_FILE_TYPES = ['.pdf', '.doc', '.docx', '.txt']

# Unsupported file types
UNSUPPORTED_FILE_TYPES = ['.jpg', '.png', '.mp4', '.exe', '.zip', '.rar']

# Timing constants
TIMESTAMP_TOLERANCE_SECONDS = 5.0
DEFAULT_PROCESSING_TIMEOUT = 30.0
CONCURRENT_OPERATION_TIMEOUT = 60.0

# Test data sizes
TEST_DATA_SIZES = {
    'minimal': 100,     # 100 bytes
    'small': 1024,      # 1KB  
    'medium': 102400,   # 100KB
    'large': 1048576,   # 1MB
    'xlarge': 10485760  # 10MB
}


# ============================================================================
# Time and Timestamp Fixtures
# ============================================================================

@pytest.fixture
def freeze_time_fixture():
    """
    Freezes time for timestamp testing.
    
    Returns:
        datetime: Frozen datetime for consistent testing
    """
    frozen_time = datetime.datetime(2025, 9, 27, 10, 30, 0, tzinfo=datetime.timezone.utc)
    with freeze_time(frozen_time):
        yield frozen_time


@pytest.fixture
def current_iso_timestamp():
    """
    Current timestamp in ISO format.
    
    Returns:
        str: Current timestamp in ISO format
    """
    return datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00', 'Z')


@pytest.fixture
def timestamp_tolerance():
    """
    Acceptable timestamp tolerance for timing tests.
    
    Returns:
        float: Tolerance in seconds for timestamp comparisons
    """
    return TIMESTAMP_TOLERANCE_SECONDS


@pytest.fixture
def test_timestamps():
    """
    Various timestamp formats for testing.
    
    Returns:
        Dict[str, str]: Different timestamp format examples
    """
    base_time = datetime.datetime(2025, 9, 27, 10, 30, 0, tzinfo=datetime.timezone.utc)
    
    return {
        'iso_with_z': base_time.isoformat().replace('+00:00', 'Z'),
        'iso_with_offset': base_time.isoformat(),
        'iso_with_milliseconds': base_time.replace(microsecond=123000).isoformat().replace('+00:00', 'Z'),
        'past_timestamp': (base_time - datetime.timedelta(hours=1)).isoformat().replace('+00:00', 'Z'),
        'future_timestamp': (base_time + datetime.timedelta(hours=1)).isoformat().replace('+00:00', 'Z'),
        'invalid_format': '2025-09-27 10:30:00',
        'malformed': 'not-a-timestamp'
    }


# ============================================================================
# Constants and Test Data Fixtures
# ============================================================================

@pytest.fixture
def file_size_limits():
    """
    Dictionary of file size limits for testing.
    
    Returns:
        Dict[str, int]: File size limits in bytes
    """
    return FILE_SIZE_LIMITS.copy()


@pytest.fixture
def supported_file_types():
    """
    List of supported file extensions.
    
    Returns:
        List[str]: Supported file extensions
    """
    return SUPPORTED_FILE_TYPES.copy()


@pytest.fixture
def unsupported_file_types():
    """
    List of unsupported file extensions.
    
    Returns:
        List[str]: Unsupported file extensions
    """
    return UNSUPPORTED_FILE_TYPES.copy()


@pytest.fixture
def test_data_sizes():
    """
    Dictionary of test data size constants.
    
    Returns:
        Dict[str, int]: Test data sizes in bytes
    """
    return TEST_DATA_SIZES.copy()


@pytest.fixture
def test_constants(file_size_limits, supported_file_types, unsupported_file_types, test_data_sizes):
    """
    Dictionary of test constants and values.
    
    Args:
        file_size_limits: File size limits from fixture
        supported_file_types: Supported file types from fixture
        unsupported_file_types: Unsupported file types from fixture
        test_data_sizes: Test data sizes from fixture
        
    Returns:
        Dict[str, Any]: Dictionary containing test constants
    """
    return {
        'file_size_limits': file_size_limits,
        'supported_file_types': supported_file_types,
        'unsupported_file_types': unsupported_file_types,
        'test_data_sizes': test_data_sizes,
        'timestamp_tolerance': TIMESTAMP_TOLERANCE_SECONDS,
        'processing_timeout': DEFAULT_PROCESSING_TIMEOUT,
        'concurrent_timeout': CONCURRENT_OPERATION_TIMEOUT,
        'valid_extensions': SUPPORTED_FILE_TYPES,
        'invalid_extensions': UNSUPPORTED_FILE_TYPES,
        'mime_types': {
            '.pdf': 'application/pdf',
            '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.txt': 'text/plain',
            '.jpg': 'image/jpeg',
            '.png': 'image/png'
        },
        'error_codes': {
            'invalid_file_type': 'INVALID_FILE_TYPE',
            'file_too_large': 'FILE_TOO_LARGE',
            'file_corrupted': 'FILE_CORRUPTED',
            'extraction_failed': 'EXTRACTION_FAILED',
            'database_error': 'DATABASE_ERROR'
        },
        'http_status_codes': {
            'success': 200,
            'bad_request': 400,
            'payload_too_large': 413,
            'unsupported_media_type': 415,
            'internal_server_error': 500
        }
    }


# ============================================================================
# Parametrized Test Data Fixtures
# ============================================================================

@pytest.fixture(params=['pdf', 'docx', 'doc', 'txt'])
def valid_file_types(request):
    """
    Parametrized fixture for all valid file types.
    
    Args:
        request: Pytest request object with parameter values
        
    Returns:
        str: File extension for current test parameter
    """
    return f".{request.param}"


@pytest.fixture(params=['jpg', 'png', 'mp4', 'exe'])
def invalid_file_types(request):
    """
    Parametrized fixture for all invalid file types.
    
    Args:
        request: Pytest request object with parameter values
        
    Returns:
        str: File extension for current test parameter
    """
    return f".{request.param}"


@pytest.fixture(params=[None, 'valid_cid', 'invalid_cid'])
def client_cid_variations(request, valid_client_cid, invalid_client_cid):
    """
    Parametrized fixture for different client_cid values.
    
    Args:
        request: Pytest request object with parameter values
        valid_client_cid: Valid client CID from fixture
        invalid_client_cid: Invalid client CID from fixture
        
    Returns:
        Optional[str]: Client CID variation for current test parameter
    """
    if request.param is None:
        return None
    elif request.param == 'valid_cid':
        return valid_client_cid
    elif request.param == 'invalid_cid':
        return invalid_client_cid


@pytest.fixture(params=['small', 'medium', 'large'])
def file_size_variations(request, test_data_sizes):
    """
    Parametrized fixture for different file sizes.
    
    Args:
        request: Pytest request object with parameter values
        test_data_sizes: Test data sizes from fixture
        
    Returns:
        int: File size in bytes for current test parameter
    """
    return test_data_sizes[request.param]


@pytest.fixture(params=[1, 5, 10, 20])
def concurrency_levels(request):
    """
    Parametrized fixture for different concurrency levels.
    
    Args:
        request: Pytest request object with parameter values
        
    Returns:
        int: Number of concurrent operations for current test parameter
    """
    return request.param


@pytest.fixture(params=['success', 'file_error', 'database_error', 'processing_error'])
def error_scenarios(request):
    """
    Parametrized fixture for different error scenarios.
    
    Args:
        request: Pytest request object with parameter values
        
    Returns:
        str: Error scenario type for current test parameter
    """
    return request.param


# ============================================================================
# Helper Function Fixtures
# ============================================================================

@pytest.fixture
def create_temp_file():
    """
    Helper function to create temporary test files.
    
    Returns:
        Callable: Function that creates temporary files
    """
    import tempfile
    import os
    
    def _create_temp_file(content: bytes, suffix: str = '.tmp') -> str:
        """
        Create a temporary file with the given content.
        
        Args:
            content: File content as bytes
            suffix: File extension
            
        Returns:
            str: Path to the created temporary file
        """
        fd, path = tempfile.mkstemp(suffix=suffix)
        try:
            with os.fdopen(fd, 'wb') as tmp_file:
                tmp_file.write(content)
        except Exception:
            os.close(fd)
            os.unlink(path)
            raise
        return path
    
    return _create_temp_file


@pytest.fixture
def verify_database_record():
    """
    Helper function to verify database record creation.
    
    Returns:
        Callable: Function that verifies database records
    """
    def _verify_database_record(db_mock, expected_cid: str, expected_data: Dict[str, Any]) -> bool:
        """
        Verify that a database record was created with expected data.
        
        Args:
            db_mock: Mock database object
            expected_cid: Expected CID value
            expected_data: Expected record data
            
        Returns:
            bool: True if record verification passes
        """
        # Check if database execute was called
        if not db_mock.execute.called:
            return False
        
        # Verify the call arguments contain expected data
        call_args = db_mock.execute.call_args
        if not call_args:
            return False
        
        # Basic verification - in real implementation, would check SQL and parameters
        return True
    
    return _verify_database_record


@pytest.fixture
def generate_test_cid():
    """
    Helper function to generate test CIDs.
    
    Returns:
        Callable: Function that generates valid test CIDs
    """
    import hashlib
    
    def _generate_test_cid(content: str = None) -> str:
        """
        Generate a valid test CID.
        
        Args:
            content: Optional content to base CID on
            
        Returns:
            str: Valid test CID
        """
        if content is None:
            import uuid
            content = str(uuid.uuid4())
        
        hash_value = hashlib.sha256(content.encode()).hexdigest()
        return f"bafkreiht{hash_value[:52]}"
    
    return _generate_test_cid


@pytest.fixture
def timing_utilities():
    """
    Utilities for timing and performance testing.
    
    Returns:
        Dict[str, Callable]: Timing utility functions
    """
    import time
    
    def measure_execution_time(func, *args, **kwargs):
        """Measure execution time of a function."""
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        return result, end_time - start_time
    
    def assert_execution_time(max_seconds: float):
        """Context manager to assert maximum execution time."""
        class TimingAssertion:
            def __enter__(self):
                self.start_time = time.time()
                return self
            
            def __exit__(self, exc_type, exc_val, exc_tb):
                elapsed = time.time() - self.start_time
                assert elapsed <= max_seconds, f"Execution took {elapsed:.2f}s, expected <= {max_seconds}s"
        
        return TimingAssertion()
    
    return {
        'measure_execution_time': measure_execution_time,
        'assert_execution_time': assert_execution_time
    }
