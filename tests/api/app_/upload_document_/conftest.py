"""
Consolidated Fixtures for upload_document testing.

This module provides all fixtures needed for testing the upload_document method
in a single, de-duplicated file. All fixtures use the centralized Factory
and constants to eliminate code duplication across the test suite.
"""
import datetime
from typing import Dict, Any, Iterable
import tempfile
import os
import time
from io import BytesIO
from unittest.mock import MagicMock, AsyncMock
import traceback
import copy


import pytest
from fastapi import UploadFile, HTTPException
from freezegun import freeze_time
import docx
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter as ReportLabLetter




from app.llm import AsyncLLMInterface
from app.app import App, make_app
from app.read_only_database import Database, make_read_only_db
from app.utils.common import get_cid


from ._utilities import TestDataFactory as Factory
from .constants import (
    BAD_INPUT_TYPES,
    CID_PATTERN,
    CONCURRENCY_LEVELS,
    DEFAULT_CONFIG_VALUES,
    ERROR_CODES,
    ERROR_RESPONSE_FIELDS,
    FILE_SIZE_LIMITS,
    FILE_SIZE_PATTERN,
    FILENAME_PATTERNS,
    HTTP_STATUS_CODES,
    ISO_TIMESTAMP_PATTERN,
    MIME_TYPES,
    RESPONSE_FIELD_TYPES,
    RESPONSE_VALIDATION_RULES,
    SUCCESS_RESPONSE_FIELDS,
    SUPPORTED_FILE_TYPES,
    TEST_DATA_SIZES,
    TEXT_CONTENT_SAMPLES,
    TIMING_CONSTANTS,
    UNSUPPORTED_FILE_TYPES,
    VALID_STATUS_VALUES,
)



import logging
import pytest


logging.getLogger("faker.factory").setLevel(logging.WARNING)


# ============================================================================
# File Content Fixtures - All file types handled by Factory
# ============================================================================

@pytest.fixture
def filename_patterns():
    """A dictionary of filename patterns for various test scenarios."""
    return FILENAME_PATTERNS.copy()

@pytest.fixture
def valid_file_contents():
    """A dictionary of valid file contents for all supported types."""
    return {
        'pdf': Factory.create_file_content(
            'pdf',
            text_content=TEXT_CONTENT_SAMPLES['multiline'],
            size='medium'
        ),
        'docx': Factory.create_file_content(
            'docx',
            text_content=TEXT_CONTENT_SAMPLES['multiline'],
            size='medium'
        ),
        'doc': Factory.create_file_content(
            'doc',
            text_content=TEXT_CONTENT_SAMPLES['multiline'],
            size='medium'
        ),
        'txt': Factory.create_file_content(
            'txt',
            text_content=TEXT_CONTENT_SAMPLES['basic'],
            size='small'
        )
    }


@pytest.fixture
def edge_case_file_contents():
    """A dictionary of file contents for various edge case scenarios."""
    return {
        'empty': Factory.create_file_content('empty'),
        'oversized_pdf': Factory.create_file_content('pdf', size='oversized'),
        'corrupted_pdf': Factory.create_file_content(
            'pdf',
            text_content=TEXT_CONTENT_SAMPLES['basic'],
            corruption='header'
        ),
        'unsupported_jpg': Factory.create_file_content('jpg')
    }


@pytest.fixture
def filename_edge_case_files():
    """A dictionary of files with edge case filenames."""
    return {
        'unicode': {
            'content': Factory.create_file_content(
                'txt',
                text_content=TEXT_CONTENT_SAMPLES['unicode']
            ),
            'filename': "测试文档_ñáéíóú_файл.txt"
        },
        'special_chars': {
            'content': Factory.create_file_content(
                'txt',
                text_content=TEXT_CONTENT_SAMPLES['basic']
            ),
            'filename': "test file & document (copy) [1] - final.txt"
        }
    }


# ============================================================================
# UploadFile Mock Fixtures - All use Factory
# ============================================================================

@pytest.fixture
def mock_upload_files(valid_file_contents, edge_case_file_contents, filename_edge_case_files):
    """A dictionary of mock UploadFile objects for various test scenarios."""
    files = {}

    # Create mocks for valid file types
    for file_type, content in valid_file_contents.items():
        ext = f".{file_type}"
        files[file_type] = Factory.create_mock('upload_file', {
            'content': content,
            'filename': f'test_document.{file_type}',
            'content_type': MIME_TYPES[ext],
            'size': len(content)
        })

    # Create mocks for edge case file contents
    files['empty'] = Factory.create_mock('upload_file', {
        'content': edge_case_file_contents['empty'],
        'filename': 'empty_file.txt',
        'content_type': MIME_TYPES['.txt'],
        'size': 0
    })
    files['oversized'] = Factory.create_mock('upload_file', {
        'content': edge_case_file_contents['oversized_pdf'],
        'filename': 'huge_file.pdf',
        'content_type': MIME_TYPES['.pdf'],
        'size': len(edge_case_file_contents['oversized_pdf'])
    })
    files['corrupted'] = Factory.create_mock('upload_file', {
        'content': edge_case_file_contents['corrupted_pdf'],
        'filename': 'corrupted_document.pdf',
        'content_type': MIME_TYPES['.pdf'],
        'size': len(edge_case_file_contents['corrupted_pdf'])
    })
    files['unsupported'] = Factory.create_mock('upload_file', {
        'content': edge_case_file_contents['unsupported_jpg'],
        'filename': 'image.jpg',
        'content_type': MIME_TYPES['.jpg'],
        'size': len(edge_case_file_contents['unsupported_jpg'])
    })

    # Create mocks for filename edge cases
    for name, data in filename_edge_case_files.items():
        content = data['content']
        filename = data['filename']
        ext = f".{filename.split('.')[-1]}"
        files[f'{name}_name'] = Factory.create_mock('upload_file', {
            'content': content,
            'filename': filename,
            'content_type': MIME_TYPES.get(ext, 'application/octet-stream'),
            'size': len(content)
        })

    return files


