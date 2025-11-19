# Function and Class stubs from '/home/kylerose1946/american_law_search/app/app.py'

Files last updated: 1758963798.7918608

Stub file last updated: 2025-09-27 02:04:08

## App

```python
class App:
    """
    The main application class that encapsulates the FastAPI app and its resources.

This class is responsible for initializing and configuring the FastAPI application,
managing shared resources like database connections and language models, and
defining the API routes and their corresponding handler functions.

Attributes:
    configs (Configs): Application configuration object.
    resources (dict): Dictionary of shared application resources.
    routes (Routes): Enum of application routes.
    db (Database): The read-only database instance.
    llm (AsyncLLMInterface): The language model interface instance.
    logger (logging.Logger): The application logger.
    fastapi (FastAPI): The FastAPI application instance.
    email (module): The email module.
    templates (Jinja2Templates): Jinja2 templates engine.
    side_menu (SideMenu): The side menu handler.
    upload_menu (UploadMenu): The upload menu handler.
    search_function (Callable): The function used for performing searches.
    frontend_path (Path): Path to the frontend source directory.
    static_file_dir (Path): Path to the static files directory.
    templates_path (Path): Path to the templates directory.
    favicon_path (Path): Path to the favicon file.
    index_name (str): The name of the index HTML file.

Public Methods:
    make_app(): Configures and returns the FastAPI application instance.
    favicon(): Serves the favicon.ico file.
    serve_index(request): Serves the main index.html page.
    serve_public_files(filename): Serves files from the public directory.
    serve_side_menu_files(filename): Serves HTML files for the side menu.
    upload_document(file, client_cid): Handles document uploads.
    search_sse_response(q, page, per_page, client_id): Provides search results via SSE.
    get_law(cid): Retrieves a legal document by its CID.
    talk_with_the_law(q, page, per_page, client_id): Interacts with the law via natural language.
    contact(name, email, message, subject, organization): Handles contact form submissions.
    account_create(): Placeholder for account creation.
    account_delete(): Placeholder for account deletion.
    account_page(): Placeholder for account page.
    """
```
* **Async:** False
* **Method:** False
* **Class:** N/A

## Contact

```python
class Contact(StrEnum):
```
* **Async:** False
* **Method:** False
* **Class:** N/A

## Dictate

```python
class Dictate:
```
* **Async:** False
* **Method:** False
* **Class:** N/A

## Document

```python
class Document(BaseModel):
```
* **Async:** False
* **Method:** False
* **Class:** N/A

## Routes

```python
class Routes(StrEnum):
```
* **Async:** False
* **Method:** False
* **Class:** N/A

## SideMenu

```python
class SideMenu:
```
* **Async:** False
* **Method:** False
* **Class:** N/A

## UploadMenu

```python
class UploadMenu:
```
* **Async:** False
* **Method:** False
* **Class:** N/A

## VoiceMode

```python
class VoiceMode:
```
* **Async:** False
* **Method:** False
* **Class:** N/A

## __init__

```python
def __init__(self, *, configs: Configs = None, resources: dict[str, Any] = None) -> None:
```
* **Async:** False
* **Method:** True
* **Class:** Dictate

## __init__

```python
def __init__(self, *, configs: Configs = None, resources: dict[str, Any] = None) -> None:
```
* **Async:** False
* **Method:** True
* **Class:** VoiceMode

## __init__

```python
def __init__(self, *, configs: Configs = None, resources: dict[str, Any] = None) -> None:
```
* **Async:** False
* **Method:** True
* **Class:** UploadMenu

## __init__

```python
def __init__(self, *, configs: Configs = None, resources: dict[str, Any] = None) -> None:
```
* **Async:** False
* **Method:** True
* **Class:** SideMenu

## __init__

```python
def __init__(self, *, configs: Configs = None, resources: dict[str, Any] = None) -> None:
```
* **Async:** False
* **Method:** True
* **Class:** App

## _add_middleware

```python
@staticmethod
def _add_middleware(app: FastAPI) -> FastAPI:
    """
    Add middleware to the FastAPI app.
    """
```
* **Async:** False
* **Method:** True
* **Class:** App

## _determine_mime_type

```python
def _determine_mime_type(path_or_bytes: str | bytes | None) -> Optional[str]:
    """
    Determine the MIME type of a file.
NOTE: Lifted from Omni-Converter Mk2 Repo

Args:
    file_path: The path to the file.
    
Returns:
    str: The MIME type of the file.
    """
```
* **Async:** False
* **Method:** False
* **Class:** N/A

