#! /usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import annotations
import csv
from pathlib import Path


import duckdb
import pandas as pd
from tqdm import tqdm


from configs import configs
from logger import logger
from utils.run_in_process_pool import run_in_process_pool
from chatbot.api.database.fix_parquet_files_in_parallel import fix_parquet_files_in_parallel

MEMORY_LIMIT_IN_MBS = 40
MISSING_DATE_CSV = configs.AMERICAN_LAW_DATA_DIR / 'missing_data.csv'
AMERICAN_LAW_DB_PATH = configs.AMERICAN_LAW_DATA_DIR / 'american_law.db'
CITATIONS_DB_PATH = configs.AMERICAN_LAW_DATA_DIR / 'citations.db'
EMBEDDINGS_DB_PATH = configs.AMERICAN_LAW_DATA_DIR / 'embeddings.db'
HTML_DB_PATH = configs.AMERICAN_LAW_DATA_DIR / 'html.db'

DB_DICT = {
    "citations": {
        "path": CITATIONS_DB_PATH,
        "table": '''
            CREATE TABLE IF NOT EXISTS citations (
                bluebook_cid VARCHAR PRIMARY KEY,
                cid VARCHAR NOT NULL,
                title TEXT NOT NULL,
                title_num VARCHAR,
                date TEXT,
                public_law_num VARCHAR,
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
                gnis VARCHAR NOT NULL
            )
        '''
    },
    "embeddings": {
        "path": EMBEDDINGS_DB_PATH,
        "table": '''
            CREATE TABLE IF NOT EXISTS embeddings (
                embedding_cid VARCHAR PRIMARY KEY,
                gnis VARCHAR NOT NULL,
                cid VARCHAR NOT NULL,
                text_chunk_order INTEGER NOT NULL,
                embedding DOUBLE[1536] NOT NULL
            )
        '''
    },
    "html": {
        "path": HTML_DB_PATH,
        "table": '''
            CREATE TABLE IF NOT EXISTS html (
                cid VARCHAR PRIMARY KEY,
                doc_id VARCHAR NOT NULL,
                doc_order INTEGER NOT NULL,
                html_title TEXT NOT NULL,
                html TEXT NOT NULL,
                gnis VARCHAR NOT NULL
            )
        '''
    },
    "american_law": {
        "path": AMERICAN_LAW_DB_PATH,
        "table": None  # No specific table creation for the main database
    }
}

def make_the_databases():
    """Create DuckDB databases if they do not exist."""
    for db in DB_DICT.values():
        path = db["path"]
        if not path.exists():
            logger.info(f"Creating new DuckDB database at {path}")
            duckdb.connect(path).close()
            logger.info("Database created successfully.")
        else:
            logger.debug(f"DuckDB database exists at {path}.")
    logger.info("All DuckDB databases checked/created successfully.")


def make_tables_in_the_databases():
    """Create tables in the DuckDB databases."""
    for db_name, db in DB_DICT.items():
        if db["table"] is not None:
            with duckdb.connect(db["path"]) as conn:
                with conn.cursor() as cursor:
                    try:
                        cursor.execute(db["table"])
                        logger.info(f"Table {db_name} created successfully.")
                    except duckdb.CatalogException as e:
                        logger.warning(f"Table {db_name} already exists. Skipping creation.")
                    except Exception as e:
                        logger.error(f"Error creating table: {e}")
                        raise e
    logger.info("All tables created successfully.")


def log_missing_data(gnis: int, missing_data: list, csv_path: Path = MISSING_DATE_CSV):
    """Log missing parquet files for a given GNIS to a CSV file."""
    existing_data = {}

    # Read existing data if file exists
    if not csv_path.exists():
        with open(csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['gnis', 'missing_data_types'])
        logger.info(f"Created new CSV file at {csv_path}")
    else:
        with open(csv_path, 'r', newline='') as f:
            reader = csv.reader(f)
            headers = next(reader, None)
            for row in reader:
                existing_data[row[0]] = row[1]

    # Update or add the GNIS entry
    existing_data[str(gnis)] = ','.join(missing_data)

    # Write data back to CSV
    with open(csv_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['gnis', 'missing_data_types'])
        for key, value in existing_data.items():
            writer.writerow([key, value])


