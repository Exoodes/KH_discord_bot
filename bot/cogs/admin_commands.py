import discord
from discord import app_commands
from discord.ext import commands

from bot.bot import KHBot


class AdminCommands(commands.Cog):
    def __init__(self, bot: KHBot):
        self.bot = bot

    @app_commands.command(name="purge")
    @app_commands.describe(amount="Number of messages to delete")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def purge(self, interaction: discord.Interaction, amount: int):
        """Deletes a number of messages in the channel"""
        if amount <= 0:
            await interaction.response.send_message(
                "Please provide a positive number of messages to delete.", ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        deleted = await interaction.channel.purge(limit=amount)

        await interaction.followup.send(f"Deleted {len(deleted)} message(s).", ephemeral=True)
        self.bot.logger.info(f"Deleted {len(deleted)} message(s) in {interaction.channel.name}")


async def setup(bot):
    await bot.add_cog(AdminCommands(bot))
