# """
# Tests for the Database class in the American Law Search application.

# This module contains unittest tests for the Database class defined in
# api_/database/database.py, focusing on testing each method for basic functionality.
# """

# import unittest
# from unittest.mock import MagicMock, patch, PropertyMock, mock_open


# import time
# import os
# from queue import Queue
# from typing import Any, Dict



# # Import the class to be tested
# try:
#     from api_.database.database import Database, try_except
# except ImportError: # Damn import errors...
#     from app.api_.database.database import Database, try_except
# from configs import configs, Configs


# def _get_mock_configs():
#     """
#     Helper function to create a mock Configs object.
#     Current Settings:
#         configs.AMERICAN_LAW_DATA_DIR = "/mock/path"
#         configs.DATABASE_CONNECTION_POOL_SIZE = 2
#         configs.DATABASE_CONNECTION_TIMEOUT = 30
#         configs.DATABASE_CONNECTION_MAX_AGE = 300
#     """
#     configs = MagicMock(spec=Configs)
#     configs.AMERICAN_LAW_DATA_DIR = "/mock/path"
#     configs.DATABASE_CONNECTION_POOL_SIZE = 2
#     configs.DATABASE_CONNECTION_TIMEOUT = 30
#     configs.DATABASE_CONNECTION_MAX_AGE = 300
#     return configs


# class TestTryExceptDecorator(unittest.TestCase):
#     """Tests for the try_except decorator."""
    
#     def test_try_except_no_exception(self):
#         """Test that try_except returns the function result when no exception occurs."""
#         @try_except(raise_=True)
#         def test_func():
#             return "success"
            
#         result = test_func()
#         self.assertEqual(result, "success")
    
#     @patch('api_.database.database.logger')
#     def test_try_except_with_exception(self, mock_logger):
#         """Test that try_except catches exceptions."""
#         @try_except(msg="Test exception",raise_=False)
#         def test_func():
#             raise ValueError("Test error")
            
#         # The function should not raise an exception
#         result = test_func()
#         self.assertIsNone(result)
#         mock_logger.exception.assert_called_once()
    
#     def test_try_except_with_reraise(self):
#         """Test that try_except re-raises exceptions when raise_ is True."""
#         @try_except(msg="Test exception", raise_=True)
#         def test_func():
#             raise ValueError("Test error")
            
#         # The function should raise an exception
#         with self.assertRaises(ValueError):
#             test_func()
    
#     @patch('api_.database.database.logger')
#     def test_try_except_specific_exception(self, mock_logger):
#         """Test that try_except only catches the specified exception type."""
#         @try_except(exception_type=ValueError, msg="Test exception", raise_=False)
#         def test_func(exc_type):
#             raise exc_type("Test error")
            
#         # Should catch ValueError
#         result = test_func(ValueError)
#         self.assertIsNone(result)
#         mock_logger.exception.assert_called_once()
        
#         # Reset the mock
#         mock_logger.reset_mock()
        
#         # Should not catch TypeError
#         with self.assertRaises(TypeError):
#             test_func(TypeError)

# class TestDatabaseInit(unittest.TestCase):
#     """Tests for the Database.__init__ method."""
    
#     def setUp(self):
#         """Set up test fixtures."""
#         self.configs = _get_mock_configs()

#         self.resources = {
#             "connect": MagicMock(return_value="connection"),
#             "close": MagicMock(),
#             "execute": MagicMock(),
#             "fetch_all": MagicMock(),
#             "fetch": MagicMock(),
#             "begin": MagicMock(),
#             "commit": MagicMock(),
#             "rollback": MagicMock(),
#             "get_cursor": MagicMock(),
#             "close_session": MagicMock(),
#         }
    
#     def test_database_init_with_resources(self):
#         """Test that Database.__init__ correctly sets up with provided resources."""
#         db = Database(configs=self.configs, resources=self.resources)
        
#         # Check that attributes were set correctly
#         self.assertEqual(db.configs, self.configs)
#         self.assertEqual(db.resources, self.resources)
#         self.assertEqual(db._connection_pool_size, self.configs.DATABASE_CONNECTION_POOL_SIZE)
#         self.assertEqual(db._connection_timeout, self.configs.DATABASE_CONNECTION_TIMEOUT)
#         self.assertEqual(db._connection_max_age, self.configs.DATABASE_CONNECTION_MAX_AGE)
        
#         # Check that the connection pool was initialized
#         self.assertEqual(db._connection_pool.qsize(), self.configs.DATABASE_CONNECTION_POOL_SIZE)
        