def attach_then_insert_from_another_db(merged_db: duckdb.DuckDBPyConnection, db_path: Path) -> None:
    try:
        merged_db.execute('BEGIN TRANSACTION;')
        table_name = db_path.stem.lower()
        merged_db.execute(f"""
            ATTACH '{db_path}' AS db1;
            INSERT INTO {table_name}
            SELECT * FROM db1.{table_name};
            DETACH db1;
        """)
        merged_db.execute(f"COMMIT;")
    except Exception as e:
        logger.error(f"Error inserting data from {db_path} into merged database: {e}")
        merged_db.execute('ROLLBACK;')

import time

def insert_into_db_from_parquet_file(parquets: list[tuple[str, Path]]) -> None:
    if not parquets:
        logger.warning("No parquet files to process.")
        return

    db_type = parquets[0][0]
    with duckdb.connect(DB_DICT[db_type]['path']) as conn:
        with conn.cursor() as cursor:
            for file in tqdm(parquets, desc="Uploading files to databases"):
                try:
                    cursor.execute('BEGIN TRANSACTION;')
                    cursor.execute(f'''
                        INSERT INTO {file[0]}
                            SELECT * FROM read_parquet('{file[1].resolve()}');
                    ''')
                    cursor.execute('COMMIT;')
                except Exception as e:
                    logger.error(f"Error inserting data into {file[0]} from {file[1]}: {e}")
                    cursor.execute('ROLLBACK;')


def get_all_the_unique_gnis_that_are_in_all_three_tables_in_the_database(cursor: duckdb.DuckDBPyConnection) -> set[str]:
    try:
        query = '''
            SELECT DISTINCT e.gnis
            FROM embeddings e
            INNER JOIN html h ON e.cid = h.cid
            INNER JOIN citations c ON e.cid = c.cid
        '''
        unique_gnis: set[str] = {row[0] for row in cursor.execute(query).fetchall()}
        logger.info(f"Found {len(unique_gnis)} unique GNIS entries present in all three tables.")
        #logger.debug(f"unique_gnis: {unique_gnis}")
        return unique_gnis

    except Exception as e:
        logger.error(f"Error retrieving unique GNIS entries: {e}")
        return set()


def check_for_complete_set_of_parquet_files(unique_gnis: set[str], base_path: Path) -> list[list[tuple[str, Path]]]:
    # Find all citation files
    citation_files = list(base_path.glob("**/*_citation.parquet"))
    logger.info(f"Found {len(citation_files)} citation files in {base_path}")

    parquet_list = []
    citation_parquet_list: list[tuple[str, Path]] = []
    html_parquet_list: list[tuple[str, Path]] = []
    embedding_parquet_list: list[tuple[str, Path]] = []

    for citation_path in tqdm(citation_files, desc="Checking for complete set of parquet files"):
        skip = False
        citation_df = None
        gnis = citation_path.stem.split('_')[0]  # Extract GNIS from filename
        if gnis in unique_gnis:
            logger.info(f"Skipping {citation_path} as it already exists in the database.")
            continue

        try:
            # Read citation data to see if it loads.
            citation_df = pd.read_parquet(citation_path.resolve())
            #logger.debug(f"citation_df for gnis '{gnis}':\n{citation_df.head()}")  # Trigger loading to check for errors
        except Exception as e:
            logger.error(f"Error reading {citation_path}: {e}")
            skip = True
        finally:
            if citation_df is not None:
                del citation_df
            if skip:
                continue

        # Get corresponding HTML file
        html_path = base_path / gnis / f"{gnis}_html.parquet"
        embedding_path = base_path / gnis / f"{gnis}_embeddings.parquet"

        missing_data = []
        # Check for missing parquet files
        if not html_path.exists():
            missing_data.append("html")
            skip = True

        if not embedding_path.exists():
            missing_data.append("embedding")
            skip = True

        if skip:
            # Log the issue to a CSV file for tracking.
            log_missing_data(gnis, missing_data)
            continue

        citation_parquet_list.append(("citations", citation_path,))
        html_parquet_list.append(("html",html_path,))
        embedding_parquet_list.append(("embeddings",embedding_path,))


    parquet_list.append(citation_parquet_list)
    parquet_list.append(html_parquet_list)
    parquet_list.append(embedding_parquet_list)
    return parquet_list


