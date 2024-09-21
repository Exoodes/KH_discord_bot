import discord
from discord import app_commands
from discord.ext import commands

from bot.bot import KHBot


class AdminCommands(commands.Cog):
    def __init__(self, bot: KHBot):
        self.bot = bot

    @app_commands.command(name="clean")
    @app_commands.describe(amount="Number of messages to delete")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def clean(self, interaction: discord.Interaction, amount: int):
        """ "Deletes a number of messages in the channel"""
        if amount <= 0:
            await interaction.response.send_message(
                "Please provide a positive number of messages to delete.", ephemeral=True
            )
            return

        # Defer the response since deletion might take a while
        await interaction.response.defer(ephemeral=True)

        # Delete messages
        deleted = await interaction.channel.purge(limit=amount)

        # Send confirmation
        await interaction.followup.send(f"Deleted {len(deleted)} message(s).", ephemeral=True)


async def setup(bot):
    await bot.add_cog(AdminCommands(bot))
