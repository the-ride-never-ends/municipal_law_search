import json


import pytest


from app.app import App

def _get_cid_from_response(response):
    """Helper function to extract CID from JSONResponse."""
    return json.loads(response.body.decode('utf-8'))['cid']

@pytest.mark.asyncio
class TestCIDGeneration:
    """Test Content Identifier (CID) generation functionality."""

    async def test_when_different_files_uploaded_sequentially_then_expect_unique_cids_generated(
        self, mock_app_instance, mock_upload_files):
        """
        GIVEN two different files are uploaded sequentially
        WHEN the upload_document method processes each file
        THEN expect the CID for the first file to be different from the CID for the second file
        """
        # Arrange
        pdf_file, docx_file = mock_upload_files['pdf'], mock_upload_files['docx']

        # Act
        pdf_response = await mock_app_instance.upload_document(pdf_file)
        docx_response = await mock_app_instance.upload_document(docx_file)

        # Extract content from JSONResponse objects
        pdf_cid = _get_cid_from_response(pdf_response)
        docx_cid = _get_cid_from_response(docx_response)

        # Assert
        assert pdf_cid != docx_cid, \
            f"Expected different CIDs for different files, but both got {pdf_response['cid']}"

    async def test_when_file_uploaded_successfully_then_expect_cid_follows_expected_format(
        self, mock_app_instance: App, mock_upload_files, test_patterns):
        """
        GIVEN any valid file is uploaded successfully
        WHEN the upload_document method generates a CID
        THEN expect the generated CID to follow the expected format and structure.
        """
        # Arrange
        test_file = mock_upload_files['pdf']
        cid_pattern = test_patterns['cid']

        # Act
        response = await mock_app_instance.upload_document(test_file)
        actual_cid = _get_cid_from_response(response)
    
        # Assert
        assert cid_pattern.match(actual_cid), \
            f"Expected CID to match pattern {cid_pattern.pattern}, got {actual_cid}"

    @pytest.mark.parametrize("file_type", ["pdf", "docx", "txt"])
    @pytest.mark.asyncio
    async def test_when_identical_content_uploaded_multiple_times_then_expect_same_cid_generated(
        self, file_type, mock_app_instance: App, files_with_identical_content):
        """
        GIVEN the same file content is uploaded multiple times
        WHEN the upload_document method processes each upload
        THEN expect identical file content to produce the same CID each time.
        """
        # Arrange
        num_files = 2
        files = files_with_identical_content[file_type]
        file1, file2 = files[:num_files]

        # Act
        response1 = await mock_app_instance.upload_document(file1)
        response2 = await mock_app_instance.upload_document(file2)
        cid1 = _get_cid_from_response(response1)
        cid2 = _get_cid_from_response(response2)

        # Assert
        assert cid1 == cid2, \
            f"Expected identical content to produce same CID, got {cid1} and {cid2}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
