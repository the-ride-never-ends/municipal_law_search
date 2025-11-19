#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
The FastAPI application that serves as an API for accessing American law documents.
"""
from __future__ import annotations



import asyncio
import atexit
import email
import json
import logging
import mimetypes
import smtplib
import ssl
import sys
import traceback
from collections import defaultdict
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr, quote
from enum import StrEnum
from pathlib import Path
from typing import Any, Callable, Optional


from functools import cached_property
from errors import StartupError, InitializationError, ResourceError, ConfigurationError


try:
    from dotenv import load_dotenv
    from fastapi import Depends, FastAPI, HTTPException, Query, Request, File, UploadFile
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
    from fastapi.staticfiles import StaticFiles
    from fastapi.templating import Jinja2Templates
    import magic
    from pydantic import BaseModel, computed_field, PrivateAttr
    from sse_starlette.sse import EventSourceResponse
    import uvicorn
except ImportError as e:
    raise StartupError(f"Error importing third-party dependencies: {e}") from e

try:
    from configs import Configs, configs as project_configs
    from logger import logger as module_logger

    import paths.search as search
    import paths.search_history as search_history
    from paths.upload_document import make_upload_document
    from schemas import LawItem
    from schemas import ErrorResponse
    from utils import get_html_db
    from llm import AsyncLLMInterface, LLM
    from read_only_database import Database, READ_ONLY_DB
except ImportError as e:
    raise StartupError(f"Error importing project modules: {e}") from e

# Load environment variables
load_dotenv()



class InitializationError(RuntimeError):
    """Custom exception for initialization errors in the App class."""
    def __init__(self, message: str):
        super().__init__(message)


class Routes(StrEnum):
    BASE = "/"
    STATIC_FILES = "/src"
    FAVICON = "/api/favicon.ico"
    PUBLIC_FILES = "/public/{filename:path}"
    SIDE_MENU_FILES = "/side-menu/{filename:path}"
    SEARCH_SSE = "/api/search/sse"
    GET_LAW = "/api/law/{cid}"
    DEMO = "/api/demo"
    LLM_CONVERSATION = "/api/llm/conversation"
    CLEAR_LLM_CONVERSATION = "/api/llm/clear-conversation"
    TALK_WITH_THE_LAW = "/api/talk_with_the_law"
    SEARCH_HISTORY = "/api/search-history"
    BLUEBOOK_CITATIONS = "/api/bluebook-citations"
    ACCOUNT_CREATE = "/api/account/create"
    ACCOUNT_DELETE = "/api/account/delete"
    ACCOUNT_PAGE = "/api/account/{account_id}"
    CONTACT = "/api/contact"
    CHROME_DEVTOOLS = "/.well-known/appspecific/com.chrome.devtools.json"
    UPLOAD_DOCUMENT = "/api/upload-document"


class Contact(StrEnum):
    GENERAL = "General Inquiry"
    SUPPORT = "Technical Support"
    FEEDBACK = "Feedback"
    PARTNER = "Partnership Opportunity"
    DATA = "Data Request"
    OTHER = "Other"


def _determine_mime_type(path_or_bytes: str | bytes | None) -> Optional[str]:
    """Determine the MIME type of a file.
    NOTE: Lifted from Omni-Converter Mk2 Repo
    
    Args:
        file_path: The path to the file.
        
    Returns:
        str: The MIME type of the file.
    """
    match path_or_bytes:
        case str():
            try:
                mime_type = magic.from_file(path_or_bytes, mime=True)
                # If magic returns generic type but extension suggests specific type, use mimetypes
                if mime_type == 'application/octet-stream':
                    guessed_type = mimetypes.guess_type(path_or_bytes)[0]
                    if guessed_type:
                        return guessed_type
                return mime_type
            except Exception:
                return mimetypes.guess_type(path_or_bytes)[0] or 'application/octet-stream'
        case bytes():
            try:
                return magic.from_buffer(path_or_bytes, mime=True)
            except (ImportError, Exception):
                return 'application/octet-stream'
        case _:
            return None

from typing import Annotated as Ann
from pydantic import AfterValidator as AV, FilePath, ValidationError


def event_dict(event: str, data: dict) -> dict:
    return {"event": event, "data": json.dumps(data)}


def is_static_web_file(file: FilePath) -> FilePath:
    valid_extensions = {'.html', '.css', '.js', '.json', '.txt', '.xml'}
    suffix = file.suffix.lower()
    if suffix not in valid_extensions:
        raise ValueError(
            f"Web file must be one of the following types: {', '.join(valid_extensions)}. Got '{suffix}' instead."
        )
    return file


class StaticWebFile(BaseModel):
    path: Ann[FilePath, AV(is_static_web_file)]

    @cached_property
    def file_response(self) -> FileResponse:
        try:
            return FileResponse(self.path)
        except ValidationError as e:
            raise HTTPException(status_code=404, details=f"Error serving static web file '{self.path}': {e}") from e



class Document(BaseModel):
    file: bytes

    _file_mime_type: str = PrivateAttr(default=None)
    _text_content: Optional[str] = PrivateAttr(default=None)
    _encoding: str = PrivateAttr(default='utf-8')

    @computed_field # type: ignore[prop-decorator]
    @property
    def text_content(self) -> str:
        """The text content of the file."""
        if self._text_content is None:
            try:
                self.text_content = self.file.decode(self._encoding)
            except UnicodeDecodeError as e:
                self.text_content = ''
        return self._text_content

    @computed_field # type: ignore[prop-decorator]
    @property
    def file_mime_type(self) -> str:
        """The MIME type of the file."""
        if self._file_mime_type is None:
            try:
                self._file_mime_type = _determine_mime_type(self.file)
            except (ImportError, Exception):
                self._file_mime_type = 'application/octet-stream'
        return self._file_mime_type


class Dictate:

    def __init__(self, *, configs: Configs, resources: dict[str, Any]) -> None:
        self.configs = configs
        self.resources = resources

        self.llm: AsyncLLMInterface = resources['llm']

    def transcribe_audio(self, audio_file: bytes) -> str:
        """
        Transcribe an audio file to text using a speech-to-text model.

        Args:
            audio_file (bytes): The audio file content in bytes.

        Returns:
            str: The transcribed text from the audio file.
        
        Raises:
            TypeError: If the audio_file is not bytes.
            ValueError: If the audio_file is empty.
            RuntimeError: If transcription unexpectedly fails.
        """
        if not isinstance(audio_file, bytes):
            raise TypeError(f"Audio file must be bytes, got {type(audio_file).__name__} instead.")
        if not audio_file:
            raise ValueError("Audio file cannot be empty.")

        try:
            transcribed_text = "Transcribed text from audio."
        except Exception as e:
            raise RuntimeError(f"Error during transcription: {e}") from e

        return transcribed_text



class VoiceMode:

    def __init__(self, *, configs: Configs, resources: dict[str, Any]) -> None:
        self.configs = configs
        self.resources = resources


class UploadMenu:

    def __init__(self, *, configs: Configs, resources: dict[str, Any]) -> None:
        self.configs = configs
        self.resources = resources

    def add_photos_and_files(self, *args, **kwargs) -> None:
        """Upload photos and files from local device."""
        raise NotImplementedError("add_photos_and_files method is not implemented yet.")

    def add_from_google_drive(self, *args, **kwargs) -> None:
        """Upload photos and files from Google Drive."""
        raise NotImplementedError("add_from_google_drive method is not implemented yet.")

    def agent_mode(self, *args, **kwargs) -> None:
        """Let an AI agent perform a task autonomously."""
        raise NotImplementedError("agent_mode method is not implemented yet.")

    def deep_research(self, *args, **kwargs) -> None:
        raise NotImplementedError("deep_research method is not implemented yet.")

    def connectors(self, *args, **kwargs) -> None:
        """Connect to third-party services like Dropbox, Google Drive, OneDrive, etc."""
        raise NotImplementedError("connectors method is not implemented yet.")

    def web_search(self, *args, **kwargs) -> None:
        """Search the web for information."""
        raise NotImplementedError("web_search method is not implemented yet.")


class SideMenu:
    def __init__(self, *, configs: Configs, resources: dict[str, Any]) -> None:
        self.configs = configs
        self.resources = resources


class App:
    """
    The main application class that encapsulates the FastAPI app and its resources.

    This class is responsible for initializing and configuring the FastAPI application,
    managing shared resources like database connections and language models, and
    defining the API routes and their corresponding handler functions.

    NOTE This class is instantiated once at startup and should be treated as a singleton.
    This class should never be instantiated directly. Use the `make_app()` factory function instead.

    Attributes:
        configs (Configs): Application configuration object.
        resources (dict): Dictionary of shared application resources.
        routes (Routes): Enum of application routes.
        read_only_db (Database): The read-only database instance.
        llm (AsyncLLMInterface): The language model interface instance.
        logger (logging.Logger): The application logger.
        fastapi (FastAPI): The FastAPI application instance.
        email (module): The email module.
        templates (Jinja2Templates): Jinja2 templates engine.
        side_menu (SideMenu): The side menu handler.
        upload_menu (UploadMenu): The upload menu handler.
        batch_processor (Callable): A function for batch processing tasks.
        search_function (Callable): The function used for performing searches.
        frontend_path (Path): Path to the frontend source directory.
        static_file_dir (Path): Path to the static files directory.
        templates_path (Path): Path to the templates directory.
        favicon_path (Path): Path to the favicon file.
        index_name (str): The name of the index HTML file.
        temp_storage (dict): A dictionary for temporary session storage.

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
    TITLE = "American Law API"
    DESCRIPTION = "API for accessing American law database"


    def __init__(self, *, configs: Configs, resources: dict[str, Any]) -> None:
        self.configs = configs
        self.resources = resources

        self.logger:          logging.Logger    = resources['logger']

        self.routes:           Routes            = Routes
        self.read_only_db:     Database          = resources['read_only_db'] # NOTE These classes are instantiated already.
        self.llm:              AsyncLLMInterface = resources['llm']
        self.fastapi:          FastAPI           = resources['fastapi']
        self.email:            email             = resources['email']
        self.templates:        Jinja2Templates   = resources['Jinja2Templates']
        self.side_menu:        SideMenu          = None # TODO implement side menu class
        self.upload_menu:      UploadMenu        = None # TODO implement upload menu class
        self.batch_processor:  Callable          = None # TODO See pdf_processor in ipfs_datasets_py
        self._search_function: Callable          = resources['search_function']
        self._upload_document: Callable          = resources['upload_document'] 
        self._event_dict:       Callable         = resources['event_dict'] 

        # Contact form email settings
        self._email_address: str = configs.ADMIN_EMAIL
        self._smtp_server: str = configs.EMAIL_SERVER
        self._smtp_port: int = configs.EMAIL_PORT
        self._smtp_username: str = configs.EMAIL_USERNAME
        self._smtp_password: str = configs.EMAIL_PASSWORD

        # LLM mode
        self.llm_mode: bool = False

        # Paths
        # TODO move to configs.py
        self.frontend_path: Path    = configs.ROOT_DIR / 'src'
        self.static_file_dir: Path  = self.frontend_path / 'static'
        self.templates_path: Path   = self.frontend_path / 'templates'
        self.favicon_path: Path     = self.static_file_dir / 'images' / 'favicon' / 'favicon.ico'
        self.index_name: str        = "index.html"

        self.templates = self.templates(directory=self.templates_path)

        self.pending_uploads: asyncio.Queue = asyncio.Queue()

        self.temp_storage = {
            "current_sessions": {
                "client_cid": {
                    "uploads": {
                        "cid": {
                            "filename": str,
                            "file_size": int,
                            "upload_timestamp": str,
                            "file_mime_type": str,
                            "text_content": str,
                        }
                    },
                    "llm_conversations": {
                        "cid": {
                            "messages": list[dict[str, Any]],
                            "last_interaction_timestamp": str,
                        }
                    }
                }
            }
        }
        self.perm_storage = defaultdict(list) # TODO implement permanent storage


    @property
    def get_mappings(self) -> dict[Routes, tuple[Callable, dict[str, Any]]]:
        """
        Mappings for GET requests.
        
        Returns:
            dict: A dictionary mapping routes to handler functions and parameters.
        """
        schema_true = {"include_in_schema": True}
        schema_false = {"include_in_schema": False}
        mappings = {
            self.routes.BASE:                (self.serve_index, {"response_class": HTMLResponse, "include_in_schema": True}),
            self.routes.FAVICON:             (self.favicon, {"include_in_schema": False}),
            self.routes.PUBLIC_FILES:        (self.serve_public_files, {"include_in_schema": True}),
            self.routes.SIDE_MENU_FILES:     (self.serve_side_menu_files, {"include_in_schema": True}),
            self.routes.SEARCH_SSE:          (self.search_sse_response, {"include_in_schema": True}),
            self.routes.LLM_CONVERSATION: (self.llm_conversation_sse, {"include_in_schema": True}),
            # self.routes.TALK_WITH_THE_LAW: (talk_with_the_law, {"include_in_schema": True}),
            self.routes.GET_LAW:             (self.get_law, {"include_in_schema": True}),
            # self.routes.SEARCH_HISTORY:    (get_search_history, {"include_in_schema": True}),
        }
        return mappings

    @property
    def put_mappings(self):
        mappings = {}
        return mappings

    @property
    def delete_mappings(self):
        mappings = {}
        return mappings

    @property
    def post_mappings(self):
        schema_true = {"include_in_schema": True}
        mappings = {
            self.routes.TALK_WITH_THE_LAW: (self.talk_with_the_law, schema_true),
            self.routes.CONTACT:           (self.contact, {"include_in_schema": True}),
            self.routes.CLEAR_LLM_CONVERSATION: (self.clear_llm_conversation, {"include_in_schema": True}),
        }
        return mappings

    @property
    def email_address(self):
        return self._email_address

    @property
    def index(self) -> str:
        return self.index_name

    @staticmethod
    def _validate_string(string: str) -> FileResponse:
        if not isinstance(string, str):
            raise TypeError(f"String must be str, got {type(string).__name__} instead.")
        string = string.strip()
        if not string:
            raise ValueError("String cannot be empty or whitespace.")
        return string

    async def favicon(self) -> FileResponse:
        """Serve the site favicon.ico file.
        
        This endpoint serves the favicon.ico file from the static images directory.
        It is marked as not included in the schema documentation.
        
        Returns:
            FileResponse: The favicon.ico file
        """
        # NOTE This cannot be a property because FastAPI requires a callable for route handlers.
        path = self.favicon_path
        try:
            return StaticWebFile(path=path).file_response  # Validate file
        except ValidationError as e:
            raise HTTPException(status_code=404, detail=str(e))

    async def serve_index(self, request: Request) -> HTMLResponse:
        """Serve the main index page of the application.
        
        This endpoint renders the main HTML template for the application,
        which is the entry point for the user interface.
        
        Args:
            request: The incoming request object
            
        Returns:
            HTMLResponse: The rendered index.html template
        """
        try:
            return self.templates.TemplateResponse(self.index, {"request": request})
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error rendering index page: {e}") from e


    async def serve_public_files(self, filename: str) -> FileResponse:
        """Serve static files from the public templates directory.
        
        This endpoint allows direct access to files in the templates directory
        via the /public/ URL path.
        
        Args:
            filename: The path of the file to serve
            
        Returns:
            FileResponse: The requested file
        Raises:
            HTTPException: 404 error if the requested file does not exist
            HTTPException: 400 error if the requested path is not a file
            HTTPException: 415 error if the file type is unsupported
        """
        try:
            filename = self._validate_string(filename)
        except Exception as e:
            raise e
        path = self.templates_path / filename
        try:
            return StaticWebFile(path=path).file_response  # Validate file
        except ValidationError as e:
            raise HTTPException(status_code=404, detail=str(e))


    async def serve_side_menu_files(self, filename: str) -> HTMLResponse:
        """Serve HTML files from the side-menu templates directory.

        This endpoint serves HTML files from the side-menu subdirectory.
        Files are:
         - about.html
         - contact.html
         - ourteam.html
         - disclaimer.html

        Args:
            filename: The name of the file to serve from the side-menu directory

        Returns:
            HTMLResponse: The requested HTML file

        Raises:
            HTTPException: 404 error if the requested file does not exist
        """
        try:
            filename = self._validate_string(filename)
        except Exception as e:
            raise e

        path = self.templates_path / 'side-menu' / filename

        try:
            return StaticWebFile(path=path).file_response 
        except ValidationError as e:
            raise HTTPException(status_code=404, detail=str(e))

    async def upload_document(
        self,
        file: UploadFile,
        client_cid: Optional[str] = None
        ) -> JSONResponse:
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
        return await self._upload_document(file, self.temp_storage, client_cid)

    async def clear_llm_conversation(
        self,
        client_id: str = None,
    ) -> JSONResponse:
        """Clear the LLM conversation history for a client.

        Args:
            client_id: Client identifier

        Returns:
            JSONResponse: Response indicating success
        """
        if "llm_conversations" in self.temp_storage and client_id in self.temp_storage["llm_conversations"]:
            del self.temp_storage["llm_conversations"][client_id]

        return JSONResponse({
            "status": "success",
            "message": "Conversation history cleared"
        })

    async def llm_conversation_sse(
        self,
        q: str = Query("", description="User message"),
        client_id: str = None,
    ) -> EventSourceResponse:
        """Server-Sent Events endpoint for LLM conversation streaming.

        This endpoint provides a streaming interface for LLM conversations.
        Unlike search, this maintains conversational context and streams
        the LLM's response token-by-token for a more interactive experience.

        The event stream includes:
        - A "conversation_started" event when processing begins
        - Multiple "token" events as the LLM generates its response
        - A "conversation_complete" event when generation is finished
        - An "error" event if any errors occur

        Args:
            q: The user's message/query string
            client_id: Client identifier for conversation history tracking

        Returns:
            EventSourceResponse: A streaming response that sends events to the client
        """
        self._validate_optional_string(q, 'q', skip_if_value_is_none=False)

        async def _event_generator():
            try:
                yield self._event_dict("conversation_started", {
                    "message": "Processing your request",
                    "query": q
                })

                # Get conversation history for this client if it exists
                conversation_history = self.temp_storage.get("llm_conversations", {}).get(client_id, [])

                # Add user message to history
                conversation_history.append({"role": "user", "content": q})

                # Stream LLM response
                full_response = ""
                async for chunk in self.llm.stream_response(q, conversation_history):
                    full_response += chunk
                    yield self._event_dict("token", {
                        "token": chunk,
                        "full_response": full_response
                    })

                # Add assistant response to history
                conversation_history.append({"role": "assistant", "content": full_response})

                # Store updated conversation history
                if "llm_conversations" not in self.temp_storage:
                    self.temp_storage["llm_conversations"] = {}
                self.temp_storage["llm_conversations"][client_id] = conversation_history

                yield self._event_dict("conversation_complete", {
                    "message": "Response complete",
                    "full_response": full_response
                })

            except Exception as e:
                trace = traceback.format_exc()
                msg = f"Error in LLM conversation stream: {e}\n{trace}"
                self.logger.error(msg)
                yield self._event_dict("error", {"message": msg})
            finally:
                if client_id is not None:
                    # Save to permanent storage if needed
                    if client_id not in self.perm_storage:
                        self.perm_storage[client_id] = []
                    self.perm_storage[client_id].append({
                        "type": "llm_conversation",
                        "timestamp": datetime.now().isoformat(),
                        "history": conversation_history
                    })

        return EventSourceResponse(_event_generator())


    async def search_sse_response(
        self,
        q: str = Query("", description="Search query"),
        page: int = Query(1, description="Page number"),
        per_page: int = Query(20, description="Items per page"),
        client_id: str = None #Depends(search_history.get_or_create_client_id),
        ) -> EventSourceResponse:
        """Server-Sent Events endpoint that streams search results incrementally.

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
        self._validate_query_params(q, page, per_page, client_id)

        kwargs = {"q": q, "page": page, "per_page": per_page, "client_id": client_id, "logger": self.logger, "llm": self.llm}

        async def _event_generator():
            try:
                yield event_dict("search_started", {"message": "Search started", "query": q})

                async for result in self._search_function(**kwargs):
                    # Send each result chunk as it becomes available
                    yield event_dict("results_update", result)

                # Final event to indicate the search is complete
                yield event_dict("search_complete", {"message": "Search completed", "query": q})

            except Exception as e:
                msg = f"Error in SSE stream: {e}"
                self.logger.error(msg)
                traceback.print_exc()
                yield event_dict("error", {"message": msg})
            finally:
                if client_id is not None:
                    self.perm_storage[client_id].append(self.temp_storage["current_sessions"].get(client_id, {}))

        return EventSourceResponse(_event_generator())

    async def get_law(self, cid: str) -> dict[str, Any]:
        """API endpoint to retrieve a specific legal document by its content ID.
        
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
        law = None
        html_conn = get_html_db(read_only=True)
        html_cursor = html_conn.cursor()
        try:
            html_cursor.execute('''
            SELECT *
            FROM citations c
            JOIN html h ON c.cid = h.cid
            WHERE c.cid = ?
            ''', (cid,))
            
            law: dict = html_cursor.fetchdf().to_dict('records')[0]
        finally:
            html_cursor.close()
            html_conn.close()
        self.logger.debug(f"law: {law}")

        if law is not None:
            return {
                'cid': law['cid'],
                'title': law['title'],
                'chapter': law['chapter'],
                'place_name': law['place_name'],
                'state_name': law['state_name'],
                'date': law['date'],
                'bluebook_citation': law['bluebook_citation'],
                'html': law['html']
            }
        else:
            raise HTTPException(status_code=404, detail="Law not found")

    async def talk_with_the_law(
        self,
        q: str = Query("", description="Search query"),
        page: int = Query(1, description="Page number"),
        per_page: int = Query(20, description="Items per page"),
        client_id: str = None, #Depends(search_history.get_or_create_client_id),
    ) -> JSONResponse:
        """API endpoint to interact with the law using a natural language query.

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
        self._validate_query_params(q, page, per_page, client_id)
        response: dict = await self.llm.query_to_sql(q)
        return JSONResponse(content=response)

    async def contact(
        self,
        name: str,
        email: str,
        message: str,
        subject: StrEnum,
        organization: Optional[str] = None,
    ) -> JSONResponse:
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
        # Validate subject first (fail fast)
        if subject not in Contact:
            raise ValueError(f"Invalid subject: {subject}. Must be one of {[s.value for s in Contact]}")

        # Validate string inputs
        string_validations = [
            (name, 'name', False), (email, 'email', False),  (message, 'message', False), 
            (subject, 'subject', False), (organization, 'organization', True)
        ]
        cleaning_dict = {}

        for value, field_name, can_be_none in string_validations:
            self._validate_optional_string(value, field_name, skip_if_value_is_none=can_be_none)
            # Quote the string to prevent injection attacks
            cleaning_dict[field_name] = f'"{quote(value.strip())}"' if value is not None else None

        name = cleaning_dict['name']
        email = cleaning_dict['email']
        message = cleaning_dict['message']
        subject = cleaning_dict['subject']
        organization = cleaning_dict.get('organization', None)

        # Construct subject line
        org_part = f" ({organization})" if organization else ""
        subject_line = f"{self.TITLE}[Form Submission] {subject.value} - {name}{org_part}"

        # Construct email body
        email_body = f"""
