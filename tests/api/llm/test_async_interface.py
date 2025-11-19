

import pytest


from app.api_.llm_.async_interface import AsyncLLMInterface
from tests.api.llm.conftest import FixtureError

@pytest.fixture
def make_async_llm_interface(
    mock_async_client,
    mock_embeddings_manager,
    mock_logger,
) -> AsyncLLMInterface:

    def _make_async_llm_interface() -> AsyncLLMInterface:
        resources = {
            "async_client": mock_async_client,
            "embeddings_manager": mock_embeddings_manager,
            "logger": mock_logger,
        }
        llm_interface = AsyncLLMInterface(resources=resources)
        return llm_interface
    return _make_async_llm_interface

