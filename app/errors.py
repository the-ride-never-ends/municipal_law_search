

class StartupError(RuntimeError):
    """Raised when there is an error during the startup process of the application."""

    def __init__(self, msg: str):
        super().__init__(f"StartupError: {msg}")


class InitializationError(RuntimeError):
    """Raised when there is an error during initialization of a class."""

    def __init__(self, msg: str):
        super().__init__(f"InitializationError: {msg}")


class ConfigurationError(RuntimeError):
    """Raised when there is an error with loading or validating a class configuration."""

    def __init__(self, msg: str):
        super().__init__(f"ConfigurationError: {msg}")


class ResourceError(RuntimeError):
    """Raised when there is an error related to instantiation of a class resource."""

    def __init__(self, msg: str):
        super().__init__(f"ResourceError: {msg}")

class LLMError(RuntimeError):
    """Raised when there is a general error related to LLM operations."""

    def __init__(self, msg: str):
        super().__init__(f"LLMError: {msg}")
