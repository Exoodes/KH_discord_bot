import os

from dotenv import load_dotenv

load_dotenv()


class Bot_config:
    DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///bot_database.db")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    ADMIN_CHANNEL_ID = int(os.getenv("ADMIN_CHANNEL_ID"))
    ROLE_PICKER_CHANNEL_ID = int(os.getenv("ROLE_PICKER_CHANNEL_ID"))
