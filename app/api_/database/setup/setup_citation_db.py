from __future__ import annotations
import os
from pathlib import Path
import sqlite3


import duckdb


def setup_citation_db(db_path: Path = None, use_duckdb: bool = True) -> sqlite3.Connection | duckdb.DuckDBPyConnection:
    """
    Set up the citation database schema.
    
    Args:
        db_path: Optional path to database file, defaults to citation_db_path
        use_duckdb: Whether to use DuckDB (True) or SQLite (False)
        
    Returns:
        Database connection object
    """
    from configs import configs, Configs
    # Use default path if none provided
    db_path = db_path or configs.AMERICAN_LAW_DATA_DIR / "american_law.db"
    
    # Use DuckDB if requested, otherwise fallback to SQLite
    if use_duckdb:
        return _setup_citation_db_duckdb(db_path)
    else:
        return _setup_citation_db_sqlite(db_path)


def _setup_citation_db_sqlite(db_path: str) -> sqlite3.Connection:
    """Setup citation database with SQLite."""
    if not os.path.exists(db_path):
        # Connect to SQLite database
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Create citations table based on the README specifications
        cursor.execute('''
        CREATE TABLE citations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bluebook_cid TEXT NOT NULL,
            cid TEXT NOT NULL,
            title TEXT NOT NULL,
            title_num TEXT,
            date TEXT,
            public_law_num TEXT,
            chapter TEXT,
            chapter_num TEXT,
            history_note TEXT,
            ordinance TEXT,
            section TEXT,
            enacted TEXT,
            year TEXT,
            place_name TEXT NOT NULL,
            state_name TEXT NOT NULL,
            state_code TEXT NOT NULL,
            bluebook_state_code TEXT NOT NULL,
            bluebook_citation TEXT NOT NULL,
            index_level_0 INTEGER
        )
        ''')
        
        # Commit changes and close connection
        conn.commit()
        print("Citation database created successfully with SQLite.")
    else:
        print("Citation database already exists. Testing to see if it is accessible.")
        # Test if the database is accessible
        try:
            # Connect to SQLite database
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Perform a schema query to check accessibility
            cursor.execute("PRAGMA table_info(citations);")
            result = cursor.fetchone()
            
            if result:
                print("Citation database is accessible.")
            else:
                print("Citation database is not accessible.")
                
        except sqlite3.Error as e:
            print(f"Error accessing citation database: {e}")
            raise e
    
    return conn


def _setup_citation_db_duckdb(db_path: str) -> duckdb.DuckDBPyConnection:
    """Setup citation database with DuckDB."""
    # Connect to DuckDB database
    conn = duckdb.connect(db_path)
    
    # Check if table exists
    result = conn.execute('''
    SELECT name FROM sqlite_master WHERE type='table' AND name='citations'
    ''').fetchone()
    
    if not result:
        # Create citations table based on the README specifications
        conn.execute('''
        CREATE TABLE citations (
            id INTEGER PRIMARY KEY,
            bluebook_cid VARCHAR NOT NULL,
            cid VARCHAR NOT NULL,
            title VARCHAR NOT NULL,
            title_num VARCHAR,
            date VARCHAR,
            public_law_num VARCHAR,
            chapter VARCHAR,
            chapter_num VARCHAR,
            history_note VARCHAR,
            ordinance VARCHAR,
            section VARCHAR,
            enacted VARCHAR,
            year VARCHAR,
            place_name VARCHAR NOT NULL,
            state_name VARCHAR NOT NULL,
            state_code VARCHAR NOT NULL,
            bluebook_state_code VARCHAR NOT NULL,
            bluebook_citation VARCHAR NOT NULL,
            index_level_0 INTEGER
        )
        ''')
        
        # Create a sequence for auto-incrementing IDs
        conn.execute("CREATE SEQUENCE IF NOT EXISTS seq_citations_id")
        
        print("Citation database created successfully with DuckDB.")
    else:
        print("Citation database already exists in DuckDB.")

    return conn