# ============================================================================
# Client and Session Fixtures - All use Factory
# ============================================================================

@pytest.fixture
def valid_cid():
    """Generate a valid CID for testing."""
    return get_cid("test_client_123")

@pytest.fixture
def client_cid_test_cases(valid_cid):
    """Dictionary containing various client CID test cases."""
    return {
        'valid': valid_cid,
        'invalid': valid_cid[:-1] + 'X',  # Slightly alter to make invalid
        'none': None,
        'multiple': [get_cid(f"client_session_{i:03d}") for i in range(1, 6)],
        'concurrent': [get_cid(f"concurrent_session_{i}")for i in range(10)]
    }


@pytest.fixture
def client_cid_variations(valid_cid):
    """Dictionary containing various client CID test cases."""
    return {
        'valid': get_cid("valid_test_client"),
        'invalid': get_cid(invalid=True, format_type='malformed'),
        'none': None,
        'empty_string': "",
        'too_short': get_cid(invalid=True, format_type='short'),
        'too_long': get_cid(invalid=True, format_type='long'),
        'wrong_prefix': get_cid(invalid=True, format_type='wrong_prefix'),
        'non_string': 12345,
        'unicode': get_cid(invalid=True, format_type='unicode'),
        'with_spaces': get_cid(invalid=True, format_type='with_spaces'),
        'special_chars': get_cid(invalid=True, format_type='special_chars')
    }


# ============================================================================
# Database and Mock Fixtures - All use Factory
# ============================================================================
from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
import logging
import email

def make_magic_mock(spec=None):
    try:
        if spec is None:
            return MagicMock()
        else:
            return MagicMock(spec=spec)
    except Exception as e:
        raise RuntimeError(f"Failed to create MagicMock for spec {spec}: {e}") from e

def make_async_mock(spec=None):
    try:
        if spec is None:
            return AsyncMock()
        else:
            return AsyncMock(spec=spec)
    except Exception as e:
        raise RuntimeError(f"Failed to create AsyncMock for spec {spec}: {e}") from e

@pytest.fixture
def mock_app_resources():
    resources = {
        "read_only_db": make_magic_mock(Database),
        "llm": make_async_mock(AsyncLLMInterface),
        "logger": make_magic_mock(logging.Logger),
        "fastapi": FastAPI, # NOTE We use real dependencies for built-in modules and third party libraries
        "Jinja2Templates": Jinja2Templates,
        "email": email,
        "side_menu": make_magic_mock(),
        "upload_menu": make_magic_mock(),
        "search_function": make_async_mock(),
        "batch_processor": make_async_mock(),
    }
    return resources

@pytest.fixture
def configs():
    """A Configs object with default values."""
    from app.configs import configs as real_configs, Configs
    configs = make_magic_mock(Configs)
    mock_config_values = dict()
    configs_copy = real_configs.model_copy()
    return 

@pytest.fixture
def mock_parameters(mock_app_resources, configs):
    """A dictionary of mock parameters for testing."""
    return {
        'configs': configs,
        'resources': mock_app_resources
    }

@pytest.fixture
def mock_app_instance(mock_parameters):
    """A mock App instance with mocked dependencies."""
    app = make_app(**mock_parameters)
    return app

def make_mock_app(resources = None, configs: dict = None):
    @pytest.fixture
    def _make_mock_app(mock_parameters):
        mock_parameters_copy = mock_parameters.copy()
        if resources is not None:
            mock_parameters_copy['resources'].update(resources)
        if configs is not None:
            mock_parameters_copy['configs'].update(configs)
        try:
            app_instance = make_app(**mock_parameters_copy)
        except Exception as e:
            raise RuntimeError(f"Failed to create mock App instance: {e}") from e
        return app_instance
    return _make_mock_app



@pytest.fixture
def mock_database_failures():
    """A dictionary of mock databases that simulate various failure conditions."""
    return {
        'generic': Factory.create_mock('database', should_fail=True, failure_type='generic'),
        'connection': Factory.create_mock('database', should_fail=True, failure_type='connection'),
        'constraint': Factory.create_mock('database', should_fail=True, failure_type='constraint'),
        'timeout': Factory.create_mock('database', should_fail=True, failure_type='timeout')
    }


@pytest.fixture
def mock_resources_with_db_failure(mock_conmock_resources):
    """Mock resources dictionary with failing database."""
    return Factory.create_mock('resources', {
        'database': {'should_fail': True}
    })





