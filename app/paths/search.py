# -*- coding: utf-8 -*-
"""
API endpoint for searching the American law database using natural language
"""
from __future__ import annotations

from datetime import datetime
import functools
import logging
import os
import sys
import traceback
from typing import Any, AsyncGenerator, Callable, Coroutine, Optional, TypeVar


import duckdb
from fastapi import HTTPException, Query
from pydantic import BaseModel, PositiveInt

sys.path.append("..")  # Add the parent directory to the path

from logger import logger as  module_logger
from configs import configs, Configs


from llm import get_llm, AsyncLLMInterface
from schemas.search_response import SearchResponse
from utils.app.search.format_initial_sql_return_from_search import format_initial_sql_return_from_search
from utils.app.search.get_embedding_and_calculate_cosine_similarity import (
    get_embedding_and_calculate_cosine_similarity
)
from utils.app.get_html_for_this_citation import get_html_for_this_citation
from utils.app._get_a_database_connection import get_a_database_connection

from utils.common import get_cid
from utils.common.run_in_process_pool import async_run_in_process_pool


from utils.app.search import (
    close_database_connection,
    close_database_cursor,
    estimate_the_total_count_without_pagination,
    format_initial_sql_return_from_search,
    get_cached_query_results,
    get_data_from_sql,
    get_database_cursor,
    get_embedding_cids,
    LLMSqlOutput,
    sort_and_save_search_query_results,
    turn_english_into_sql,
    make_search_query_table_if_it_doesnt_exist,
)



