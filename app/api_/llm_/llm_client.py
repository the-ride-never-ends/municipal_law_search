"""
LLM Client implementation for American Law database.
Provides integration with OpenAI APIs and RAG components for legal research.
"""
import asyncio
import os
from pathlib import Path
import sqlite3
from typing import Annotated as Ann, Any, Callable, Coroutine, Dict, List, Optional


import duckdb
import numpy as np
import pandas as pd
from openai import AsyncOpenAI, OpenAI, OpenAIError
from pydantic import (
    AfterValidator as AV, 
    BaseModel, 
    BeforeValidator as BV, 
    computed_field, 
    Field,
    PrivateAttr, 
    TypeAdapter, 
    ValidationError
)
import tiktoken


from configs import configs, Configs
from logger import logger
from utils.app import clean_html
from utils.common import safe_format
from utils.llm.cosine_similarity import cosine_similarity
from utils.llm.load_prompt_from_yaml import load_prompt_from_yaml, Prompt
from .constants import MODEL_USAGE_COSTS_USD_PER_MILLION_TOKENS


def calculate_llm_api_cost(prompt: str, data: str, out: str, model: str) -> Optional[int]:
    # Initialize the tokenizer for the GPT model
    if model not in MODEL_USAGE_COSTS_USD_PER_MILLION_TOKENS:
        logger.error(f"Model {model} not found in usage costs.")
        return

    if model not in tiktoken.model.MODEL_PREFIX_TO_ENCODING.keys() or model not in tiktoken.model.MODEL_TO_ENCODING.keys():
        logger.error(f"Model {model} not found in tiktoken.")
        return

    tokenizer = tiktoken.encoding_for_model(model)

    # request and response
    request = str(prompt) + str(data)
    response = str(out)

    # Tokenize 
    request_tokens = tokenizer.encode(request)
    response_tokens = tokenizer.encode(response)

    # Counting the total tokens for request and response separately
    input_tokens = len(request_tokens)
    output_tokens = len(response_tokens)

    # Actual costs per 1 million tokens
    cost_per_1M_input_tokens = MODEL_USAGE_COSTS_USD_PER_MILLION_TOKENS[model]["input"]
    cost_per_1M_output_tokens = MODEL_USAGE_COSTS_USD_PER_MILLION_TOKENS[model]["output"]

    if cost_per_1M_output_tokens is None:
        output_cost = 0
    else:
        output_cost = (output_tokens / 10**6) * cost_per_1M_output_tokens
        
    input_cost = (input_tokens / 10**6) * cost_per_1M_input_tokens
    total_cost = input_cost + output_cost
    return total_cost




class AsyncLLMInput(BaseModel):
    client: Any
    user_message: str # NOTE For RAG, the found documents should be passed here.
    system_prompt: str = "You are a helpful assistant."
    use_rag: bool = False
    max_tokens: int = 4096
    temperature: float = 0 # Deterministic output
    response_parser: Callable = lambda x: x # This should be a partial function.
    formatting: Optional[str] = None

    _configs: Configs = PrivateAttr(default=configs)

    async def get_response(self) -> Optional[Any]:
        if self.use_rag:
            # Get an embedding of user_message (for future implementation)
            self.user_message = self._use_rag()

        try:
            _response = await self.client.chat.completions.create(
                model=self._configs.OPENAI_MODEL,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                messages=[
                    {"role": "system", "content": self.system_prompt.strip()},
                    {"role": "user", "content": self.user_message}
                ]
            )
        except Exception as e:
            logger.error(f"{type(e)} generating response: {e}")
            return "Error generating response. Please try again."

        if _response.choices[0].message.content:
            return AsyncLLMOutput(
                response=_response.choices[0].message.content.strip(),
                system_prompt=self.system_prompt.strip(),
                user_message=self.user_message,
                context_used=_response.usage.total_tokens,
                model=self._configs.OPENAI_MODEL,
                response_parser=self.response_parser,
            )
        else:
            return "No response generated. Please try again."

    async def _get_embedding(self) -> List[float]:
        """
        Generate an embedding of the user's message.
        
        Returns:
            Embedding vector
        """
        try:
            response = await self.client.embeddings.create(
                input=self.user_message,
                model=self._configs.OPENAI_EMBEDDING_MODEL
            )
        except Exception as e:
            logger.error(f"{type(e)} generating embedding: {e}")
            return []

        if response.data[0].embedding:
            return response.data[0].embedding
        else:
            logger.error("No embedding generated. Please try again.")
            return []

    async def _use_rag(self, user_message: str, system_message: str) -> Optional[tuple[str, str]]:
        """
        Use RAG to find relevant documents and generate a response.
        
        Args:
            user_message: The user's message
            system_message: The system prompt
        """
        user_message = user_message.strip('\n').strip()


