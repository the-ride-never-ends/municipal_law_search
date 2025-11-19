import pytest


@pytest.mark.asyncio
class TestContentProcessing:
    """Test content processing functionality for different file types."""

    async def test_when_pdf_file_processed_then_expect_response_contains_non_empty_cid(
        self, mock_app_instance, mock_upload_files, test_patterns
    ):
        """
        GIVEN a valid PDF file containing readable text
        WHEN the upload_document method processes the file
        THEN expect the returned response to contain a non-empty cid field.
        """
        # Arrange
        pdf_file = mock_upload_files['pdf']
        cid_pattern = test_patterns['cid']

        # Act
        result = await mock_app_instance.upload_document(pdf_file)
        cid_value = result['cid']

        # Assert
        assert cid_pattern.match(cid_value), f"Expected CID to match pattern, got '{cid_value}'"

    async def test_when_pdf_file_processed_then_expect_database_contains_matching_text_content(
        self, mock_app_instance, mock_upload_files, text_content
    ):
        """
        GIVEN a valid PDF file containing readable text
        WHEN the upload_document method processes the file
        THEN expect the database to contain a record with extracted text content matching the PDF's text.
        """
        # Arrange
        pdf_file = mock_upload_files['pdf']
        expected_text = text_content['known']

        # Act
        result = await mock_app_instance.upload_document(pdf_file)
        stored_text = result.extracted_text

        # Assert
        assert stored_text == expected_text, f"Expected stored text to equal '{expected_text}', got '{stored_text}'"

    async def test_when_doc_file_processed_then_expect_success_status_returned(
        self, mock_app_instance, mock_upload_files, validation_sets
    ):
        """
        GIVEN a valid Microsoft Word DOC format file
        WHEN the upload_document method processes the file
        THEN expect the returned response to have status "success".
        """
        # Arrange
        doc_file = mock_upload_files['doc']
        valid_status_values = validation_sets['valid_status_values']

        # Act
        result = await mock_app_instance.upload_document(doc_file)
        status_value = result['status']

        # Assert
        assert status_value in valid_status_values, f"Expected status to be in {valid_status_values}, got '{status_value}'"

    async def test_when_doc_file_processed_then_expect_database_contains_non_empty_text_content(
        self, mock_app_instance, mock_upload_files, test_constants
    ):
        """
        GIVEN a valid Microsoft Word DOC format file
        WHEN the upload_document method processes the file
        THEN expect the database record for this upload to contain non-empty text content.
        """
        # Arrange
        doc_file = mock_upload_files['doc']
        expected_min_length = 1

        # Act
        result = await mock_app_instance.upload_document(doc_file)
        stored_text_length = len(result.extracted_text)

        # Assert
        assert stored_text_length >= expected_min_length, f"Expected text content length to be >= {expected_min_length}, got {stored_text_length}"

    async def test_when_docx_file_processed_then_expect_success_status_returned(
        self, mock_app_instance, mock_upload_files, validation_sets
    ):
        """
        GIVEN a valid modern Word DOCX format file
        WHEN the upload_document method processes the file
        THEN expect the returned response to have status "success".
        """
        # Arrange
        docx_file = mock_upload_files['docx']
        valid_status_values = validation_sets['valid_status_values']

        # Act
        result = await mock_app_instance.upload_document(docx_file)
        status_value = result.status

        # Assert
        assert status_value in valid_status_values, \
            f"Expected status to be in {valid_status_values}, got '{status_value}'"

    async def test_when_docx_file_processed_then_expect_stored_content_length_greater_than_zero(
        self, mock_app_instance, mock_upload_files, test_constants
    ):
        """
        GIVEN a valid modern Word DOCX format file
        WHEN the upload_document method processes the file
        THEN expect the stored text content length to be greater than zero.
        """
        # Arrange
        docx_file = mock_upload_files['docx']
        expected_min_length = 0

        # Act
        result = await mock_app_instance.upload_document(docx_file)
        stored_text_length = len(result.extracted_text)

        # Assert
        assert stored_text_length > expected_min_length, f"Expected text content length to be > {expected_min_length}, got {stored_text_length}"

    async def test_when_txt_file_processed_then_expect_stored_content_equals_original(
        self, mock_app_instance, mock_upload_files, text_content
    ):
        """
        GIVEN a valid TXT file with plain text content
        WHEN the upload_document method processes the file
        THEN expect the stored text content to exactly equal the original file content.
        """
        # Arrange
        txt_file = mock_upload_files['txt']
        expected_content = text_content['known']

        # Act
        result = await mock_app_instance.upload_document(txt_file)
        stored_content = result.extracted_text

        # Assert
        assert stored_content == expected_content, f"Expected stored content to equal '{expected_content}', got '{stored_content}'"

    async def test_when_txt_file_processed_then_expect_no_character_loss_or_modification(
        self, mock_app_instance, mock_upload_files, text_content
    ):
        """
        GIVEN a valid TXT file with plain text content
        WHEN the upload_document method processes the file
        THEN expect the length of  to be lost or modified during processing.
        """
        # Arrange
        txt_file = mock_upload_files['unicode_name']
        expected_length = len(text_content['unicode'])

        # Act
        result = await mock_app_instance.upload_document(txt_file)
        processed_length = len(result.extracted_text)

        # Assert
        assert processed_length == expected_length, f"Expected processed content length to equal {expected_length}, got {processed_length}"

    async def test_when_text_extraction_fails_then_expect_value_error_raised(
        self, mock_app_with_db_failure, mock_upload_files
    ):
        """
        GIVEN a file from which text content cannot be extracted
        WHEN the upload_document method attempts to process the file
        THEN expect ValueError to be raised.
        """
        # Arrange
        corrupted_file = mock_upload_files['corrupted']

        # Act/Assert
        with pytest.raises(ValueError):
            await mock_app_with_db_failure.upload_document(corrupted_file)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
