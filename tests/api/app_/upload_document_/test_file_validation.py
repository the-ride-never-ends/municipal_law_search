import pytest
from fastapi import UploadFile, HTTPException
from io import BytesIO

@pytest.mark.asyncio
class TestFileValidation:
    """Test file validation functionality for upload_document method."""

    async def test_when_valid_pdf_file_uploaded_then_expect_success_status_returned(self, mock_upload_files, mock_app_instance):
        """
        GIVEN a valid PDF file is prepared for upload
        WHEN the upload_document method is called with the PDF file
        THEN expect the returned JSONResponse to have status field equal to "success".
        """
        # Arrange
        pdf_file = mock_upload_files['pdf']
        expected_status = "success"

        # Act
        result = await mock_app_instance.upload_document(pdf_file, None)

        # Assert
        assert result.status == expected_status, f"Expected status to be {expected_status}, got {result.status} instead"

    async def test_when_empty_file_uploaded_then_expect_error_status_returned(self, mock_upload_files, mock_app_instance):
        """
        GIVEN a zero-byte file is prepared for upload
        WHEN the upload_document method is called with the empty file
        THEN expect the returned JSONResponse to have status field equal to "error".
        """
        # Arrange
        empty_file = mock_upload_files['empty']
        expected_status = "error"

        # Act
        result = await mock_app_instance.upload_document(empty_file, None)

        # Assert
        assert result.status == expected_status, f"Expected status to be {expected_status}, got {result.status} instead"
    

    @pytest.mark.parametrize(
        "file_key, status_code_key",
        [
            ("unsupported", "unsupported_media_type"),
            ("oversized", "payload_too_large"),
        ],
    )
    async def test_when_invalid_file_uploaded_then_expect_http_exception_raised(
        self, mock_upload_files, mock_app_instance, test_constants, file_key, status_code_key
    ):
        """
        GIVEN an invalid file (unsupported type, oversized) is prepared for upload
        WHEN the upload_document method is called with the file
        THEN expect an HTTPException with the appropriate status code to be raised.
        """
        # Arrange
        invalid_file = mock_upload_files[file_key]
        expected_status_code = test_constants["http_status_codes"][status_code_key]

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await mock_app_instance.upload_document(invalid_file, None)

        assert exc_info.value.status_code == expected_status_code, \
            f"For {file_key} file, expected HTTP status {expected_status_code}, "f"got {exc_info.value.status_code} instead"

    async def test_when_empty_file_uploaded_then_expect_file_empty_error_code_returned(self, mock_upload_files, mock_app_instance, test_constants):
        """
        GIVEN a zero-byte file is prepared for upload
        WHEN the upload_document method is called with the empty file
        THEN expect the returned JSONResponse to have the appropriate error code.
        """
        # Arrange
        empty_file = mock_upload_files['empty']
        expected_error_code = test_constants['error_codes']['FILE_EMPTY']

        # Act
        result = await mock_app_instance.upload_document(empty_file, None)

        # Assert
        assert result.error_code == expected_error_code, f"Expected error code to be {expected_error_code}, got {result.error_code} instead"

    async def test_when_corrupted_file_uploaded_then_expect_http_exception_400_raised(self, mock_upload_files, mock_app_instance, test_constants):
        """
        GIVEN a corrupted or unreadable file is prepared for upload
        WHEN the upload_document method is called with the corrupted file
        THEN expect HTTPException with status 400 to be raised.
        """
        # Arrange
        corrupted_file = mock_upload_files['corrupted']
        expected_status_code = test_constants['http_status_codes']['bad_request']

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await mock_app_instance.upload_document(corrupted_file, None)
        
        assert exc_info.value.status_code == expected_status_code, f"Expected HTTP status {expected_status_code}, got {exc_info.value.status_code} instead"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
