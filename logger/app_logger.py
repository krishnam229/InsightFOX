import os
from loguru import logger as loguru_logger
from typing import Any, Generator
from contextlib import contextmanager
# Define log file path
LOG_FILE = "logs/app.log"

# Ensure the logs directory exists
os.makedirs("logs", exist_ok=True)

# Configure Loguru Logger
loguru_logger.add(
    LOG_FILE,
    rotation="1 day",
    retention="10 days",
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
           "<level>{level: <8}</level> | "
           "<cyan>{file}</cyan>:<cyan>{name}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
)


class AppLogger:
    """
    Logging class using Loguru for structured logging.
    Provides synchronous and asynchronous logging capabilities.
    """

    def __init__(self):
        pass

    def log_info(self, *args: Any, **kwargs: Any) -> None:
        """Synchronous logging with level selection."""
        level = kwargs.pop("level", "INFO")
        message = " ".join(map(str, args))
        loguru_logger.opt(depth=1).log(level, message, **kwargs)

    async def log_info_async(self, *args: Any, **kwargs: Any) -> None:
        """Asynchronous logging for async functions."""
        level = kwargs.pop("level", "INFO")
        message = " ".join(map(str, args))
        loguru_logger.opt(depth=1).log(level, message, **kwargs)

    def log_error(self, *args: Any, **kwargs: Any) -> None:
        """Synchronous error logging."""
        message = " ".join(map(str, args))
        loguru_logger.opt(depth=1).error(message, **kwargs)

    async def log_error_async(self, *args: Any, **kwargs: Any) -> None:
        """Asynchronous error logging."""
        message = " ".join(map(str, args))
        loguru_logger.opt(depth=1).error(message, **kwargs)

    def log_debug(self, *args: Any, **kwargs: Any) -> None:
        """Synchronous debug logging."""
        message = " ".join(map(str, args))
        loguru_logger.opt(depth=1).debug(message, **kwargs)

    async def log_debug_async(self, *args: Any, **kwargs: Any) -> None:
        """Asynchronous debug logging."""
        message = " ".join(map(str, args))
        loguru_logger.opt(depth=1).debug(message, **kwargs)

    def log_warning(self, *args: Any, **kwargs: Any) -> None:
        """Synchronous warning logging."""
        message = " ".join(map(str, args))
        loguru_logger.opt(depth=1).warning(message, **kwargs)

    async def log_warning_async(self, *args: Any, **kwargs: Any) -> None:
        """Asynchronous warning logging."""
        message = " ".join(map(str, args))
        loguru_logger.opt(depth=1).warning(message, **kwargs)


# Instantiate global logger instance
app_logger = AppLogger()