def upload_files_to_database(parquet_list: list[list[tuple[str, Path]]]) -> None:
    for input, output in run_in_process_pool(insert_into_db_from_parquet_file, parquet_list):
        if output:
            logger.info(f"Processed {input} successfully.")
        else:
            logger.error(f"Failed to process {input}.")
    logger.info(f"Finished uploading parquet files to databases.")




def merge_database_into_the_american_law_db(cursor: duckdb.DuckDBPyConnection) -> None:
    # Merge the databases into one 'american_law.db'
    logger.info("Merging databases into american_law.db")
    
    for name, db in DB_DICT.items():
        if db["path"] is not None:
            db_path = str(db['path'].resolve())
            
            # Skip if we're trying to attach the database to itself
            if 'american_law.db' in str(db_path):
                logger.info(f"Skipping {db_path} as it's the target database itself")
                continue
                
            logger.info(f"Processing database {db_path} to merge into american_law.db")
            
            # Attach the database once for all operations
            try:
                cursor.execute(f"ATTACH '{db_path}' AS db1")
                
                # Create the destination table structure within a transaction
                cursor.execute("BEGIN TRANSACTION")
                try:
                    cursor.execute(f"CREATE TABLE IF NOT EXISTS {name} AS SELECT * FROM db1.{name} WHERE 0")
                    cursor.execute("COMMIT")
                    logger.info(f"Created table {name} in american_law.db")
                except Exception as e:
                    cursor.execute("ROLLBACK")
                    logger.error(f"Failed to create table structure for {name}: {e}")
                    cursor.execute("DETACH db1")
                    continue  # Skip to next table if structure creation fails
                
                # Get table statistics - DuckDB compatible approach
                row_count = cursor.execute(f"SELECT COUNT(*) FROM db1.{name}").fetchone()[0]
                
                # Use a simple sampling approach to estimate size
                try:
                    # Sample first 100 rows to estimate average row size
                    sample_data = cursor.execute(f"SELECT * FROM db1.{name} LIMIT 100").fetchall()
                    sample_size = 0
                    
                    # Estimate size by converting to string
                    for row in sample_data:
                        for col in row:
                            sample_size += len(str(col))
                    
                    avg_row_size = sample_size / len(sample_data) if sample_data else 0
                    size_mb = (avg_row_size * row_count) / 1024 / 1024
                except Exception as e:
                    # Fallback if sampling fails
                    logger.warning(f"Size estimation failed: {e}. Using row count for chunking.")
                    size_mb = row_count / 10000  # Rough estimate: assume 10K rows per MB
                    
                logger.info(f"Table {name} has {row_count} rows taking approximately {size_mb:.2f} MB")
                
                # Calculate chunking
                num_chunks = max(1, int(size_mb / MEMORY_LIMIT_IN_MBS) + 1)
                chunk_size = max(1, row_count // num_chunks)
                logger.info(f"Splitting {name} into {num_chunks} chunks for processing.")
                
                # Process each chunk
                successful_rows = 0
                for i in range(num_chunks):
                    start_row = i * chunk_size
                    # Calculate end for current chunk
                    end_row = min(row_count, start_row + chunk_size)
                    current_chunk_size = end_row - start_row
                    
                    logger.info(f"Processing chunk {i+1}/{num_chunks} of {name} table (rows {start_row}-{end_row})")
                    try:
                        cursor.execute("BEGIN TRANSACTION")
                        cursor.execute(f"""
                            INSERT INTO {name}
                            SELECT * FROM db1.{name}
                            LIMIT {current_chunk_size} OFFSET {start_row};
                        """)
                        cursor.execute("COMMIT")
                        successful_rows += current_chunk_size
                        logger.info(f"Chunk {i+1}/{num_chunks} of {name} merged successfully")
                    except Exception as e:
                        cursor.execute("ROLLBACK")
                        logger.error(f"Error merging chunk {i+1}/{num_chunks} of {name}: {e}")
                        # Option to retry this chunk with smaller batch
                        if current_chunk_size > 100:
                            logger.info(f"Retrying with smaller batches for chunk {i+1}")
                            # Retry with smaller batches
                            sub_batch_size = max(1, current_chunk_size // 10)
                            for j in range(0, current_chunk_size, sub_batch_size):
                                sub_start = start_row + j
                                sub_size = min(sub_batch_size, start_row + current_chunk_size - sub_start)
                                try:
                                    cursor.execute("BEGIN TRANSACTION")
                                    cursor.execute(f"""
                                        INSERT INTO {name}
                                        SELECT * FROM db1.{name}
                                        LIMIT {sub_size} OFFSET {sub_start};
                                    """)
                                    cursor.execute("COMMIT")
                                    successful_rows += sub_size
                                    logger.info(f"Sub-batch {j//sub_batch_size + 1} of chunk {i+1} merged successfully")
                                except Exception as sub_e:
                                    cursor.execute("ROLLBACK")
                                    logger.error(f"Sub-batch {j//sub_batch_size + 1} of chunk {i+1} failed: {sub_e}")
                
                # Verify the merge was successful
                dest_count = cursor.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
                if dest_count == row_count:
                    logger.info(f"Table {name} merged successfully: {dest_count}/{row_count} rows transferred")
                else:
                    logger.warning(f"Table {name} merge incomplete: only {dest_count}/{row_count} rows transferred")
                    
            except Exception as e:
                logger.error(f"Unexpected error processing table {name}: {e}")
            finally:
                # Always detach the database
                try:
                    cursor.execute("DETACH db1")
                except Exception as e:
                    logger.error(f"Error detaching database: {e}")
                    
    logger.info("Database merge operation completed")


def create_american_law_db(base_path: Path = None):
    """Process the dataset and store in DuckDB database"""
    if not AMERICAN_LAW_DB_PATH.exists():
        logger.info(f"Creating new DuckDB database at {AMERICAN_LAW_DB_PATH}")
        duckdb.connect(AMERICAN_LAW_DB_PATH).close()
        logger.info("Database created successfully.")
    else:
        with duckdb.connect(AMERICAN_LAW_DB_PATH) as conn:
            with conn.cursor() as cursor:
                # Check if the database has any data in it.
                cursor.execute("SELECT COUNT(*) FROM citations")
                count = cursor.fetchone()[0]
                if count > 0:
                    logger.info("Database already contains data. Skipping creation.")
                    return
                else:
                    logger.info("Database is empty. Proceeding with data upload.")

                    make_the_databases()

                    make_tables_in_the_databases()

                    unique_gnis = get_all_the_unique_gnis_that_are_in_all_three_tables_in_the_database(cursor)

                    parquet_list = check_for_complete_set_of_parquet_files(unique_gnis, base_path)

                    upload_files_to_database(parquet_list)

                    merge_database_into_the_american_law_db(cursor)


    logger.info("All databases merged into american_law.db successfully.")


if __name__ == "__main__":
    # Fix the parquet files of any errors
    # for parquet_type in ["_citation.parquet", "_embeddings.parquet", "_html.parquet"]:
    #     fix_parquet_files_in_parallel(parquet_type)
    #     logger.info(f"Fixed {parquet_type} files.")

    base_path = configs.PARQUET_FILES_DIR
    create_american_law_db(base_path)