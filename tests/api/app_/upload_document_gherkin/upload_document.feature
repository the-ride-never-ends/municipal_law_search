Feature: Document Upload API
  As a Lawyer, Paralegal or Legal Assistant
  I want to upload documents through an API endpoint
  So that documents can be processed, stored, and tracked by other system components

Background:
    Given the system backend "app" exists with the following attributes, properties, and methods:
        | name                  | type                | description                                                          | args                               | kwargs | returns                     |
        | configs               | Configs             | "Application configuration object"                                   | N/A                                | N/A    | Configs instance            |
        | resources             | dict                | "Dictionary of shared application resources"                         | N/A                                | N/A    | dict                        |
        | routes                | Routes              | "StrEnum of application routes"                                      | N/A                                | N/A    | Routes enum                 |
        | db                    | Database            | "The read-only database instance"                                    | N/A                                | N/A    | Database instance           |
        | llm                   | AsyncLLMInterface   | "The language model interface instance"                              | N/A                                | N/A    | AsyncLLMInterface instance  |
        | logger                | logging.Logger      | "The application logger"                                             | N/A                                | N/A    | Logger instance             |
        | fastapi               | FastAPI             | "The FastAPI application instance"                                   | N/A                                | N/A    | FastAPI instance            |
        | email                 | module              | "The email module"                                                   | N/A                                | N/A    | module                      |
        | templates             | Jinja2Templates     | "Jinja2 templates engine"                                            | N/A                                | N/A    | Jinja2Templates instance    |
        | side_menu             | SideMenu            | "The side menu handler"                                              | N/A                                | N/A    | SideMenu instance           |
        | upload_menu           | UploadMenu          | "The upload menu handler"                                            | N/A                                | N/A    | UploadMenu instance         |
        | search_function       | Coroutine           | "The function used for performing searches"                          | N/A                                | N/A    | Callable                    |
        | frontend_path         | Path                | "Path to the frontend source directory"                              | N/A                                | N/A    | Path object                 |
        | static_file_dir       | Path                | "Path to the static files directory"                                 | N/A                                | N/A    | Path object                 |
        | templates_path        | Path                | "Path to the templates directory"                                    | N/A                                | N/A    | Path object                 |
        | favicon_path          | Path                | "Path to the favicon file"                                           | N/A                                | N/A    | Path object                 |
        | index_name            | str                 | "The name of the index HTML file"                                    | N/A                                | N/A    | str                         |
        | make_app              | Coroutine           | "Configures and returns the FastAPI application instance"            |                                    |        | FastAPI instance            |
        | favicon               | Coroutine           | "Serves the favicon.ico file"                                        |                                    |        | FileResponse                |
        | serve_index           | Coroutine           | "Serves the main index.html page"                                    | "request"                          |        | HTMLResponse                |
        | serve_public_files    | Coroutine           | "Serves files from the public directory"                             | "filename"                         |        | FileResponse                |
        | serve_side_menu_files | Coroutine           | "Serves HTML files for the side menu"                                | "filename"                         |        | FileResponse                |
        | upload_document       | Coroutine           | "Handles document uploads"                                           | "file", "client_cid"               |        | JSONResponse                |
        | search_sse_response   | Coroutine           | "Provides search results via SSE"                                    | "q", "page", "per_page", "client_id" |        | EventSourceResponse       |
        | get_law               | Coroutine           | "Retrieves a legal document by its CID"                              | "cid"                              |        | JSONResponse                |
        | talk_with_the_law     | Coroutine           | "Interacts with the law via natural language"                        | "q", "page", "per_page", "client_id" |        | EventSourceResponse       |
        | contact               | Coroutine           | "Handles contact form submissions"                                   | "name", "email", "message", "subject", "organization" | | JSONResponse    |
        | account_create        | Coroutine           | "Placeholder for account creation"                                   |                                    |        | JSONResponse                |
        | account_delete        | Coroutine           | "Placeholder for account deletion"                                   |                                    |        | JSONResponse                |
        | account_page          | Coroutine           | "Placeholder for account page"                                       |                                    |        | HTMLResponse                |
        | account_update        | Coroutine           | "Placeholder for account updates"                                    |                                    |        | JSONResponse                |
    And "app" supports document processing pipeline
    And "app" has a read-only database connection attribute "db"
    And "app" has a temporary storage for file uploads property "temp_storage"
    And "app" can validate file formats and sizes 
    And "app" can extract text from PDF, DOC, DOCX, and TXT files
    And "app" can generate content identifiers (CIDs) in CIDv1 using the raw codec and base32 encoding
    And "app" can store document content and metadata in "temp_storage"
    And "app" can match uploads to client sessions

  Scenario Outline: Successfully upload a valid document without client association
    Given I have a valid <supported_format> file named <filename>
    And the file size is between 0 and the maximum bytes limit <file_size>
    And the file content can be converted into human-readable, plaintext strings
    When I send a POST request to "/api/upload-document" with the file
    Then the response status is "success"
    And the response is a CID in CIDv1 format
    And the response filename should be <filen_ame>
    And the response file size should be <file_size>
    And the response should include an upload timestamp "timestamp" in ISO 8601 format
    And the document metadata should exist in the "temp_storage" as a dictionary
    And the document content should be in the document metadata as a human-readable, plaintext string

  Scenario: Successfully upload a DOCX document with client CID association
    Given I have a valid DOCX file named "report.docx"
    And the file size is 524288 bytes
    And I have a valid client CID <clientcid>
    When I send a POST request to "/api/upload-document" with the file and client_cid
    Then the response status should be "success"
    And the response should have a valid CID
    And the upload should be associated with client CID "bafkreiabc123xyz"
    And the client upload history should include this document

  Scenario: Upload a TXT file successfully
    Given I have a valid TXT file named "notes.txt"
    And the file size is 2048 bytes
    When I send a POST request to "/api/upload-document" with the file
    Then the response status should be "success"
    And the response should have a valid CID
    And the text content should be extracted directly

  Scenario: Upload a DOC file successfully
    Given I have a valid DOC file named "legacy.doc"
    And the file size is 102400 bytes
    When I send a POST request to "/api/upload-document" with the file
    Then the response status should be "success"
    And the response should have a valid CID
    And the document content should be extracted and stored

  Scenario: Reject upload with invalid file type
    Given I have a file named "image.jpg"
    And the file type is "image/jpeg"
    When I send a POST request to "/api/upload-document" with the file
    Then the response status should be "error"
    And the response message should indicate "Invalid file type"
    And the response error_code should be "INVALID_FILE_TYPE"
    And the response cid should be empty string
    And the response filename should be empty string
    And the response file_size should be 0
    And an HTTPException with status 400 should be raised

  Scenario: Reject upload exceeding maximum file size
    Given I have a valid PDF file named "large.pdf"
    And the file size exceeds the maximum allowed size
    When I send a POST request to "/api/upload-document" with the file
    Then the response status should be "error"
    And the response message should indicate file size exceeded
    And an HTTPException should be raised
    And the response error_code should be 413
    And the response message should have "file size exceeds the maximum allowed limit"
    And the response cid should be empty string
    And the response filename should be empty string
    And the response file_size should be 0

  Scenario: Reject unsupported media type
    Given I have a file with unsupported media type
    When I send a POST request to "/api/upload-document" with the file
    Then the response status should be "error"
    And an HTTPException should be raised
    And the response message should have "file is corrupt or malformed"
    And the response error_code should be 415
    And the response cid should be empty string

  Scenario: Handle corrupted file upload
    Given I have a corrupted PDF file named "corrupted.pdf"
    And the file cannot be read or processed
    When I send a POST request to "/api/upload-document" with the file
    Then the response status should be "error"
    And an HTTPException should be raised
    And the response error_code should be 400
    And the response message should have "file is corrupt or malformed"
    And the response cid should be empty string

  Scenario: Handle invalid client CID format
    Given I have a valid PDF file named "document.pdf"
    And I provide an invalid client_cid "invalid-cid-format"
    When I send a POST request to "/api/upload-document" with the file and client_cid
    Then a ValueError should be raised
    And the response status should be "error"
    And the error message should have "invalid CID format"

  Scenario: Handle file content extraction failure
    Given I have a valid PDF file that cannot have its content extracted
    When I send a POST request to "/api/upload-document" with the file
    Then a ValueError should be raised
    And the response status should be "error"
    And the response message should have "content extraction failed"
    And the response message should have the traceback

  Scenario: Handle temporary storage failure
    Given I have a valid PDF file named "document.pdf"
    And the temporary storage system is unavailable
    When I send a POST request to "/api/upload-document" with the file
    Then an IOError should be raised
    And the response status should be "error"
    And the response message should have "temporary storage failure"

  Scenario: Handle internal processing failure
    Given I have a valid PDF file named "document.pdf"
    And an unexpected error occurs during processing
    When I send a POST request to "/api/upload-document" with the file
    Then an HTTPException with status 500 should be raised
    And the response status should be "error"
    And the response message should indicate internal server error
    And the response cid should be empty string

  Scenario: Handle incorrect file parameter type
    Given I provide a non-UploadFile object as the file parameter
    When I send a POST request to "/api/upload-document"
    Then a TypeError should be raised
    And the response status should be "error"

  Scenario: Verify response timestamp format
    Given I have successfully uploaded a valid PDF file
    When I receive the response
    Then the upload_timestamp should be in ISO 8601 format
    And the timestamp should reflect the current time

  @schema
  Scenario: Validate success response schema
    Given a successful upload has occurred
    Then the response should have field "status" with value "success"
    And the response should have field "message" with value "File uploaded successfully"
    And the response should have field "error_code" with empty string
    And the response should have field "cid" with a valid CIDv1 string
    And the response should have field "filename" with the input filename
    And the response should have field "file_size" with a positive integer
    And the response should have field "upload_timestamp" with an ISO 8601 timestamp

  @schema
  Scenario: Validate error response schema
    Given an upload has failed
    Then the response should have field "status" with value "error"
    And the response should have field "message" with a human readable error message
    And the response should have field "error_code" with a string machine readable error code
    And the response should have field "cid" with empty string
    And the response should have field "filename" with empty string
    And the response should have field "file_size" with value 0
    And the response should have field "upload_timestamp" with an ISO 8601 timestamp

  @requirements
  Scenario: Verify supported file types
    Then "app" should support file type ".pdf" with media type "application/pdf"
    And "app" should support file type ".doc" with media type "application/msword"
    And "app" should support file type ".docx" with media type "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    And "app" should support file type ".txt" with media type "text/plain"
