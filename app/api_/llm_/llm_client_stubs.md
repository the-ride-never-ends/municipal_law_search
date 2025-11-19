# Function and Class stubs from '/home/kylerose1946/american_law_search/app/api_/llm_/llm_client.py'

Files last updated: 1763266085.7130241

Stub file last updated: 2025-11-16 20:09:33

## LLMClient

```python
class LLMClient:
    """
    Asynchronous client for LLM API integration with RAG capabilities.
Handles embeddings integration and semantic search against the law database.
    """
```
* **Async:** False
* **Method:** False
* **Class:** N/A

## AsyncLLMInput

```python
class AsyncLLMInput(BaseModel):
```
* **Async:** False
* **Method:** False
* **Class:** N/A

## AsyncLLMOutput

```python
class AsyncLLMOutput(BaseModel):
```
* **Async:** False
* **Method:** False
* **Class:** N/A

## LLMOutput

```python
class LLMOutput(BaseModel):
```
* **Async:** False
* **Method:** False
* **Class:** N/A

## OpenAiClient

```python
class OpenAiClient:
```
* **Async:** False
* **Method:** False
* **Class:** N/A

## __init__

```python
def __init__(self, resources: dict = None, configs: Configs = None):
    """
    Initialize the OpenAI client for American Law dataset RAG.

Args:
    resources: Dictionary of resources for embeddings and database queries
    configs: Configuration object
    """
```
* **Async:** False
* **Method:** True
* **Class:** OpenAiClient

## __init__

```python
def __init__(self, resources: dict = None, configs: Configs = None, api_key: str = None, model: str = "gpt-4o", embedding_model: str = "text-embedding-3-small", embedding_dimensions: int = 1536, temperature: float = 0.2, max_tokens: int = 4096):
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
```
* **Async:** False
* **Method:** True
* **Class:** LLMClient

## _get_embedding

```python
async def _get_embedding(self) -> List[float]:
    """
    Generate an embedding of the user's message.

Returns:
    Embedding vector
    """
```
* **Async:** True
* **Method:** True
* **Class:** AsyncLLMInput

## _use_rag

```python
async def _use_rag(self, user_message: str, system_message: str) -> Optional[tuple[str, str]]:
    """
    Use RAG to find relevant documents and generate a response.

Args:
    user_message: The user's message
    system_message: The system prompt
    """
```
* **Async:** True
* **Method:** True
* **Class:** AsyncLLMInput

## async_get_embeddings

```python
async def async_get_embeddings(self, texts: List[str]) -> List[List[float]]:
```
* **Async:** True
* **Method:** True
* **Class:** OpenAiClient

## async_get_response

```python
async def async_get_response(self, user_message: str = None, system_prompt: str = None, *, return_raw_response: bool = False, model: Optional[str] = None, temperature: Optional[float] = None, max_tokens: Optional[int] = None) -> str:
    """
            
    """
```
* **Async:** True
* **Method:** True
* **Class:** OpenAiClient

## calculate_llm_api_cost

```python
def calculate_llm_api_cost(prompt: str, data: str, out: str, model: str) -> Optional[int]:
```
* **Async:** False
* **Method:** False
* **Class:** N/A

## cost

```python
@computed_field
@property
def cost(self) -> float:
```
* **Async:** False
* **Method:** True
* **Class:** AsyncLLMOutput

## cost

```python
@computed_field
@property
def cost(self) -> float:
```
* **Async:** False
* **Method:** True
* **Class:** LLMOutput

## execute_sql_query

```python
def execute_sql_query(self, query: str, raise_on_e: bool = False) -> Optional[List[Dict[str, Any]]]:
```
* **Async:** False
* **Method:** True
* **Class:** LLMClient

## generate_rag_response

```python
async def generate_rag_response(self, query: str, use_embeddings: bool = True, top_k: int = 5, system_prompt: Optional[str] = None) -> Dict[str, Any]:
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
```
* **Async:** True
* **Method:** True
* **Class:** LLMClient

## get_embeddings

```python
def get_embeddings(self, texts: List[str]) -> List[List[float]]:
```
* **Async:** False
* **Method:** True
* **Class:** OpenAiClient

## get_embeddings

```python
async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
    """
    Generate embeddings for a list of text inputs using OpenAI's embedding model.

Args:
    texts: List of text strings to generate embeddings for
    
Returns:
    List of embedding vectors
    """
```
* **Async:** True
* **Method:** True
* **Class:** LLMClient

## get_parsed_response

```python
async def get_parsed_response(self) -> Any:
    """
    Asynchronously parse the response using the provided parser
    """
```
* **Async:** True
* **Method:** True
* **Class:** AsyncLLMOutput

## get_response

```python
async def get_response(self) -> Optional[Any]:
```
* **Async:** True
* **Method:** True
* **Class:** AsyncLLMInput

## get_response

```python
def get_response(self, user_message: str = None, system_prompt: str = None, *, return_raw_response: bool = False, model: Optional[str] = None, temperature: Optional[float] = None, max_tokens: Optional[int] = None) -> str:
    """
            
    """
```
* **Async:** False
* **Method:** True
* **Class:** OpenAiClient

## get_single_embedding

```python
async def get_single_embedding(self, text: str) -> List[float]:
    """
    Generate an embedding for a single text input.

Args:
    text: Text string to generate an embedding for
    
Returns:
    Embedding vector
    """
```
* **Async:** True
* **Method:** True
* **Class:** LLMClient

## query_database

```python
async def query_database(self, query: str, limit: int = None) -> List[Dict[str, Any]]:
    """
    Query the database for relevant laws.

Args:
    query: Search query
    limit: Maximum number of results to return
    
Returns:
    List of matching law records
    """
```
* **Async:** True
* **Method:** True
* **Class:** LLMClient

## response

```python
def response(self) -> Any:
```
* **Async:** False
* **Method:** True
* **Class:** LLMOutput

## search_embeddings

```python
async def search_embeddings(self, query: str, gnis: Optional[str] = None, top_k: int = 5) -> List[Dict[str, Any]]:
    """
    Search for relevant documents using embeddings.

Args:
    query: Search query
    gnis: Optional file ID to limit search to
    top_k: Number of top results to return
    
Returns:
    List of relevant documents with similarity scores
    """
```
* **Async:** True
* **Method:** True
* **Class:** LLMClient
