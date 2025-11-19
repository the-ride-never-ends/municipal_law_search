"""
A module to manage the database connection and operations.
This module provides a singleton instance of the Database class, which is read-only by default.
"""
from typing import Callable

from errors import InitializationError, ResourceError
from configs import configs as project_configs, Configs
from logger import logger as  module_logger
from api_.database import Database
from api_.database.dependencies.duckdb_database import DuckDbDatabase



def make_read_only_db(resources: dict[str, Callable] = None, configs: Configs = None) -> Database:
    """
    Factory function to create a new Database instance.
    
    This function initializes a new Database object with the provided configurations
    and DuckDB resources. It is intended to be used for creating database connections
    as needed.

    Args:
        resources (dict[str, Any], optional): A dictionary of callables to override injected defaults. Defaults to None.
        configs (Configs, optional): A Configs object to override default configurations. Defaults to None.

    Returns:
        Database: A new instance of the Database class.
    """
    # Export resources dictionary for use with Database class
    configs = configs or project_configs
    _resources = resources or {}
    db = DuckDbDatabase()
    db.logger = logger = _resources.pop("logger", module_logger)

    try:
        duckdb_resources = {
            "begin": _resources.pop("begin", db.begin),
            "close": _resources.pop("close", db.close),
            "commit": _resources.pop("commit", db.commit),
            "connect": _resources.pop("connect", db.connect),
            "create_function": _resources.pop("create_function", db.create_function),
            "create_index_if_not_exists": _resources.pop("create_index_if_not_exists", db.create_index_if_not_exists),
            "create_table_if_not_exists": _resources.pop("create_table_if_not_exists", db.create_table_if_not_exists),
            "execute": _resources.pop("execute", db.execute),
            "fetch": _resources.pop("fetch", db.fetch),
            "fetch_all": _resources.pop("fetch_all", db.fetch_all),
            "fetch_one": _resources.pop("fetch_one", db.fetch),
            "get_cursor": _resources.pop("get_cursor", db.get_cursor),
            "rollback": _resources.pop("rollback", db.rollback),
            "read_only": _resources.pop("read_only", True),  # Set read_only to True for read-only access
            "logger": logger,
        }
    except KeyError as e:
        raise ResourceError(f"Missing required resource for DuckDB initialization: {e}") from e
    except Exception as e:
        raise ResourceError(f"Unexpected error initializing DuckDB resources: {e}")

    for key in _resources.keys():
        if key not in duckdb_resources:
            raise KeyError(f"Unexpected resource key: {key}")

    try:
        return Database(configs=configs, resources=duckdb_resources)
    except Exception as e:
        raise InitializationError(f"Error initializing Database instance: {e}") from e

# Initialize the singleton database instance with DuckDB resources.
READ_ONLY_DB = None
READ_ONLY_DB = make_read_only_db()

# Close the database connection when the program is terminated.
def close_db_connection():
    if READ_ONLY_DB is not None:
        READ_ONLY_DB.exit()
        print("Database connection closed.")


