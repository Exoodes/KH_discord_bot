import os


class Bot_config:
    DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///bot_database.db")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    # Add any other configuration variables here
