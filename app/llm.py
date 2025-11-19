# -*- coding: utf-8 -*-
"""
Initialize singleton for LLM.
"""
import sys
from typing import Any, TypeVar


sys.path.append("..")  # Add the parent directory to the path


from pydantic import ValidationError


from logger import logger as module_logger
from configs import configs as project_configs, Configs
from errors import InitializationError, ResourceError, ConfigurationError
from api_.llm_.async_interface import AsyncLLMInterface
from app.api_.llm_.embeddings_manager import EmbeddingsManager
from api_.llm_.dependencies.async_openai_client import AsyncOpenAIClient
from api_.llm_.load_prompt_from_yaml import load_prompt_from_yaml


LlmClient = TypeVar("LlmClient")


def _make_embeddings_manager(configs: Configs = project_configs) -> EmbeddingsManager:
    resources = {}
    try:
        embeddings_manager = EmbeddingsManager(configs=configs, resources=resources)
        return embeddings_manager
    except Exception as e:
        raise e


def _make_async_openai_client(configs: Configs = project_configs) -> AsyncOpenAIClient:
    try:
        async_client = AsyncOpenAIClient(
            api_key=configs.OPENAI_API_KEY.get_secret_value(),
            model=configs.OPENAI_MODEL,
            embedding_model=configs.OPENAI_EMBEDDING_MODEL,
            configs=configs
        )
        return async_client
    except Exception as e:
        raise e


def make_llm(resources: dict[str, Any] = {}, configs: Configs = project_configs) -> AsyncLLMInterface:

    try:
        Configs.model_validate(configs)
    except ValidationError as e:
        raise ConfigurationError(f"LLM configurations failed to validate: {e.errors()}") from e
    except Exception as e:
        raise ConfigurationError(f"Unexpected error validating LLM configs") from e

    try:
        resources_ = {
            "embeddings_manager": resources.pop("embeddings_manager", _make_embeddings_manager(configs=configs)),
            "async_client": resources.pop("async_client", _make_async_openai_client(configs=configs)),
            "logger": resources.pop("logger", module_logger),
            "load_prompt_from_yaml": resources.pop("load_prompt_from_yaml", load_prompt_from_yaml),
        }
    except Exception as e:
        raise ResourceError(f"Error initializing resources for LLM: {e}") from e

    try:
        llm = AsyncLLMInterface(resources=resources_, configs=configs)
        llm.logger.info("LLM interface initialized successfully")
    except Exception as e:
        raise InitializationError(f"Error initializing LLM interface: {e}") from e
    else:
        return llm

LLM = make_llm()