Subject: {subject.value}
Name: {name}
Organization: {organization or "N/A"}
Time: {datetime.now().astimezone().isoformat()}
Email: {email}

Message:
{message}
"""
        # Create email message
        msg = MIMEMultipart()
        msg['From'] = formataddr((name, email))
        msg['To'] = self.email_address
        msg['Subject'] = subject_line
        msg['Reply-To'] = email

        # Attach the body
        msg.attach(MIMEText(email_body.strip(), 'plain', 'utf-8'))
        error_tuple = None

        try:
            # Create SMTP connection with SSL
            context = ssl.create_default_context()

            with smtplib.SMTP(self._smtp_server, self._smtp_port) as server:
                server.starttls(context=context)
                server.login(self._smtp_username, self._smtp_password)

                # Send email
                server.send_message(msg)

            return JSONResponse({
                "status": "success", 
                "message": "Contact form submitted successfully"
            })

        except smtplib.SMTPAuthenticationError as e:
            error_tuple = (f"Authentication failed.", f"\n{e}", 500)
        except smtplib.SMTPRecipientsRefused as e:
            error_tuple = (f"Invalid recipient email address", f"\n{e}", 400)
        except smtplib.SMTPException as e:
            error_tuple = (f"Failed to send email.", f"\n{e}", 500)
        except ConnectionError as e:
            error_tuple = (f"Unable to connect to email server.", f"\n{e}", 503)
        except Exception as e:
            error_tuple = (f"An unexpected {type(e).__name__} error occurred.", f"\n{e}", 500)
        finally:
            if error_tuple is not None:
                if "unexpected" in error_tuple[0].lower():
                    self.logger.exception(f"Unexpected error sending contact form: {e}")
                else:
                    self.logger.error(f"Contact form error: {error_tuple[0]}{error_tuple[1]}") 
                return JSONResponse(
                    {"status": "error",
                     "message": error_tuple[0] + " Please try again later.\n" + error_tuple[1]},
                     status_code=error_tuple[2]
                )

    async def account_create(self):
        raise NotImplementedError("Account creation endpoint not implemented yet.")

    async def account_delete(self):
        raise NotImplementedError("Account delete endpoint not implemented yet.")

    async def account_page(self):
        raise NotImplementedError("Account page endpoint not implemented yet.")

    @staticmethod
    def _validate_optional_string(value: Any, var_name: str, skip_if_value_is_none: bool = False) -> None:
        if skip_if_value_is_none and value is None:
            return
        if not isinstance(value, str):
            raise TypeError(f"'{var_name}' must be an str, got {type(value).__name__} instead.")
        if not value.strip():
            raise ValueError(f"'{var_name}' must be a non-empty string, got {value}.")

    @staticmethod
    def _validate_integer(value: Any, var_name: str, skip_if_value_is_none: bool = False) -> None:
        if skip_if_value_is_none and value is None:
            return
        if not isinstance(value, int):
            raise TypeError(f"'{var_name}' must be an integer, got {type(value).__name__} instead.")
        if value < 1:
            raise ValueError(f"'{var_name}' must be a positive integer, got {value}.")


    def _validate_query_params(self, q: str, page: int, per_page: int, client_id: str) -> None:
        """Validate query parameters for search endpoints.
        
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
        string_params = [(q, 'q'),(client_id, 'client_id')]
        integer_params = [(per_page, 'per_page'), (page, 'page')]

        for arg, name in string_params:
            self._validate_optional_string(arg, name, skip_if_value_is_none=True)

        for arg, name in integer_params:
            self._validate_integer(arg, name)


    def _map_static_files(self, app: FastAPI) -> FastAPI:
        """Mount static files to the FastAPI app."""
        app.mount(
            self.routes.STATIC_FILES, 
            StaticFiles(directory=self.static_file_dir), 
            name=self.routes.STATIC_FILES.value.lstrip('/')
        )
        return app

    @staticmethod
    def _add_middleware(app: FastAPI) -> FastAPI:
        """Add middleware to the FastAPI app."""
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        return app

    def make_app(self) -> FastAPI:
        """
        Configure and return the FastAPI application instance.
        
        Returns:
            FastAPI: The configured FastAPI application instance.

        Raises:
            TypeError: If any route handler function is not callable.
            InitializationError: If there are unexpected errors during App initialization.
        """
        app = FastAPI(title=self.TITLE, description=self.DESCRIPTION)
        try:
            app = self._add_middleware(app)
        except Exception as e:
            raise InitializationError(f"Error initializing App middleware: {e}") from e
        try:
            app = self._map_static_files(app)
        except Exception as e:
            raise InitializationError(f"Error initializing App static files: {e}") from e

        # Register GET routes
        for route, (func, params) in self.get_mappings.items():
            if func is None:
                continue
            if not callable(func):
                raise TypeError(f"Function for route '{route}' is not callable.")
            try:
                app.get(route, **params)(func)
            except Exception as e:
                raise InitializationError(f"Error adding GET route '{route}': {e}") from e

        # Register POST routes
        for route, (func, params) in self.post_mappings.items():
            if func is None:
                continue
            if not callable(func):
                raise TypeError(f"Function for route '{route}' is not callable.")
            try:
                app.post(route, **params)(func)
            except Exception as e:
                raise InitializationError(f"Error adding POST route '{route}': {e}") from e

        return app


