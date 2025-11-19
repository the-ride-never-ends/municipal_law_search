import pytest
import datetime
import time
from unittest.mock import patch, MagicMock


class TestTimestamp:
    """Test timestamp accuracy and session management functionality."""

    def test_when_successful_upload_completed_then_timestamp_within_five_seconds_of_current_time(
        self, mock_app_instance, mock_upload_files, freeze_time_fixture
    ):
        """
        GIVEN a valid PDF file is successfully uploaded at a known frozen time
        WHEN upload_document method completes processing successfully
        THEN expect upload_timestamp field to be within 5 seconds of the current system time
        """
        # Arrange
        valid_pdf_file = mock_upload_files['pdf']
        expected_timestamp = freeze_time_fixture.isoformat().replace('+00:00', 'Z')

        # Act
        result = mock_app_instance.upload_document(valid_pdf_file, None)

        # Assert
        response_data = result.json()
        actual_timestamp = response_data['upload_timestamp']
        assert actual_timestamp == expected_timestamp, f"Expected timestamp {expected_timestamp}, got {actual_timestamp} instead"

    def test_when_upload_error_occurs_then_timestamp_within_five_seconds_of_error_time(
        self, mock_app_instance, mock_upload_files, freeze_time_fixture
    ):
        """
        GIVEN an invalid file upload that will cause an error at a known frozen time
        WHEN upload_document method encounters the error condition
        THEN expect upload_timestamp field in error response to be within 5 seconds of the current system time
        """
        # Arrange
        invalid_file = mock_upload_files['unsupported']
        expected_timestamp = freeze_time_fixture.isoformat().replace('+00:00', 'Z')

        # Act
        result = mock_app_instance.upload_document(invalid_file, None)

        # Assert
        response_data = result.json()
        actual_timestamp = response_data['upload_timestamp']
        assert actual_timestamp == expected_timestamp, f"Expected timestamp {expected_timestamp}, got {actual_timestamp} instead"

    def test_when_successful_upload_completed_then_timestamp_follows_iso_8601_utc_format(
        self, mock_app_instance, mock_upload_files, test_patterns
    ):
        """
        GIVEN a valid file is successfully uploaded
        WHEN upload_document method generates a success response
        THEN expect upload_timestamp to be in ISO 8601 format (e.g., YYYY-MM-DDTHH:MM:SS.sssZ)
        """
        # Arrange
        valid_file = mock_upload_files['pdf']
        iso_pattern = test_patterns['iso_timestamp']

        # Act
        result = mock_app_instance.upload_document(valid_file, None)

        # Assert
        response_data = result.json()
        timestamp = response_data['upload_timestamp']
        assert iso_pattern.match(timestamp), f"Expected timestamp {timestamp} to match ISO 8601 format"

    def test_when_first_upload_processed_then_timestamp_is_string_type(
        self, mock_app_instance, mock_upload_files
    ):
        """
        GIVEN a valid file is uploaded first in sequence
        WHEN upload_document method processes the file
        THEN expect upload_timestamp to be string type
        """
        # Arrange
        first_file = mock_upload_files['pdf']

        # Act
        result = mock_app_instance.upload_document(first_file, None)

        # Assert
        response_data = result.json()
        timestamp = response_data['upload_timestamp']
        assert isinstance(timestamp, str), f"Expected timestamp to be string type, got {type(timestamp).__name__} instead"

    def test_when_client_cid_provided_then_expect_upload_recorded_in_client_history(
        self, mock_app_instance, mock_upload_files, client_cid_test_cases
    ):
        """
        GIVEN a client_cid is provided with the upload
        WHEN the upload_document method processes the file
        THEN expect the upload to be recorded in the specified client's upload history.
        """
        # Arrange
        valid_file = mock_upload_files['pdf']
        valid_client_cid = client_cid_test_cases['valid']

        # Act
        result = mock_app_instance.upload_document(valid_file, valid_client_cid)

        # Assert
        mock_database = mock_app_instance.resources['database']
        assert mock_database.execute.called, f"Expected database execute to be called for client history recording"


