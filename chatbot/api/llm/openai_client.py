"""
OpenAI Client implementation for American Law database.
Provides integration with OpenAI APIs and RAG components for legal research.
"""
from typing import Callable, List, Literal, Dict, Any, Never, Optional


import duckdb
import numpy as np
from openai import OpenAI
import pandas as pd
from pydantic import AfterValidator as AV, BaseModel, BeforeValidator as BV, computed_field, PrivateAttr, TypeAdapter, ValidationError
import tiktoken


from logger import logger
from configs import configs, Configs
from utils.chatbot.clean_html import clean_html
from utils.llm.load_prompt_from_yaml import load_prompt_from_yaml, Prompt


# From: https://platform.openai.com/docs/pricing
MODEL_USAGE_COSTS_USD_PER_MILLION_TOKENS = {
    "gpt-4o": {
        "input": 2.50,
        "output": 10.00
    },
    "gpt-4.5-preview": {
        "input": 75.00,
        "output": 150.00
    },
    "gpt-4-turbo": {
        "input": 10.00,
        "output": 30.00
    },
    "gpt-4": {
        "input": 30.00,
        "output": 60.00
    },
    "gpt-4-32k": {
        "input": 60.00,
        "output": 120.00
    },
    "gpt-3.5-turbo": {
        "input": 0.50,
        "output": 1.50
    },
    "gpt-3.5-turbo-instruct": {
        "input": 1.50,
        "output": 2.00
    },
    "gpt-3.5-turbo-16k-0613": {
        "input": 3.00,
        "output": 4.00
    },
    "gpt-4o-mini": {
        "input": 0.15,
        "output": 0.60
    },
    "o1": {
        "input": 15.00,
        "output": 60.00
    },
    "o1-pro": {
        "input": 150.00,
        "output": 600.00
    },
    "o1-mini": {
        "input": 1.10,
        "output": 4.40
    },
    "o3-mini": {
        "input": 1.10,
        "output": 4.40
    },
    "chatgpt-4o-latest": {
        "input": 5.00,
        "output": 15.00
    },
    "text-embedding-3-small": {
        "input": 0.02,
        "output": None
    },
    "text-embedding-3-large": {
        "input": 0.13,
        "output": None
    },
    "text-embedding-ada-002": {
        "input": 0.10,
        "output": None
    },
    "davinci-002": {
        "input": 2.00,
        "output": 2.00
    },
    "babbage-002": {
        "input": 0.40,
        "output": 0.40
    }
}

def _calc_cost(x: int, cost_per_1M: float):
    if cost_per_1M is None:
        return 0
    else:
        return (x / 10**6) * cost_per_1M

def calculate_cost(prompt: str, data: str, output: str, model: str) -> Optional[float]:
    # Initialize the tokenizer for the GPT model
    if model not in MODEL_USAGE_COSTS_USD_PER_MILLION_TOKENS:
        logger.error(f"Model {model} not found in usage costs.")
        return

    if model not in tiktoken.model.MODEL_PREFIX_TO_ENCODING.keys() or model not in tiktoken.model.MODEL_TO_ENCODING.keys():
        logger.error(f"Model {model} not found in tiktoken.")
        return

    tokenizer = tiktoken.encoding_for_model(model)

    # Counting the total tokens for request and response separately
    input_tokens = len(tokenizer.encode(prompt + data))
    output_tokens = len(tokenizer.encode(str(output)))

    # Actual costs per 1 million tokens
    cost_per_1M_input_tokens = MODEL_USAGE_COSTS_USD_PER_MILLION_TOKENS[model]["input"]
    cost_per_1M_output_tokens = MODEL_USAGE_COSTS_USD_PER_MILLION_TOKENS[model]["output"]

    # Calculate the cost, then add them.
    output_cost = _calc_cost(output_tokens, cost_per_1M_output_tokens)
    input_cost = _calc_cost(input_tokens, cost_per_1M_input_tokens)
    total_cost = round(input_cost + output_cost, 2) if total_cost > 0 else 0 
    logger.debug(f"Total Cost: {total_cost} Cost breakdown:\n'input_tokens': {input_tokens}\n'output_tokens': {output_tokens}\n'input_cost': {input_cost}, 'output_cost': {output_cost}")
    return total_cost


class LLMOutput(BaseModel):
    llm_response: str
    system_prompt: str
    user_message: str
    context_used: int
    response_parser: Callable

    _configs: Configs = PrivateAttr(default=configs)

    @computed_field # type: ignore[prop-decorator]
    @property
    def cost(self) -> float:
        if self.llm_response is not None:
            return calculate_cost(self.system_prompt, self.user_message, self.llm_response, self._configs.OPENAI_MODEL)
        else: 
            return 0

    @computed_field # type: ignore[prop-decorator]
    @property
    def parsed_llm_response(self) -> Any:
        return self.llm_response_parser(self.llm_response)


