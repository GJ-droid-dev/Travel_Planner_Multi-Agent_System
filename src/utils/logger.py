import logging
import structlog
import sys
from src.config import settings

def setup_logging():
    """Configure structured logging for the application."""
    
    # Set the standard logging level
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            # If we are in dev, output colored text. In prod, output JSON.
            structlog.dev.ConsoleRenderer() if settings.app_env.lower() == "development" else structlog.processors.JSONRenderer()
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

def get_logger(name: str):
    """Get a structlog bound logger."""
    return structlog.get_logger(name)
