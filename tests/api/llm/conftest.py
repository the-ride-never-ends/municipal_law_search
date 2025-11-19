

from unittest.mock import AsyncMock, MagicMock


import openai
import pytest


from app.llm import make_llm
from app.configs import configs as project_configs, Configs
from app.logger import logger as module_logger



class FixtureError(Exception):
    """Errors related to test fixture setup."""
    def __init__(self, message: str):
        super().__init__(message)

@pytest.fixture
def real_configs() -> MagicMock:
    try:
        configs = Configs()
        configs.model_validate()
    except Exception as e:
        raise FixtureError(f"Error creating real_configs fixture: {e}") from e
    return configs

@pytest.fixture
def mock_configs(real_configs) -> MagicMock:
    try:
        configs_copy = real_configs.copy(deep=True)
    except Exception as e:
        raise FixtureError(f"Error creating mock_configs fixture: {e}") from e
    return configs_copy

@pytest.fixture
def mock_client():
    client = MagicMock(spec=openai.OpenAI)
    return client

@pytest.fixture
def mock_async_client() -> AsyncMock:
    async_client = AsyncMock(spec=openai.AsyncOpenAI)
    return async_client

@pytest.fixture
def mock_logger() -> MagicMock:
    logger = MagicMock(spec_set=module_logger)
    return logger
