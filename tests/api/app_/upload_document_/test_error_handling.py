import pytest
from fastapi import HTTPException


from .constants import UNSUPPORTED_FILE_TYPES, BAD_INPUT_TYPES


class TestErrorHandling:
    """Test error handling functionality for upload_document method."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "file_key, expected_status_code, app_fixture_name, description",
        [
            ('corrupted', 400, 'mock_app_instance', "invalid file types or corrupted files"),
            ('oversized', 413, 'mock_app_instance', "file exceeds size limit"),
            ('unsupported', 415, 'mock_app_instance', "unsupported file format"),
            ('pdf', 500, 'mock_app_with_db_failure', "internal server errors"),
        ]
    )
    async def test_upload_document_http_exceptions(self, file_key, expected_status_code, app_fixture_name, description, mock_upload_files, request):
        """
        GIVEN various error conditions during file upload
        WHEN the upload_document method is called
        THEN expect an appropriate HTTPException to be raised.
        """
        # Arrange
        app_instance = request.getfixturevalue(app_fixture_name)
        file_to_upload = mock_upload_files[file_key]

        # Act/Assert
        with pytest.raises(HTTPException) as exc_info:
            await app_instance.upload_document(file_to_upload, None)
        
        assert exc_info.value.status_code == expected_status_code, f"Failed on case: {description}. Expected status code {expected_status_code}, got {exc_info.value.status_code} instead"


    @pytest.mark.asyncio
    async def test_when_content_extraction_fails_then_expect_value_error_raised(self, content_extraction_error_simulation, mock_app_instance):
        """
        GIVEN file content input that cannot be processed or extracted
        WHEN the upload_document method is called
        THEN expect ValueError to be raised.
        """
        # Arrange
        pdf_error_mock = content_extraction_error_simulation['pdf']

        # Act/Assert
        with pytest.raises(ValueError):
            await mock_app_instance.upload_document(pdf_error_mock, None)


    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "invalid_type",
        [type for type in BAD_INPUT_TYPES]
    )
    async def test_when_incorrect_parameter_types_for_file_provided_then_expect_type_error_raised(
        self, invalid_type, mock_app_instance):
        """
        GIVEN incorrect parameter types are provided for file argument
        WHEN the upload_document method is called
        THEN expect TypeError to be raised.
        """
        # Act/Assert
        with pytest.raises(TypeError, match=r"file must be an UploadFile object"):
            await mock_app_instance.upload_document(invalid_type, None)


    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "invalid_type",
        [type for type in BAD_INPUT_TYPES]
    )
    async def test_when_incorrect_parameter_types_for_client_cid_provided_then_expect_type_error_raised(
        self, invalid_type, mock_app_instance, valid_file_contents):
        """
        GIVEN incorrect parameter types are provided for client_cid argument
        WHEN the upload_document method is called
        THEN expect TypeError to be raised.
        """
        valid_file = valid_file_contents['pdf']

        # Act/Assert
        with pytest.raises(TypeError, m=r"client_cid must be a string or None"):
            await mock_app_instance.upload_document(valid_file, invalid_type)


    @pytest.mark.asyncio
    async def test_when_file_operations_fail_then_expect_io_error_raised(self, file_read_error_simulation, mock_app_instance):
        """
        GIVEN file cannot be read or temporary storage fails
        WHEN the upload_document method performs file operations
        THEN expect IOError to be raised.
        """
        # Act/Assert
        with pytest.raises(IOError, match=r"Failed to read file content"):
            await mock_app_instance.upload_document(file_read_error_simulation, None)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])