class SearchFunction:
    """
    Core class for performing natural language searches on the American law database.
    
    This class orchestrates the entire search process, including query transformation,
    database access, embedding similarity calculations, and result caching. It uses
    a language model to convert natural language queries into SQL and supports both
    cached search responses and live searches with streaming results.
    
    The search process involves several steps:
    1. Check for cached results from previous similar queries
    2. Determine user intent using LLM
    3. Convert natural language to SQL using LLM
    4. Execute SQL query with pagination
    5. Calculate embedding similarity scores for semantic ranking
    6. Retrieve HTML content for results
    7. Cache results for future use
    
    This class is designed to be used as an async context manager to ensure proper
    resource cleanup.
    
    Attributes:
        search_query: The natural language search query
        llm: The language model interface for query translation
        resources: Dictionary of utility functions and resources
        configs: Application configuration
        query_table_embedding_cids: List of content IDs with similarity scores
        cid_set: Set of content IDs to avoid duplicates
        html_set: Set of HTML contents to avoid duplicates
        total: Total number of results
        class_connection: Database connection
        class_cursor: Database cursor
        search_query_cid: Content ID for the search query
        search_query_embedding: Vector embedding of the search query
    """
    # TODO Abstract-out duckdb

    def __init__(self, 
                 search_query: str = None, 
                 resources: dict[str, Callable] = None, 
                 configs: Configs = None
                ):
        """
        Initialize the SearchFunction with necessary dependencies.
        
        This constructor sets up all the required resources, initializes the database
        connection, and prepares the search query. It also validates the input parameters
        and creates the search query content ID.
        
        Args:
            search_query: The natural language search query
            llm: The language model interface for query translation
            resources: Dictionary of utility functions and resources
            configs: Application configuration
            
        Raises:
            ValueError: If search_query is None or empty, or if llm is None
        """
        self.resources = resources
        self.configs = configs

        self.search_query: str = search_query.lower()
        self.llm: AsyncLLMInterface = self.resources['get_llm']()
        self.logger: logging.Logger = self.resources['logger']

        if not self.search_query:
            raise ValueError("Search query cannot be None or empty.")
        if not self.llm:
            raise ValueError("LLM cannot be None.")
        if not self.logger:
            raise ValueError("Logger cannot be None.")

        # Define initial variable states
        self.query_table_embedding_cids: list[str]    = []
        self.cid_set:                    set[str]     = set()
        self.html_set:                   set[str]     = set()
        self.total:                      PositiveInt  = 0

        self.class_connection = None
        self.class_cursor = None
        self.search_query_cid:       str           = None
        self.search_query_embedding: list[float]   = None
        self.offset:                 PositiveInt   = None

        # Get the classes functions.
        ## Sync
        #self._make_search_query_table_if_it_doesnt_exist:   Callable = self.resources['make_search_query_table_if_it_doesnt_exist']
        self._get_a_database_connection:                     Callable = self.resources['get_a_database_connection']
        self._get_database_cursor:                           Callable = self.resources['get_database_cursor']
        self._get_data_from_sql:                             Callable = self.resources['get_data_from_sql']
        self._get_cached_query_results:                      Callable = self.resources['get_cached_query_results']
        self._get_cid:                                       Callable = self.resources['get_cid']
        self._get_html_for_this_citation:                    Callable = self.resources['get_html_for_this_citation']
        self._sort_and_save_search_query_results:            Callable = self.resources['sort_and_save_search_query_results']
        self._format_initial_sql_return_from_search:         Callable = self.resources['format_initial_sql_return_from_search']
        self._estimate_the_total_count_without_pagination:   Callable = self.resources['estimate_the_total_count_without_pagination']
        self._close_database_connection:                     Callable = self.resources['close_database_connection']
        self._close_database_cursor:                         Callable = self.resources['close_database_cursor']
        self._get_embedding_and_calculate_cosine_similarity: Callable = self.resources['get_embedding_and_calculate_cosine_similarity']
        # Async
        self._async_run_in_process_pool:                     Coroutine = self.resources['async_run_in_process_pool']
        self._get_single_embedding:                          Coroutine = self.resources['get_single_embedding']
        self._turn_english_into_sql:                         Coroutine = self.resources['turn_english_into_sql']
        self._determine_user_intent:                         Coroutine = self.resources['determine_user_intent']
        # Schemas
        self._LLMSqlOutput:                                  BaseModel  = self.resources['LLMSqlOutput'] 

        # Run these start up functions
        #self._make_search_query_table_if_it_doesnt_exist()


        self.class_connection = self._get_a_database_connection()
        self.class_cursor = self._get_database_cursor(self.class_connection)
        
        self.search_query_cid = self._get_cid(search_query)

    async def __aenter__(self) -> 'SearchFunction':
        """
        Async context manager entry point.

        Returns:
            The SearchFunction instance
        """
        self.search_query_embedding = await self._get_single_embedding(self.search_query)
        return self


    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        """
        Async context manager exit point.

        Ensures all database resources are properly closed when the context is exited,
        even if an exception occurred.

        Args:
            exc_type: The exception type, if an exception was raised in the context
            exc_value: The exception value, if an exception was raised in the context
            traceback: The traceback, if an exception was raised in the context

        Returns:
            None
        """
        self.close_cursor_and_connection()
        return


    def close_cursor_and_connection(self) -> None:
        """Closes the database cursor and connection."""
        if self.class_cursor:
            self._close_database_cursor(self.class_cursor)
        if self.class_connection:
            self._close_database_connection(self.class_connection)


    def get_data_from_sql(self, cursor, return_a: str = 'dict', sql_query: str = None, how_many: int = None) -> list[dict[str, Any]]:
        """
        Execute a SQL query and return the results in the specified format.

        Args:
            cursor: The database cursor to use for executing the query
            return_a: The format to return results in ('dict', 'tuple', or 'df')
            sql_query: The SQL query to execute
            how_many: How many results to return (for 'tuple' format)
            
        Returns:
            List of dictionaries, list of tuples, or a pandas DataFrame, depending on return_a
        """
        return self._get_data_from_sql(cursor, return_a=return_a, sql_query=sql_query, how_many=how_many)


    def estimate_the_total_count_without_pagination(self, sql_query: str) -> int:
        """
        Estimate the total count of records that would be returned by a SQL query.
        This is used to determine the total number of pages for pagination and 
        to provide count information to the client.

        Args:
            sql_query: The SQL query whose results we want to count

        Returns:
            int: Total number of records that would be returned by the query
        """
        # First, estimate the total count without pagination
        count_query = f"SELECT COUNT(*) AS total FROM ({sql_query}) as subquery"
        self._estimate_the_total_count_without_pagination(self.class_cursor, count_query)
        self.class_cursor.execute(count_query)
        total: int = self.class_cursor.fetchone()[0]
        self.logger.info(f"Total results from SQL query: {total}")
        return total


    def execute_the_actual_query_with_pagination(self, sql_query: str) -> list[dict[str, Any]]:
        """
        Executes the SQL query with pagination and formats the initial results.

        This method executes the given SQL query using the class cursor,
        processes the results to avoid duplicates, and formats them using the
        _format_initial_sql_return_from_search utility.

        Args:
            sql_query: The SQL query to execute

        Returns:
            list[dict]: Initial formatted results from the SQL query
        """
        self.class_cursor.execute(sql_query)
        df_dict = self.class_cursor.fetchdf().to_dict('records')
        for row in df_dict:
            # Skip if the CID isn't there or if it's already in the set.
            if "cid" not in row.keys() or row['cid'] in self.cid_set:
                    continue
            else:
                self.logger.debug(f"Adding cid {row['cid']} to cid_set")
                self.cid_set.add(row['cid'])

                initial_results: list[dict] = [
                    self._format_initial_sql_return_from_search(row) 
                    for row in df_dict if "bluebook_cid" in row.keys()
                ]
                return initial_results


    async def execute_embedding_search(
            self, 
            initial_results: list[dict[str, Any]], 
            cumulative_results: list,
            batch_size: int = 1000
            ) -> AsyncGenerator[list[dict], None]:
        """
        Performs embedding-based similarity search and retrieves content for results.
        
        This async generator method processes the initial SQL results, calculates
        embedding similarity scores for semantic ranking, retrieves HTML content for
        matching documents, and yields incremental result updates to enable streaming.
        
        The algorithm:
        1. For each batch of content IDs from the initial results:
           a. Create a partial function for calculating cosine similarity with the query embedding
           b. Run the similarity calculations in parallel using process pools
           c. Sort the results by similarity score (highest first)
           d. Add the scored results to the query_table_embedding_cids list
           e. For each content ID in the results:
              i. Find the corresponding row in the initial results
              ii. Get the HTML content for the citation
              iii. Add the HTML to the row if not already seen
              iv. Add the expanded row to cumulative_results
           f. Yield the current cumulative_results for incremental updates
        
        Args:
            initial_results: Initial results from the SQL query
            cumulative_results: Accumulated results list to update incrementally
            
        Yields:
            list[dict]: Updated cumulative results after each batch of processing
        """
        # Get the embedding CIDs from the initial results, piece-meal.
        # NOTE TESTING at batch_size=1000
        for embedding_id_list in get_embedding_cids(initial_results, batch_size=batch_size):
            pull_list = []
            embedding_id_list: list[dict[str, str]]

            embedding_func: Callable = functools.partial(
                get_embedding_and_calculate_cosine_similarity,
                query_embedding=self.search_query_embedding,
            )

            pull_list: list[tuple[str, float]] = await get_embeddings_in_parallel(embedding_func, embedding_id_list, pull_list)

            # Order the pull list by their cosine similarity score.
            pull_list = sorted(pull_list, key=lambda x: x[1], reverse=True)
            #self.logger.debug(f"pull_list: {pull_list}: pull_list") 
            self.query_table_embedding_cids.extend(pull_list)

            for cid, _ in pull_list:
                # Find the corresponding row in the initial results
                for row_dict in initial_results:
                    if row_dict['cid'] == cid:
                        # Get the HTML content for this citation
                        html: str = self._get_html_for_this_citation(row_dict)
                        if html in self.html_set:
                            continue
                        else:
                            self.html_set.add(html)
                            row_dict['html'] = html
                            cumulative_results.append(row_dict)
                            break
            yield cumulative_results


    def sort_and_save_search_query_results(self) -> None:
        """
        Sort the results by similarity score and save the top 100 to the database.
        This allows for caching of search results for future queries that are similar.

        Returns:
            None
        """
        if self.query_table_embedding_cids:
            self._sort_and_save_search_query_results(
                search_query_cid=self.search_query_cid,
                search_query=self.search_query,
                search_query_embedding=self.search_query_embedding,
                query_table_embedding_cids=self.query_table_embedding_cids,
                total=self.total
            )

    async def turn_english_into_sql(self, page: int, per_page: int) -> str:
        """
        Convert a natural language query to a SQL query using the LLM.

        Args:
            page: The page number of results to retrieve (1-based)
            per_page: The number of results per page

        Returns:
            str: A SQL query string generated by the LLM

        Raises:
            HTTPException: If there is an error generating the SQL query or if the LLM
                          fails to produce a valid query
        """
        try:
            offset = (page - 1) * per_page
            sql_query = await self._turn_english_into_sql(
                search_query=self.search_query,
                per_page=per_page,
                offset=offset,
                llm=self.llm,
                parser=self._LLMSqlOutput
            )
        except Exception as e:
            self.logger.error(f"Error in search: {e}")
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=str(e)) from e

        if sql_query is None:
            raise HTTPException(status_code=500, detail="LLM did not generate a proper SQL query.")
        else:
            return sql_query


    def get_cached_query_results(self, page: int = 1, per_page: int = 20) -> dict[str, Any] | None:
        """
        Retrieve previously cached search results for the current query.
        
        This method checks if the current search query has been executed before and
        if its results are stored in the search_query table. If found, it returns
        the cached results with the appropriate pagination, avoiding the need for
        a full search operation.
        
        The algorithm:
        1. Call the _get_cached_query_results utility with the search query CID and pagination info
        2. Check if any cached results were found
        3. If found, log success and return the cached results
        4. If not found, log the need for a full search and return None
        5. Handle any exceptions that occur during the cache lookup
        
        Args:
            page: The page number of results to retrieve (1-based)
            per_page: The number of results per page
            
        Returns:
            dict[str, Any] | None: The cached search results if found, otherwise None
            
        Raises:
            HTTPException: If there is an error accessing the cache
        """
        try:
            cached_results = self._get_cached_query_results(
                search_query_cid=self.search_query_cid,
                page=page,
                per_page=per_page
            )
            if cached_results is not None and len(cached_results) > 0:
                self.logger.info(f"Cached results found for query '{self.search_query}'.\nReturning cached results...")
                return cached_results
            else:
                self.logger.debug(f"No cached results found for query '{self.search_query}'.\nPerforming full search...")
                return None
        except Exception as e:
            self.logger.error(f"Error in search: {e}")
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=str(e)) from e


    def format_search_response(self, cumulative_results: list[dict], page: int, per_page: int) -> dict:
        """
        Format the search results into a standardized response structure.
        
        This method takes the accumulated search results and formats them into a
        standardized SearchResponse structure. It includes the results, pagination
        information, and total counts to help the client properly display the results.
        
        The algorithm:
        1. Create a SearchResponse instance with the accumulated results and pagination info
        2. Calculate the total number of pages based on the total results and page size
        3. Log that a response is being yielded
        4. Convert the response to a dictionary for serialization
        
        Args:
            cumulative_results: List of search result dictionaries
            page: The current page number
            per_page: The number of results per page
            
        Returns:
            dict: The formatted search response as a dictionary
        """
        search_response: SearchResponse = SearchResponse(
            results=cumulative_results.copy(),
            total=self.total,
            page=page,
            per_page=per_page,
            total_pages=self._calc_total_pages(self.total, per_page)
        )
        self.logger.debug(f"Sorting search response by cosine similarity score...")
        #search_response.order_by_cosine_similarity_score()
        self.logger.debug(f"Yielding search response...")
        return search_response.model_dump()


    async def figure_out_what_the_user_wants(self, search_query: str) -> None:
        """
        Determine the user's intent from the search query and validate it.
        
        This method uses the language model to analyze the user's query and determine
        if it is a valid search request. It provides content filtering by rejecting
        inappropriate queries and ensures that the query is actually a search request,
        not some other type of request (like a command or conversation).
        
        The algorithm:
        1. Call the _determine_user_intent utility with the search query
        2. Check if a valid intent was returned
        3. Check if the query was flagged as inappropriate
        4. Check if the query is recognized as a search request
        5. Raise appropriate exceptions for invalid queries
        
        Args:
            search_query: The user's natural language query
            
        Returns:
            None
            
        Raises:
            HTTPException: If the query is inappropriate or not a search request
            ValueError: If the LLM fails to determine the intent
        """
        try:
            intent = await self._determine_user_intent(search_query)
        except Exception as e:
            self.logger.error(f"Error determining user intent: {e}")
            raise HTTPException(status_code=400, detail="Unable to determine user intent")

        if intent is None:
            raise ValueError("LLM produced None as the intent.")

        if "FLAGGED" in intent:
            self.logger.error(f"Query flagged as inappropriate: {search_query}")
            raise HTTPException(status_code=400, detail="Query flagged as inappropriate")
        
        if "SEARCH" not in intent:
            self.logger.error(f"Query not flagged as a search: {search_query}")
            raise HTTPException(status_code=400, detail="Query not flagged as a search")


    @staticmethod
    def _calc_total_pages(total: int, per_page: int) -> int:
        """
        Calculate the total number of pages based on total results and page size.
        
        This utility method calculates how many pages are needed to display all
        results given the total number of results and the number of results per page.
        It uses the ceiling division formula to ensure that any partial page at the
        end is counted as a full page.
        
        Args:
            total: The total number of results
            per_page: The number of results per page
            
        Returns:
            int: The total number of pages needed
            
        Example:
            >>> _calc_total_pages(101, 20)
            6  # 101 results with 20 per page = 5 full pages + 1 partial page
        """
        return (total + per_page - 1) // per_page


    async def search(self, page: int = 1, per_page: int = 20, batch_size: int = 1000, client_id: Optional[str] = None) -> AsyncGenerator[dict, None]:
        """
        Search for citations in the database using a natural language query.
        
        This is the main search method that coordinates the entire search process.
        It implements a multi-stage search pipeline:
        
        1. Check for cached results to avoid redundant processing
        2. Verify user intent with the LLM to ensure the query is a search request
        3. Convert natural language to SQL using the LLM
        4. Execute the SQL query and get initial results
        5. Perform embedding-based similarity ranking
        6. Stream results incrementally to enable responsive UI
        7. Cache results for future use
        8. Save the search to the user's search history
        
        The algorithm in detail:
        1. Check for cached results in the search_query table
           - If found, yield them and return early
        2. Determine user intent using the LLM
           - Reject inappropriate queries or non-search requests
        3. Convert the natural language query to SQL using the LLM
        4. Count total matching records for pagination
        5. Execute the SQL query with pagination
        6. For each batch of results:
           a. Calculate embedding similarities
           b. Retrieve HTML content
           c. Yield incremental results for streaming
        7. Close database connections
        8. Sort and cache results for future use
        9. Save the search to the user's search history if client_id is provided
        10. Yield final complete results
        
        Args:
            page: The page number of results to retrieve (1-based)
            per_page: The number of results per page
            client_id: Optional client identifier for search history tracking
            
        Yields:
            dict: Search response containing results, pagination info, and totals
            
        Notes:
            This method yields incremental updates to enable streaming results
            to the client for a more responsive user experience.
        """
        self.logger.info(f"Received request for search at {datetime.now()}")
 
        # Check if the query already exists in the search_query table
        # If they do, yield the cached results and return.
        cached_results = self.get_cached_query_results(page, per_page)
        if cached_results:
            # If we have cached results and a client ID, save to search history
            if client_id:
                from utils.app.search.save_search_history import save_search_history
                save_search_history(
                    search_query_cid=self.search_query_cid,
                    search_query=self.search_query,
                    client_id=client_id,
                    result_count=cached_results.get('total', 0)
                )
            yield cached_results
            return # Return to prevent a full embedding search.

        try:
            await self.figure_out_what_the_user_wants(self.search_query)
        except Exception as e:
            # If the user intent is not a search, we tell the user to try again.
            # TODO Implement this
            self.logger.error(f"Error determining user intent: {e}")

        sql_query = await self.turn_english_into_sql(page, per_page)

        self.total = self.estimate_the_total_count_without_pagination(sql_query)
        cumulative_results = []

        if self.total != 0:
            self.logger.debug(f"self.total: {self.total}")
            initial_results = self.execute_the_actual_query_with_pagination(sql_query)
            if initial_results:
                async for cumulative_results in self.execute_embedding_search(initial_results, cumulative_results):
                    search_response = self.format_search_response(cumulative_results, page, per_page)
                    yield search_response

        # NOTE we call close_cursor_and_connection because duckdb only allows concurrency for read-only connections.
        # TODO Create separate database for intermediate cached results.
        self.close_cursor_and_connection()

        self.sort_and_save_search_query_results()
        
        # Save search to history if client_id is provided and we have results
        if client_id and self.total > 0:
            from utils.app.search.save_search_history import save_search_history
            save_search_history(
                search_query_cid=self.search_query_cid,
                search_query=self.search_query,
                client_id=client_id,
                result_count=self.total
            )

        # Final yield with complete results
        yield {
            'results': cumulative_results,
            'total': self.total,
            'page': page,
            'per_page': per_page,
            'total_pages': self._calc_total_pages(self.total, per_page)
        }


