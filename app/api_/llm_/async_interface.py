"""
Asynchronous API interface for the LLM integration with the American Law dataset.
Provides access to OpenAI-powered legal research and RAG components with async support.
"""
import asyncio
import json
import logging
from pathlib import Path
import re
from typing import Any, AsyncGenerator, Optional


from pydantic import ValidationError, BaseModel, Field

from configs import Configs
from .dependencies.async_openai_client import AsyncOpenAIClient
from .embeddings_manager import EmbeddingsManager
from utils.llm.validate_and_correct_sql_query_string import validate_and_correct_sql_query_string
from app.errors import LLMError


class _ConversationHistory(BaseModel):
    user_prompt: str = Field(..., min_length=1)
    system_prompt: str = Field(..., min_length=1)
    conversation_history: list[dict[str, str]] = Field(..., default_factory=list)


def parse_sse_event(raw_text: str) -> Optional[dict]:
    """
    Parse a single SSE event from raw text.
    
    Args:
        raw_text: Raw SSE event text containing event type and data
        
    Returns:
        Parsed event data as dictionary, or None if parsing fails
    """
    if not raw_text or not raw_text.strip():
        return None

    lines = raw_text.strip().split('\n')
    event_type = None
    event_data = None

    for line in lines:
        if line.startswith('event:'):
            event_type = line.split('event:', 1)[1].strip()
        elif line.startswith('data:'):
            data_str = line.split('data:', 1)[1].strip()
            try:
                event_data = json.loads(data_str)
            except json.JSONDecodeError as e:
                return None

    if event_data:
        return event_data
    return None


def extract_delta(event_data: dict) -> Optional[str]:
    """
    Extract text delta from a parsed SSE event.
    
    Args:
        event_data: Parsed event dictionary
        
    Returns:
        Text delta string, or None if not a delta event
    """
    if not event_data:
        return None

    event_type = event_data.get('type')

    if event_type == 'response.output_text.delta':
        return event_data.get('delta', '')

    return None


def extract_complete_text(event_data: dict) -> Optional[str]:
    """
    Extract complete text from a done event.
    
    Args:
        event_data: Parsed event dictionary
        
    Returns:
        Complete text string, or None if not a done event
    """
    if not event_data:
        return None
    
    event_type = event_data.get('type')
    
    if event_type == 'response.output_text.done':
        return event_data.get('text', '')
    
    return None


