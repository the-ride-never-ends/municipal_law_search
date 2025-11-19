import pytest


class TestResponseFormat:
    """Test response format validation for upload_document method."""

    def test_when_file_uploaded_successfully_then_expect_response_contains_all_required_fields(
        self, mock_app_instance, mock_upload_files, expected_response_fields
    ):
        """
        GIVEN a file is successfully uploaded and processed
        WHEN the upload_document method returns a response
        THEN expect the JSON response to contain all required fields (status, message, cid, filename, file_size, upload_timestamp) with correct data types.
        """
        # Arrange
        upload_file = mock_upload_files['pdf']
        expected_fields = set(expected_response_fields['success'])
        
        # Act
        response = mock_app_instance.upload_document(upload_file, None)
        response_data = response.json()
        actual_fields = set(response_data.keys())
        
        # Assert
        assert actual_fields == expected_fields, f"Expected response fields {expected_fields}, got {actual_fields} instead"

    def test_when_successful_upload_completed_then_expect_status_field_equals_success(
        self, mock_app_instance, mock_upload_files, validation_sets
    ):
        """
        GIVEN a file is successfully uploaded and processed
        WHEN the upload_document method returns a success response
        THEN expect status field to equal "success".
        """
        # Arrange
        upload_file = mock_upload_files['pdf']
        expected_status = "success"
        
        # Act
        response = mock_app_instance.upload_document(upload_file, None)
        response_data = response.json()
        actual_status = response_data['status']
        
        # Assert
        assert actual_status == expected_status, f"Expected status to be {expected_status}, got {actual_status} instead"

    def test_when_successful_upload_completed_then_expect_message_field_not_empty(
        self, mock_app_instance, mock_upload_files
    ):
        """
        GIVEN a file is successfully uploaded and processed
        WHEN the upload_document method returns a success response
        THEN expect message field to not be empty.
        """
        # Arrange
        upload_file = mock_upload_files['pdf']
        
        # Act
        response = mock_app_instance.upload_document(upload_file, None)
        response_data = response.json()
        message = response_data['message']
        
        # Assert
        assert len(message) > 0, f"Expected message to not be empty, got message with length {len(message)} instead"

    def test_when_successful_upload_completed_then_expect_filename_field_matches_original(
        self, mock_app_instance, mock_upload_files
    ):
        """
        GIVEN a file is successfully uploaded and processed
        WHEN the upload_document method returns a success response
        THEN expect response filename field to match the original uploaded filename.
        """
        # Arrange
        upload_file = mock_upload_files['pdf']
        expected_filename = upload_file.filename
        
        # Act
        response = mock_app_instance.upload_document(upload_file, None)
        response_data = response.json()
        actual_filename = response_data['filename']
        
        # Assert
        assert actual_filename == expected_filename, f"Expected filename to be {expected_filename}, got {actual_filename} instead"

    def test_when_successful_upload_completed_then_expect_file_size_field_matches_actual_size(
        self, mock_app_instance, mock_upload_files
    ):
        """
        GIVEN a file is successfully uploaded and processed
        WHEN the upload_document method returns a success response
        THEN expect response file_size field to match the actual uploaded file size in bytes.
        """
        # Arrange
        upload_file = mock_upload_files['pdf']
        expected_file_size = upload_file.size
        
        # Act
        response = mock_app_instance.upload_document(upload_file, None)
        response_data = response.json()
        actual_file_size = response_data['file_size']
        
        # Assert
        assert actual_file_size == expected_file_size, f"Expected file_size to be {expected_file_size}, got {actual_file_size} instead"

    def test_when_successful_upload_completed_then_expect_cid_field_matches_generated_identifier(
        self, mock_app_instance, mock_upload_files, test_patterns
    ):
        """
        GIVEN a file is successfully uploaded and processed
        WHEN the upload_document method returns a success response
        THEN expect response cid field to match the generated content identifier.
        """
        # Arrange
        upload_file = mock_upload_files['pdf']
        cid_pattern = test_patterns['cid']
        
        # Act
        response = mock_app_instance.upload_document(upload_file, None)
        response_data = response.json()
        actual_cid = response_data['cid']
        
        # Assert
        assert cid_pattern.match(actual_cid), f"Expected cid to match pattern {cid_pattern.pattern}, got {actual_cid} instead"

    @pytest.mark.parametrize("expected_field", [
        "status", "message", "error_code", "upload_timestamp"
    ])
    def test_when_upload_error_occurs_then_expect_response_contains_error_field(
        self, mock_app_with_db_failure, mock_upload_files, expected_field
    ):
        """
        GIVEN an error occurs during upload processing
        WHEN the upload_document method returns an error response
        THEN expect the response to contain the expected field.
        """
        # Arrange
        upload_file = mock_upload_files['pdf']
        
        # Act
        response = mock_app_with_db_failure.upload_document(upload_file, None)
        response_data = response.json()
        
        # Assert
        assert expected_field in response_data, f"Expected error response to contain field '{expected_field}', but it did not."


    def test_when_upload_error_occurs_then_expect_status_field_equals_error(
        self, mock_app_with_db_failure, mock_upload_files
    ):
        """
        GIVEN an error occurs during upload processing
        WHEN the upload_document method returns an error response
        THEN expect status field to equal "error".
        """
        # Arrange
        upload_file = mock_upload_files['pdf']
        expected_status = "error"

        # Act
        response = mock_app_with_db_failure.upload_document(upload_file, None)
        response_data = response.json()
        actual_status = response_data['status']

        # Assert
        assert actual_status == expected_status, f"Expected status to be {expected_status}, got {actual_status} instead"


    def test_when_upload_error_occurs_then_expect_message_field_describes_failure(
        self, mock_app_with_db_failure, mock_upload_files
    ):
        """
        GIVEN an error occurs during upload processing
        WHEN the upload_document method returns an error response
        THEN expect message field to describe the failure.
        """
        # Arrange
        upload_file = mock_upload_files['pdf']
        
        # Act
        response = mock_app_with_db_failure.upload_document(upload_file, None)
        response_data = response.json()
        message = response_data['message']
        
        # Assert
        assert len(message) > 0, f"Expected error message to not be empty, got message with length {len(message)} instead"

    def test_when_upload_error_occurs_then_expect_error_code_field_not_empty(
        self, mock_app_with_db_failure, mock_upload_files
    ):
        """
        GIVEN an error occurs during upload processing
        WHEN the upload_document method returns an error response
        THEN expect error_code field to be a non-empty string.
        """
        # Arrange
        upload_file = mock_upload_files['pdf']
        
        # Act
        response = mock_app_with_db_failure.upload_document(upload_file, None)
        response_data = response.json()
        error_code = response_data['error_code']
        
        # Assert
        assert len(error_code) > 0, f"Expected error_code to not be empty, got error_code with length {len(error_code)} instead"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])