import sqlite3


import duckdb


from configs import configs


_AMERICAN_LAW_DB_PATH =  configs.AMERICAN_LAW_DATA_DIR / "american_law.db"


def _get_db(db_path: str, use_duckdb: bool = True, read_only: bool = True) -> sqlite3.Connection | duckdb.DuckDBPyConnection:
    """
    Get a database connection.
    
    Args:
        db_path: Path to the database file
        use_duckdb: Whether to use DuckDB (True) or SQLite (False)
        
    Returns:
        Database connection object
    """
    if use_duckdb:
        return duckdb.connect(db_path, read_only=read_only)
    else:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn

# Database connections
def get_citation_db(read_only: bool = True, use_duckdb: bool = True) -> sqlite3.Connection | duckdb.DuckDBPyConnection:
    """Get connection to citation database."""
    return _get_db(_AMERICAN_LAW_DB_PATH, use_duckdb, read_only)

def get_html_db(read_only: bool = True, use_duckdb: bool = True) -> sqlite3.Connection | duckdb.DuckDBPyConnection:
    """Get connection to HTML database."""
    return _get_db(_AMERICAN_LAW_DB_PATH, use_duckdb, read_only)

def get_embeddings_db(read_only: bool = True, use_duckdb: bool = True) -> sqlite3.Connection | duckdb.DuckDBPyConnection:
    """Get connection to embeddings database."""
    return _get_db(_AMERICAN_LAW_DB_PATH, use_duckdb, read_only)

def get_american_law_db(read_only: bool = True, use_duckdb: bool = True) -> sqlite3.Connection | duckdb.DuckDBPyConnection:
    """Get connection to citation database."""
    return _get_db(_AMERICAN_LAW_DB_PATH, use_duckdb, read_only)