class AsyncLLMInterface:
    """
    Asynchronous interface for interacting with OpenAI LLM capabilities for the American Law dataset.
    Provides a simplified async API for accessing embeddings search and RAG functionality.
    """

    def __init__(self, *, configs: Configs, resources: dict[str, Any]) -> None:
        """
        Initialize the async LLM interface.
        
        Args:
            api_key: OpenAI API key
            configs: Configuration object containing all required settings
        """
        self.configs = configs
        self.resources = resources

        self.logger: logging.Logger = resources["logger"]

        self.api_key: str = configs.OPENAI_API_KEY.get_secret_value()
        self.data_path: Path = configs.AMERICAN_LAW_DATA_DIR
        self.db_path: Path = configs.AMERICAN_LAW_DB_PATH
        self.model: str = configs.OPENAI_MODEL
        self.embedding_model: str = configs.OPENAI_EMBEDDING_MODEL
        self.voice_model: str = configs.OPENAI_VOICE_MODEL
        self.system_prompt: str = configs.SYSTEM_PROMPT

        # Initialize clients
        self.async_client: AsyncOpenAIClient = resources["async_client"]

        self.embeddings_manager: EmbeddingsManager = resources["embeddings_manager"]
        self.logger.info(f"Initialized Embeddings Manager with model: {self.embedding_model}")
        self.logger.info(f"Initialized AsyncLLMInterface with model: {self.model}")


    async def ask_question(
        self,
        query: str,
        use_rag: bool = True,
        use_embeddings: bool = True,
        document_limit: int = 5,
        custom_system_prompt: str = "You are a legal research assistant specializing in American municipal and county laws."
    ) -> dict[str, Any]:
        """
        Ask a question about American law asynchronously.
        
        Args:
            query: User's question
            use_rag: Whether to use Retrieval Augmented Generation
            use_embeddings: Whether to use embeddings search for RAG
            document_limit: Maximum number of context documents to include
            custom_system_prompt: Custom system prompt for LLM
            
        Returns:
            Dictionary with the generated response and additional information
        """
        self.logger.info(f"Processing question: {query}")
        messages = [
            {"role": "system", "content": custom_system_prompt},
            {"role": "user", "content": query}
        ]
        response = {
            "query": query,
            "context_used": [],
            "model_used": self.async_client.model,
            "total_tokens": 0
        }
        if use_rag:
            # Use RAG to generate a response with context
            response = await self.async_client.generate_rag_response(
                query=query,
                use_embeddings=use_embeddings,
                top_k=document_limit,
                system_prompt=custom_system_prompt
            )
        else:
            # Use OpenAI directly without RAG context
            try:
                chat_response = await self.async_client.chat_completion(messages=messages)
                response.update({
                    "response": chat_response,
                    "total_tokens": self.async_client.total_tokens
                })
            except Exception as e:
                self.logger.error(f"Error in direct LLM query: {e}")
                response.update({
                    "response": f"Error generating response: {str(e)}",
                    "error": str(e)
                })
        return response

    async def get_single_embedding(self, text: str) -> list[float]:
        """
        Get a single embedding for a given text asynchronously.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        try:
            return await self.async_client.get_embeddings(text)
        except Exception as e:
            raise e
        # if len(embedding_list) > 1:
        #     self.logger.warning(f"Multiple embeddings returned for text: '{text}'. Returning first one.")
        # return embedding_list[0]

    def _format_messages(
            self, 
            system_prompt: str, 
            user_prompt: str, 
            conversation_history: list[dict[str, str]] = []
        ) -> list[dict[str, str]]:
        """Format messages for LLM input."""
        if not conversation_history:
            return [
                {"role": "system", "content": system_prompt.strip()},
                {"role": "user", "content": user_prompt.strip()}
            ]
        else:
            messages = [{"role": "system", "content": system_prompt.strip()}]
            for msg in conversation_history:
                messages.append({"role": msg["role"], "content": msg["content"].strip()})
            messages.append({"role": "user", "content": user_prompt.strip()})
            return messages


    async def _generic_response_stream(
            self, *,
            system_prompt: str, 
            user_prompt: str, 
            conversation_history: list[dict[str, str]] = []
        ) -> AsyncGenerator[Any, None]:
        """Stream a generic response from the LLM asynchronously."""

        messages = self._format_messages(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            conversation_history=conversation_history
        )

        stream = await self.async_client.client.responses.create(
            model=self.model,
            input=messages,
            temperature=0, # Deterministic output
            stream=True,
        )
        self.logger.debug("Started streaming response from LLM")
        yield stream

    async def _generic_response(
            self, *, 
            system_prompt: str, 
            user_prompt: str, 
            conversation_history: list[dict[str, str]] = []
            ) -> Any:
        """Return a generic response from the LLM asynchronously."""

        messages = self._format_messages(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            conversation_history=conversation_history
        )

        return await self.async_client.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=1024,
            temperature=0 # Deterministic output
        )

    async def stream_response(self, query: str, conversation_history: list[dict[str, str]]) -> AsyncGenerator[str, None]:
        """
        Stream LLM response token by token.
        
        Args:
            query: User's current message
            conversation_history: List of previous messages
            
        Yields:
            str: Individual tokens or chunks of the response
        
        Raises:
            ValueError: If inputs are invalid
            LLMError: If there is an error generating the response stream
        """
        kwargs = {
            "user_prompt": query,
            "system_prompt": self.system_prompt,
            "conversation_history": conversation_history
        }

        try:
            _ConversationHistory.model_validate(kwargs)
        except ValidationError as e:
            raise ValueError(f"Invalid inputs: {e.errors()}") from e

        try:
            async for event in self._generic_response_stream(**kwargs):

                # Read the entire response body
                await event.response.aread()
                raw_text = event.response.text

                # Parse SSE events from the raw text
                events = raw_text.strip().split('\n\n')
                
                for event_text in events:
                    if not event_text.strip():
                        continue

                    # Parse the event
                    event_data = parse_sse_event(event_text)
                    if not event_data:
                        continue

                    # Extract delta text
                    delta = extract_delta(event_data)
                    if delta:
                        asyncio.sleep(0.01)  # Slight delay to simulate streaming
                        yield delta

        except Exception as e:
            raise LLMError(f"Error streaming LLM response: {e}") from e


    async def determine_user_intent(self, message: str) -> str:
        """
        Determine the user's intent based on the query asynchronously.
        
        Args:
            query: User's input query
            
        Returns:
            Intent type as a string
        """
        if not isinstance(message, str):
            self.logger.error(f"Input message must be a string, got {type(message).__name__}")
            return "OTHER"
        message = message.strip()
        if not message:
            self.logger.error("Input message is empty after stripping")
            return "OTHER"

        # Make sure the response isn't anything nasty.
        response = await self.async_client.client.moderations.create(
            model="omni-moderation-latest",
            input=message,
        )
        if response.results[0].flagged:
            self.logger.warning(f"Message flagged by moderation: {message}")
            return "FLAGGED"
 
        self.logger.debug(f"Entering Determine Intent")
        system_prompt = """
        You are an intent classifier for a legal search system. Your job is to determine what the user wants to do with their query.
        Classify the user's intent into one of these categories:
        1. SEARCH - User wants to find specific laws or cases
        2. QUESTION - User is asking a legal question that needs explanation
        3. CITATION - User is looking for a specific citation or reference
        4. OTHER - None of the above
        Consider any direct or indirect or general information as a basis for your classification.
        Wrap your final answer in Markdown (e.g. ```plaintext```).
        """
        try:
            response = await self.async_client.client.chat.completions.create(
                model="gpt-3.5-turbo-0125",
                messages=[
                    {"role": "system", "content": system_prompt.strip()},
                    {"role": "user", "content": f"Message: {message}".strip()}
                ],
                max_tokens=1024,
                temperature=0 # Deterministic output
            )
            if response.choices:
                choice_content = response.choices[0].message.content.strip().lower()
                self.logger.debug(f"Determine intent content: '{choice_content}'")

                if "```" in choice_content:
                    choice_content = choice_content.split("```")[1].strip()

                self.logger.debug(f"Determine intent content after stripping: '{choice_content}'")

                # Extract intent from the classifier response
                if "search" in choice_content:
                    return "SEARCH"
                elif "question" in choice_content:
                    return "QUESTION"
                elif "citation" in choice_content:
                    return "CITATION"
                elif "other" in choice_content:
                    return "OTHER"
                else:
                    # Default fallback if the response doesn't match any category.
                    # This includes cases where the model returns a malformed or .
                    self.logger.error("Response did not match expected intent categories")
                    self.logger.debug(f"Response content: {choice_content}")
                    return "OTHER"  # Default to search as fallback
            else:
                self.logger.error("No valid choice in the GPT response")
                return "OTHER"  # Default fallback
        except Exception as e:
            self.logger.error(f"Error in determine_intent_basic: {e}", exc_info=True)
            return "OTHER"  # Fallback in case of exception


    async def search_embeddings(
        self,
        query: str,
        file_id: Optional[str] = None,
        top_k: int = 5
    ) -> list[dict[str, Any]]:
        """
        Search for relevant documents using embeddings asynchronously.
        
        Args:
            query: Search query
            file_id: Optional file ID to limit search to
            top_k: Number of top results to return
            
        Returns:
            list of relevant documents with similarity scores
        """
        # Generate embedding for the query
        query_embedding = await self.async_client.get_embeddings(query)
        
        if file_id:
            # Search in a specific file
            results = self.embeddings_manager.search_embeddings_in_file(
                query_embedding=query_embedding,
                file_id=file_id,
                top_k=top_k
            )
            
            # Add metadata for each result
            enriched_results = []
            for result in results:
                metadata = self.embeddings_manager.get_document_metadata(result['cid'], file_id)
                if metadata:
                    result.update(metadata)
                    enriched_results.append(result)
            
            return enriched_results
        else:
            # Search across all files (limited number)
            return self.embeddings_manager.search_across_files(
                query_embedding=query_embedding,
                max_files=10,  # Limit for performance
                top_k=top_k
            )
    
    async def generate_citation_answer(
        self,
        query: str,
        citation_codes: list[str],
        system_prompt: Optional[str] = None
    ) -> dict[str, Any]:
        """
        Generate an answer to a question with specific citation references.
        
        Args:
            query: User's question
            citation_codes: list of citation codes to use as context
            system_prompt: Custom system prompt
            
        Returns:
            Dictionary with the generated response and additional information
        """
        # Collect content from the specified citations
        context_docs = []
        
        for cid in citation_codes:
            # Try to find the document in the database
            doc = self.embeddings_manager.search_db_by_cid(cid)
            
            if doc:
                context_docs.append(doc)
        
        # Build context text
        context_text = "Relevant legal information:\n\n"
        for i, doc in enumerate(context_docs):
            context_text += f"[{i+1}] {doc.get('title', 'Untitled')} - {doc.get('place_name', 'Unknown location')}, {doc.get('state_name', 'Unknown state')}\n"
            context_text += f"Citation: {doc.get('bluebook_citation', 'No citation available')}\n"
            content = doc.get('content', '')
            if content:
                content = content[:1000] + "..." if len(content) > 1000 else content
                context_text += f"Content: {content}\n\n"
        
        # Default system prompt if none provided
        if system_prompt is None:
            system_prompt = """You are a legal research assistant specializing in American municipal and county laws.
