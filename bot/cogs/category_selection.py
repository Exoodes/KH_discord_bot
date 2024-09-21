import logging

import discord
from discord import app_commands
from discord.ext import commands

from bot.bot import KHBot
from database.models import BotMessage, BotMessageType, Category


class CategorySelection(commands.Cog):
    def __init__(self, bot: KHBot):
        self.bot = bot

    @app_commands.command(name="remove_category")
    @app_commands.checks.has_permissions(administrator=True)
    async def remove_category(self, interaction: discord.Interaction, name: str):
        await interaction.response.defer(ephemeral=True)
        session = self.bot.db.Session()

        try:
            category = session.query(Category).filter_by(name=name).first()
            if category:
                session.delete(category)
                session.commit()

                await self.update_category_message()

                response = f"Category '{name}' has been removed."
            else:
                response = f"Category '{name}' not found."
        except Exception as e:
            session.rollback()
            response = f"An error occurred: {str(e)}"
        finally:
            await interaction.followup.send(response, ephemeral=True)
            session.close()

    @app_commands.command(name="add_category")
    @app_commands.checks.has_permissions(administrator=True)
    async def add_category(
        self, interaction: discord.Interaction, name: str, emoji: str, is_public: bool = True
    ) -> None:
        await interaction.response.defer(ephemeral=True)
        session = self.bot.db.Session()

        try:
            new_category = Category(name=name, emoji=emoji, is_public=is_public)
            session.add(new_category)
            session.commit()

            await self.update_category_message()

            await interaction.followup.send(f"Category '{name}' with emoji {emoji} has been added.", ephemeral=True)
        except Exception as e:
            session.rollback()
            await interaction.followup.send(f"An error occurred: {str(e)}", ephemeral=True)
        finally:
            session.close()

    @app_commands.command(name="setup_category_message")
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_category_message(self, interaction: discord.Interaction, channel: discord.TextChannel):
        embed = await self.create_category_embed()
        message = await channel.send(embed=embed)

        session = self.bot.db.Session()
        try:
            categories = session.query(Category).all()
            for category in categories:
                await message.add_reaction(category.emoji)

            bot_message = BotMessage(
                channel_id=channel.id, message_id=message.id, message_type=BotMessageType.CategoryChooser
            )
            session.add(bot_message)
            session.commit()
        finally:
            session.close()

        await interaction.response.send_message("Category selection message has been set up.", ephemeral=True)

    async def update_category_message(self) -> None:
        session = self.bot.db.Session()

        try:
            bot_message = session.query(BotMessage).filter_by(message_type=BotMessageType.CategoryChooser).first()
            if bot_message:
                channel = self.bot.get_channel(bot_message.channel_id)
                message = await channel.fetch_message(bot_message.message_id)

                new_embed = await self.create_category_embed()
                await message.edit(embed=new_embed)

                # Update reactions
                await message.clear_reactions()
                categories = session.query(Category).all()
                for category in categories:
                    await message.add_reaction(category.emoji)

        except Exception as e:
            logging.error(f"Error updating category message: {str(e)}")

        finally:
            session.close()

    async def create_category_embed(self) -> discord.Embed:
        embed = discord.Embed(title="Category Selection", description="React to join a category!")
        session = self.bot.db.Session()

        try:
            categories = session.query(Category).all()
            for category in categories:
                embed.add_field(name=f"{category.emoji} {category.name}", value="\u200b", inline=False)
        finally:
            session.close()
        return embed


async def setup(bot):
    await bot.add_cog(CategorySelection(bot))
