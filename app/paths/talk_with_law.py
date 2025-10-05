"""
Use an LLM with GraphRAG to answer questions about American municipal law.
"""
from pathlib import Path
from typing import Callable


from configs import configs, Configs


from llm import get_llm
from api_.llm_.async_interface import AsyncLLMInterface


class TalkWithLawFunction:
    """
    Use an LLM with GraphRAG to answer questions about American municipal law.
    
    This class provides methods to query the database and retrieve information
    about American municipal law using a language model.
    
    Parameters:
        db_path (str): Path to the American law database.
        resources (dict[str, Callable], optional): A dictionary of resources, including the language model.
        configs (Configs, optional): Configuration object containing application-wide settings.

    Attributes:
        db_path (Path): Path to the American law database.
        llm (AsyncLLMInterface): Language model to use for processing.
    """
    
    def __init__(self, 
                 db_path: str, 
                 resources: dict[str, Callable] = None,
                 configs: Configs = None
                 ) -> None:
        self.configs = configs
        self.resources = resources

        self.db_path: Path = Path(db_path)
        self.llm: AsyncLLMInterface = self.resources['get_llm']()

resources = {
    'get_llm': get_llm,
}

async def function():
    pass