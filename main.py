import logging

from dotenv import load_dotenv

from bot.bot import run_bot
from config import Bot_config


def setup_logging():
    logging.basicConfig(
        filename="logs/bot.log",
        level=getattr(logging, Bot_config.LOG_LEVEL),
        format="%(asctime)s:%(levelname)s:%(message)s",
    )


if __name__ == "__main__":
    load_dotenv()
    setup_logging()
    run_bot()
