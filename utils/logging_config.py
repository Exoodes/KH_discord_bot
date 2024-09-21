import logging

from config import Bot_config


def setup_logging():
    # Create a custom logger
    logger = logging.getLogger("discord_bot")
    logger.setLevel(logging.DEBUG)  # Set to lowest level, handlers will filter

    # Create handlers
    c_handler = logging.StreamHandler()  # Console handler
    f_handler = logging.FileHandler("logs/bot.log")
    c_handler.setLevel(logging.WARNING)  # Less detailed for console
    f_handler.setLevel(getattr(logging, Bot_config.LOG_LEVEL))  # More detailed for file

    # Create formatters and add it to handlers
    format = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    c_handler.setFormatter(format)
    f_handler.setFormatter(format)

    # Add handlers to the logger
    logger.addHandler(c_handler)
    logger.addHandler(f_handler)

    return logger


# Use it like this in your code:
# logger = setup_logging()
# logger.debug('This is a debug message')
# logger.info('This is an info message')
# logger.warning('This is a warning message')
# logger.error('This is an error message')
# logger.critical('This is a critical message')