@pytest.fixture
def mock_app_with_db_failure(configs, mock_resources_with_db_failure):
    """A mock App instance with failing database dependencies."""
    return Factory.create_mock('app', {
        'configs': configs,
        'resources': mock_resources_with_db_failure
    }, should_fail=True, failure_type='database')


# ============================================================================
# Response and Validation Fixtures - All use constants and Factory
# ============================================================================




# ==========================================
# TEXT CONTENT FIXTURES
# ==========================================

@pytest.fixture
def text_in_the_image():
    """Simple text content for image OCR testing."""
    return "Hello world!"


@pytest.fixture
def text_with_entities_in_image():
    """Text content with named entities for testing entity extraction."""
    lines = (
        "Barack Obama was the 44th President of the United States.",
        "Michelle Obama was the First Lady.",
        "They have two daughters, Malia and Sasha."
    )
    return lines


@pytest.fixture
def expected_text() -> tuple[str, ...]:
    """Expected text content for standard PDF documents."""
    lines = (
        "Hello my baby!",
        "Hello my honey!",
        "Hello my rag-time gal!"
    )
    return lines


@pytest.fixture
def expected_text_zero_entities() -> tuple[str, ...]:
    """Text content with no named entities for testing."""
    lines = (
        "99 bottles of beer on the wall, 99 bottles of beer.",
        "Take one down, pass it around.",
        "98 bottles of beer on the wall.",
    )
    return lines


@pytest.fixture
def expected_text_with_one_entity() -> tuple[str, ...]:
    """Text content with exactly one named entity for testing."""
    lines = (
        "Hitler is a man.",
        "No man can survive falling into lava.",
        "Therefore, Hitler cannot survive falling into lava",
    )
    return lines


@pytest.fixture
def expected_text_with_two_entities() -> tuple[str, ...]:
    """Text content with two named entities for testing."""
    lines = (
        "Socrates is a man.",
        "John Madden is a man.",
        "All men are mortal.",
        "Therefore, Socrates and John Madden are mortal."
    )
    return lines


@pytest.fixture
def expected_text_with_two_entities_with_close_connection() -> tuple[str, ...]:
    """Text content with two closely connected entities for relationship testing."""
    lines = (
        "Franklin Delano Roosevelt was president.",
        "Theodore Roosevelt was a relative of Franklin Delano Roosevelt.",
        "Therefore, Theodore Roosevelt is related to a president."
    )
    return lines


@pytest.fixture
def expected_text_with_two_entities_with_weak_connection() -> tuple[str, ...]:
    """Text content with two weakly connected entities for relationship testing."""
    lines = (
        "Big Floppa is a cat.",
        "The Andromeda galaxy is vast.",
        "Therefore, they are unrelated."
    )
    return lines

@pytest.fixture
def unicode_text():
    """Text content with Unicode characters for encoding testing."""
    lines = (
        "Accented characters: café, naïve, résumé, jalapeño, piñata",
        "Greek letters: α, β, γ, δ, ε, Ω, Φ, Ψ",
        "Mathematical symbols: ∑, ∏, ∫, √, ∞, ≤, ≥, ≠",
        "Currency symbols: $, €, £, ¥, ₹",
        "Chinese characters: 你好世界 (Hello World)",
        "Japanese characters: こんにちは (Hello)",
        "Arabic characters: مرحبا (Hello)",
        "Russian characters: Привет (Hello)",
    )
    return lines

@pytest.fixture
def minimal_text():
    return ("Hello world!",)

@pytest.fixture
def special_character_text():
    return ("Content with special characters: !@#$%^&*()_+-=[]{}|;:\"'<>?,.\\/",)

@pytest.fixture
def large_text():
    base_line = "This is a line of text to be repeated.\n"
    repeat_count = 1000
    return tuple(base_line for _ in range(repeat_count))

@pytest.fixture
def empty_text():
    return ("",)

@pytest.fixture
def whitespace_text():
    return ("   \n\t  \n",)

@pytest.fixture
def legal_text():
    """Legal text from the US Constitution for testing."""
    return (
        "UNITED STATES CONSTITUTION",
        "",
        """
        We the People of the United States, in Order to form a more perfect Union,
        establish Justice, insure domestic Tranquility, provide for the common defence,
        promote the general Welfare, and secure the Blessings of Liberty to ourselves
        and our Posterity, do ordain and establish this Constitution for the United
        States of America.
        """,
        "",
        "ARTICLE I",
        """
        Section 1. All legislative Powers herein granted shall be vested in a Congress
        of the United States, which shall consist of a Senate and House of Representatives.
        """,
    )


@pytest.fixture
def text_content(
    expected_text,
    unicode_text,
    minimal_text,
    special_character_text,
    large_text,
    legal_text
    ):
    """Dictionary of various text content samples for testing."""
    return {
        'expected_text': expected_text,
        'unicode_text': unicode_text,
        'minimal_text': minimal_text,
        'special_character_text': special_character_text,
        'large_text': large_text,
        'legal_text': legal_text
    }


