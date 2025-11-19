"""
Database and Mock Fixtures for upload_document testing.

This module provides mock database instances and App objects
for testing database integration and failure scenarios.
"""
from unittest.mock import Mock, AsyncMock, MagicMock
from typing import Dict, Any, Optional
import pytest
from fastapi import HTTPException


def _create_mock_database(should_fail: bool = False, failure_type: str = "generic") -> Mock:
    """
    Create a mock database instance with configurable behavior.
    
    Args:
        should_fail: Whether database operations should fail
        failure_type: Type of failure to simulate
        
    Returns:
        Mock: Database mock with configured behavior
    """
    mock_db = Mock()
    
    if should_fail:
        if failure_type == "connection":
            mock_db.execute.side_effect = ConnectionError("Database connection failed")
            mock_db.fetch_one.side_effect = ConnectionError("Database connection failed")
            mock_db.fetch_all.side_effect = ConnectionError("Database connection failed")
        elif failure_type == "constraint":
            mock_db.execute.side_effect = Exception("UNIQUE constraint failed")
            mock_db.fetch_one.side_effect = Exception("UNIQUE constraint failed")
            mock_db.fetch_all.side_effect = Exception("UNIQUE constraint failed")
        elif failure_type == "timeout":
            mock_db.execute.side_effect = TimeoutError("Database operation timed out")
            mock_db.fetch_one.side_effect = TimeoutError("Database operation timed out")
            mock_db.fetch_all.side_effect = TimeoutError("Database operation timed out")
        else:
            mock_db.execute.side_effect = Exception("Database operation failed")
            mock_db.fetch_one.side_effect = Exception("Database operation failed")
            mock_db.fetch_all.side_effect = Exception("Database operation failed")
    else:
        # Successful database operations
        mock_db.execute.return_value = True
        mock_db.fetch_one.return_value = {
            'cid': 'bafkreiht123456789abcdef',
            'filename': 'test_document.pdf',
            'file_size': 1024,
            'text_content': 'Extracted text content',
            'client_cid': None,
            'upload_timestamp': '2025-09-27T10:30:00Z'
        }
        mock_db.fetch_all.return_value = [mock_db.fetch_one.return_value]
    
    # Connection management
    mock_db.connect = Mock()
    mock_db.close = Mock()
    mock_db.__enter__ = Mock(return_value=mock_db)
    mock_db.__exit__ = Mock(return_value=None)
    
    return mock_db


def _create_mock_configs() -> Mock:
    """
    Create a mock configuration object.
    
    Returns:
        Mock: Configuration object mock
    """
    configs = Mock()
    configs.max_file_size = 50 * 1024 * 1024  # 50MB
    configs.supported_file_types = ['.pdf', '.doc', '.docx', '.txt']
    configs.database_url = "sqlite:///test.db"
    configs.upload_directory = "/tmp/uploads"
    configs.log_level = "INFO"
    return configs


def _create_mock_resources() -> Dict[str, Mock]:
    """
    Create a mock resources dictionary.
    
    Returns:
        Dict[str, Mock]: Mock resources dictionary
    """
    mock_db = _create_mock_database()
    
    return {
        'database': mock_db,
        'logger': Mock(),
        'cid_generator': Mock(return_value="bafkreiht123456789abcdef"),
        'text_extractor': Mock(return_value="Extracted text content"),
        'file_processor': Mock(),
        'timestamp_generator': Mock(return_value="2025-09-27T10:30:00Z")
    }


# ============================================================================
# Database and Mock Fixtures
# ============================================================================

@pytest.fixture
def mock_database():
    """
    A mock database instance for testing database operations.
    
    Returns:
        Mock: Database mock with standard methods
    """
    return _create_mock_database(should_fail=False)


@pytest.fixture
def database_failure_mock():
    """
    A mock database that simulates failure conditions.
    
    Returns:
        Mock: Database mock that raises exceptions
    """
    return _create_mock_database(should_fail=True, failure_type="generic")


@pytest.fixture
def database_connection_failure_mock():
    """
    A mock database that simulates connection failures.
    
    Returns:
        Mock: Database mock that raises connection exceptions
    """
    return _create_mock_database(should_fail=True, failure_type="connection")


@pytest.fixture
def database_constraint_failure_mock():
    """
    A mock database that simulates constraint violations.
    
    Returns:
        Mock: Database mock that raises constraint exceptions
    """
    return _create_mock_database(should_fail=True, failure_type="constraint")


@pytest.fixture
def database_timeout_failure_mock():
    """
    A mock database that simulates timeout errors.
    
    Returns:
        Mock: Database mock that raises timeout exceptions
    """
    return _create_mock_database(should_fail=True, failure_type="timeout")


@pytest.fixture
def configs():
    """
    Mock configuration object.
    
    Returns:
        Mock: Configuration object mock
    """
    return _create_mock_configs()


@pytest.fixture
def resources():
    """
    Mock resources dictionary.
    
    Returns:
        Dict[str, Mock]: Mock resources dictionary
    """
    return _create_mock_resources()


@pytest.fixture
def mock_resources_with_db_failure():
    """
    Mock resources dictionary with failing database.
    
    Returns:
        Dict[str, Mock]: Mock resources with failing database
    """
    resources = _create_mock_resources()
    resources['database'] = _create_mock_database(should_fail=True)
    return resources


@pytest.fixture
def mock_app_instance(configs, resources):
    """
    A mock App instance with mocked dependencies.
    
    Args:
        configs: Mock configuration from fixture
        resources: Mock resources from fixture
        
    Returns:
        Mock: App instance mock with all dependencies
    """
    from unittest.mock import patch
    
    # Create mock App instance
    mock_app = Mock()
    mock_app.configs = configs
    mock_app.resources = resources
    mock_app.db = resources['database']
    mock_app.logger = resources['logger']
    
    # Mock the upload_document method behavior
    async def mock_upload_document(file, client_cid=None):
        # Simulate successful upload
        return {
            "status": "success",
            "message": "File uploaded successfully",
            "cid": "bafkreiht123456789abcdef",
            "filename": file.filename,
            "file_size": file.size,
            "upload_timestamp": "2025-09-27T10:30:00Z"
        }
    
    mock_app.upload_document = AsyncMock(side_effect=mock_upload_document)
    
    return mock_app


@pytest.fixture
def mock_app_with_db_failure(configs, mock_resources_with_db_failure):
    """
    A mock App instance with failing database dependencies.
    
    Args:
        configs: Mock configuration from fixture
        mock_resources_with_db_failure: Mock resources with failing DB from fixture
        
    Returns:
        Mock: App instance mock with failing database
    """
    mock_app = Mock()
    mock_app.configs = configs
    mock_app.resources = mock_resources_with_db_failure
    mock_app.db = mock_resources_with_db_failure['database']
    mock_app.logger = mock_resources_with_db_failure['logger']
    
    # Mock the upload_document method to simulate database failure
    async def mock_upload_document_with_failure(file, client_cid=None):
        raise HTTPException(status_code=500, detail="Database operation failed")
    
    mock_app.upload_document = AsyncMock(side_effect=mock_upload_document_with_failure)
    
    return mock_app