## _event_generator

```python
async def _event_generator():
```
* **Async:** True
* **Method:** False
* **Class:** N/A

## _map_static_files

```python
def _map_static_files(self, app: FastAPI) -> FastAPI:
    """
    Mount static files to the FastAPI app.
    """
```
* **Async:** False
* **Method:** True
* **Class:** App

## _validate_integer

```python
@staticmethod
def _validate_integer(value: Any, var_name: str, skip_if_value_is_none: bool = False) -> None:
```
* **Async:** False
* **Method:** True
* **Class:** App

## _validate_query_params

```python
def _validate_query_params(self, q: str, page: int, per_page: int, client_id: str) -> None:
    """
    Validate query parameters for search endpoints.

This method checks the types and values of the query parameters
to ensure they meet the expected criteria. It raises appropriate
exceptions if any parameter is invalid.

Args:
    q: The search query string
    page: The page number to retrieve
    per_page: The number of results per page
    client_id: Client identifier for search history tracking
    
Raises:
    TypeError: If any parameter is of the wrong type
    ValueError: If any parameter has an invalid value
    """
```
* **Async:** False
* **Method:** True
* **Class:** App

## _validate_string

```python
@staticmethod
def _validate_string(value: Any, var_name: str, skip_if_value_is_none: bool = False) -> None:
```
* **Async:** False
* **Method:** True
* **Class:** App

## account_create

```python
async def account_create(self):
```
* **Async:** True
* **Method:** True
* **Class:** App

## account_delete

```python
async def account_delete(self):
```
* **Async:** True
* **Method:** True
* **Class:** App

## account_page

```python
async def account_page(self):
```
* **Async:** True
* **Method:** True
* **Class:** App

## add_from_google_drive

```python
def add_from_google_drive(self, *args, **kwargs) -> None:
    """
    Upload photos and files from Google Drive.
    """
```
* **Async:** False
* **Method:** True
* **Class:** UploadMenu

## add_photos_and_files

```python
def add_photos_and_files(self, *args, **kwargs) -> None:
    """
    Upload photos and files from local device.
    """
```
* **Async:** False
* **Method:** True
* **Class:** UploadMenu

## agent_mode

```python
def agent_mode(self, *args, **kwargs) -> None:
    """
    Let an AI agent perform a task autonomously.
    """
```
* **Async:** False
* **Method:** True
* **Class:** UploadMenu

## connectors

```python
def connectors(self, *args, **kwargs) -> None:
    """
    Connect to third-party services like Dropbox, Google Drive, OneDrive, etc.
    """
```
* **Async:** False
* **Method:** True
* **Class:** UploadMenu

## contact

```python
async def contact(self, name: str, email: str, message: str, subject: StrEnum, organization: Optional[str] = None) -> JSONResponse:
    """
    API endpoint to submit a contact form.

Args:
    name: Full name of the contact
    email: Email address of the contact
    message: Message content from the contact
    subject: Subject category from predefined enum
    organization: Optional organization name

Returns:
    JSONResponse: Response indicating success/failure of form submission

Raises:
    ValueError: If subject is not in valid Contact enum values
    ValidationError: If string inputs fail validation
    """
```
* **Async:** True
* **Method:** True
* **Class:** App

## deep_research

```python
def deep_research(self, *args, **kwargs) -> None:
```
* **Async:** False
* **Method:** True
* **Class:** UploadMenu

## delete_mappings

```python
@property
def delete_mappings(self):
```
* **Async:** False
* **Method:** True
* **Class:** App

## email_address

```python
@property
def email_address(self):
```
* **Async:** False
* **Method:** True
* **Class:** App

## favicon

```python
async def favicon(self) -> FileResponse:
    """
    Serve the site favicon.ico file.

This endpoint serves the favicon.ico file from the static images directory.
It is marked as not included in the schema documentation.

Returns:
    FileResponse: The favicon.ico file
    """
```
* **Async:** True
* **Method:** True
* **Class:** App

## file_mime_type

```python
@computed_field
@property
def file_mime_type(self) -> str:
    """
    The MIME type of the file.
    """
```
* **Async:** False
* **Method:** True
* **Class:** Document

## make_app

```python
def make_app(self) -> FastAPI:
```
* **Async:** False
* **Method:** True
* **Class:** App

## make_app

```python
def make_app(resources: Optional[dict] = None, configs: Optional[BaseModel] = None) -> FastAPI:
```
* **Async:** False
* **Method:** False
* **Class:** N/A