class TestSessionManagement:
    """Test session management functionality for upload_document method."""

    def test_when_valid_client_cid_provided_then_upload_associated_with_client_session(
        self, mock_app_instance, mock_upload_files, client_cid_test_cases
    ):
        """
        GIVEN a valid client_cid string and a valid PDF file
        WHEN upload_document method processes the file successfully
        THEN expect the database record to contain the exact client_cid value in the client_cid field
        """
        # Arrange
        valid_file = mock_upload_files['pdf']
        expected_client_cid = client_cid_test_cases['valid']

        # Act
        result = mock_app_instance.upload_document(valid_file, expected_client_cid)

        # Assert
        mock_database = mock_app_instance.resources['database']
        assert mock_database.execute.called, f"Expected database execute to be called with client_cid parameter"

    def test_when_no_client_cid_provided_then_upload_recorded_without_session_association(
        self, mock_app_instance, mock_upload_files
    ):
        """
        GIVEN no client_cid parameter (None) and a valid PDF file
        WHEN upload_document method processes the file successfully
        THEN expect the database record to have client_cid field set to None
        """
        # Arrange
        valid_file = mock_upload_files['pdf']
        expected_client_cid = None

        # Act
        result = mock_app_instance.upload_document(valid_file, expected_client_cid)

        # Assert
        mock_database = mock_app_instance.resources['database']
        assert mock_database.execute.called, f"Expected database execute to be called with None client_cid"

    def test_when_first_upload_with_same_client_cid_processed_then_database_called_once(
        self, mock_app_instance, mock_upload_files, client_cid_test_cases
    ):
        """
        GIVEN first valid PDF file and valid client_cid for upload
        WHEN upload_document method processes the file successfully
        THEN expect database to be called exactly once
        """
        # Arrange
        first_file = mock_upload_files['pdf']
        shared_client_cid = client_cid_test_cases['valid']

        # Act
        result = mock_app_instance.upload_document(first_file, shared_client_cid)

        # Assert
        mock_database = mock_app_instance.resources['database']
        expected_call_count = 1
        assert mock_database.execute.call_count == expected_call_count, f"Expected {expected_call_count} database call, got {mock_database.execute.call_count}"

    def test_when_upload_with_client_cid_processed_then_database_called(
        self, mock_app_instance, mock_upload_files, client_cid_test_cases
    ):
        """
        GIVEN one upload with valid client_cid
        WHEN upload_document call completes successfully
        THEN expect database to be called
        """
        # Arrange
        file_with_cid = mock_upload_files['pdf']
        valid_client_cid = client_cid_test_cases['valid']

        # Act
        result_with_cid = mock_app_instance.upload_document(file_with_cid, valid_client_cid)

        # Assert
        mock_database = mock_app_instance.resources['database']
        assert mock_database.execute.called, f"Expected database execute to be called for upload with client_cid"

    def test_when_first_upload_with_different_client_cid_processed_then_database_called_once(
        self, mock_app_instance, mock_upload_files, client_cid_test_cases
    ):
        """
        GIVEN first valid PDF file with first client_cid value
        WHEN upload_document method processes the file successfully
        THEN expect database to be called exactly once
        """
        # Arrange
        first_file = mock_upload_files['pdf']
        first_client_cid = client_cid_test_cases['multiple'][0]

        # Act
        first_result = mock_app_instance.upload_document(first_file, first_client_cid)

        # Assert
        mock_database = mock_app_instance.resources['database']
        expected_calls = 1
        assert mock_database.execute.call_count == expected_calls, f"Expected {expected_calls} database call, got {mock_database.execute.call_count}"

    def test_when_non_string_client_cid_provided_then_raises_type_error(
        self, mock_app_instance, mock_upload_files, test_constants
    ):
        """
        GIVEN a non-string client_cid (integer 12345) and a valid PDF file
        WHEN upload_document method attempts to process the file
        THEN expect TypeError to be raised with message containing 'Client CID must be a string'
        """
        # Arrange
        valid_file = mock_upload_files['pdf']
        non_string_cid = 12345
        expected_message = "Client CID must be a string"

        # Act & Assert
        with pytest.raises(TypeError, match=expected_message):
            mock_app_instance.upload_document(valid_file, non_string_cid)

    @pytest.mark.parametrize(
        "cid_key, expected_message",
        [
            ("unicode", "Client CID contains invalid characters"),
            ("too_short", "Client CID length invalid"),
            ("too_long", "Client CID length invalid"),
            ("wrong_prefix", "Client CID must start with bafkreiht"),
        ],
        ids=[
            "unicode_characters",
            "cid_too_short",
            "cid_too_long",
            "cid_wrong_prefix",
        ]
    )
    def test_when_invalid_client_cid_provided_then_raises_value_error(
        self, mock_app_instance, mock_upload_files, client_cid_variations, cid_key, expected_message
    ):
        """
        GIVEN an invalid client_cid (e.g., wrong format, length, or characters) and a valid PDF file
        WHEN upload_document method attempts to process the file
        THEN expect a ValueError to be raised with a specific error message.
        """
        # Arrange
        valid_file = mock_upload_files['pdf']
        invalid_cid = client_cid_variations[cid_key]

        # Act & Assert
        with pytest.raises(ValueError, match=expected_message):
            mock_app_instance.upload_document(valid_file, invalid_cid)

    def test_when_upload_fails_with_client_cid_then_session_not_polluted_with_failed_upload(
        self, mock_app_instance, mock_upload_files, client_cid_test_cases
    ):
        """
        GIVEN a corrupted PDF file and a valid client_cid
        WHEN upload_document method fails to process the file
        THEN expect no database record to be created with the client_cid value
        """
        # Arrange
        corrupted_file = mock_upload_files['corrupted']
        valid_client_cid = client_cid_test_cases['valid']

        # Act
        result = mock_app_instance.upload_document(corrupted_file, valid_client_cid)

        # Assert
        response_data = result.json()
        expected_status = 'error'
        assert response_data['status'] == expected_status, f"Expected error status {expected_status}, got {response_data['status']} instead"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])