class LLMInput(BaseModel):
    client: BaseModel
    user_message: str
    system_prompt: str = "You are a helpful assistant."
    use_rag: bool = False
    max_tokens: int = 4096
    temperature: float = 0 # Deterministic output
    response_parser: Callable = lambda x: x # This should be a partial function.
    format_dict: Optional[dict] = None

    _configs: Configs = PrivateAttr(default=configs)

    @computed_field # type: ignore[prop-decorator]
    @property
    def response(self) -> Optional[LLMOutput]:
        try:
            _response = self.client.chat.completions.create(
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
            return LLMOutput(
                response=_response.choices[0].message.content.strip(),
                system_prompt=self.system_prompt.strip(),
                user_message=self.user_message,
                context_used=_response.usage.total_tokens,
                model=self._configs.OPENAI_MODEL,
                response_parser=self.llm_response_parser,
            )
        else:
            return "No response generated. Please try again."

    @computed_field # type: ignore[prop-decorator]
    @property
    def embedding(self) -> List[float]:
        """
        Generate an embedding for the user's message.
        
        Args:
            text: Text string to generate an embedding for
            
        Returns:
            Embedding vector
        """
        try:
            embeddings = self.client.embeddings.create(
                input=self.user_message,
                model=self._configs.OPENAI_EMBEDDING_MODEL
            )
        except Exception as e:
            logger.error(f"{type(e)} generating embedding: {e}")
            return []

        if embeddings.data[0].embedding:
            return embeddings.data[0].embedding
        else:
            logger.error("No embedding generated. Please try again.")
            return []


class LLMEngine(BaseModel):
    pass


class OpenAIClient:
    """
    Client for OpenAI API integration with RAG capabilities for the American Law dataset.
    Handles embeddings integration and semantic search against the law database.
    """
    
    def __init__(
        self, 
        api_key: str = None,
        model: str = "gpt-4o",
        embedding_model: str = "text-embedding-3-small",
        embedding_dimensions: int = 1536,
        temperature: float = 0.2,
        max_tokens: int = 4096,
        configs: Optional[Configs] = None
    ):
        """
        Initialize the OpenAI client for American Law dataset RAG.
        
        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env variable)
            model: OpenAI model to use for completion/chat
            embedding_model: OpenAI model to use for embeddings
            embedding_dimensions: Dimensions of the embedding vectors
            temperature: Temperature setting for LLM responses
            max_tokens: Maximum tokens for LLM responses
            data_path: Path to the American Law dataset files
            db_path: Path to the SQLite database
        """
        self.configs = configs

        self.api_key = api_key
        if not self.api_key:
            raise ValueError("OpenAI API key must be provided either as an argument or in the OPENAI_API_KEY environment variable")
        
        self.client = OpenAI(api_key=self.api_key)
        self.model = model
        self.embedding_model = embedding_model
        self.embedding_dimensions = embedding_dimensions
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        # Set data paths
        self.data_path = configs.AMERICAN_LAW_DATA_DIR
        self.db_path = configs.AMERICAN_LAW_DB_PATH

        logger.info(f"Initialized OpenAI client: LLM model: {model}, embedding model: {embedding_model}")


    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
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
            processed_texts = [text.strip('\n').strip() for text in texts]
            processed_texts = [text if text else " " for text in processed_texts]

            response = self.client.embeddings.create(
                input=processed_texts,
                model=self.embedding_model
            )
            
            # Extract the embedding vectors from the response
            embeddings = [data.embedding for data in response.data]
            return embeddings
            
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise


    def get_single_embedding(self, text: str) -> List[float]:
        """
        Generate an embedding for a single text input.
        
        Args:
            text: Text string to generate an embedding for
            
        Returns:
            Embedding vector
        """
        embeddings = self.get_embeddings([text])
        return embeddings[0] if embeddings[0] is not None else []


    def search_embeddings(
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
        query_embedding = self.get_single_embedding(query)
        
        results = []

        try:
            # Connect to the database
            conn = duckdb.connect(self.db_path, read_only=True)
            
            # Create the SQL query
            sql_query = """
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
                DOT_PRODUCT(e.embedding, ARRAY(SELECT vec FROM query_embedding)) / 
                (SQRT(DOT_PRODUCT(e.embedding, e.embedding)) * 
                 SQRT(DOT_PRODUCT(ARRAY(SELECT vec FROM query_embedding), 
                          ARRAY(SELECT vec FROM query_embedding)))) as similarity_score 
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
                
            # Execute the query with the embedding as parameter
            results_list = conn.execute(sql_query, [query_embedding]).fetchdf().to_dict('records')
            
            # Convert to list of dictionaries
            results = []
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

            conn.close()
            return results
            
        except Exception as e:
            logger.error(f"Error searching embeddings with DuckDB: {e}")
            return []
        
    def query_database(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Query the database for relevant laws using DuckDB.
        
        Args:
            query: Search query
            limit: Maximum number of results to return
            
        Returns:
            List of matching law records
        """
        try:
            # Connect to the database - DuckDB can also connect to SQLite files
            with duckdb.connect(self.db_path, read_only=True) as conn:
                # Simple text search
                sql_query = f"""
                    SELECT id, cid, title, chapter, place_name, state_name, date, 
                        bluebook_citation, content
                    FROM citations
                    WHERE lower(search_text) LIKE '%{query.lower()}%'
                    ORDER BY place_name, title
                    LIMIT {limit}
                """
                # Execute query and fetch results
                results = conn.execute(sql_query).fetchdf().to_dict('records')
            return results
        except Exception as e:
            logger.error(f"Error querying database with DuckDB: {e}")
            return []


    def generate_rag_response(
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
            context_docs = self.search_embeddings(query, top_k=top_k)
        else:
            # Use database text search as fallback
            context_docs = self.query_database(query, limit=top_k)

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
        prompt: Prompt = load_prompt_from_yaml(
            "generate_rag_response", 
            self.configs, 
            query=query, 
            context=context_text
        )
        try:
            output = LLMInput(
                client=self.client,
                user_message=prompt.user_prompt.content,
                system_prompt=prompt.system_prompt.content,
                max_tokens=prompt.settings.max_tokens,
                temperature=prompt.settings.temperature,
            )
            output = output.response

            # Append the citations
            generated_response += f"\n\n{references.strip()}" if output is not None else "No response generated. Please try again."

            return {
                "query": query,
                "response": generated_response,
                "context_used": [doc.get('bluebook_citation', 'No citation') for doc in context_docs],
                "model_used": self.model,
                "total_tokens": output.usage.total_tokens
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