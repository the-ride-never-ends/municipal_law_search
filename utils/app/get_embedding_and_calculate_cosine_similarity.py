from typing import Optional, Generator


import duckdb


from logger import logger
from configs import configs
from utils.llm.cosine_similarity import cosine_similarity


_ARBITRARY_SIMILARITY_SCORE_THRESHOLD = 0.5


def get_embedding_and_calculate_cosine_similarity(
    embedding_data: dict[str, str],
    query_embedding: list[float] = None,
) -> Optional[tuple[str,str]]:
    """
    Calculate the cosine similarity between a query embedding and a given embedding.

    Args:
        embedding_data (dict[str, str]): A dictionary containing the embedding_cid and cid.
        query_embedding (list[float], optional): The embedding vector for the query.

    Returns:
        Optional[tuple[str, float]]: A tuple containing the CID and similarity score if the
                                    cosine similarity exceeds the threshold, otherwise None.
    """
    try:
        # Extract the embedding and CID from the input data
        embedding_cid = embedding_data.get("embedding_cid")
        cid = embedding_data.get("cid")

        if not embedding_cid or not cid:
            logger.debug("No embedding CID or CID found in the input data.")
            return None

        with duckdb.connect(configs.AMERICAN_LAW_DATA_DIR / "embeddings.db", read_only=True) as conn:
            with conn.cursor() as cursor:

                # Fetch the embedding from the database
                cursor.execute('''
                    SELECT embedding, cid
                    FROM embeddings
                    WHERE embedding_cid = ?
                    LIMIT 1;
                ''', (embedding_cid,))
                embedding: dict = cursor.fetchdf().to_dict(orient='records')[0]
                if not embedding:
                    logger.debug(f"No embedding found for the given CID {cid}.")
                    return None

                embedding_vector = embedding.get("embedding")
                if embedding_vector is None:
                    return None

                # Calculate the cosine similarity
                similarity_score = cosine_similarity(query_embedding, embedding_vector)
                logger.debug(f"\nCosine similarity score: {similarity_score}")

                # Yield the CID if the similarity score exceeds the threshold
                if similarity_score >= _ARBITRARY_SIMILARITY_SCORE_THRESHOLD:
                    return cid, similarity_score
                else:
                    return None

    except Exception as e:
        logger.error(f"Error in get_embedding_and_calculate_cosine_similarity: {e}")
        return None