#         # Check that the connect method was called the right number of times
#         self.assertEqual(self.resources["connect"].call_count, 
#                         self.configs.DATABASE_CONNECTION_POOL_SIZE)
    
#     def test_database_init_with_defaults(self):
#         """Test Database.__init__ with default values."""
#         # Set only required resources
#         minimal_resources = {
#             "connect": MagicMock(return_value="connection"),
#             "close": MagicMock(),
#             "execute": MagicMock(),
#             "fetch_all": MagicMock(),
#             "fetch": MagicMock(),
#             "begin": MagicMock(),
#             "commit": MagicMock(),
#             "rollback": MagicMock(),
#             "get_cursor": MagicMock(),
#         }
        
#         db = Database(configs=self.configs, resources=minimal_resources)
        
#         # Check default values
#         self.assertIsNone(db._session)
#         self.assertIsNone(db._transaction_conn)
#         self.assertFalse(db._read_only)  # Default is False if not provided
#         self.assertEqual(db._db_path, self.configs.AMERICAN_LAW_DATA_DIR)
    
#     def test_database_init_connection_error(self):
#         """Test that exceptions during connection pool initialization are handled."""
#         # Make connect raise an exception
#         self.resources["connect"].side_effect = Exception("Connection error")
        
#         # Database initialization should raise an exception
#         with self.assertRaises(Exception):
#             Database(configs=self.configs, resources=self.resources)



# class TestDatabaseConnectionPool(unittest.TestCase):
#     """Tests for Database connection pool methods."""
    
#     def setUp(self):
#         """Set up test fixtures."""
#         self.configs = _get_mock_configs()

#         self.resources = {
#             "connect": MagicMock(return_value="connection"),
#             "close": MagicMock(),
#             "execute": MagicMock(),
#             "fetch_all": MagicMock(),
#             "fetch": MagicMock(),
#             "begin": MagicMock(),
#             "commit": MagicMock(),
#             "rollback": MagicMock(),
#             "get_cursor": MagicMock(),
#             "close_session": MagicMock(),
#         }
        
#         self.db = Database(configs=self.configs, resources=self.resources)
    
#     def test_flush_connection_pool(self):
#         """Test that _flush_connection_pool correctly closes all connections."""
#         # Verify initial pool size
#         self.assertEqual(self.db._connection_pool.qsize(), 
#                        self.configs.DATABASE_CONNECTION_POOL_SIZE)
        
#         # Flush the pool
#         self.db._flush_connection_pool()
        
#         # Check that close was called for each connection
#         self.assertEqual(self.resources["close"].call_count, 
#                        self.configs.DATABASE_CONNECTION_POOL_SIZE)
        
#         # Check that the pool is now empty
#         self.assertTrue(self.db._connection_pool.empty())
    
#     def test_init_connection_pool(self):
#         """Test that _init_connection_pool creates the correct number of connections."""
#         # First, clear the pool
#         self.db._flush_connection_pool()
#         self.resources["close"].reset_mock()
#         self.resources["connect"].reset_mock()
        
#         # Re-initialize the pool
#         self.db._init_connection_pool()
        
#         # Check that connect was called the right number of times
#         self.assertEqual(self.resources["connect"].call_count, 
#                        self.configs.DATABASE_CONNECTION_POOL_SIZE)
        
#         # Check that the pool is now full
#         self.assertEqual(self.db._connection_pool.qsize(), 
#                        self.configs.DATABASE_CONNECTION_POOL_SIZE)
    
#     def test_get_connection_from_pool(self):
#         """Test that _get_connection_from_pool returns a connection."""
#         # Get a connection from the pool
#         conn = self.db._get_connection_from_pool()
        
#         # Check that it's the expected connection
#         self.assertEqual(conn, "connection")
        
#         # Check that the pool now has one less connection
#         self.assertEqual(self.db._connection_pool.qsize(), 
#                        self.configs.DATABASE_CONNECTION_POOL_SIZE - 1)
    
#     def test_get_connection_from_empty_pool(self):
#         """Test getting connection from an empty pool reinitializes the pool."""
#         # Empty the pool
#         while not self.db._connection_pool.empty():
#             self.db._connection_pool.get()
        
#         self.resources["connect"].reset_mock()
        
#         # Get a connection - should reinitialize the pool
#         conn = self.db._get_connection_from_pool()
        
#         # Check that connect was called to reinitialize the pool
#         self.assertEqual(self.resources["connect"].call_count, 
#                        self.configs.DATABASE_CONNECTION_POOL_SIZE)
        
#         # And that we got a connection
#         self.assertEqual(conn, "connection")
    