## get_law

```python
async def get_law(self, cid: str) -> dict[str, Any]:
    """
    API endpoint to retrieve a specific legal document by its content ID.

This endpoint retrieves a single legal document by its unique content ID (CID).
It returns the complete document including metadata and HTML content.

The algorithm:
1. Connect to the HTML database in read-only mode
2. Execute a SQL query joining the citations and HTML tables
3. Filter by the provided CID
4. Format the result as a LawItem response
5. Close database resources
6. Return the document or a 404 error if not found

Args:
    cid: The content identifier of the legal document to retrieve
    
Returns:
    LawItem: The legal document with metadata and HTML content
    
Raises:
    HTTPException: 404 error if the document is not found
    
Example:
    ```
    GET /api/law/bafkreihvwc5kg3estvqpicmmqghwiriti6mz5w3lk4k3app3guwk6onrq4
    ```
    """
```
* **Async:** True
* **Method:** True
* **Class:** App

## get_mappings

```python
@property
def get_mappings(self) -> dict[Routes, tuple[Callable, dict[str, Any]]]:
    """
    Mappings for GET requests.

Returns:
    dict: A dictionary mapping routes to handler functions and parameters.
    """
```
* **Async:** False
* **Method:** True
* **Class:** App

## get_side_menu

```python
def get_side_menu(resources: Optional[dict] = None, configs: Optional[BaseModel] = None) -> SideMenu:
```
* **Async:** False
* **Method:** False
* **Class:** N/A

## get_upload_menu

```python
def get_upload_menu(resources: Optional[dict] = None, configs: Optional[BaseModel] = None) -> UploadMenu:
```
* **Async:** False
* **Method:** False
* **Class:** N/A

## index

```python
@property
def index(self) -> str:
```
* **Async:** False
* **Method:** True
* **Class:** App

## post_mappings

```python
@property
def post_mappings(self):
```
* **Async:** False
* **Method:** True
* **Class:** App

## put_mappings

```python
@property
def put_mappings(self):
```
* **Async:** False
* **Method:** True
* **Class:** App

## search_sse_response

```python
async def search_sse_response(self, q: str = Query('', description='Search query'), page: int = Query(1, description='Page number'), per_page: int = Query(20, description='Items per page'), client_id: str = None) -> EventSourceResponse:
    """
    Server-Sent Events endpoint that streams search results incrementally.

This endpoint implements Server-Sent Events (SSE) to provide a streaming
interface for search results. It allows the client to receive results
incrementally as they become available, providing a more responsive user
experience for searches that may take time to complete.

The event stream includes:
- A "search_started" event when the search begins
- Multiple "results_update" events as results are found
- A "search_complete" event when the search is finished
- An "error" event if any errors occur during the search

This endpoint also saves search queries to the user's search history.

Args:
    q: The search query string
    page: The page number to retrieve
    per_page: The number of results per page
    client_id: Client identifier for search history tracking

Returns:
    EventSourceResponse: A streaming response that sends events to the client
    
Example:
    ```javascript
    // Client-side JavaScript
    const eventSource = new EventSource('/api/search/sse?q=zoning laws');
    eventSource.addEventListener('results_update', (event) => {
    const results = JSON.parse(event.data);
    // Update UI with results
    });
    ```
    """
```
* **Async:** True
* **Method:** True
* **Class:** App

## serve_index

```python
async def serve_index(self, request: Request) -> HTMLResponse:
    """
    Serve the main index page of the application.

This endpoint renders the main HTML template for the application,
which is the entry point for the user interface.

Args:
    request: The incoming request object
    
Returns:
    HTMLResponse: The rendered index.html template
    """
```
* **Async:** True
* **Method:** True
* **Class:** App

## serve_public_files

```python
async def serve_public_files(self, filename: str) -> FileResponse:
    """
    Serve static files from the public templates directory.

This endpoint allows direct access to files in the templates directory
via the /public/ URL path.

Args:
    filename: The path of the file to serve
    
Returns:
    FileResponse: The requested file
    """
```
* **Async:** True
* **Method:** True
* **Class:** App

## serve_side_menu_files

```python
async def serve_side_menu_files(self, filename: str) -> HTMLResponse:
    """
    Serve HTML files from the side-menu templates directory.

This endpoint serves HTML files from the side-menu subdirectory.
Files include:
 - about.html
 - contact.html
 - ourteam.html
 - disclaimer.html

Args:
    filename: The name of the file to serve from the side-menu directory

Returns:
    HTMLResponse: The requested HTML file
    """
```
* **Async:** True
* **Method:** True
* **Class:** App

