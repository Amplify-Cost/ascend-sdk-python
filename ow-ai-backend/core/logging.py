"""
Centralized Logging Configuration
Provides consistent logging across the application
"""
import logging
import sys
from core.config import settings


def setup_logging():
    """Configure application-wide logging"""
    
    # Create logger
    logger = logging.getLogger("owai")
    logger.setLevel(getattr(logging, settings.LOG_LEVEL))
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, settings.LOG_LEVEL))
    
    # Create formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(console_handler)
    
    return logger


# Create global logger instance
logger = setup_logging()
