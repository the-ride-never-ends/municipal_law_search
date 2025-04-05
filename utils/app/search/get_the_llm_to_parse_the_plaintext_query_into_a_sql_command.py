from typing import Optional, Union


from chatbot.api.llm.interface import LLMInterface
from chatbot.api.llm.async_interface import AsyncLLMInterface
from logger import logger


async def get_the_llm_to_parse_the_plaintext_query_into_a_sql_command(
        search_query: str, 
        use_llm: bool = True, 
        per_page: int = 20, 
        offset: int = 0,
        llm_interface: Union[LLMInterface, AsyncLLMInterface] = None
        ) -> Optional[str]:
    """
    Converts a plaintext search query into a SQL command using an LLM asynchronously.
    This function takes a plaintext search query and uses an LLM to generate a SQL 
    command. It also ensures that the generated SQL query includes pagination parameters 
    (`LIMIT` and `OFFSET`) if they are not already present.

    Args:
        search_query (str): The plaintext search query to be converted into a SQL command.
        use_llm (bool, optional): A flag to enable or disable the use of the LLM for query 
            conversion. Defaults to True.
        per_page (int, optional): The number of results to return per page. Defaults to 20.
        offset (int, optional): The number of results to skip before starting to return rows. 
            Defaults to 0.
        llm_interface (Union[LLMInterface, AsyncLLMInterface], optional): The LLM interface to use. Defaults to None.
    Returns:
        Optional[str]: The generated SQL query string with pagination applied, or None if the 
        query could not be generated.
    """
    # Get the LLM to parse the plaintext query into a SQL command.
    sql_query = None
    if use_llm and llm_interface and search_query.strip():
        logger.info(f"Converting query to SQL: {search_query}")
        
        # Check if we're using the async interface
        if isinstance(llm_interface, AsyncLLMInterface):
            sql_result = await llm_interface.query_to_sql(search_query)
        else:
            # For backward compatibility with the sync interface
            sql_result = llm_interface.query_to_sql(search_query)
            
        sql_query: str = sql_result.get("sql_query")

        # Add pagination to the generated SQL if it doesn't already have it
        if sql_query and "LIMIT" not in sql_query.upper():
            if ";" in sql_query:
                sql_query = sql_query.replace(";", f" LIMIT {per_page} OFFSET {offset};")
            else:
                sql_query = f"{sql_query} LIMIT {per_page} OFFSET {offset}"
        
        logger.info(f"Generated SQL query: {sql_query}")
    return sql_query