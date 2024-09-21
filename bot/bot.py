import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

from config import Bot_config
from database.models import Database

load_dotenv()


class KHBot(commands.Bot):
    def __init__(self):
        self.db = Database(Bot_config.DATABASE_URL)

        intents = discord.Intents.all()
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        for filename in os.listdir("./bot/cogs"):
            if filename.endswith(".py"):
                if filename == "__init__.py":
                    continue
                await self.load_extension(f"bot.cogs.{filename[:-3]}")

    async def on_ready(self):
        try:
            synced = await self.tree.sync()
            print(f"Synced {len(synced)} commands")
            for command in synced:
                print(f"\tCommand {command.name} ready")
        except Exception as e:
            print(e)
        print("Bot is up and running")


bot = KHBot()


def run_bot():
    bot.run(Bot_config.DISCORD_TOKEN)


if __name__ == "__main__":
    run_bot()