def get_upload_menu(
        resources: dict[str, Any] = {},
        configs: BaseModel = project_configs,
        ) -> UploadMenu:

    try:
        Configs.model_validate(configs)
    except ValidationError as e:
        raise ConfigurationError(f"configs failed validation: {e.errors()}") from e

    try:
        resources_ = {
            "read_only_db": resources.pop('read_only_db', READ_ONLY_DB),
            "llm": resources.pop("llm", LLM),
            "logger": resources.pop("logger", module_logger),
            "fastapi": resources.pop("fastapi", FastAPI),
            "email": resources.pop("email", email),
        }
    except Exception as e:
        raise ResourceError(f"Error setting up resources for UploadMenu: {e}") from e

    try:
        upload_menu_instance = UploadMenu(configs=configs, resources=resources_)
    except Exception as e:
        raise InitializationError(f"Error initializing UploadMenu: {e}") from e
    return upload_menu_instance


def get_side_menu(resources: Optional[dict] = None, configs: Optional[BaseModel] = None) -> SideMenu:
    configs = configs or project_configs
    resources = resources or {}
    resources = {
        "read_only_db": resources.pop('read_only_db', READ_ONLY_DB),
        "llm": resources.pop("llm", LLM),
        "logger": resources.pop("logger", module_logger),
        "fastapi": resources.pop("fastapi", FastAPI),
        "email": resources.pop("email", email),
    }
    try:
        side_menu_instance = SideMenu(configs=configs, resources=resources)
    except Exception as e:
        raise InitializationError(f"Error initializing SideMenu: {e}") from e
    return side_menu_instance