@pytest.fixture
def text_fixtures_dict(
    text_in_the_image,
    text_with_entities_in_image,
    expected_text,
    expected_text_zero_entities,
    expected_text_with_one_entity,
    expected_text_with_two_entities,
    expected_text_with_two_entities_with_close_connection,
    expected_text_with_two_entities_with_weak_connection
):
    """Dictionary containing all text fixtures."""
    return {
        "text_in_the_image": text_in_the_image,
        "text_with_entities_in_image": text_with_entities_in_image,
        "expected_text": expected_text,
        "expected_text_zero_entities": expected_text_zero_entities,
        "expected_text_with_one_entity": expected_text_with_one_entity,
        "expected_text_with_two_entities": expected_text_with_two_entities,
        "expected_text_with_two_entities_with_close_connection": expected_text_with_two_entities_with_close_connection,
        "expected_text_with_two_entities_with_weak_connection": expected_text_with_two_entities_with_weak_connection
    }


# ==========================================
# PDF DOCUMENT FIXTURES
# ==========================================


@pytest.fixture
def expected_response_fields():
    """Dictionary of required fields for success and error responses."""
    return {
        'success': list(SUCCESS_RESPONSE_FIELDS),
        'error': list(ERROR_RESPONSE_FIELDS)
    }


@pytest.fixture
def test_patterns():
    """Dictionary of regex patterns for validation."""
    return {
        'cid': CID_PATTERN,
        'iso_timestamp': ISO_TIMESTAMP_PATTERN,
        'file_size': FILE_SIZE_PATTERN
    }


@pytest.fixture
def validation_sets():
    """Dictionary of sets for validation purposes."""
    return {
        'valid_status_values': VALID_STATUS_VALUES.copy(),
        'valid_error_codes': set(ERROR_CODES.values())
    }


@pytest.fixture
def sample_responses():
    """A dictionary of sample success and error responses."""
    return {
        'success': Factory.create_response('success', {
            'cid': get_cid("sample_success"),
            'filename': 'test_document.pdf',
            'file_size': FILE_SIZE_LIMITS['medium_file']
        }),
        'error': Factory.create_response(
            'error',
            {'message': 'Upload failed: Invalid file type'},
            error_code=ERROR_CODES['INVALID_FILE_TYPE']
        )
    }


@pytest.fixture
def response_field_types():
    """Expected types for response fields."""
    return RESPONSE_FIELD_TYPES.copy()


@pytest.fixture
def response_validation_rules():
    """Validation rules for response fields."""
    return RESPONSE_VALIDATION_RULES.copy()


# ============================================================================
# Content and Text Fixtures - All use constants
# ============================================================================

from contextlib import contextmanager
from pathlib import Path
from typing import Tuple, Generator


## Basic Valid PDF files.
CUSTOM_METADATA = {
    "ligma": "Ligma what?",
    "sugma": 69,
    "sawcon": ["buffa", "deeze", "nutz"]
}

SAMPLE_METADATA = {
    "author": "Rahul Ligma",
    "title": "The Ligma Chronicles",
    "subject": "An Epic Tale of Ligma on the Quest for Sugma",
    "keywords": "ligma, sugma, sawcon"
}

@pytest.fixture
def custom_metadata():
    CUSTOM_METADATA 

@pytest.fixture
def sample_metadata():
    return SAMPLE_METADATA

@pytest.fixture
def paths(test_constants):
    return test_constants['pdf_paths']

@pytest.fixture
def pagesize(test_constants):
    return test_constants["page_size"]

TEXT_CONTENT = {
    'expected_text': TEXT_CONTENT_SAMPLES['multiline'],
    'unicode': TEXT_CONTENT_SAMPLES['unicode'],
    'large': TEXT_CONTENT_SAMPLES['large'],
    'minimal': TEXT_CONTENT_SAMPLES['minimal'],
    'empty': TEXT_CONTENT_SAMPLES['empty'],
    'whitespace': TEXT_CONTENT_SAMPLES['whitespace'],
    'legal': TEXT_CONTENT_SAMPLES['legal']
}





@pytest.fixture
def test_constants(tmp_path, sample_metadata):
    return {
        "sample_text": "This is a sample text for PDF processing tests.",
        "sample_image_text": "Sample Image",
        "sample_metadata": {**sample_metadata},
        "sample_image_path": tmp_path / "test_image.png",
        "sample_pdf_path": tmp_path / "test_document.pdf",
        "page_size": ReportLabLetter,
        "image_paths": {
            "png": tmp_path / "test_image.png"
        },
        "pdf_paths": {
            "valid": tmp_path / "valid.pdf",
            "invalid": tmp_path / "invalid.pdf",
            "encrypted": tmp_path / "encrypted.pdf",
            "corrupted": tmp_path / "corrupted.pdf",
            "no_read_perms": tmp_path / "no_read_perms.pdf",
            "empty": tmp_path / "empty.pdf",
            "unsupported_version": tmp_path / "unsupported_version.pdf",
            "image": tmp_path / "image.pdf",
            "flat": tmp_path / "flat.pdf",
            "scanned": tmp_path / "scanned.pdf",
            "zero_pages": tmp_path / "zero_pages.pdf",
            "fake": tmp_path / "fake.pdf",
            "locked": tmp_path / "locked.pdf",
            "not_a_pdf": tmp_path / "not_a_pdf.txt"
        },
    }

