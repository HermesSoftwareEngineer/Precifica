import logging

logger = logging.getLogger(__name__)

def index():
    logger.info("Index page accessed")
    return 'Hello, World! Structure Organized.'
