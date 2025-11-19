"""
Response and Validation Fixtures for upload_document testing.

This module provides fixtures for response validation, patterns,
and expected response structures.
"""
import re
from typing import List, Pattern
import pytest


# ============================================================================
# Pattern and Validation Constants
# ============================================================================

# CID pattern based on IPFS/libp2p specifications (simplified)
CID_PATTERN = re.compile(r'^bafkreiht[a-zA-Z0-9]{52}$')

# ISO 8601 timestamp pattern
ISO_TIMESTAMP_PATTERN = re.compile(
    r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{3})?Z?$'
)

# File size pattern (positive integers)
FILE_SIZE_PATTERN = re.compile(r'^\d+$')

# Status values
VALID_STATUS_VALUES = {"success", "error"}

# Error codes
VALID_ERROR_CODES = {
    "INVALID_FILE_TYPE",
    "FILE_TOO_LARGE",
    "FILE_CORRUPTED",
    "EXTRACTION_FAILED",
    "DATABASE_ERROR",
    "PROCESSING_ERROR",
    "INVALID_CLIENT_CID",
    "FILE_EMPTY",
    "UNSUPPORTED_FORMAT"
}

# Success response required fields
SUCCESS_RESPONSE_FIELDS = {
    "status",
    "message", 
    "cid",
    "filename",
    "file_size",
    "upload_timestamp"
}

# Error response required fields
ERROR_RESPONSE_FIELDS = {
    "status",
    "message",
    "error_code",
    "upload_timestamp"
}


# ============================================================================
# Response and Validation Fixtures
# ============================================================================

@pytest.fixture
def expected_success_response_fields():
    """
    List of required fields in successful upload response.
    
    Returns:
        List[str]: Field names required in success response
    """
    return list(SUCCESS_RESPONSE_FIELDS)


@pytest.fixture
def expected_error_response_fields():
    """
    List of required fields in error upload response.
    
    Returns:
        List[str]: Field names required in error response
    """
    return list(ERROR_RESPONSE_FIELDS)


@pytest.fixture
def valid_cid_pattern():
    """
    Regex pattern for valid CID format validation.
    
    Returns:
        Pattern[str]: Compiled regex pattern for CID validation
    """
    return CID_PATTERN


@pytest.fixture
def iso_timestamp_pattern():
    """
    Regex pattern for ISO timestamp format validation.
    
    Returns:
        Pattern[str]: Compiled regex pattern for ISO timestamp
    """
    return ISO_TIMESTAMP_PATTERN


@pytest.fixture
def file_size_pattern():
    """
    Regex pattern for valid file size format.
    
    Returns:
        Pattern[str]: Compiled regex pattern for file size validation
    """
    return FILE_SIZE_PATTERN


@pytest.fixture
def valid_status_values():
    """
    Set of valid status values for responses.
    
    Returns:
        set[str]: Valid status values
    """
    return VALID_STATUS_VALUES.copy()


@pytest.fixture
def valid_error_codes():
    """
    Set of valid error codes for error responses.
    
    Returns:
        set[str]: Valid error codes
    """
    return VALID_ERROR_CODES.copy()


@pytest.fixture
def sample_success_response():
    """
    Sample successful upload response structure.
    
    Returns:
        dict: Sample success response
    """
    return {
        "status": "success",
        "message": "File uploaded successfully",
        "cid": "bafkreiht123456789abcdef123456789abcdef123456789abcdef12",
        "filename": "test_document.pdf",
        "file_size": 1048576,
        "upload_timestamp": "2025-09-27T10:30:00Z"
    }


@pytest.fixture
def sample_error_response():
    """
    Sample error upload response structure.
    
    Returns:
        dict: Sample error response
    """
    return {
        "status": "error",
        "message": "Upload failed: Invalid file type",
        "error_code": "INVALID_FILE_TYPE",
        "upload_timestamp": "2025-09-27T10:30:15Z"
    }


@pytest.fixture
def response_field_types():
    """
    Expected types for response fields.
    
    Returns:
        dict: Field names mapped to expected Python types
    """
    return {
        "status": str,
        "message": str,
        "cid": str,
        "filename": str,
        "file_size": int,
        "upload_timestamp": str,
        "error_code": str
    }


@pytest.fixture
def response_validation_rules():
    """
    Validation rules for response fields.
    
    Returns:
        dict: Field validation rules
    """
    return {
        "status": {
            "required": True,
            "type": str,
            "allowed_values": VALID_STATUS_VALUES
        },
        "message": {
            "required": True,
            "type": str,
            "min_length": 1,
            "max_length": 500
        },
        "cid": {
            "required_for_success": True,
            "type": str,
            "pattern": CID_PATTERN,
            "length": 59  # bafkreiht + 52 characters
        },
        "filename": {
            "required_for_success": True,
            "type": str,
            "min_length": 1,
            "max_length": 255
        },
        "file_size": {
            "required_for_success": True,
            "type": int,
            "min_value": 0
        },
        "upload_timestamp": {
            "required": True,
            "type": str,
            "pattern": ISO_TIMESTAMP_PATTERN
        },
        "error_code": {
            "required_for_error": True,
            "type": str,
            "allowed_values": VALID_ERROR_CODES
        }
    }
