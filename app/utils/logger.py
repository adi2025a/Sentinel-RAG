import logging
import sys

# Configure the root logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

def get_logger(name: str) -> logging.Logger:
    """
    Returns a logger instance with the given name.
    Usage:
        from app.utils.logger import get_logger
        logger = get_logger(__name__)
        logger.info("Hello from my module")
    """
    return logging.getLogger(name)



# from app.utils.logger import get_logger

# logger = get_logger(__name__)

# logger.info("This is an info log")
# logger.error("This is an error log")
