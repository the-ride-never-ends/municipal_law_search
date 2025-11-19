"""
Constants for upload_document testing.

This module provides all shared constants used across test fixtures,
eliminating duplication and providing a single source of truth for
all test configuration values.
"""
import re
from typing import Dict, Any, List, Set


# ============================================================================
# File Configuration Constants
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

# Test data sizes for content generation
TEST_DATA_SIZES = {
    'minimal': 100,     # 100 bytes
    'small': 1024,      # 1KB  
    'medium': 102400,   # 100KB
    'large': 1048576,   # 1MB
    'xlarge': 10485760  # 10MB
}


BAD_INPUT_TYPES = [None, 123, 45.67, [], {}, set(), (1, 2), True, b'bytes']


# Supported file types
SUPPORTED_FILE_TYPES = ['.pdf', '.doc', '.docx', '.txt']

# Unsupported file types
UNSUPPORTED_FILE_TYPES = ['.jpg', '.png', '.mp4', '.exe', '.zip', '.rar', '.gif', '.bmp']

# MIME types mapping
MIME_TYPES = {
    '.pdf': 'application/pdf',
    '.doc': 'application/msword',
    '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    '.txt': 'text/plain',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.png': 'image/png',
    '.gif': 'image/gif',
    '.bmp': 'image/bmp',
    '.mp4': 'video/mp4',
    '.exe': 'application/octet-stream',
    '.zip': 'application/zip',
    '.rar': 'application/x-rar-compressed'
}


# ============================================================================
# Response and Validation Constants
# ============================================================================

# Valid status values
VALID_STATUS_VALUES = {"success", "error"}

# Error codes
ERROR_CODES = {
    'INVALID_FILE_TYPE': 'INVALID_FILE_TYPE',
    'FILE_TOO_LARGE': 'FILE_TOO_LARGE', 
    'FILE_CORRUPTED': 'FILE_CORRUPTED',
    'EXTRACTION_FAILED': 'EXTRACTION_FAILED',
    'DATABASE_ERROR': 'DATABASE_ERROR',
    'PROCESSING_ERROR': 'PROCESSING_ERROR',
    'INVALID_CLIENT_CID': 'INVALID_CLIENT_CID',
    'FILE_EMPTY': 'FILE_EMPTY',
    'UNSUPPORTED_FORMAT': 'UNSUPPORTED_FORMAT',
    'NETWORK_ERROR': 'NETWORK_ERROR',
    'PERMISSION_ERROR': 'PERMISSION_ERROR',
    'TIMEOUT_ERROR': 'TIMEOUT_ERROR',
    'MEMORY_ERROR': 'MEMORY_ERROR',
    'ENCODING_ERROR': 'ENCODING_ERROR'
}

# HTTP status codes
HTTP_STATUS_CODES = {
    'success': 200,
    'bad_request': 400,
    'unauthorized': 401,
    'forbidden': 403,
    'not_found': 404,
    'method_not_allowed': 405,
    'payload_too_large': 413,
    'unsupported_media_type': 415,
    'unprocessable_entity': 422,
    'internal_server_error': 500,
    'bad_gateway': 502,
    'service_unavailable': 503,
    'gateway_timeout': 504
}

# Success response required fields
SUCCESS_RESPONSE_FIELDS = {
    'status',
    'message', 
    'cid',
    'filename',
    'file_size',
    'upload_timestamp'
}

# Error response required fields
ERROR_RESPONSE_FIELDS = {
    'status',
    'message',
    'error_code',
    'upload_timestamp'
}

# Response field type mappings
RESPONSE_FIELD_TYPES = {
    'status': str,
    'message': str,
    'cid': str,
    'filename': str,
    'file_size': int,
    'upload_timestamp': str,
    'error_code': str
}


# ============================================================================
# Pattern and Validation Constants
# ============================================================================

# CID pattern based on IPFS/libp2p specifications (simplified)
CID_PATTERN = re.compile(r'^bafkreiht[a-zA-Z0-9]{52}$')

# ISO 8601 timestamp pattern
ISO_TIMESTAMP_PATTERN = re.compile(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{3})?Z?$')

# File size pattern (positive integers)
FILE_SIZE_PATTERN = re.compile(r'^\d+$')

# Filename patterns
FILENAME_PATTERNS = {
    'basic': re.compile(r'^[a-zA-Z0-9_\-\.]+$'),
    'with_spaces': re.compile(r'^[a-zA-Z0-9_\-\.\s]+$'),
    'unicode': re.compile(r'^[\w\-\.\s\u00C0-\u017F\u4e00-\u9fff]+$', re.UNICODE),
    'special_chars': re.compile(r'^[\w\-\.\s\(\)\[\]&!@#$%^*+={}|;:\'\"<>?,/\\]+$')
}