## talk_with_the_law

```python
async def talk_with_the_law(self, q: str = Query('', description='Search query'), page: int = Query(1, description='Page number'), per_page: int = Query(20, description='Items per page'), client_id: str = None) -> JSONResponse:
    """
    API endpoint to interact with the law using a natural language query.

This endpoint allows users to ask questions about the law and receive
responses based on the underlying legal documents. It uses a language
model to interpret the query and generate a response.

Args:
    q (str): The natural language query string. Default is an empty string.
    page (int): The page number to retrieve. Default is 1.
    per_page (str): The number of results per page Default is 20.
    client_id (str, optional): Client identifier for search history tracking. Default is None.

Returns:
    JSONResponse: The generated response from the language model

Example:
    ```
    GET /api/talk_with_the_law?q=What are the zoning laws in California?
    ```
    """
```
* **Async:** True
* **Method:** True
* **Class:** App

## text_content

```python
@computed_field
@property
def text_content(self) -> str:
    """
    The text content of the file.
    """
```
* **Async:** False
* **Method:** True
* **Class:** Document

## transcribe_audio

```python
def transcribe_audio(self, audio_file: bytes) -> str:
    """
    Transcribe an audio file to text using a speech-to-text model.
    """
```
* **Async:** False
* **Method:** True
* **Class:** Dictate

## upload_document

```python
async def upload_document(self, file: UploadFile, client_cid: Optional[str] = None) -> JSONResponse:
    """
        API endpoint to handle document uploads from the frontend.

This method processes document uploads from the JavaScript frontend's uploadDocument
function. It integrates with the existing document processing pipeline to:
- Validate uploaded file format and size constraints
- Extract text content from PDF, DOC, DOCX, TXT files.
- Generate content identifiers (CIDs) for document tracking
- Store document metadata and content in the database
- Optionally associate uploads with client sessions for history tracking

    Args:
        file (UploadFile): The uploaded file object from FastAPI's multipart form data.
            Supported formats are .pdf, .doc, .docx, and .txt files.
        client_id (str, optional): Client CID for associating uploads
            with user sessions and maintaining upload history. Defaults to None.

    Returns:
        JSONResponse: A JSON response containing the upload status and metadata.

        Response:
            - status (str): Upload result status, set to "success" if successful, otherwise "error"
            - message (str): Human-readable description of successful upload or error details.
            - cid (str): Content identifier for the uploaded document. Set to empty string if upload failed.
            - filename (str): Original filename of the uploaded document. Set to empty string if upload failed.
            - file_size (int): Size of the uploaded file in bytes. Set to 0 if upload failed.
            - error_code (str): Machine-readable error identifier. Set to empty string if status is "success".
            - upload_timestamp (str): ISO timestamp of when upload completed or error occurred.

    Raises:
        HTTPException: 400 error for invalid file types, oversized files, or corrupted uploads
        HTTPException: 413 error if file exceeds maximum allowed size
        HTTPException: 415 error for unsupported media types
        HTTPException: 500 error for internal processing failures
        ValueError: If file content cannot be extracted or processed, or client ID is not a valid CID
        TypeError: If file or client ID types are incorrect
        IOError: If file cannot be read or temporary storage fails

    Examples:
        Frontend JavaScript usage:
        ```javascript
        const formData = new FormData();
        formData.append("file", file);
        const response = await fetch("/api/upload-document", {
            method: "POST",
            body: formData,
        });
        ```
        Success response format:
        ```json
        {
            "status": "success",
            "message": "File uploaded successfully",
            "cid": "bafkreihvwc5kg3estvqpicmmqghwiriti6mz5w3lk4k3app3guwk6onrq4",
            "filename": "document.pdf",
            "file_size": 1048576,
            "upload_timestamp": "2025-09-26T10:30:00Z"
        }
        ```
        Error response format:
        ```json
        {
            "status": "error",
            "message": "Upload failed: Invalid file type",
            "error_code": "INVALID_FILE_TYPE"
        }
        ```
    
    """
```
* **Async:** True
* **Method:** True
* **Class:** App

## web_search

```python
def web_search(self, *args, **kwargs) -> None:
    """
    Search the web for information.
    """
```
* **Async:** False
* **Method:** True
* **Class:** UploadMenu
