import os

import discord
from discord import app_commands
from discord.ext import commands

from config import Bot_config
from database.database import Database
from utils.logging_config import setup_logging


class KHBot(commands.Bot):
    def __init__(self):
        self.db = Database(Bot_config.DATABASE_URL)
        self.admin_channel_id = Bot_config.ADMIN_CHANNEL_ID
        self.role_picker_channel_id = Bot_config.ROLE_PICKER_CHANNEL_ID
        self.logger = setup_logging()

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
                self.logger.info(f"Loaded {filename}")

    async def on_ready(self):
        try:
            synced = await self.tree.sync()
            self.logger.info(f"Synced {len(synced)} commands")
        except Exception as e:
            print(e)

        await self.cogs["CategorySelection"].on_ready()
        print("Bot is up and running")
        self.logger.info("Bot is up and running")

    async def on_command(self, ctx: commands.Context) -> None:
        self.logger.info(f"Command '{ctx.command}' was invoked by {ctx.author} in {ctx.guild}")

    async def on_app_command_completion(self, interaction: discord.Interaction, command: app_commands.Command):
        full_command_name = command.qualified_name
        channel = interaction.channel
        category = channel.category if channel else None
        self.logger.info(
            f"Slash command '{full_command_name}' was invoked by {interaction.user} in {interaction.guild}, "
            f"channel: {channel.name if channel else 'N/A'}, category: {category.name if category else 'N/A'}"
        )


bot = KHBot()


def run_bot():
    bot.run(Bot_config.DISCORD_TOKEN)