resources = {
    'async_run_in_process_pool': async_run_in_process_pool,
    'close_database_connection': close_database_connection,
    'close_database_cursor': close_database_cursor,
    'determine_user_intent': lambda query: get_llm().determine_user_intent(query),
    'estimate_the_total_count_without_pagination': estimate_the_total_count_without_pagination,
    'format_initial_sql_return_from_search': format_initial_sql_return_from_search,
    'get_a_database_connection': get_a_database_connection,
    'get_cached_query_results': get_cached_query_results,
    'get_cid': get_cid,
    'get_data_from_sql': get_data_from_sql,
    'get_database_cursor': get_database_cursor,
    'get_embedding_and_calculate_cosine_similarity': get_embedding_and_calculate_cosine_similarity,
    'get_embedding_cids': get_embedding_cids,
    'get_html_for_this_citation': get_html_for_this_citation,
    'get_single_embedding': lambda text: get_llm().get_single_embedding(text),
    'get_llm': get_llm,
    'LLMSqlOutput': LLMSqlOutput,
    'make_search_query_table_if_it_doesnt_exist': make_search_query_table_if_it_doesnt_exist,
    'sort_and_save_search_query_results': sort_and_save_search_query_results,
    'turn_english_into_sql': turn_english_into_sql
}


def _make_cid_list(embedding_id_list: list[tuple[str, str]], cid_name: str) -> str:
    cid_list = [
        f" {cid_name} = '{cid[cid_name].strip()}'" if i == 1 else f" OR {cid_name} = '{cid[cid_name].strip()}'"
        for i, cid in enumerate(embedding_id_list, start=1)
    ]
    cid_list = ''.join(cid_list)
    return cid_list

