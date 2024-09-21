import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

from config import Bot_config

load_dotenv()


class MyBot(commands.Bot):
    def __init__(self):
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
        except Exception as e:
            print(e)
        print("Bot is up and running")


bot = MyBot()


def run_bot():
    bot.run(Bot_config.DISCORD_TOKEN)


if __name__ == "__main__":
    run_bot()
