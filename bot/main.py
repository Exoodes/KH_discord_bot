import os
import logging

from dotenv import load_dotenv
import disnake as discord
from disnake.ext import commands

from utils.logging import setup_logging
from bot import KH_BOT

initial_cogs = [
    "cogs.admin"
]

if __name__ == "__main__":
    load_dotenv()
    setup_logging()

    TOKEN = os.getenv('DISCORD_TOKEN')

    intents = discord.Intents.all()
    bot = KH_BOT(command_prefix=commands.when_mentioned_or(
        "/"), intents=intents)

    log = logging.getLogger()
    for extension in initial_cogs:
        try:
            bot.load_extension(extension)
        except Exception:
            log.error('Failed to load extension %s.', extension, exc_info=True)

    bot.run(TOKEN)
