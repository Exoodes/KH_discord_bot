import logging

import discord
from discord import app_commands
from discord.ext import commands

from bot.bot import KHBot
from database.models import BotMessage, BotMessageType, Category, CategoryRequest, ConfigEmoji, UserCategory


class CategorySelection(commands.Cog):
    def __init__(self, bot: KHBot):
        self.bot = bot

    async def on_ready(self):
        await self.setup_category_choosing_message()

    @app_commands.command(name="remove_category")
    @app_commands.checks.has_permissions(administrator=True)
    async def remove_category(self, interaction: discord.Interaction, name: str):
        await interaction.response.defer(ephemeral=True)
        session = self.bot.db.Session()

        try:
            category = session.query(Category).filter_by(name=name).first()
            if category:
                category = discord.utils.get(interaction.guild.categories, id=category.channel_id)
                await category.delete()

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
            overwrites = {}
            overwrites[interaction.guild.default_role] = discord.PermissionOverwrite(view_channel=False)
            category = await interaction.guild.create_category(name=f"{name}", overwrites=overwrites)

            new_category = Category(channel_id=category.id, name=name, emoji=emoji, is_public=is_public)
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
    async def setup_category_message(self, interaction: discord.Interaction):
        embed = await self.create_category_embed()
        channel = self.bot.get_channel(self.bot.role_picker_channel_id)
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

    async def setup_category_choosing_message(self):
        session = self.bot.db.Session()

        role_picker = session.query(BotMessage).filter_by(message_type=BotMessageType.CategoryChooser).first()
        session.close()

        if not role_picker:
            # Nothing in database
            await self.create_category_choosing_message()
            return

        if role_picker.channel_id != self.bot.role_picker_channel_id:
            # Channel ID doesn't match
            await self.create_category_choosing_message()
            return

        channel = self.bot.get_channel(role_picker.channel_id)
        try:
            await channel.fetch_message(role_picker.message_id)
        except discord.NotFound:
            # Message not found
            await self.create_category_choosing_message()

    async def create_category_choosing_message(self):
        session = self.bot.db.Session()
        role_picker = session.query(BotMessage).filter_by(message_type=BotMessageType.CategoryChooser).first()
        if role_picker:
            session.delete(role_picker)
            session.commit()

        embed = await self.create_category_embed()
        channel = self.bot.get_channel(self.bot.role_picker_channel_id)

        message = await channel.send(embed=embed)

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

    async def on_reaction_role_picker(self, payload: discord.RawReactionActionEvent):
        session = self.bot.db.Session()

        try:
            bot_message = (
                session.query(BotMessage)
                .filter_by(
                    channel_id=payload.channel_id,
                    message_id=payload.message_id,
                    message_type=BotMessageType.CategoryChooser,
                )
                .first()
            )
            if not bot_message:
                return

            category = session.query(Category).filter_by(emoji=str(payload.emoji)).first()
            if not category:
                return

            if category.is_public:
                category_channel = self.bot.get_channel(category.channel_id)
                await category_channel.set_permissions(payload.member, view_channel=True)
                logging.info(f"User {payload.user_id} joined category {category.name}")
                return

            user_category = (
                session.query(UserCategory).filter_by(user_id=payload.user_id, category_id=category.id).first()
            )
            if user_category:
                channel = self.bot.get_channel(payload.channel_id)
                message = await channel.fetch_message(payload.message_id)
                reaction = discord.utils.get(message.reactions, emoji=payload.emoji.name)
                await reaction.remove(payload.member)
                return

            admin_channel = self.bot.get_channel(self.bot.admin_channel_id)
            admin_embed = await self.create_admin_embed(payload.member, category)
            admin_message = await admin_channel.send(embed=admin_embed)

            new_request = CategoryRequest(
                user_id=payload.user_id, category_id=category.id, request_message_id=admin_message.id
            )
            session.add(new_request)
            session.commit()

            accept_emoji = session.query(ConfigEmoji).filter_by(purpose="accept").first()
            decline_emoji = session.query(ConfigEmoji).filter_by(purpose="decline").first()
            await admin_message.add_reaction(accept_emoji.emoji_id)
            await admin_message.add_reaction(decline_emoji.emoji_id)

            channel = self.bot.get_channel(payload.channel_id)
            message = await channel.fetch_message(payload.message_id)
            reaction = discord.utils.get(message.reactions, emoji=payload.emoji.name)
            await reaction.remove(payload.member)
        finally:
            session.close()

    async def on_reaction_decline(self, payload: discord.RawReactionActionEvent):
        session = self.bot.db.Session()
        request = session.query(CategoryRequest).filter_by(request_message_id=payload.message_id).first()

        request.status = "declined"
        session.commit()

        # Notify user
        user = self.bot.get_user(request.user_id)
        category = session.query(Category).filter_by(id=request.category_id).first()
        await user.send(f"Your request to join the category '{category.name}' has been denied.")

        # Update admin message
        channel = self.bot.get_channel(payload.channel_id)
        admin_message = await channel.fetch_message(payload.message_id)
        embed = admin_message.embeds[0]
        embed.add_field(name="Status", value="Denied", inline=False)
        embed.add_field(name="Denied by", value=payload.member.name, inline=False)
        await admin_message.edit(embed=embed)
        await admin_message.clear_reactions()

        # Log the action
        logging.info(
            f"Admin {payload.member.name} denied category request for user {request.user_id} to join category {category.name}"
        )

    async def on_reaction_accept(self, payload: discord.RawReactionActionEvent):
        session = self.bot.db.Session()
        request = session.query(CategoryRequest).filter_by(request_message_id=payload.message_id).first()

        request.status = "approved"
        session.commit()

        # Notify user
        user = self.bot.get_user(request.user_id)
        category = session.query(Category).filter_by(id=request.category_id).first()
        await user.send(f"Your request to join the category '{category.name}' has been approved.")

        # Add user to category
        category_channel = self.bot.get_channel(category.channel_id)
        await category_channel.set_permissions(payload.member, view_channel=True)

        # Update admin message
        channel = self.bot.get_channel(payload.channel_id)
        admin_message = await channel.fetch_message(payload.message_id)
        embed = admin_message.embeds[0]
        embed.add_field(name="Status", value="approved", inline=False)
        embed.add_field(name="Accepted by", value=payload.member.name, inline=False)
        await admin_message.edit(embed=embed)
        await admin_message.clear_reactions()

        # Log the action
        logging.info(
            f"Admin {payload.member.name} accepted category request for user {request.user_id} to join category {category.name}"
        )

    async def handle_request(self, payload: discord.RawReactionActionEvent) -> None:
        session = self.bot.db.Session()

        accept_emoji = session.query(ConfigEmoji).filter_by(purpose="accept").first()
        decline_emoji = session.query(ConfigEmoji).filter_by(purpose="decline").first()

        if payload.emoji.name == accept_emoji.emoji_id:
            await self.on_reaction_accept(payload)
        elif payload.emoji.name == decline_emoji.emoji_id:
            await self.on_reaction_decline(payload)

        session.close()

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent) -> None:
        if payload.user_id == self.bot.user.id:
            return

        session = self.bot.db.Session()

        chooser_message = (
            session.query(BotMessage)
            .filter_by(
                channel_id=payload.channel_id,
                message_id=payload.message_id,
                message_type=BotMessageType.CategoryChooser,
            )
            .first()
        )
        if chooser_message:
            session.close()
            await self.on_reaction_role_picker(payload)
            return

        request_message = (
            session.query(CategoryRequest).filter_by(request_message_id=payload.message_id, status="pending")
        ).first()

        if request_message:
            await self.handle_request(payload)

        session.close()

    async def create_admin_embed(self, user: discord.User, category: Category) -> discord.Embed:
        embed = discord.Embed(
            title="Category Join Request", description=f"{user.mention} wants to join {category.name}"
        )
        embed.add_field(name="User", value=user.name, inline=True)
        embed.add_field(name="Category", value=category.name, inline=True)
        return embed

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