#     def test_get_connection_pool_aged_connection(self):
#         """Test that aged connections are replaced."""
#         # Empty the pool
#         self.db._flush_connection_pool()
        
#         # Create a connection with timestamp older than max age
#         old_time = time.time() - self.configs.DATABASE_CONNECTION_MAX_AGE - 10
#         conn_info = {
#             'connection': "old_connection",
#             'created_at': old_time,
#             'last_used': old_time
#         }
#         self.db._connection_pool.put(conn_info)
        
#         self.resources["connect"].reset_mock()
#         self.resources["close"].reset_mock()
        
#         # Get the connection - should replace the aged connection
#         conn = self.db._get_connection_from_pool()
        
#         # Check that close was called for the old connection
#         self.resources["close"].assert_called_once_with("old_connection")
        
#         # Check that connect was called to create a new connection
#         self.resources["connect"].assert_called_once()
    
#     def test_return_connection_to_pool(self):
#         """Test that _return_connection_to_pool adds a connection back to the pool."""
#         # Get a connection to make space in the pool
#         conn = self.db._get_connection_from_pool()
#         initial_size = self.db._connection_pool.qsize()
        
#         # Return the connection
#         self.db._return_connection_to_pool(conn)
        
#         # Check that the pool now has one more connection
#         self.assertEqual(self.db._connection_pool.qsize(), initial_size + 1)
    
#     def test_return_connection_to_full_pool(self):
#         """Test returning a connection to a full pool closes it."""
#         # Create a full pool
#         # For this test, we'll use a small Queue we create ourselves
#         self.db._connection_pool = Queue(maxsize=1)
#         self.db._connection_pool.put({
#             'connection': "existing_connection",
#             'created_at': time.time(),
#             'last_used': time.time()
#         })
        
#         self.resources["close"].reset_mock()
        
#         # Return a connection to the full pool
#         self.db._return_connection_to_pool("new_connection")
        
#         # Check that close was called for the new connection
#         self.resources["close"].assert_called_once_with("new_connection")


# class TestDatabaseContextManagers(unittest.TestCase):
#     """Tests for Database context managers."""
    
#     def setUp(self):
#         """Set up test fixtures."""
#         self.configs = _get_mock_configs()

#         self.resources = {
#             "connect": MagicMock(return_value="connection"),
#             "close": MagicMock(),
#             "execute": MagicMock(),
#             "fetch_all": MagicMock(),
#             "fetch": MagicMock(),
#             "begin": MagicMock(),
#             "commit": MagicMock(),
#             "rollback": MagicMock(),
#             "get_cursor": MagicMock(),
#             "close_session": MagicMock(),
#         }
        
#         self.db = Database(configs=self.configs, resources=self.resources)
    
#     def test_database_context_manager(self):
#         """Test Database class as a context manager."""
#         with self.db as db:
#             # Check that the context manager returns the database
#             self.assertEqual(db, self.db)
        
#         # Check that exit closes all connections
#         self.resources["close"].assert_called()
#         self.assertTrue(self.db._connection_pool.empty())

#     def test_connection_context_manager(self):
#         """Test connection_context_manager context manager."""
#         # Reset call counts
#         self.resources["close"].reset_mock()

#         self.db.close = MagicMock()
        
#         with self.db.connection_context_manager() as conn:
#             # Check that we got a connection
#             self.assertEqual(conn, "connection")
        
#         # Check that close was called (the connection is returned to the pool)
#         self.db.close.assert_called_once_with("connection")
    
#     def test_connection_context_manager_with_error(self):
#         """Test connection_context_manager with an error."""
#         # Reset call counts
#         self.resources["close"].reset_mock()
        
#         self.db.close = MagicMock()

#         # Use context manager with an error
#         with self.assertRaises(ValueError):
#             with self.db.connection_context_manager() as conn:
#                 raise ValueError("Test error")
        
#         # Check that close was still called
#         self.db.close.assert_called_once_with("connection")
        
#     def test_transaction_context_manager(self):
#         """Test transaction context manager."""
#         # Reset call counts
#         self.resources["begin"].reset_mock()
#         self.resources["commit"].reset_mock()
#         self.resources["rollback"].reset_mock()
#         self.resources["close"].reset_mock()
        
#         # Mock the close method to avoid calling close_session directly
#         self.db.close = MagicMock()
        
#         with self.db.transaction_context_manager() as conn:
#             # Check that we got a connection
#             self.assertEqual(conn, "connection")
        
#         # Check that commit was called, but not rollback
#         self.resources["commit"].assert_called_once_with("connection")
#         self.resources["rollback"].assert_not_called()
        
#         # Check that close was called
#         self.db.close.assert_called_once_with("connection")
        