DEFAULT_RESOURCE_KEYS = {
    "read_only_db",
    "llm",
    "logger",
    "fastapi",
    "Jinja2Templates",
    "email",
    "side_menu",
    "upload_menu",
    "search_function",
    "batch_processor"
}

def make_app(
        resources: dict[str, Any] = {}, 
        configs: BaseModel = project_configs,
        ) -> FastAPI:
    """
    Factory function to create a new FastAPI instance for the American Law Search website's backend.

    Args:
        resources (dict[str, Any], optional): A dictionary of callables to override injected defaults. Defaults to None.

        Resources are:
            - read_only_db (Database): Read-only database connection (default: READ_ONLY_DB)
            - llm (AsyncLLMInterface): Language model instance (default: LLM)
            - logger (logging.Logger): Logger instance (default: module_logger)
            - fastapi (ModuleType): FastAPI class (default: FastAPI)
            - Jinja2Templates (Jinja2Templates): Jinja2Templates class (default: Jinja2Templates)
            - email (ModuleType): Email module (default: email)
            - side_menu (SideMenu): SideMenu instance (default: get_side_menu())
            - upload_menu (UploadMenu): UploadMenu instance (default: get_upload_menu())
            - search_function (AsyncGenerator): Search function (default: search.function)

        configs (Configs, optional): A Configs object to override default initialization configurations. Defaults to None.

        Configs attributes set upon initialization are:
            - ADMIN_EMAIL (str): Admin email address
            - EMAIL_SERVER (str): SMTP server address
            - EMAIL_PORT (int): SMTP server port
            - EMAIL_USERNAME (str): SMTP username
            - EMAIL_PASSWORD (str): SMTP password
            - ROOT_DIR (Path): Root directory of the project

    Returns:
        FastAPI: The configured FastAPI application instance.

    Raises:
        TypeError: If resources is not a dict or configs is not a BaseModel instance.
        KeyError: If resources contains unexpected keys.
        ConfigurationError: If configs fail validation.
        ResourceError: If there are errors setting up resources.
        InitializationError: If an error occurs during App initialization.
    """
    if not isinstance(resources, dict):
        raise TypeError(f"'resources' must be a dict, got {type(resources).__name__} instead.")
    else:
        if not resources:
            pass
        for key in resources.keys():
            if key not in DEFAULT_RESOURCE_KEYS:
                raise KeyError(f"Unexpected resource key in resources: {key}")

    if not isinstance(configs, BaseModel):
        raise TypeError(f"'configs' must be a BaseModel instance, got {type(configs).__name__} instead.")

    try:
        Configs.model_validate(configs)
    except ValidationError as e:
        raise ConfigurationError(f"configs failed validation: {e.errors()}") from e

    try:
        resources_ = {
            "read_only_db": resources.pop('read_only_db', READ_ONLY_DB),
            "llm": resources.pop("llm", LLM),
            "logger": resources.pop("logger", module_logger),
            "fastapi": resources.pop("fastapi", FastAPI),
            "Jinja2Templates": resources.pop("Jinja2Templates", Jinja2Templates),
            "email": resources.pop("email", email),
            "side_menu": resources.pop("side_menu", get_side_menu()),
            "upload_menu": resources.pop("upload_menu", get_upload_menu()),
            "search_function": resources.pop("search_function", search.function),
            "upload_document": resources.pop("upload_document", make_upload_document().upload_document),
            "batch_processor": resources.pop("batch_processor", None),
            "event_dict": resources.pop("event_dict", event_dict),
        }
    except Exception as e:
        raise ResourceError(f"Error setting up resources for App: {e}") from e

    try:
        app_instance = App(configs=configs, resources=resources_)
    except KeyError as e:
        raise InitializationError(f"Failed to initialize App due to invalid resource key: {e}") from e
    except AttributeError as e:
        raise InitializationError(f"Failed to initialize App due to invalid config attribute: {e}") from e
    except Exception as e:
        raise InitializationError(f"Unexpected error initializing App: {e}") from e
    else:
        return app_instance

