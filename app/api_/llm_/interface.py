"""
API interface for the LLM integration with the American Law dataset.
Provides access to OpenAI-powered legal research and RAG components.
"""
import os
from pathlib import Path
import re
from typing import Dict, Any, List, Optional


from pydantic import BaseModel


from logger import logger
from configs import configs, Configs
from .dependencies.openai_client import OpenAIClient, LLMInput, LLMOutput
from .embeddings_manager import EmbeddingsManager


def _validate_and_correct_sql_query_string(sql_query: str, fix_broken_queries: bool = True) -> Optional[str]:
    """
    Validate and correct a SQL query string.
    
    Args:
        sql_query: The SQL query string to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    logger.debug(f"Validating SQL query: {sql_query}")

    # Check if it's an empty string
    if not sql_query.strip():
        logger.warning("Empty SQL query string provided.")
        return None
    
    # Check if it any markdown patterns.
    if "```sql" in sql_query or "```" in sql_query:
        logger.warning("SQL query contains markdown code blocks.")
        if fix_broken_queries:
            # Remove markdown code blocks
            sql_query = sql_query.replace("```sql", "").replace("```", "").strip()
            logger.info("Removed markdown code blocks from SQL query.")
            logger.debug(f"Cleaned SQL query after markdown removal: {sql_query}")
        else:
            logger.error("SQL query contains markdown code blocks and fix_broken_queries is False.")
            return None

    # Check if it's got SELECT in it
    if not re.search(r'^\s*SELECT\s', sql_query, re.IGNORECASE):
        logger.warning("SQL query does not start with SELECT.")
        return None

    # Check if it's got doubled elements like SELECT SELECT or LIMIT 10 LIMIT 20
    sql_query = re.sub(r'\b(SELECT|LIMIT)\s+\1', r'\1', sql_query, flags=re.IGNORECASE).strip()
    logger.debug(f"Cleaned SQL query after doubled elements removal: {sql_query}")
    return sql_query if sql_query else None


class LLMInterface:
    """
    Interface for interacting with OpenAI LLM capabilities for the American Law dataset.
    Provides a simplified API for accessing embeddings search and RAG functionality.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        configs: Optional[Configs] = None,
    ):
        """
        Initialize the LLM interface.
        
        Args:
            api_key: OpenAI API key
            model: OpenAI model to use
            embedding_model: OpenAI embedding model to use
            data_path: Path to the American Law dataset files
            db_path: Path to the SQLite database
        """
        self.configs = configs

        self.api_key: str = api_key or os.environ.get("OPENAI_API_KEY")
        self.data_path: Path = configs.AMERICAN_LAW_DATA_DIR
        self.db_path: Path = configs.AMERICAN_LAW_DB_PATH
        self.model: str = configs.OPENAI_MODEL
        self.embedding_model: str = configs.OPENAI_EMBEDDING_MODEL

        # Initialize clients
        self.openai_client: OpenAIClient = OpenAIClient(
            api_key=self.api_key,
            model=self.model,
            embedding_model=self.embedding_model,
            configs=self.configs
        )
        logger.info(f"Initialized LLM interface with model: {self.model}")
    
        self.embeddings_manager = EmbeddingsManager(configs=self.configs)
        logger.info(f"Initialized Embeddings Manager with model: {self.embedding_model}")


    def ask_question(
        self,
        query: str,
        use_rag: bool = True,
        use_embeddings: bool = True,
        document_limit: int = 5,
        custom_system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Ask a question about American law.
        
        Args:
            query: User's question
            use_rag: Whether to use Retrieval Augmented Generation
            use_embeddings: Whether to use embeddings search for RAG
            document_limit: Maximum number of context documents to include
            custom_system_prompt: Custom system prompt for LLM
            
        Returns:
            Dictionary with the generated response and additional information
        """
        logger.info(f"Processing question: {query}")
        
        if use_rag:
            # Use RAG to generate a response with context
            response = self.openai_client.generate_rag_response(
                query=query,
                use_embeddings=use_embeddings,
                document_limit=document_limit,
                system_prompt=custom_system_prompt
            )
        else:
            # Use OpenAI directly without RAG context
            try:
                chat_response = self.openai_client.client.chat.completions.create(
                    model=self.openai_client.model,
                    temperature=self.openai_client.temperature,
                    max_tokens=self.openai_client.max_tokens,
                    messages=[
                        {"role": "system", "content": custom_system_prompt or "You are a legal research assistant specializing in American municipal and county laws."},
                        {"role": "user", "content": query}
                    ]
                )
                
                response = {
                    "query": query,
                    "response": chat_response.choices[0].message.content,
                    "context_used": [],
                    "model_used": self.openai_client.model,
                    "total_tokens": chat_response.usage.total_tokens
                }
            except Exception as e:
                logger.error(f"Error in direct LLM query: {e}")
                response = {
                    "query": query,
                    "response": f"Error generating response: {str(e)}",
                    "context_used": [],
                    "model_used": self.openai_client.model,
                    "error": str(e)
                }
        
        return response


    def _generic_response(self, message: str = None, system_prompt: str = None) -> str:
        return self.openai_client.client.chat.completions.create(
            model="gpt4o",
            messages=[
                {"role": "system", "content": system_prompt.strip()},
                {"role": "user", "content": message.strip()}
            ],
            max_tokens=1024,
            temperature=0 # Deterministic output
        )


    def determine_user_intent(self, message: str) -> str:
        """
        Determine the user's intent based on the query.
        
        Args:
            query: User's input query
            
        Returns:
            Intent type as a string
        """
        # Make sure the response isn't anything nasty.
        response = self.openai_client.client.moderations.create(
            model="omni-moderation-latest",
            input=message,
        )
        if response.results[0].flagged:
            logger.warning(f"Message flagged by moderation: {message}")
            return "OTHER"
 
        logger.debug(f"Entering Determine Intent")
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
            response = self.openai_client.client.chat.completions.create(
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
                logger.debug(f"Determine intent content: '{choice_content}'")

                if "```" in choice_content:
                    choice_content = choice_content.split("```")[1].strip()
                
                logger.debug(f"Determine intent content after stripping: '{choice_content}'")

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
                    logger.error("Response did not match expected intent categories")
                    logger.debug(f"Response content: {choice_content}")
                    return "OTHER"  # Default to search as fallback
            else:
                logger.error("No valid choice in the GPT response")
                return "OTHER"  # Default fallback
        except Exception as e:
            logger.error(f"Error in determine_intent_basic: {e}", exc_info=True)
            return "OTHER"  # Fallback in case of exception


    def search_embeddings(
        self,
        query: str,
        file_id: Optional[str] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant documents using embeddings.
        
        Args:
            query: Search query
            file_id: Optional file ID to limit search to
            top_k: Number of top results to return
            
        Returns:
            List of relevant documents with similarity scores
        """
        # Generate embedding for the query
        query_embedding = self.openai_client.get_single_embedding(query)
        
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
    
    def generate_citation_answer(
        self,
        query: str,
        citation_codes: List[str],
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate an answer to a question with specific citation references.
        
        Args:
            query: User's question
            citation_codes: List of citation codes to use as context
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
            response = self.openai_client.client.chat.completions.create(
                model=self.openai_client.model,
                temperature=self.openai_client.temperature,
                max_tokens=self.openai_client.max_tokens,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Question: {query}\n\n{context_text}"}
                ]
            )
            
            return {
                "query": query,
                "response": response.choices[0].message.content,
                "context_used": [doc.get('bluebook_citation', 'No citation') for doc in context_docs],
                "model_used": self.openai_client.model,
                "total_tokens": response.usage.total_tokens
            }
            
        except Exception as e:
            logger.error(f"Error generating citation answer: {e}")
            return {
                "query": query,
                "response": f"Error generating response: {str(e)}",
                "context_used": [doc.get('bluebook_citation', 'No citation') for doc in context_docs],
                "model_used": self.openai_client.model,
                "error": str(e)
            }
    
    def query_to_sql(
        self,
        query: str,
        custom_system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Convert a natural language query into a PostgreSQL command for searching the American Law database.
        
        Args:
            query: User's plaintext query
            custom_system_prompt: Optional custom system prompt for the SQL generation
            
        Returns:
            Dictionary with the generated SQL query and additional information
        """
        logger.info(f"Converting query to SQL: {query}")
        
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
6. Include ORDER BY clauses for relevance
7. When searching text in the html table, use the html field
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
            response = self.openai_client.client.chat.completions.create(
                model=self.openai_client.model,
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
                logger.warning(f"Generated SQL doesn't contain SELECT statement: {sql_query}")
                sql_query = f"-- Warning: This may not be a valid SQL query\n{sql_query}"

            sql_query = _validate_and_correct_sql_query_string(sql_query)
            if sql_query is None:
                logger.error("SQL query validation failed or returned empty. The LLM probably messed up.")
            else:
                logger.info(f"SQL query validated successfully")

            output_dict = {
                "original_query": query,
                "sql_query": sql_query if sql_query else "-- Error: No valid SQL query generated",
                "model_used": self.openai_client.model,
                "total_tokens": response.usage.total_tokens,
                "error": None if sql_query else "Invalid SQL query generated"
            }
            return output_dict
        
        except Exception as e:
            logger.error(f"Error converting query to SQL: {e}")
            return {
                "original_query": query,
                "sql_query": f"-- Error generating SQL query: {str(e)}",
                "error": str(e)
            }