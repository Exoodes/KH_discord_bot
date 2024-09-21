import os

import discord
from discord.ext import commands

from config import Bot_config
from database.models import Database


class KHBot(commands.Bot):
    def __init__(self):
        self.db = Database(Bot_config.DATABASE_URL)
        self.admin_channel_id = Bot_config.ADMIN_CHANNEL_ID
        self.role_picker_channel_id = Bot_config.ROLE_PICKER_CHANNEL_ID

        intents = discord.Intents.all()
        intents.message_content = True
        intents.reactions = True

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

        await self.cogs["CategorySelection"].on_ready()
        print("Bot is up and running")


bot = KHBot()


def run_bot():
    bot.run(Bot_config.DISCORD_TOKEN)


if __name__ == "__main__":
    run_bot()