#     def test_transaction_context_manager_with_error(self):
#         """Test transaction context manager with an error."""
#         # Reset call counts
#         self.resources["begin"].reset_mock()
#         self.resources["commit"].reset_mock()
#         self.resources["rollback"].reset_mock()
#         self.resources["close"].reset_mock()
        
#         # Mock the close method to avoid calling close_session directly
#         self.db.close = MagicMock()
        
#         # Use context manager with an error
#         with self.assertRaises(ValueError):
#             with self.db.transaction_context_manager() as conn:
#                 raise ValueError("Test error")
        
#         # Check that rollback was called, but not commit
#         self.resources["commit"].assert_not_called()
#         self.resources["rollback"].assert_called_once_with("connection")
        
#         # Check that close was still called
#         self.db.close.assert_called_once_with("connection")


# class TestDatabaseQueries(unittest.TestCase):
#     """Tests for Database query methods."""
    
#     def setUp(self):
#         """Set up test fixtures."""
#         self.configs = _get_mock_configs()

#         self.resources = {
#             "connect": MagicMock(return_value="connection"),
#             "close": MagicMock(),
#             "execute": MagicMock(return_value="execute_result"),
#             "fetch_all": MagicMock(return_value=["result1", "result2"]),
#             "fetch": MagicMock(return_value=["result1"]),
#             "begin": MagicMock(return_value="connection"),
#             "commit": MagicMock(return_value="connection"),
#             "rollback": MagicMock(return_value="connection"),
#             "get_cursor": MagicMock(return_value="cursor"),
#             "close_session": MagicMock(),
#         }
        
#         self.db = Database(configs=self.configs, resources=self.resources)
    
#     def test_get_cursor(self):
#         """Test get_cursor method."""
#         cursor = self.db.get_cursor("connection")
        
#         # Check that the cursor was retrieved
#         self.resources["get_cursor"].assert_called_once_with("connection")
#         self.assertEqual(cursor, "cursor")
    
#     def test_execute_without_params(self):
#         """Test execute method without parameters."""
#         result = self.db.execute("SELECT * FROM test")
        
#         # Check that execute was called correctly
#         self.resources["execute"].assert_called_once_with("connection", "SELECT * FROM test")
#         self.assertEqual(result, "execute_result")
    
#     def test_execute_with_params(self):
#         """Test execute method with parameters."""
#         result = self.db.execute("SELECT * FROM test WHERE id = ?", (1,))
        
#         # Check that execute was called correctly
#         self.resources["execute"].assert_called_once_with(
#             "connection", "SELECT * FROM test WHERE id = ?", (1,)
#         )
#         self.assertEqual(result, "execute_result")
    
#     def test_fetch_without_params(self):
#         """Test fetch method without parameters."""
#         result = self.db.fetch("SELECT * FROM test")
        
#         # Check that fetch was called correctly
#         self.resources["fetch"].assert_called_once_with(
#             "connection", "SELECT * FROM test", None, 1, None
#         )
#         self.assertEqual(result, ["result1"])
    
#     def test_fetch_with_params(self):
#         """Test fetch method with parameters."""
#         result = self.db.fetch(
#             "SELECT * FROM test WHERE id = ?", 
#             (1,), 
#             num_results=5, 
#             return_format="dict"
#         )
        
#         # Check that fetch was called correctly
#         self.resources["fetch"].assert_called_once_with(
#             "connection", "SELECT * FROM test WHERE id = ?", (1,), 5, "dict"
#         )
#         self.assertEqual(result, ["result1"])
    
#     def test_fetch_all_without_params(self):
#         """Test fetch_all method without parameters."""
#         result = self.db.fetch_all("SELECT * FROM test")
        
#         # Check that fetch_all was called correctly
#         self.resources["fetch_all"].assert_called_once_with(
#             "connection", "SELECT * FROM test", None, None
#         )
#         self.assertEqual(result, ["result1", "result2"])
    
#     def test_fetch_all_with_params(self):
#         """Test fetch_all method with parameters."""
#         result = self.db.fetch_all(
#             "SELECT * FROM test WHERE id = ?", 
#             (1,), 
#             return_format="dict"
#         )
        
#         # Check that fetch_all was called correctly
#         self.resources["fetch_all"].assert_called_once_with(
#             "connection", "SELECT * FROM test WHERE id = ?", (1,), "dict"
#         )
#         self.assertEqual(result, ["result1", "result2"])