def _make_mock_pdf(c: canvas.Canvas, pdf_elements):
    """Helper function to draw text elements on a PDF canvas."""
    x, y, lines = pdf_elements
    match pdf_elements:
        case tuple():
            if len(lines) == 1:
                c.drawString(x, y, text)
            else:
                for idx, line in enumerate(lines):
                    c.drawString(x, y - idx * 15, line)
        case list():
            for x, y, text in pdf_elements:
                c.drawString(x, y, text)
        case _:
            raise TypeError(f"Invalid pdf_elements type: {type(pdf_elements).__name__}")
    return c


def _make_pdf_image(c: canvas.Canvas, draw_string_args, draw_image_args, draw_image_kwargs):
    c.drawString(*draw_string_args)
    c.drawImage(*draw_image_args, **draw_image_kwargs)
    return c


@contextmanager
def _make_canvas(path: Path | BytesIO, page_size: Tuple[int, int]) -> Generator[canvas.Canvas, None, None]:
    c = None
    match path:
        case Path():
            path = str(path)
        case BytesIO():
            pass # already BytesIO
        case _:
            raise TypeError(f"Expected path to be Path or BytesIO, got {type(path).__name__}")
    try:
        c = canvas.Canvas(path, pagesize=page_size)
        yield c
    except Exception as e:
        raise RuntimeError(f"Failed to create canvas: {e}") from e
    finally:
        if c is not None:
            c.save()
        if isinstance(path, BytesIO):
            path.seek(0)


@pytest.fixture
def pdf_elements(text_content, sample_metadata) -> list[tuple[int, int, str]]:
    x = 100
    return [
        (x, 700, f"Author: {sample_metadata['author']}"),
        (x, 650, f"Title: {sample_metadata['title']}"),
        (x, 600, f"Subject: {sample_metadata['subject']}"),
        (x, 550, f"Keywords: {sample_metadata['keywords']}"),
        (x, 500, text_content["known"]),
    ]

def make_pdf_elements(name: str):
    """Fixture factory to create PDF elements based on test constants."""
    @pytest.fixture
    def _pdf_elements(test_constants):
        assert len(test_constants[name]) == 3, "Test constant must have exactly three lines of text."
        x = 100
        first, second, third = test_constants[name]
        return [
            (x, 700, first),
            (x, 650, second),
            (x, 600, third),
        ]
    return _pdf_elements

import asyncio

def _make_upload_file(filename: str, buffer: BytesIO) -> UploadFile:
    """Helper function to create an UploadFile from a BytesIO buffer."""
    print(f"buffer.getvalue for {filename}: {buffer.getvalue()[:100]}...")
    buffer.seek(0)
    try:
        upload_file = UploadFile(file=buffer, filename=filename)
        file_bytes = asyncio.run(upload_file.read())
        print(f"upload_file.read for {filename}: {file_bytes[:100]}...")
        buffer.seek(0)  # Reset buffer after read
        return upload_file
    except Exception as e:
        raise RuntimeError(f"Failed to create UploadFile: {e}") from e


@contextmanager
def _buffer():
    buffer = BytesIO()
    try:
        yield buffer
    finally:
        buffer.seek(0)


def make_pdf_file(text_content_key: str):
    """Fixture factory to create in-memory PDF UploadFile with specified text content."""

    @pytest.fixture
    def _make_pdf_file(text_content):
        try:
            lines = text_content[text_content_key]
        except KeyError as e:
            raise KeyError(f"Invalid text_content_key: {text_content_key}") from e
    
        assert isinstance(lines, tuple), f"lines must be a tuple, got {type(lines).__name__}."

        x, y = 100, 500
        filename = f"{text_content_key}.pdf"
        buffer = BytesIO()
        try:
            with _make_canvas(buffer, ReportLabLetter) as c:
                elements = (x, y, lines)
                c = _make_mock_pdf(c, elements)
            buffer.seek(0)
            return _make_upload_file(filename, buffer)
        except RuntimeError as e:
            raise e from e
        except Exception as e:
            raise IOError(f"Failed to create PDF in memory: {e}") from e

    return _make_pdf_file


def make_txt_file(text_content_key):

    @pytest.fixture
    def _make_txt_file(text_content):

        try:
            lines = text_content[text_content_key]
        except KeyError as e:
            raise KeyError(f"Invalid text_content_key: {text_content_key}") from e
        
        assert isinstance(lines, tuple), f"lines must be a tuple, got {type(lines).__name__}."

        file_string: str = ""
        filename = f"{text_content_key}.pdf"
        buffer = BytesIO()
        try:
            for line in lines:
                file_string += line + "\n"
        except TypeError as e:
            raise e
        try:
            buffer.write(file_string.encode('utf-8'))
        except Exception as e:
            raise IOError(f"Failed to write to buffer: {e}") from e
        buffer.seek(0)
    
        return _make_upload_file(filename, buffer)

    return _make_txt_file


def make_docx_file(text_content_key):

    @pytest.fixture
    def _make_docx_file(text_content):

        try:
            lines = text_content[text_content_key]
        except KeyError as e:
            raise KeyError(f"Invalid text_content_key: {text_content_key}") from e

        assert isinstance(lines, tuple), f"lines must be a tuple, got {type(lines).__name__}."

        # Create an in-memory DOCX with python-docx
        buffer = BytesIO()
        filename = f"{text_content_key}.docx"
        doc = docx.Document()
        try:
            for line in lines:
                doc.add_paragraph(line)
        except TypeError as e:
            raise e
        else:
            try:
                doc.save(buffer)
            except Exception as e:
                raise IOError(f"Failed to create DOCX in memory: {e}") from e
        buffer.seek(0)
        return _make_upload_file(filename, buffer)

    return _make_docx_file