Answer the question based on the provided legal citations.
For legal citations, use Bluebook format when available. Be concise but thorough."""
        
        # Generate response using OpenAI
        try:
            response = await self.async_client.client.chat.completions.create(
                model=self.async_client.model,
                temperature=self.async_client.temperature,
                max_tokens=self.async_client.max_tokens,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Question: {query}\n\n{context_text}"}
                ]
            )
            
            return {
                "query": query,
                "response": response.choices[0].message.content,
                "context_used": [doc.get('bluebook_citation', 'No citation') for doc in context_docs],
                "model_used": self.async_client.model,
                "total_tokens": response.usage.total_tokens
            }
            
        except Exception as e:
            self.logger.error(f"Error generating citation answer: {e}")
            return {
                "query": query,
                "response": f"Error generating response: {str(e)}",
                "context_used": [doc.get('bluebook_citation', 'No citation') for doc in context_docs],
                "model_used": self.async_client.model,
                "error": str(e)
            }

    async def query_to_sql(
        self,
        query: str,
        custom_system_prompt: Optional[str] = None
    ) -> dict[str, Any]:
        """
        Convert a natural language query into a PostgreSQL command for searching the American Law database.
        
        Args:
            query: User's plaintext query
            custom_system_prompt: Optional custom system prompt for the SQL generation
            
        Returns:
            Dictionary with the generated SQL query and additional information
        """
        self.logger.info(f"Converting query to SQL: {query}")
        
        # Define available tables and their schema for context
        schema_info = """
        Available tables and their schema:
        
        1. citations:
           - bluebook_cid (VARCHAR): Unique and primary key CID for citation
           - cid (VARCHAR): CID for the citation's associated law (foreign key)
           - title (TEXT): Plaintext version of the law's title
           - title_num (TEXT): Number in the law's title
           - chapter (TEXT): Chapter title containing the law
           - chapter_num (TEXT): Chapter number
           - place_name (TEXT): Place where the law is in effect
           - state_name (TEXT): State where the place is located
           - state_code (TEXT): Two-letter state abbreviation
           - bluebook_citation (TEXT): Bluebook citation for the law
           
        2. html:
           - cid (VARCHAR): Unique and primary key CID for the law
           - doc_id (TEXT): Unique ID based on law's title
           - doc_order (INTEGER): Relative location of law in corpus
           - html_title (TEXT): Raw HTML of law's title
           - html (TEXT): Raw HTML content of the law
           
        3. embeddings:
           - embedding_cid (VARCHAR): Unique and primary CID for the embedding
           - gnis (VARCHAR): Place's GNIS id
           - cid (VARCHAR): CID for associated law (foreign key)
           - text_chunk_order (INTEGER): Relative location of embedding
           - embedding (DOUBLE[1536]): Embedding vector for the law.
        """
        
        # Default system prompt if none provided
        if custom_system_prompt is None:
            system_prompt = f"""You are a SQL expert specializing in legal database queries.
