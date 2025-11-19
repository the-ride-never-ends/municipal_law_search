import pytest
from fastapi import UploadFile


class TestParameterValidation:
    """Test parameter validation for upload_document method."""

    @pytest.mark.asyncio
    async def test_when_no_file_parameter_provided_then_expect_type_error_raised(self, mock_app_instance):
        """
        GIVEN an App instance with no file parameter provided
        WHEN the upload_document method is called without the file parameter
        THEN expect TypeError to be raised with message containing 'missing 1 required positional argument'.
        """
        # Arrange
        expected_error_msg = "missing 1 required positional argument"

        # Act & Assert
        with pytest.raises(TypeError, match=expected_error_msg):
            await mock_app_instance.upload_document()

    @pytest.mark.asyncio
    async def test_when_invalid_file_parameter_type_provided_then_expect_type_error_raised(self, mock_app_instance):
        """
        GIVEN an App instance and a non-UploadFile object as the file parameter
        WHEN the upload_document method is called with the invalid file type
        THEN expect TypeError to be raised.
        """
        # Arrange
        invalid_file = "not_an_upload_file"

        # Act & Assert
        with pytest.raises(TypeError, match=r"file must be an UploadFile object"):
            await mock_app_instance.upload_document(invalid_file)

    @pytest.mark.asyncio
    async def test_when_client_cid_is_none_then_expect_no_exceptions_raised(self, mock_app_instance, mock_upload_files):
        """
        GIVEN an App instance with valid file and client_cid set to None
        WHEN the upload_document method is called
        THEN expect no exceptions to be raised during method execution.
        """
        # Arrange
        valid_file = mock_upload_files['pdf']
        client_cid = None

        # Act & Assert (no exception should be raised)
        result = await mock_app_instance.upload_document(valid_file, client_cid)
        assert result is not None

    @pytest.mark.asyncio
    async def test_when_client_cid_is_none_then_expect_success_status_returned(self, mock_app_instance, mock_upload_files):
        """
        GIVEN an App instance with valid file and client_cid set to None
        WHEN the upload_document method is called
        THEN expect the returned JSONResponse to have status field equal to "success".
        """
        # Arrange
        valid_file = mock_upload_files['pdf']
        client_cid = None
        expected_status = "success"

        # Act
        result = await mock_app_instance.upload_document(valid_file, client_cid)
        response_data = result.body.decode('utf-8')

        # Assert
        assert expected_status in response_data, f"Expected status '{expected_status}' to be in response, got {response_data}"

    # @pytest.mark.asyncio
    # async def test_when_valid_client_cid_provided_then_expect_upload_associated_with_client(self, mock_app_instance, mock_upload_files, client_cid_test_cases):
    #     """
    #     GIVEN an App instance with valid file and properly formatted CID string for client_cid
    #     WHEN the upload_document method is called
    #     THEN expect the method to accept the client_cid and associate the upload with that client.
    #     """
    #     # Arrange
    #     valid_file = mock_upload_files['pdf']
    #     valid_client_cid = client_cid_test_cases['valid']

    #     # Act
    #     result = await mock_app_instance.upload_document(valid_file, valid_client_cid)

    #     # Assert
    #     assert result is not None, f"Expected method to return result when valid client_cid provided, got None"

    @pytest.mark.asyncio
    async def test_when_invalid_client_cid_format_provided_then_expect_value_error_raised(self, mock_app_instance, mock_upload_files, client_cid_variations):
        """
        GIVEN an App instance with valid file and improperly formatted client_cid string
        WHEN the upload_document method is called
        THEN expect ValueError to be raised.
        """
        # Arrange
        valid_file = mock_upload_files['pdf']
        invalid_client_cid = client_cid_variations['invalid']

        # Act & Assert
        with pytest.raises(ValueError):
            await mock_app_instance.upload_document(valid_file, invalid_client_cid)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])