#     @patch('builtins.open', mock_open(read_data='SELECT * FROM test'))
#     @patch('os.path.exists', return_value=True)
#     def test_execute_script_with_path(self, mock_exists):
#         """Test execute_script method with a file path."""
#         result = self.db.execute_script(path="/path/to/script.sql")
        
#         # Check that execute was called correctly - note the lack of third parameter
#         self.resources["execute"].assert_called_once_with(
#             "connection", 'SELECT * FROM test'
#         )
#         self.assertEqual(result, "execute_result")
    
#     def test_execute_script_with_script(self):
#         """Test execute_script method with a script string."""
#         result = self.db.execute_script(script="SELECT * FROM test")
        
#         # Check that execute was called correctly - note the lack of third parameter
#         self.resources["execute"].assert_called_once_with(
#             "connection", "SELECT * FROM test"
#         )
#         self.assertEqual(result, "execute_result")
    
#     def test_execute_script_with_neither(self):
#         """Test execute_script method with neither script nor path."""
#         with self.assertRaises(ValueError):
#             self.db.execute_script()
    
#     @patch('os.path.exists', return_value=False)
#     def test_execute_script_with_nonexistent_file(self, mock_exists):
#         """Test execute_script method with a nonexistent file."""
#         with self.assertRaises(FileNotFoundError):
#             self.db.execute_script(path="/path/to/nonexistent.sql")


# class TestDatabaseTransactions(unittest.TestCase):
#     """Tests for Database transaction methods."""
    
#     def setUp(self):
#         """Set up test fixtures."""
#         self.configs = _get_mock_configs()

#         self.resources = {
#             "connect": MagicMock(return_value="connection"),
#             "close": MagicMock(),
#             "execute": MagicMock(),
#             "fetch_all": MagicMock(),
#             "fetch": MagicMock(),
#             "begin": MagicMock(return_value="connection"),
#             "commit": MagicMock(),
#             "rollback": MagicMock(),
#             "get_cursor": MagicMock(),
#             "close_session": MagicMock(),
#         }
        
#         self.db = Database(configs=self.configs, resources=self.resources)
    
#     def test_begin(self):
#         """Test begin method."""
#         result = self.db.begin("connection")
        
#         # Check that begin was called correctly
#         self.resources["begin"].assert_called_once_with("connection")
#         self.assertEqual(result, "connection")
    
#     def test_commit(self):
#         """Test commit method."""
#         self.db.commit("connection")
        
#         # Check that commit was called correctly
#         self.resources["commit"].assert_called_once_with("connection")
    
#     def test_rollback(self):
#         """Test rollback method."""
#         # Set up mock to return the connection
#         self.resources["rollback"].return_value = "connection"
        
#         self.db.rollback("connection")
        
#         # Check that rollback was called correctly
#         self.resources["rollback"].assert_called_once_with("connection")
        
#     def test_connect(self):
#         """Test connect method."""
#         # Reset the mock to clear the initialization calls
#         self.resources["connect"].reset_mock()
        
#         conn = self.db.connect()
        
#         # Connection should be from the pool, not a new connection
#         self.resources["connect"].assert_not_called()
#         self.assertEqual(conn, "connection")
    
#     def test_close_with_session(self):
#         """Test close method."""
#         # Set up a session to be closed
#         self.db._session = "some_session"  # This just needs to be not None
        
#         # Now close the connection
#         self.db.close("connection")
        
#         # Assert that close_session was called
#         self.resources["close_session"].assert_called_once_with("connection")
        
#         # Also assert that _session is reset to None
#         self.assertIsNone(self.db._session)

#     def test_close_no_session(self):
#         """Test close method when there is no active session."""
#         # Ensure no session exists
#         self.db._session = None
        
#         # Now close the connection
#         self.db.close("connection")
        
#         # Assert that close_session was not called
#         self.resources["close_session"].assert_not_called()

#     def test_close_with_full_pool(self):
#         """Test close method with a full connection pool."""
#         # Mock connection_pool.full() to return True
#         self.db._connection_pool.full = MagicMock(return_value=True)
#         self.db.close("connection")
#         self.resources["close"].assert_called_once_with("connection")

#     def test_close_session(self):
#         """Test close_session method."""
#         # Set a mock session
#         self.db._session = "session"
        
#         self.db.close_session("connection")
        
#         # Check that close_session was called and session was cleared
#         self.resources["close_session"].assert_called_once_with("connection")
#         self.assertIsNone(self.db._session)
    
#     def test_exit(self):
#         """Test exit method."""
#         self.db.exit()
        
#         # Check that all connections were closed
#         self.assertTrue(self.db._connection_pool.empty())
#         self.assertIsNone(self.db._session)


# if __name__ == '__main__':
#     unittest.main()