def make_fastapi_app(
        resources: dict[str, Any] = {}, 
        configs: BaseModel = project_configs,
        return_fastapi_instance: bool = True
        ) -> FastAPI:
    """
    Convenience function to create and return a FastAPI instance.

    Args:
        resources (dict[str, Any], optional): A dictionary of callables to override injected
        defaults. Defaults to None.
        configs (Configs, optional): A Configs object to override default initialization
        configurations. Defaults to None.
        return_fastapi_instance (bool, optional): If True, return the FastAPI instance.
        If False, return the App instance. Defaults to True.

    Returns:
        FastAPI: The configured FastAPI application instance.

    Raises:
        InitializationError: If there are errors during App initialization or FastAPI configuration.
    """
    try:
        app_instance = make_app(resources=resources, configs=configs)
    except Exception as e:
        raise StartupError(f"Unexpected error creating App instance: {e}") from e

    try:
        return app_instance.make_app() if return_fastapi_instance else app_instance
    except Exception as e:
        raise StartupError(f"Unexpected error configuring FastAPI app: {e}") from e


# Set up the FastAPI app
app = make_fastapi_app()

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from .read_only_database import close_db_connection

def clear_futures():
    """Clear any pending asyncio futures to prevent warnings on shutdown."""
    try:
        loop = asyncio.get_event_loop()
        pending = asyncio.all_tasks(loop=loop)
        for task in pending:
            task.cancel()
        loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
    except (KeyboardInterrupt, asyncio.exceptions.CancelledError) as e:
        pass
    except Exception as e:
        print(f"Unexpected error clearing asyncio futures: {e}")


atexit.register(close_db_connection)
atexit.register(clear_futures)


def main():
    error = 0
    try:
        uvicorn.run("app:app", host="0.0.0.0", port=8080, reload=True)
    except KeyboardInterrupt:
        module_logger.info("Server interrupted by user.")
    except Exception as e:
        import traceback
        print(f"Error while running app: {e}\nTraceback:\n{traceback.format_exc()}")
        error = 1
    finally:
        if READ_ONLY_DB is not None:
            READ_ONLY_DB.exit()
        module_logger.info("Server stopped.")
        return error


if __name__ == '__main__':
    sys.exit(main())
