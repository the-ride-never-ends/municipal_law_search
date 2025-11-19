import pytest
from fastapi import HTTPException


class TestDatabaseIntegration:
    """Test database integration functionality for upload_document method."""

    def test_when_file_uploaded_successfully_then_expect_database_query_returns_one_record(
        self, mock_app_instance, mock_upload_files, client_cid_test_cases
    ):
        """
        GIVEN a file is successfully uploaded and processed
        WHEN the upload_document method completes
        THEN expect database query for the upload CID to return exactly one record.
        """
        # Arrange
        expected_record_count = 1
        valid_file = mock_upload_files['pdf']
        valid_client_cid = client_cid_test_cases['valid']

        # Act
        mock_app_instance.upload_document(valid_file, valid_client_cid)

        actual_record_count = len(mock_app_instance.db.execute.return_value.fetchall())

        # Assert
        assert actual_record_count == expected_record_count, \
            f"Expected {expected_record_count} database record, got {actual_record_count} instead"

    def test_when_file_uploaded_successfully_then_expect_metadata_fields_match_upload_values(
        self, mock_app_instance, mock_upload_files, client_cid_test_cases
    ):
        """
        GIVEN a file is successfully uploaded and processed
        WHEN the upload_document method completes
        THEN expect each metadata field in the database to match the expected values from the upload.
        """
        # Arrange
        valid_file = mock_upload_files['pdf']
        valid_client_cid = client_cid_test_cases['valid']
        expected_filename = valid_file.filename

        # Act
        mock_app_instance.upload_document(valid_file, valid_client_cid)
        actual_filename = mock_app_instance.db.execute.fetchall()[0]['filename']

        # Assert
        assert actual_filename == expected_filename, \
            f"Expected filename to be {expected_filename}, got {actual_filename} instead"

    @pytest.mark.parametrize(
        "text_type",
        ["known","unicode",]
    )
    def test_when_file_with_extractable_text_uploaded_then_expect_database_returns_expected_text(
        self, mock_app_instance, mock_upload_files, text_content, text_type
    ):
        """
        GIVEN a file with extractable text content is uploaded
        WHEN the upload_document method processes the file
        THEN expect database query for the text content to return the expected extracted text.
        """
        # Arrange
        expected_text = text_content[text_type]
        valid_file = mock_upload_files['txt']

        # Act
        mock_app_instance.upload_document(valid_file)
        actual_text = mock_app_instance.db.execute.fetchall()[0]['extracted_text']

        # Assert
        assert actual_text == expected_text, \
            f"Expected database text content for type '{text_type}' to be '{expected_text}', got {actual_text} instead."

    def test_when_client_cid_provided_then_expect_upload_included_in_client_history(
        self, mock_app_instance, mock_upload_files, client_cid_test_cases
    ):
        """
        GIVEN a valid file and a client_cid parameter are provided
        WHEN the upload_document method processes the upload
        THEN expect database query for uploads by client_cid to include this upload record.
        """
        # Arrange
        expected_upload_cid = 'bafkreiht' + 'b' * 52
        valid_file = mock_upload_files['txt']
        valid_client_cid = client_cid_test_cases['valid']

        # Act
        mock_app_instance.upload_document(valid_file, valid_client_cid)
        upload_cids_in_history = [record['cid'] for record in mock_app_instance.db.execute.fetchall()]

        # Assert
        assert expected_upload_cid in upload_cids_in_history, \
            f"Expected upload CID {expected_upload_cid} to be included in client history"

    def test_when_client_cid_provided_then_expect_upload_record_contains_correct_client_cid(
        self, mock_app_instance, mock_upload_files, client_cid_test_cases
    ):
        """
        GIVEN a valid file and a client_cid parameter are provided
        WHEN the upload_document method processes the upload
        THEN expect the upload record to contain the correct client_cid value.
        """
        # Arrange
        expected_client_cid = client_cid_test_cases['valid']
        valid_file = mock_upload_files['docx']

        # Act
        mock_app_instance.upload_document(valid_file, expected_client_cid)
        actual_client_cid = mock_app_instance.db.execute.fetchall()[0]['client_cid']

        # Assert
        assert actual_client_cid == expected_client_cid, \
            f"Expected upload record client_cid to be {expected_client_cid}, got {actual_client_cid} instead"

    def test_when_database_operations_fail_then_expect_http_exception_500_raised(
        self, mock_app_with_db_failure, mock_upload_files, test_constants
    ):
        """
        GIVEN database operations fail during upload processing
        WHEN the upload_document method encounters the database failure
        THEN expect HTTPException with status 500 to be raised.
        """
        # Arrange
        expected_status_code = test_constants['http_status_codes']['internal_server_error']
        valid_file = mock_upload_files['pdf']

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            mock_app_with_db_failure.upload_document(valid_file)

        assert exc_info.value.status_code == expected_status_code, \
            f"Expected HTTPException status code to be {expected_status_code}, got {exc_info.value.status_code} instead"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])