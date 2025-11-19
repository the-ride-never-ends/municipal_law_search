"""
Utilities and Factories for upload_document testing.

This module provides unified factory functions for creating test data,
eliminating duplication across fixture modules. All common patterns
for CID generation, file creation, mock creation, and response generation
are centralized here.
"""
import io
import hashlib
import uuid
import zipfile
import datetime
import logging
from unittest.mock import Mock, AsyncMock, MagicMock
from typing import Dict, Any, Optional, List, Tuple
import traceback


from fastapi import UploadFile, HTTPException


from app.app import make_app
from app.utils.common.get_cid import get_cid
from app.llm import AsyncLLMInterface
from app.read_only_database import make_read_only_db, Database


class TestDataFactory:
    """
    Centralized factory for creating all types of test data.
    
    This factory eliminates duplication by providing single methods
    that can generate various types of test data with different
    configurations based on parameters.
    """
    NUM_CHARS_CID = 52  # Standard CID length
    SHORT_CID_LENGTH = 20
    CID_PREFIX = "bafkreiht"

    INVALID_CID_FORMATS = {
        'malformed': "invalid_cid_format_12345",
        'wrong_prefix': "qmfkreiht" + hashlib.sha256(b"test").hexdigest()[:NUM_CHARS_CID],
        'too_short': CID_PREFIX, 
        'with_spaces': f"{CID_PREFIX} 123456789abcdef",
        'special_chars': f"{CID_PREFIX}!@#$%^&*()",
        'unicode': f"{CID_PREFIX}测试",
        'empty': "",
        'numeric': 12345
    }

    SIZE_MULTIPLIERS = {
        'minimal': 1,
        'small': 10,
        'medium': 100,
        'large': 1000,
        'oversized': 100000
    }

    @classmethod
    def make_cid(cls, content: str = None, invalid: bool = False, format_type: str = 'standard') -> str:
        """
        Generate CIDs for testing - the single source of truth for CID generation.
        
        Args:
            content: Optional content to base CID on, otherwise generates random
            invalid: If True, generates invalid CID format
            format_type: Type of CID format ('standard', 'short', 'long', 'malformed')
            
        Returns:
            str: Generated CID in requested format
        """
        if invalid:
            return cls.INVALID_CID_FORMATS[format_type]

        input_content = content or str(uuid.uuid4())

        cid_value = get_cid(input_content, for_string=True)

        match format_type:
            case 'short':
                return cid_value[:cls.SHORT_CID_LENGTH]
            case 'long':
                return f"{cid_value}extra_chars"
            case _:  # standard
                return cid_value

    @classmethod
    def create_file_content(
        cls,
        file_type: str,
        text_content: str = None,
        size: str = 'medium',
        corruption: str = 'none',
        encoding: str = 'utf-8'
    ) -> bytes:
        """
        Unified file content creation - handles all file types in one place.
        
        Args:
            file_type: Type of file ('pdf', 'docx', 'doc', 'txt', 'jpg', etc.)
            text_content: Text to embed in file
            size: Size category ('minimal', 'small', 'medium', 'large', 'oversized')
            corruption: Corruption type ('none', 'header', 'structure', 'encoding')
            encoding: Text encoding for text-based files
            
        Returns:
            bytes: Generated file content
        """
        # Handle special case for 'empty' file type
        if file_type == 'empty':
            return b''

        if text_content is None:
            text_content = cls._generate_text_content(size)

        if corruption != 'none':
            return cls._corrupt_content(file_type, text_content, corruption)

        # Dispatch to specific file creators
        creators = {
            'pdf': cls._create_pdf_content,
            'docx': cls._create_docx_content, 
            'doc': cls._create_doc_content,
            'txt': cls._create_txt_content,
            'jpg': cls._create_jpg_content,
            'png': cls._create_png_content,
            'empty': lambda text, enc: b''
        }
        if file_type not in creators:
            raise KeyError(f"Unsupported file type: {file_type}")

        creator = creators[file_type]
        return creator(text_content, encoding)

    @classmethod
    def _generate_text_content(cls, size: str) -> str:
        """Generate text content of specified size."""
        base_content = "This is test content for upload_document testing."

        if size not in cls.SIZE_MULTIPLIERS:
            raise KeyError(f"Unsupported size category: {size}")

        return (base_content + "\n") * cls.SIZE_MULTIPLIERS[size]

    @staticmethod
    def _create_pdf_content(text_content: str, encoding: str) -> bytes:
        """Create valid PDF content."""
        pdf_template = f"""%PDF-1.4
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
        return pdf_template.encode(encoding)

    @staticmethod
    def _create_docx_content(text_content: str, encoding: str) -> bytes:
        """Create valid DOCX content."""
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as docx:
            docx.writestr('[Content_Types].xml', 
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                '<Default Extension="xml" ContentType="application/xml"/>'
                '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
                '</Types>')

            docx.writestr('_rels/.rels',
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
                '</Relationships>')

            docx.writestr('word/document.xml',
                f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                f'<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
                f'<w:body>'
                f'<w:p><w:r><w:t>{text_content}</w:t></w:r></w:p>'
                f'</w:body>'
                f'</w:document>')

        buffer.seek(0)
        return buffer.getvalue()

    @staticmethod
    def _create_doc_content(text_content: str, encoding: str) -> bytes:
        """Create valid DOC content."""
        doc_header = b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1'  # OLE signature
        doc_body = text_content.encode(encoding)
        padding = b'\x00' * (512 - len(doc_body) % 512) if len(doc_body) % 512 else b''
        return doc_header + doc_body + padding

    @staticmethod
    def _create_txt_content(text_content: str, encoding: str) -> bytes:
        """Create TXT content."""
        return text_content.encode(encoding)

    @staticmethod
    def _create_jpg_content(text_content: str, encoding: str) -> bytes:
        """Create minimal JPG header."""
        return b'\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xFF\xDB'

    @staticmethod
    def _create_png_content(text_content: str, encoding: str) -> bytes:
        """Create minimal PNG header."""
        return b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR'

    @classmethod
    def _corrupt_content(cls, file_type: str, text_content: str, corruption: str) -> bytes:
        """Create corrupted file content."""
        base_content = cls.create_file_content(file_type, text_content)

        match corruption:
            case 'header':
                return b'CORRUPTED_HEADER' + base_content[10:]
            case 'structure':
                return base_content[:len(base_content)//2] + b'\xFF\xFE\xFD' + base_content[len(base_content)//2+10:]
            case 'encoding':
                return b'\xFF\xFE\xFD' + base_content
            case 'truncated':
                return base_content[:len(base_content)//2]
            case _:
                return base_content + b'\x00\xFF\xFE\xFD'

    @classmethod
    def create_mock(
        cls,
        mock_type: str,
        should_fail: bool = False,
        failure_type: str = 'generic'
    ) -> Mock:
        """
        Unified mock creation - handles all mock types in one place.

        Args:
            mock_type: Type of mock ('upload_file', 'database', 'app', 'error')
            config: Configuration parameters for the mock
            should_fail: Whether mock should simulate failures
            failure_type: Type of failure to simulate

        Returns:
            Mock: Configured mock object
        """
        mock_creators = {
            'database': cls._create_database_mock,
            'app': cls._create_app_mock,
            'resources': cls._create_resources_mock,
            'error': cls._create_error_mock
        }
        if mock_type not in mock_creators:
            raise KeyError(f"Unsupported mock type: {mock_type}\n{traceback.print_exc()}")

        creator = mock_creators[mock_type]
        return creator(should_fail, failure_type)

    @classmethod
    def _create_upload_file_mock(cls, config: Dict, should_fail: bool, failure_type: str) -> Mock:
        """Create UploadFile mock."""
        content = config.get('content', b'test content')
        filename = config.get('filename', 'test.txt')
        content_type = config.get('content_type', 'text/plain')
        size = config.get('size', len(content))

        file_stream = io.BytesIO(content)
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = filename
        mock_file.content_type = content_type
        mock_file.size = size
        mock_file.file = file_stream

        if should_fail:
            if failure_type == 'read_error':
                mock_file.read = AsyncMock(side_effect=IOError("Cannot read file"))
            elif failure_type == 'seek_error':
                mock_file.seek = Mock(side_effect=IOError("Cannot seek in file"))
            else:
                mock_file.read = AsyncMock(side_effect=Exception("File operation failed"))
        else:
            async def mock_read(size: int = -1) -> bytes:
                if size == -1:
                    file_stream.seek(0)
                    return file_stream.read()
                return file_stream.read(size)

            mock_file.read = AsyncMock(side_effect=mock_read)
            mock_file.seek = lambda offset, whence=0: file_stream.seek(offset, whence)

        return mock_file

    @classmethod
    def _create_database_mock(cls, config: Dict, should_fail: bool, failure_type: str) -> Mock:
        """Create database mock."""
        mock_db = Mock()

        if should_fail:
            error_types = {
                'connection': ConnectionError("Database connection failed"),
                'constraint': Exception("UNIQUE constraint failed"),
                'timeout': TimeoutError("Database operation timed out"),
                'permission': PermissionError("Database access denied"),
                'disk_full': OSError("No space left on device")
            }
            if failure_type not in error_types:
                raise KeyError(f"Unsupported failure type: {failure_type}")

            error = error_types[failure_type]

            mock_db.execute.side_effect = error
            mock_db.fetch_one.side_effect = error
            mock_db.fetch_all.side_effect = error
        else:
            mock_db.execute.return_value = True
            mock_db.fetch_one.return_value = config['record']
            mock_db.fetch_all.return_value = [mock_db.fetch_one.return_value]

        # Connection management
        mock_db.connect = Mock()
        mock_db.close = Mock()
        mock_db.__enter__ = Mock(return_value=mock_db)
        mock_db.__exit__ = Mock(return_value=None)

        return mock_db

    @classmethod
    def _create_app_mock(cls, config: Dict, should_fail: bool, failure_type: str) -> Mock:
        """Create App instance mock."""
        from app.configs import configs

        resources = {
            "llm": AsyncMock(spec_set=AsyncLLMInterface),
            "logger": MagicMock(spec=logging.Logger),
            "db": AsyncMock(spec=Database),
        }

        mock_app = make_app(resources=resources, configs=configs)

        return mock_app

    @staticmethod
    def _create_configs_mock(config: Dict) -> Mock:
        """Create configuration mock."""
        configs = Mock()
        configs.max_file_size = config['max_file_size']
        configs.supported_file_types = config['supported_file_types']
        configs.database_url = config['database_url']
        configs.upload_directory = config['upload_directory']
        configs.log_level = config['log_level']
        return configs

    @classmethod
    def _create_resources_mock(cls, config: Dict, should_fail: bool, failure_type: str) -> Mock:
        """Create resources dictionary mock."""
        mock_db = cls.create_mock('database', config.get('database', {}), should_fail, failure_type)

        return {
            'database': mock_db,
            'logger': Mock(),
            'cid_generator': Mock(return_value=cls.make_cid()),
            'text_extractor': Mock(return_value="Extracted text content"),
            'file_processor': Mock(),
            'timestamp_generator': Mock(return_value=cls.create_timestamp())
        }

    @staticmethod
    def _create_error_mock(failure_type: str) -> Mock:
        """Create error simulation mock."""
        mock = Mock()

        error_types = {
            'io_error': IOError("File operation failed"),
            'value_error': ValueError("Content extraction failed"),
            'type_error': TypeError("Invalid parameter type"),
            'http_400': HTTPException(status_code=400, detail="Bad Request"),
            'http_413': HTTPException(status_code=413, detail="Payload Too Large"),
            'http_415': HTTPException(status_code=415, detail="Unsupported Media Type"),
            'http_500': HTTPException(status_code=500, detail="Internal Server Error"),
            'network_error': ConnectionError("Network connection lost"),
            'memory_error': MemoryError("Insufficient memory"),
            'permission_error': PermissionError("Permission denied"),
            'timeout_error': TimeoutError("Operation timed out"),
            'encoding_error': UnicodeDecodeError('utf-8', b'\xff\xfe', 0, 1, 'invalid start byte')
        }
        if failure_type not in error_types:
            raise KeyError(f"Unsupported failure type: {failure_type}")

        mock.side_effect = error_types[failure_type]
        return mock


    @classmethod
    def create_response(
        cls, 
        status: str,
        data: Optional[Dict[str, Any]] = {
            'message': 'Operation completed successfully',
            'cid': lambda : get_cid(str(uuid.uuid4()), for_string=True),
            'filename': 'test_document.pdf',
            'file_size': 1024
        },
        error_code: str = None,
        timestamp: str = None
    ) -> Dict[str, Any]:
        """
        Unified response creation - single source of truth for response structure.
        
        Args:
            status: Response status ('success' or 'error')
            data: Additional response data
            error_code: Error code for error responses
            timestamp: Custom timestamp (generated if None)
            
        Returns:
            Dict[str, Any]: Properly structured response
        """
        data = data or {}

        if timestamp is None:
            timestamp = cls.create_timestamp()

        base_response = {
            'status': status,
            'upload_timestamp': timestamp
        }

        if status == 'success':
            success_response = {
                **base_response,
                'message': data['message'],
                'cid': data['cid'],
                'filename': data['filename'],
                'file_size': data['file_size']
            }
            return success_response
        else:  # error
            error_response = {
                **base_response,
                'message': data['message'],
                'error_code': error_code
            }
            return error_response

    @staticmethod
    def create_timestamp(offset_seconds: int = 0) -> str:
        """
        Create ISO timestamp - single source for all timestamp generation.

        Args:
            offset_seconds: Offset from current time in seconds

        Returns:
            str: ISO formatted timestamp
        """
        timestamp = datetime.datetime.now(datetime.timezone.utc)
        if offset_seconds != 0:
            timestamp += datetime.timedelta(seconds=offset_seconds)
        return timestamp.isoformat().replace('+00:00', 'Z')

    @classmethod
    def create_multiple_files(
        cls,
        count: int,
        file_type: str = 'pdf',
        identical_content: bool = False,
        base_filename: str = 'test_document'
    ) -> List[Tuple[bytes, str]]:
        """
        Create multiple files for concurrent testing.
        
        Args:
            count: Number of files to create
            file_type: Type of files to create
            identical_content: Whether all files should have identical content
            base_filename: Base filename pattern
            
        Returns:
            List[Tuple[bytes, str]]: List of (content, filename) tuples
        """
        files = []
        base_content = "Shared content for multiple files" if identical_content else None

        for i in range(count):
            content = cls.create_file_content(
                file_type,
                text_content=base_content or f"Content for file {i+1}",
                size='medium'
            )
            filename = f"{base_filename}_{i+1}.{file_type}"
            files.append((content, filename))

        return files
