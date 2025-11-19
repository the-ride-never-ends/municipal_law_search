# try_except.py

from functools import wraps
import inspect
from typing import Callable, Coroutine, Optional, Any


from app.logger import logger as module_logger


def try_except(func: Callable = lambda x: x, 
               raise_: bool = None,
               exception_type: Exception = Exception, 
               msg: str = "An unexpected exception occurred",
               default_return: Optional[Any] = None
               ) -> Callable:
    """
    Decorator to handle exceptions in a function.

    Args:
        raise_: Whether to re-raise the exception after logging.
            NOTE: This must be manually set to True or False. 
                This reduces the risk of accidentally raising or passing an exception.
        func: The function to decorate
        exceptiontype: The type of exception to catch
        msg: The message to log on exception
        default_return: The value to return if an exception occurs. Only returned if raise_ is False

    Returns:
        A wrapped function that handles exceptions
    """

    def decorator(func: Callable | Coroutine) -> Callable | Coroutine:

        # Check if the function is asynchronous
        async_ = inspect.iscoroutinefunction(func)

        @wraps(func)
        def wrapper(*args, **kwargs):
            if raise_ is None:
                raise ValueError("raise must be set to True or False")
            errored = None
            try:
                return func(*args, **kwargs)
            except exception_type as e:
                module_logger.exception(f"{msg}: {e}", stacklevel=2) # Raise the stack level up to the caller
                errored = e
            finally:
                if errored is None:
                    module_logger.debug(f"Function {func.__name__} completed successfully.")
                else:
                    module_logger.debug(f"Function {func.__name__} failed with error: {errored}")
                    if raise_:
                        raise errored
                    else:
                        if default_return is not None:
                            return default_return

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            if raise_ is None:
                raise ValueError("raise_ must be set to True or False")
            errored = None
            try:
                return await func(*args, **kwargs)
            except exception_type as e:
                module_logger.exception(f"{msg}: {e}", stacklevel=2) # Raise the stack level up to the caller
                errored = e
            finally:
                if errored is None:
                    module_logger.debug(f"Function {func.__name__} completed successfully.")
                else:
                    module_logger.debug(f"Function {func.__name__} failed with error: {errored}")
                    if raise_:
                        raise errored
                    else:
                        if default_return is not None:
                            return default_return

        return async_wrapper if async_ else wrapper
    return decorator