FACTORY_FUNCTIONS = {
    'pdf': make_pdf_file,
    'txt': make_txt_file,
    'docx': make_docx_file
}

@pytest.fixture
def factory_functions():
    return {
        'pdf': FACTORY_FUNCTIONS['pdf'],
        'txt': FACTORY_FUNCTIONS['txt'],
        'docx': FACTORY_FUNCTIONS['docx']
    }

@pytest.fixture
def test_files(factory_functions):
    return {
        "pdf": {
            key: FACTORY_FUNCTIONS[key] for key in TEXT_CONTENT.keys()
        },
        "docx": {
            key: FACTORY_FUNCTIONS[key] for key in TEXT_CONTENT.keys()
        },
        "txt": {
            key: FACTORY_FUNCTIONS[key] for key in TEXT_CONTENT.keys()
        }
    }


def make_file_text_pair(file_type: str, text_content_key: str):
    """Fixture factory to create (file_content, expected_text) pairs."""

    @pytest.fixture
    def _file_text_pair(test_files, text_content):

        try:
            expected_text = text_content[text_content_key]
        except KeyError as e:
            raise KeyError(f"Invalid text_content_key: {text_content_key}") from e

        try:
            file_content = test_files[file_type][text_content_key]
        except KeyError as e:
            raise KeyError(f"Invalid file_type: {file_type}, {text_content_key}") from e

        return file_content, expected_text

    return _file_text_pair


pdf_with_known_text = make_file_text_pair('pdf', 'expected_text')
docx_with_unicode_text = make_file_text_pair('docx', 'unicode')
txt_with_legal_content = make_file_text_pair('txt', 'legal')

NUMBER_OF_FILES = 4


def make_files_with_identical_content(file_type: str, text_content_key: str):
    """Multiple files with identical content for CID consistency testing."""
    files = []
    try:
        func = FACTORY_FUNCTIONS[file_type]
    except KeyError as e:
        raise KeyError(f"Invalid file_type: {file_type}") from e

    try:
        for _ in range(NUMBER_OF_FILES):
            file = func(text_content_key)
            files.append(file)
    except Exception as e:
        raise RuntimeError(f"Failed to create files: {e}") from e

    return files

pdf_file = make_pdf_file('expected_text')
pdf_file2 = make_pdf_file('expected_text')
docx_file = make_docx_file('expected_text')
docx_file2 = make_docx_file('expected_text')
txt_file = make_txt_file('expected_text')
txt_file2 = make_txt_file('expected_text')



@pytest.fixture
def files_with_identical_content(
    pdf_file, 
    pdf_file2,
    docx_file,
    docx_file2,
    txt_file,
    txt_file2
    ):
    """A dictionary of lists of files with identical content."""
    pdf_files = [pdf_file, pdf_file2]
    docx_files = [docx_file, docx_file2]
    txt_files = [txt_file, txt_file2]

    return {
        "pdf": pdf_files,
        "docx": docx_files,
        "txt": txt_files
    }


@pytest.fixture
def content_extraction_test_cases():
    """Various content types for comprehensive extraction testing."""
    test_cases = {}
    for content_type, text_content in TEXT_CONTENT_SAMPLES.items():
        content = make_pdf_file(content_type)
        test_cases[content_type] = (content, text_content)
    return test_cases


@pytest.fixture
def text_processing_edge_cases():
    """Edge cases for text processing validation."""
    return {
        "null_bytes": b"Content with \x00 null bytes",
        "mixed_encoding": "Mixed encoding: café".encode('utf-8') + b'\xff\xfe',
        "very_long_line": ("A" * 10000).encode('utf-8'),
        "control_characters": "Content with \t tabs \r carriage returns \n newlines".encode('utf-8'),
        "binary_content": Factory.create_file_content('jpg'),
        "partial_utf8": b'\xc3\xa9\xc3',  # Incomplete UTF-8 sequence
    }


@pytest.fixture
def expected_content_lengths():
    """Expected content lengths for validation testing."""
    return {
        content_type: len(text_content) for content_type, text_content in TEXT_CONTENT_SAMPLES.items()
    }


# ============================================================================
# Error Simulation Fixtures - All use Factory
# ============================================================================

def _make_mock_error(e: Exception, msg: str) -> MagicMock:
    try:
        e = type(e)(msg)
    except Exception as ex:
        raise RuntimeError(f"Failed to create mock error: {ex}") from ex
    return MagicMock(side_effect=e)

def _make_mock_http_error(status_code: int, detail: str) -> HTTPException:
    try:
        e = HTTPException(status_code=status_code, detail=detail)
    except Exception as ex:
        raise RuntimeError(f"Failed to create HTTPException mock: {ex}") from ex
    return MagicMock(side_effect=e)

