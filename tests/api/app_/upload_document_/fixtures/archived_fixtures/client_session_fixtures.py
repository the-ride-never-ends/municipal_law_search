"""
Client and Session Fixtures for upload_document testing.

This module provides fixtures for client CID management and session
tracking used in testing the upload_document method functionality.
"""
import hashlib
import uuid
from typing import List, Optional
import pytest


def _generate_valid_cid(content: str = None) -> str:
    """
    Generate a valid CID (Content Identifier) for testing.
    
    Args:
        content: Optional content to base CID on, otherwise generates random
        
    Returns:
        str: Valid CID in proper format
    """
    if content is None:
        content = str(uuid.uuid4())
    
    # Simulate CID generation (simplified version)
    # Real CIDs are base58-encoded multihashes, this is a simplified version
    hash_value = hashlib.sha256(content.encode()).hexdigest()
    return f"bafkreiht{hash_value[:52]}"  # Simplified CID format


def _generate_invalid_cid_format() -> str:
    """
    Generate an invalid CID format for testing.
    
    Returns:
        str: Invalid CID format
    """
    return "invalid_cid_format_12345"


# ============================================================================
# Client and Session Fixtures
# ============================================================================

@pytest.fixture
def valid_client_cid():
    """
    A valid client CID string.

    Returns:
        str: Valid client CID in proper format
    """
    return _generate_valid_cid("test_client_session_001")


@pytest.fixture
def invalid_client_cid():
    """
    An invalid client CID format.
    
    Returns:
        str: Invalid client CID format
    """
    return _generate_invalid_cid_format()


@pytest.fixture
def none_client_cid():
    """
    None value for client_cid parameter.
    
    Returns:
        None: None value for testing optional parameter
    """
    return None


@pytest.fixture
def multiple_client_cids():
    """
    List of different valid client CIDs for concurrent testing.
    
    Returns:
        List[str]: Multiple valid client CIDs
    """
    return [
        _generate_valid_cid("client_session_001"),
        _generate_valid_cid("client_session_002"),
        _generate_valid_cid("client_session_003"),
        _generate_valid_cid("client_session_004"),
        _generate_valid_cid("client_session_005")
    ]


@pytest.fixture
def concurrent_client_sessions():
    """
    Multiple client sessions for concurrent testing.
    
    Returns:
        List[str]: Multiple client CIDs for concurrent testing
    """
    return [
        _generate_valid_cid(f"concurrent_session_{i}")
        for i in range(10)
    ]


@pytest.fixture
def client_cid_variations():
    """
    Dictionary containing various client CID test cases.
    
    Returns:
        dict: Various client CID test scenarios
    """
    return {
        'valid': _generate_valid_cid("valid_test_client"),
        'invalid': _generate_invalid_cid_format(),
        'none': None,
        'empty_string': "",
        'too_short': "bafkrei",
        'too_long': _generate_valid_cid("test") + "extra_characters_that_make_it_too_long",
        'wrong_prefix': "qmfkreiht" + hashlib.sha256(b"test").hexdigest()[:52],
        'non_string': 12345,
        'unicode': "bafkreiht测试",
        'with_spaces': "bafkreiht 123456789abcdef",
        'special_chars': "bafkreiht!@#$%^&*()"
    }