Your task is to convert natural language questions into PostgreSQL queries.
Use the following database schema information:

{schema_info}

Important guidelines:
1. Always return a valid PostgreSQL query that can be executed directly
2. For full-text search, use the LIKE operator with wildcards (%)
3. Join tables when necessary using the cid field
4. For queries about specific states, filter by state_name or state_code
5. For queries about specific places, filter by place_name
6. For queries about certain topics, filter by keyword in the html field
7. Include ORDER BY clauses for relevance
8. Always include the following fields in the SELECT statement when selecting from the citations table:
   - cid
   - bluebook_cid
   - title
   - chapter
   - place_name
   - state_name
   - date
   - bluebook_citation
9. Use related terms and synonyms based on context clues in the question (e.g. "pets" implies "animals", "dogs", "cats", etc.)

Return ONLY the SQL query without any explanations."""
        else:
            system_prompt = custom_system_prompt
        
        try:
            # Generate SQL using OpenAI
            response = await self.async_client.client.chat.completions.create(
                model=self.async_client.model,
                temperature=0.2,  # Lower temperature for more deterministic output
                max_tokens=500,   # SQL queries shouldn't be too long
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Convert this question to a PostgreSQL query: {query}"}
                ]
            )
            
            # Extract the SQL query
            sql_query = response.choices[0].message.content.strip()
            
            # Basic validation to ensure it looks like SQL
            if not re.search(r'SELECT|select', sql_query):
                self.logger.warning(f"Generated SQL doesn't contain SELECT statement: {sql_query}")
                sql_query = f"-- Warning: This may not be a valid SQL query\n{sql_query}"

            sql_query = await validate_and_correct_sql_query_string(sql_query)
            if sql_query is None:
                self.logger.error("SQL query validation failed or returned empty. The LLM probably messed up.")
            else:
                self.logger.info(f"SQL query validated successfully")

            output_dict = {
                "original_query": query,
                "sql_query": sql_query if sql_query else "-- Error: No valid SQL query generated",
                "model_used": self.async_client.model,
                "total_tokens": response.usage.total_tokens,
                "error": None if sql_query else "Invalid SQL query generated"
            }
            return output_dict
        
        except Exception as e:
            self.logger.error(f"Error converting query to SQL: {e}")
            return {
                "original_query": query,
                "sql_query": f"-- Error generating SQL query: {str(e)}",
                "error": str(e)
            }