# ============================================================================
# Content and Text Constants
# ============================================================================

# Pre-defined text content for various test scenarios
TEXT_CONTENT_SAMPLES = {
    'basic': "This is a comprehensive test document for content extraction testing.",
    
    'multiline': """This is a comprehensive test document for content extraction testing.

It contains multiple paragraphs with various formatting and special characters.

Special characters: !@#$%^&*()_+-=[]{}|;:'"<>?,.

Numbers: 1234567890

Mixed content: The year 2025 marks significant progress in AI technology.""",
    
    'unicode': """Unicode Test Document

This document contains various Unicode characters for testing:

Accented characters: café, naïve, résumé, jalapeño, piñata
Greek letters: α, β, γ, δ, ε, Ω, Φ, Ψ
Mathematical symbols: ∑, ∏, ∫, √, ∞, ≤, ≥, ≠
Currency symbols: $, €, £, ¥, ₹
Chinese characters: 你好世界 (Hello World)
Japanese characters: こんにちは (Hello)
Arabic characters: مرحبا (Hello)
Russian characters: Привет (Hello)

This tests the system's ability to handle international text.""",
    
    'legal': """UNITED STATES CONSTITUTION

We the People of the United States, in Order to form a more perfect Union,
establish Justice, insure domestic Tranquility, provide for the common defence,
promote the general Welfare, and secure the Blessings of Liberty to ourselves
and our Posterity, do ordain and establish this Constitution for the United
States of America.

ARTICLE I
Section 1. All legislative Powers herein granted shall be vested in a Congress
of the United States, which shall consist of a Senate and House of Representatives.""",
    
    'minimal': "Minimal content.",
    
    'empty': "",
    
    'whitespace': """   

\t\t\t

   \n\n\n   

""",
    
    'large': "This is line {} with repeated content for testing large file processing.\n" * 1000,
    
    'special_chars': "Content with special characters: !@#$%^&*()_+-=[]{}|;:\"'<>?,.\\/"
}


# ============================================================================
# Timing and Performance Constants
# ============================================================================

# Timing constants
TIMING_CONSTANTS = {
    'timestamp_tolerance_seconds': 5.0,
    'default_processing_timeout': 30.0,
    'concurrent_operation_timeout': 60.0,
    'file_read_timeout': 10.0,
    'database_operation_timeout': 15.0,
    'network_request_timeout': 20.0
}

# Concurrency test parameters
CONCURRENCY_LEVELS = [1, 2, 5, 10, 20, 50]

# Performance thresholds
PERFORMANCE_THRESHOLDS = {
    'small_file_processing_ms': 100,
    'medium_file_processing_ms': 500,
    'large_file_processing_ms': 2000,
    'database_insert_ms': 50,
    'content_extraction_ms': 1000
}


# ============================================================================
# Database and Configuration Constants
# ============================================================================

# Default configuration values
DEFAULT_CONFIG_VALUES = {
    'max_file_size': FILE_SIZE_LIMITS['max_size'],  # 50MB
    'supported_file_types': SUPPORTED_FILE_TYPES,
    'database_url': "sqlite:///test.db",
    'upload_directory': "/tmp/uploads",
    'log_level': "DEBUG",
    'enable_concurrent_uploads': True,
    'max_concurrent_uploads': 10,
    'cleanup_temp_files': True,
    'validate_file_integrity': True
}

# Database record field names
DATABASE_FIELDS = {
    'cid': 'cid',
    'filename': 'filename', 
    'file_size': 'file_size',
    'text_content': 'text_content',
    'client_cid': 'client_cid',
    'upload_timestamp': 'upload_timestamp',
    'content_type': 'content_type',
    'file_hash': 'file_hash',
    'processing_status': 'processing_status'
}


# ============================================================================
# Error Simulation Constants  
# ============================================================================

# Error types for simulation
ERROR_SIMULATION_TYPES = {
    'io_error': 'io_error',
    'value_error': 'value_error', 
    'type_error': 'type_error',
    'network_error': 'network_error',
    'memory_error': 'memory_error',
    'permission_error': 'permission_error',
    'timeout_error': 'timeout_error',
    'encoding_error': 'encoding_error',
    'database_connection_error': 'connection',
    'database_constraint_error': 'constraint',
    'database_timeout_error': 'timeout',
    'file_corruption_header': 'header',
    'file_corruption_structure': 'structure',
    'file_corruption_encoding': 'encoding',
    'file_corruption_truncated': 'truncated'
}