@pytest.fixture
def error_simulations():
    """A dictionary of mocks that simulate various error conditions."""
    return {
        'io': _make_mock_error(IOError, "Simulated I/O error"),
        'value': _make_mock_error(ValueError, "Simulated value error"),
        'type': _make_mock_error(TypeError, "Simulated type error"),
        'database': _make_mock_error(Exception, "Simulated database error"),
        'timeout': _make_mock_error(TimeoutError, "Simulated timeout error"),
        'os': _make_mock_error(OSError, "Simulated OS error"),
        'memory': _make_mock_error(MemoryError, "Simulated memory error"),
        'permission': _make_mock_error(PermissionError, "Simulated permission error"),
        'http_400': _make_mock_http_error(400, "Simulated HTTP 400 error"),
        'http_413': _make_mock_http_error(413, "Simulated HTTP 413 error"),
        'http_415': _make_mock_http_error(415, "Simulated HTTP 415 error"),
        'http_500': _make_mock_http_error(500, "Simulated HTTP 500 error"),
    }

def make_mock_error(key: str):
    """Fixture factory to create specific error simulation mocks."""
    def _get_mock_error(error_simulations):
        try:
            return error_simulations[key]
        except KeyError as e:
            raise KeyError(f"Invalid error simulation key: {key}") from e
    return _get_mock_error

file_read_error_simulation = make_mock_error('io')
content_extraction_error_simulation = make_mock_error('value')
cid_generation_error_simulation = make_mock_error('value')
database_error_simulations = make_mock_error('database')

@pytest.fixture
def content_extraction_error_simulation(error_simulations):
    """Simulates content extraction failures for various file types."""
    return {
        file_type.strip('.'): error_simulations['value']
        for file_type in SUPPORTED_FILE_TYPES
    }


@pytest.fixture
def database_error_simulations():
    """Simulates various database error conditions."""
    return {
        'connection_error': MagicMock(side_effect=ConnectionError("Database connection failed")),
        'timeout_error': MagicMock(side_effect=TimeoutError("Database operation timed out")),
        'constraint_error': MagicMock(side_effect=ValueError("Database constraint violated")),
        'permission_error': MagicMock(side_effect=PermissionError("Database permission denied")),
        'disk_full_error': MagicMock(side_effect=OSError("No space left on device"))
    }



@pytest.fixture
def processing_error_simulations():
    """A dictionary of mocks that simulate various processing-related errors."""
    return {
        "network": MagicMock(side_effect=Exception("Network error during processing")),
        "memory": MagicMock(side_effect=MemoryError("Out of memory during processing")),
        "permission": MagicMock(side_effect=PermissionError("Permission denied during processing")),
        "timeout": MagicMock(side_effect=TimeoutError("Processing timed out")),
        "encoding": MagicMock(side_effect=UnicodeDecodeError("utf-8", b"", 0, 1, "invalid start byte"))
    }

# ============================================================================
# Time and Constants Fixtures - All use constants
# ============================================================================

@pytest.fixture
def base_timestamp():
    return datetime.datetime(2025, 9, 27, 10, 30, 0, tzinfo=datetime.timezone.utc)

@pytest.fixture
def freeze_time_fixture(base_timestamp):
    """Freezes time for timestamp testing."""
    frozen_time = base_timestamp
    with freeze_time(frozen_time):
        yield frozen_time


@pytest.fixture
def timestamp_tolerance():
    """Acceptable timestamp tolerance for timing tests."""
    return TIMING_CONSTANTS['timestamp_tolerance_seconds']


@pytest.fixture
def test_timestamps(base_timestamp):
    """Various timestamp formats for testing."""
    return {
        'base_time': base_timestamp,
        'valid_timestamp': Factory.create_timestamp(),
        'past_timestamp': Factory.create_timestamp(-3600),
        'future_timestamp': Factory.create_timestamp(3600),
        'invalid_format': '2025-09-27 10:30:00',
        'invalid_string': 'not-a-timestamp'
    }


@pytest.fixture
def test_constants():
    """A dictionary of all test constants and values."""
    return {
        'file_size_limits': FILE_SIZE_LIMITS.copy(),
        'bad_input_types': BAD_INPUT_TYPES.copy(),
        'test_data_sizes': TEST_DATA_SIZES.copy(),
        'timestamp_tolerance': TIMING_CONSTANTS['timestamp_tolerance_seconds'],
        'processing_timeout': TIMING_CONSTANTS['default_processing_timeout'],
        'concurrent_timeout': TIMING_CONSTANTS['concurrent_operation_timeout'],
        'valid_extensions': SUPPORTED_FILE_TYPES.copy(),
        'invalid_extensions': UNSUPPORTED_FILE_TYPES.copy(),
        'mime_types': MIME_TYPES.copy(),
        'error_codes': ERROR_CODES.copy(),
        'http_status_codes': HTTP_STATUS_CODES.copy()
    }


# ============================================================================
# Parametrized Test Data Fixtures - All use constants
# ============================================================================

from fastapi import UploadFile



@pytest.fixture(params=['pdf', 'docx', 'doc', 'txt'])
def valid_file_types(request):
    """Parametrized fixture for all valid file types."""
    return f".{request.param}"


@pytest.fixture(params=['jpg', 'png', 'mp4', 'exe'])
def invalid_file_types(request):
    """Parametrized fixture for all invalid file types."""
    return f".{request.param}"