def _pull_embeddings_from_db(embedding_id_list: list[tuple[str, str]]) -> list[dict]:

    # Create the SQL query to pull the embeddings from the database.
    query = "SELECT embedding, cid FROM embeddings WHERE" + embedding_id_list

    # Pull the embeddings from the database as a list of dictionaries.
    with duckdb.connect(configs.AMERICAN_LAW_DATA_DIR / "embeddings.db", read_only=True) as conn:
        with conn.cursor() as cursor:
            cursor.execute(query)
            return cursor.fetchdf().to_dict(orient='records')

# NOTE We need to do this to get around pickling errors.
async def get_embeddings_in_parallel(
        func: Callable, 
        embedding_id_list: list[dict[str, str]], 
        pull_list: list
        ) -> list[tuple[str, float]]:

    cid_list = _make_cid_list(embedding_id_list, "embedding_cid")

    embeddings_with_cids = _pull_embeddings_from_db(cid_list) # -> list[dict[str, str|float]]

    async for _, embedding_id in async_run_in_process_pool(func, embeddings_with_cids):
        if embedding_id is not None:
            pull_list.append(embedding_id)
    return pull_list


async def function(
    q: str = "",
    page: int = Query(1, description="Page number"),
    per_page: int = Query(20, description="Items per page"),
    client_id: str = None,
    logger: logging.Logger = module_logger,
    llm: AsyncLLMInterface = None,
) -> AsyncGenerator[dict[str, Any], None]:
    """
    API endpoint for searching the American law database using natural language.
    
    This endpoint provides a user-friendly interface for searching legal documents
    using natural language queries. It leverages a language model to understand
    the query intent, convert it to SQL, and rank results semantically.
    
    Features:
    - Natural language understanding via LLM
    - Semantic ranking with embeddings
    - Cached results for performance
    - Streaming results for responsiveness
    - Pagination support
    - Search history tracking (when client_id is provided)
    
    The algorithm:
    1. Create a SearchFunction instance with the query and dependencies
    2. Use the SearchFunction as an async context manager
    3. Stream results from the search method to the client
    4. Save the search to history if client_id is provided
    
    Args:
        q: The natural language search query
        page: The page number of results to retrieve (1-based)
        per_page: The number of results per page
        client_id: Optional client identifier for search history tracking
        
    Yields:
        dict: Search response containing results, pagination info, and totals
        
    Example:
        ```
        GET /api/search?q=zoning laws in California&page=1&per_page=20
        ```
    """
    resources['logger'] = logger
    resources['get_llm'] = get_llm if llm is None else lambda: llm
    async with SearchFunction(search_query=q, resources=resources, configs=configs) as search_func:
        async for result in search_func.search(page=page, per_page=per_page, client_id=client_id):
            yield result