class AsyncLLMOutput(BaseModel):
    response: str
    system_prompt: str
    user_message: str
    context_used: int
    model: str
    response_parser: Callable

    _configs: Configs = PrivateAttr(default=configs)

    @computed_field # type: ignore[prop-decorator]
    @property
    def cost(self) -> float:
        if self.response is not None:
            return calculate_llm_api_cost(self.system_prompt, self.user_message, self.response, self.model)
        else: 
            return 0

    async def get_parsed_response(self) -> Any:
        """Asynchronously parse the response using the provided parser"""
        return self.response_parser(self.response)


class LLMOutput(BaseModel):
    response: str
    system_prompt: str
    user_message: str
    context_used: int
    response_parser: Callable = Field(default_factory=lambda: lambda x: x)

    _configs: Configs = PrivateAttr(default=configs)

    @computed_field # type: ignore[prop-decorator]
    @property
    def cost(self) -> float:
        if self.response is not None:
            return calculate_llm_api_cost(self.system_prompt, self.user_message, self.response, self._configs.OPENAI_MODEL)
        else: 
            return 0

    def response(self) -> Any:
        return self.response_parser(self.response)




class OpenAiClient:

    def __init__(self, resources: dict = None, configs: Configs = None):
        """
        Initialize the OpenAI client for American Law dataset RAG.
        
        Args:
            resources: Dictionary of resources for embeddings and database queries
            configs: Configuration object
        """
        self.resources = resources
        self.configs = configs

        self.api_key: str = configs.OPENAI_API_KEY
        if not self.api_key:
            raise ValueError("API key must be provided either as an argument or as an environment variable (e.g. EXPORT OPENAI_API_KEY=...)")

        self.client = OpenAI(api_key=self.api_key)
        self.async_client = AsyncOpenAI(api_key=self.api_key)

        # Defaults for OpenAI API
        self.model: str = configs.OPENAI_MODEL
        self.embedding_model: str = configs.OPENAI_EMBEDDING_MODEL
        self.embedding_dimensions: int = 1536
        self.temperature: float = 0.2
        self.max_tokens: int = 4096
        
        # Set data paths
        self.data_path: Path = configs.AMERICAN_LAW_DATA_DIR
        self.db_path: Path = configs.AMERICAN_LAW_DB_PATH

        logger.info(f"Initialized OpenAI client: LLM model: {self.model}, embedding model: {self.embedding_model}")

    async def async_get_embeddings(self, texts: List[str]) -> List[List[float]]:
        response = await self.async_client.embeddings.create(
            input=texts,
            model=self.embedding_model
        )
        # Extract the embedding vectors from the response
        return [data.embedding for data in response.data]

    def get_embeddings(self, texts: str | List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of text inputs using OpenAI's embedding model.
        
        Args:
            texts: List of text strings to generate embeddings for
            
        Returns:
            List of embedding vectors (one vector per input text)
            
        Raises:
            OpenAIError: If the API request fails
            
        Examples:
            >>> texts = ["Hello world", "Legal document text"]
            >>> embeddings = client.get_embeddings(texts)
            >>> len(embeddings)  # doctest: +SKIP
            2
        """
        match texts:
            case str():
                texts = texts.strip()
                if not texts:
                    raise ValueError("Input text string cannot be empty.")
                texts = [texts]
            case list():
                _texts = []
                for idx, text in enumerate(texts):
                    if not isinstance(text, str):
                        raise TypeError(f"All items in the input list must be strings. Item at index {idx} is of type {type(text).__name__}.")
                    text = text.strip()
                    if not text:
                        raise ValueError(f"Input text at index {idx} cannot be an empty string.")
                    _texts.append(text)
                texts = _texts
            case _:
                raise TypeError(f"Input texts must be a string or a list of strings, got {type(texts).__name__}.")

        try:
            response = self.client.embeddings.create(
                input=texts,
                model=self.embedding_model
            )
        except Exception as e:
            logger.error(f"{type(e)} generating embeddings: {e}")
        # Extract the embedding vectors from the response
        return [data.embedding for data in response.data]


    async def async_get_response(self,
                            user_message: str = None,
                            system_prompt: str = None,
                            return_raw_response: bool = False,
                            model: Optional[str] = None,
                            temperature: Optional[float] = None,
                            max_tokens: Optional[int] = None,
                            ) -> str | Any:
        """
        Asynchronously generate a response using OpenAI's chat completion API.
        
        Args:
            user_message: The user's input message/query
            system_prompt: The system prompt to guide the AI's behavior
            return_raw_response: If True, return the raw OpenAI response object
            model: Override the default model for this request
            temperature: Override the default temperature for this request
            max_tokens: Override the default max_tokens for this request

        Returns:
            The AI-generated response as a string, or the raw response object if requested.
            If an error occurs, returns an error message string.

        Examples:
            >>> response = await async_get_response(
            ...     user_message="What is the capital of France?",
            ...     system_prompt="You are a knowledgeable assistant.",
            ...     return_raw_response=False,
            ...     model="gpt-4o",
            ...     temperature=0.5,
            ...     max_tokens=150
            ... )
            >>> print(response)  # doctest: +SKIP
            'The capital of France is Paris.'
        """
        try:
            _response = await self.async_client.chat.completions.create(
                model=model if model else self.model,
                temperature=temperature if temperature else self.temperature,
                max_tokens=max_tokens if max_tokens else self.max_tokens,
                messages=[
                    {"role": "system", "content": system_prompt.strip()},
                    {"role": "user", "content": user_message}
                ]
            )
        except Exception as e:
            logger.error(f"{type(e)} generating response: {e}")
            return "Error generating response. Please try again."

        if _response.choices[0].message.content:
            return _response if return_raw_response else _response.choices[0].message.content.strip()
        else:
            return "No response generated. Please try again."


    def get_response(self,
                    user_message: str = None,
                    system_prompt: str = None,
                    *,
                    return_raw_response: bool = False,
                    model: Optional[str] = None,
                    temperature: Optional[float] = None,
                    max_tokens: Optional[int] = None,
                    ) -> str:
        """
        """
        try:
            _response = self.client.chat.completions.create(
                model=model if model else self.model,
                temperature=temperature if temperature else self.temperature,
                max_tokens=max_tokens if max_tokens else self.max_tokens,
                messages=[
                    {"role": "system", "content": system_prompt.strip()},
                    {"role": "user", "content": user_message}
                ]
            )
        except Exception as e:
            logger.error(f"{type(e)} generating response: {e}")
            return "Error generating response. Please try again."

        if _response.choices[0].message.content:
            return _response if return_raw_response else _response.choices[0].message.content.strip()
        else:
            return "No response generated. Please try again."


class LLMClient:
    """
    Asynchronous client for LLM API integration with RAG capabilities.
    Handles embeddings integration and semantic search against the law database.
    """
    
    def __init__(
        self, 
        resources: dict = None,
        configs: Configs = None,
        api_key: str = None,
        model: str = "gpt-4o",
        embedding_model: str = "text-embedding-3-small",
        embedding_dimensions: int = 1536,
        temperature: float = 0.2,
        max_tokens: int = 4096,
    ):
        """
        Initialize the OpenAI client for American Law dataset RAG.
        
        Args:
            api_key: the LLM API key (defaults to OPENAI_API_KEY env variable)
            model: An LLM model to use for completion/chat
            embedding_model: An embedding model to use for embeddings
            embedding_dimensions: Dimensions of the embedding vectors
            temperature: Temperature setting for LLM responses
            max_tokens: Maximum tokens for LLM responses
        """
        self.resources = resources
        self.configs = configs

        self.api_key: str = api_key
        if not self.api_key:
            raise ValueError("API key must be provided either as an argument or as an environment variable (e.g. EXPORT OPENAI_API_KEY=...)")

        self._get_embeddings: Coroutine = self.resources['async_get_embeddings']
        self._search_embeddings: Coroutine = self.resources['search_embeddings']
        self._execute_sql_query: Callable = self.resources['execute_sql_query']

        self.client = AsyncOpenAI(api_key=self.api_key)
        self.model: str = model
        self.embedding_model: str = embedding_model
        self.embedding_dimensions: int = embedding_dimensions
        self.temperature: float = temperature
        self.max_tokens: int = max_tokens
        
        # Set data paths
        self.data_path: Path = configs.AMERICAN_LAW_DATA_DIR
        self.db_path: Path = configs.AMERICAN_LAW_DB_PATH

        logger.info(f"Initialized LLMClient client")


    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of text inputs using OpenAI's embedding model.
        
        Args:
            texts: List of text strings to generate embeddings for
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        try:
            # Prepare texts by stripping whitespace and handling empty strings
            processed_texts = [text.strip() for text in texts]
            processed_texts = [text if text else " " for text in processed_texts]

            return await self._get_embeddings(processed_texts)
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise e


    async def get_single_embedding(self, text: str) -> List[float]:
        """
        Generate an embedding for a single text input.
        
        Args:
            text: Text string to generate an embedding for
            
        Returns:
            Embedding vector
        """
        embeddings = await self.get_embeddings([text])
        if embeddings:
            return embeddings[0]
        return []


    async def search_embeddings(
        self, 
        query: str, 
        gnis: Optional[str] = None, 
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant documents using embeddings.
        
        Args:
            query: Search query
            gnis: Optional file ID to limit search to
            top_k: Number of top results to return
            
        Returns:
            List of relevant documents with similarity scores
        """
        # Generate embedding for the query
        query_embedding = await self.get_single_embedding(query)
        
        results = []
        # Create the SQL query
        sql_query = f"""
        WITH query_embedding AS (
            SELECT UNNEST($1) as vec
        ), 
        similarity_scores AS (
            SELECT 
            c.id, 
            c.cid, 
            c.title, 
            c.chapter, 
            c.place_name, 
            c.state_name, 
            c.date, 
            c.bluebook_citation, 
            c.content, 
            DOT_PRODUCT(e.embedding, ARRAY(SELECT vec FROM {query_embedding})) / 
            (SQRT(DOT_PRODUCT(e.embedding, e.embedding)) * 
                SQRT(DOT_PRODUCT(ARRAY(SELECT vec FROM {query_embedding}), 
                        ARRAY(SELECT vec FROM {query_embedding})))) as similarity_score 
            FROM 
            citations c 
            JOIN 
            embeddings e ON c.id = e.citation_id 
            WHERE 
            1=1
        """
        
        # Add GNIS filter if provided
        if gnis:
            sql_query += f" AND c.gnis = '{gnis}'"
            
        sql_query += f"""
        )
        SELECT * FROM similarity_scores
        ORDER BY similarity_score DESC
        LIMIT {top_k}
        """
        try:
            # Execute the query with the embedding as parameter
            results_list: list[dict] = self._execute_sql_query(sql_query)
        except Exception as e:
            logger.error(f"Error searching embeddings: {e}")
            return []

        # UNpack into a list of dictionaries
        for row in results_list:
            results.append({
                'id': row['id'],
                'cid': row['cid'],
                'title': row['title'],
                'chapter': row['chapter'],
                'place_name': row['place_name'],
                'state_name': row['state_name'],
                'date': row['date'],
                'bluebook_citation': row['bluebook_citation'],
                'content': row['content'],
                'similarity_score': float(row['similarity_score'])
            })

        return results

    def execute_sql_query(self, query: str, raise_on_e: bool = False) -> Optional[List[Dict[str, Any]]]:
        try:
            # Execute the query with the embedding as parameter
            return self._execute_sql_query(query)
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            if raise_on_e:
                raise e
            return []


    async def query_database(self, query: str, limit: int = None) -> List[Dict[str, Any]]:
        """
        Query the database for relevant laws.
        
        Args:
            query: Search query
            limit: Maximum number of results to return
            
        Returns:
            List of matching law records
        """
        # Simple text search of citations
        sql_query = f"""
            SELECT id, cid, title, chapter, place_name, state_name, date, 
                    bluebook_citation, content
            FROM citations
            WHERE lower(search_text) LIKE '%{query.lower()}%'
            ORDER BY place_name, title
        """
        if limit is not None:
            if limit > 0:
                # Add limit to the SQL query
                sql_query += f" LIMIT {limit};"
        # Execute query and fetch results
        return self.execute_sql_query(sql_query)


    async def generate_rag_response(
        self, 
        query: str, 
        use_embeddings: bool = True,
        top_k: int = 5,
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a response using RAG (Retrieval Augmented Generation).
        
        Args:
            query: User query
            use_embeddings: Whether to use embeddings for search
            top_k: Number of context documents to include
            system_prompt: Custom system prompt
            
        Returns:
            Dictionary with the generated response and context used
        """
        # Retrieve relevant context
        context_docs = []
        
        if use_embeddings:
            # Use embedding-based semantic search
            context_docs = await self.search_embeddings(query, top_k=top_k)
        else:
            # Use database text search as fallback
            context_docs = await self.query_database(query, limit=top_k)

        # Build context for the prompt
        context_text = "Relevant legal information:\n\n"
        references = "Citation(s):\n\n"

        for i, doc in enumerate(context_docs):
            context_text += f"[{i+1}] {doc.get('title', 'Untitled')} - {doc.get('place_name', 'Unknown location')}, {doc.get('state_name', 'Unknown state')}\n"
            references += f"{i+1}. {doc.get('bluebook_citation', 'No citation available')}\n"
            context_text += f"Citation: {doc.get('bluebook_citation', 'No citation available')}\n"
            # Limit html to avoid excessively long prompts
            html = doc.get('html', '')
            if html:
                # Turn the HTML into a string.
                content = clean_html(html)
                content = content[:1000] + "..." if len(content) > 1000 else content
                context_text += f"Content: {content}\n\n"
        
        # Default system prompt if none provided
        if system_prompt is None:
            system_prompt = """
    You are a legal research assistant specializing in American municipal and county laws. 
    Answer questions based on the provided legal context information. 
    If the provided context doesn't contain enough information to answer the question confidently, 
    acknowledge the limitations of the available information and suggest what additional 
    information might be helpful.
    For legal citations, use Bluebook format when available. Be concise but thorough.
            """
        # Generate response using OpenAI
        prompt: Prompt = load_prompt_from_yaml("generate_rag_response", self.configs, query=query, context=context_text)
        if system_prompt is not None:
            prompt.system_prompt = system_prompt.strip()
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                messages=[
                    {"role": "system", "content": system_prompt.strip()},
                    {"role": "user", "content": f"Question: {query}\n\n{context_text}"}
                ]
            )
            
            generated_response = response.choices[0].message.content.strip()
            
            # Append the citations
            generated_response += f"\n\n{references.strip()}"
            
            return {
                "query": query,
                "response": generated_response,
                "context_used": [doc.get('bluebook_citation', 'No citation') for doc in context_docs],
                "model_used": self.model,
                "total_tokens": response.usage.total_tokens
            }
            
        except Exception as e:
            logger.error(f"Error generating RAG response: {e}")
            return {
                "query": query,
                "response": f"Error generating response: {str(e)}",
                "context_used": [],
                "model_used": self.model,
                "error": str(e)
            }