@pytest.fixture(params=[None, 'valid_cid', 'invalid_cid'])
def client_cid_variations_param(request, valid_client_cid, invalid_client_cid):
    """Parametrized fixture for different client_cid values."""
    match request.param:
        case None:
            return None
        case 'valid_cid':
            return valid_client_cid
        case 'invalid_cid':
            return invalid_client_cid


@pytest.fixture(params=['small', 'medium', 'large'])
def file_size_variations(request, test_data_sizes):
    """Parametrized fixture for different file sizes."""
    return test_data_sizes[request.param]


@pytest.fixture(params=[1, 5, 10, 20])
def concurrency_levels(request):
    """Parametrized fixture for different concurrency levels."""
    return request.param


@pytest.fixture(params=['success', 'file_error', 'database_error', 'processing_error'])
def error_scenarios(request):
    """Parametrized fixture for different error scenarios."""
    return request.param


# ============================================================================
# Concurrent Testing Fixtures - All use Factory
# ============================================================================

@pytest.fixture
def concurrent_upload_files():
    """A dictionary of file sets for concurrent upload testing."""
    args = (5, 'pdf')
    different_files_data = Factory.create_multiple_files(*args, identical_content=False)
    identical_files_data = Factory.create_multiple_files(*args, identical_content=True)
    return {
        'different': [content for content, filename in different_files_data],
        'identical': [content for content, filename in identical_files_data]
    }


# ============================================================================
# Helper Function Fixtures - All use Factory or constants
# ============================================================================

@pytest.fixture
def create_temp_file():
    """Helper function to create temporary test files."""

    def _create_temp_file(content: bytes, suffix: str = '.tmp') -> str:
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
    """Helper function to verify database record creation."""
    def _verify_database_record(db_mock, expected_cid: str, expected_data: Dict[str, Any]) -> bool:
        if not db_mock.execute.called:
            return False
        call_args = db_mock.execute.call_args
        return call_args is not None
    
    return _verify_database_record


@pytest.fixture
def generate_test_cid():
    """Helper function to generate test CIDs."""
    return get_cid


@pytest.fixture
def timing_utilities():
    """Utilities for timing and performance testing."""

    
    def measure_execution_time(func, *args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        return result, end_time - start_time
    
    def assert_execution_time(max_seconds: float):
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


# ============================================================================
# Comprehensive Test Scenario Fixtures
# ============================================================================

@pytest.fixture
def all_file_type_scenarios():
    """All combinations of valid file types with different content."""
    scenarios = []
    for file_type in ['pdf', 'docx', 'doc', 'txt']:
        for content_type, text_content in TEXT_CONTENT_SAMPLES.items():
            if content_type not in ['large', 'empty']:  # Skip problematic content
                content = Factory.create_file_content(file_type, text_content=text_content)
                mock_file = Factory.create_mock('upload_file', {
                    'content': content,
                    'filename': f'test_{content_type}.{file_type}',
                    'content_type': MIME_TYPES[f'.{file_type}'],
                    'size': len(content)
                })
                scenarios.append((file_type, content_type, mock_file))
    return scenarios


@pytest.fixture
def all_error_scenarios():
    """All combinations of error types and failure conditions."""
    scenarios = {}

    # File-related errors
    scenarios['file_errors'] = {
        'empty': Factory.create_mock('upload_file', {'content': b'', 'size': 0}),
        'oversized': Factory.create_mock('upload_file', {
            'content': Factory.create_file_content('pdf', size='oversized'),
            'size': FILE_SIZE_LIMITS['oversized']
        }),
        'corrupted': Factory.create_mock('upload_file', {
            'content': Factory.create_file_content('pdf', corruption='header')
        }),
        'unsupported': Factory.create_mock('upload_file', {
            'content': Factory.create_file_content('jpg'),
            'content_type': MIME_TYPES['.jpg'],
            'filename': 'image.jpg'
        })
    }

    # Database errors
    scenarios['database_errors'] = {
        'connection': Factory.create_mock('database', should_fail=True, failure_type='connection'),
        'constraint': Factory.create_mock('database', should_fail=True, failure_type='constraint'),
        'timeout': Factory.create_mock('database', should_fail=True, failure_type='timeout')
    }

    # Processing errors
    scenarios['processing_errors'] = {
        'io_error': Factory.create_mock('error', failure_type='io_error'),
        'extraction_error': Factory.create_mock('error', failure_type='value_error'),
        'memory_error': Factory.create_mock('error', failure_type='memory_error')
    }

    return scenarios


@pytest.fixture
def concurrent_test_matrix():
    """Matrix of concurrent testing scenarios."""
    matrix = []
    limit = 4
    for level in CONCURRENCY_LEVELS[:limit]:
        # Same files
        same_files = Factory.create_multiple_files(level, 'pdf', identical_content=True)
        matrix.append(('same_files', level, same_files))
        
        # Different files  
        diff_files = Factory.create_multiple_files(level, 'pdf', identical_content=False)
        matrix.append(('different_files', level, diff_files))
        
        # Mixed file types
        mixed_files = []
        for idx, file_type in enumerate(['pdf', 'docx', 'doc', 'txt']):
            if idx >= level:
                break
            files = Factory.create_multiple_files(1, file_type, identical_content=False)
            mixed_files.extend(files)
        matrix.append(('mixed_types', level, mixed_files[:level]))

    return matrix