# Mock failure configurations
MOCK_FAILURE_CONFIGS = {
    'intermittent_failure_rate': 0.3,  # 30% failure rate
    'cascading_failure_count': 3,      # Number of cascading failures
    'retry_attempt_limit': 5,          # Maximum retry attempts
    'backoff_multiplier': 2.0,         # Exponential backoff multiplier
    'max_backoff_seconds': 60.0        # Maximum backoff time
}


# ============================================================================
# Test Environment Constants
# ============================================================================

# File system paths
TEST_PATHS = {
    'temp_directory': '/tmp/test_uploads',
    'fixtures_directory': '/fixtures',
    'test_data_directory': '/test_data',
    'logs_directory': '/logs'
}

# Test identifiers and markers
TEST_MARKERS = {
    'unit': 'unit',
    'integration': 'integration',
    'performance': 'performance',
    'concurrent': 'concurrent',
    'error_handling': 'error_handling',
    'slow': 'slow'
}

# Resource limits for testing
RESOURCE_LIMITS = {
    'max_memory_mb': 512,
    'max_cpu_percent': 80,
    'max_disk_usage_mb': 1024,
    'max_open_files': 100,
    'max_network_connections': 50
}


# ============================================================================
# Validation Rules
# ============================================================================

# Response validation rules
CID_PREFIX = 'bafkreiht'
FIFTY_TWO = 52

RESPONSE_VALIDATION_RULES = {
    'status': {
        'required': True,
        'type': str,
        'allowed_values': VALID_STATUS_VALUES
    },
    'message': {
        'required': True,
        'type': str,
        'min_length': 1,
        'max_length': 500
    },
    'cid': {
        'required_for_success': True,
        'type': str,
        'pattern': CID_PATTERN,
        'length': len(CID_PREFIX) + FIFTY_TWO
    },
    'filename': {
        'required_for_success': True,
        'type': str,
        'min_length': 1,
        'max_length': 255
    },
    'file_size': {
        'required_for_success': True,
        'type': int,
        'min_value': 0,
        'max_value': FILE_SIZE_LIMITS['max_size']
    },
    'upload_timestamp': {
        'required': True,
        'type': str,
        'pattern': ISO_TIMESTAMP_PATTERN
    },
    'error_code': {
        'required_for_error': True,
        'type': str,
        'allowed_values': set(ERROR_CODES.values())
    }
}

# File validation rules
FILE_VALIDATION_RULES = {
    'filename': {
        'min_length': 1,
        'max_length': 255,
        'forbidden_chars': ['<', '>', ':', '"', '|', '?', '*'],
        'reserved_names': ['CON', 'PRN', 'AUX', 'NUL'] + [f'COM{i}' for i in range(1, 10)] + [f'LPT{i}' for i in range(1, 10)]
    },
    'file_size': {
        'min_size': FILE_SIZE_LIMITS['min_size'],
        'max_size': FILE_SIZE_LIMITS['max_size']
    },
    'content_type': {
        'allowed_types': list(MIME_TYPES.values()),
        'forbidden_types': ['application/x-executable', 'application/x-msdownload']
    }
}


# ============================================================================
# Comprehensive Test Scenarios
# ============================================================================

# All test scenario configurations in one place
TEST_SCENARIOS = {
    'valid_uploads': {
        'file_types': SUPPORTED_FILE_TYPES,
        'sizes': ['small', 'medium', 'large'],
        'content_types': ['basic', 'unicode', 'legal'],
        'client_cid_types': [None, 'valid']
    },
    'invalid_uploads': {
        'file_types': UNSUPPORTED_FILE_TYPES,
        'sizes': ['empty', 'oversized'],
        'corruption_types': ['header', 'structure', 'encoding', 'truncated'],
        'client_cid_types': ['invalid', 'malformed']
    },
    'error_conditions': {
        'io_errors': ['read_error', 'seek_error', 'permission_error'],
        'database_errors': ['connection', 'constraint', 'timeout'],
        'processing_errors': ['extraction_failed', 'cid_generation_failed'],
        'network_errors': ['connection_lost', 'timeout']
    },
    'concurrent_scenarios': {
        'levels': CONCURRENCY_LEVELS,
        'file_patterns': ['identical', 'unique', 'mixed'],
        'client_patterns': ['same_client', 'different_clients', 'mixed_clients']
    }
}