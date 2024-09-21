from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands
from sqlalchemy.orm import Session

from bot.bot import KHBot
from database.models import BotMessage, BotMessageType, Category, CategoryRequest, ConfigEmoji, UserCategory


class CategorySelection(commands.Cog):
    def __init__(self, bot: KHBot):
        self.bot = bot

    async def on_ready(self):
        await self.setup_category_selection_message()

    @app_commands.command(name="remove_category")
    @app_commands.describe(name="Name of the category to remove")
    @app_commands.checks.has_permissions(administrator=True)
    async def remove_category(self, interaction: discord.Interaction, name: str):
        await interaction.response.defer(ephemeral=True)

        with self.bot.db.dp_session() as session:
            try:
                category_to_delete = session.query(Category).filter_by(name=name).first()
                if category_to_delete:
                    discord_category = discord.utils.get(interaction.guild.categories, id=category_to_delete.channel_id)
                    if discord_category:
                        await discord_category.delete()

                    session.delete(category_to_delete)

                    response = f"Category '{name}' has been removed."
                else:
                    response = f"Category '{name}' not found."
            except Exception as e:
                response = f"An error occurred: {str(e)}"

        await self.update_category_message()
        self.bot.logger.info(response, exc_info=True)
        await interaction.followup.send(response, ephemeral=True)

    @app_commands.command(name="add_category")
    @app_commands.describe(
        name="Name of the category to add",
        emoji="Emoji to represent the category",
        is_public="Whether the category is public",
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def add_category(
        self, interaction: discord.Interaction, name: str, emoji: str, is_public: bool = True
    ) -> None:
        await interaction.response.defer(ephemeral=True)

        with self.bot.db.dp_session() as session:
            try:
                overwrites = {interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False)}
                category = await interaction.guild.create_category(name=f"{name}", overwrites=overwrites)
                new_category = Category(channel_id=category.id, name=name, emoji=emoji, is_public=is_public)
                session.add(new_category)

                response = f"Category '{name}' with emoji {emoji} has been added."
            except Exception as e:
                response = f"Error while adding category: {str(e)}"

        await self.update_category_message()
        self.bot.logger.info(response, exc_info=True)
        await interaction.followup.send(response, ephemeral=True)

    async def setup_category_selection_message(self):
        with self.bot.db.dp_session() as session:
            role_picker = session.query(BotMessage).filter_by(message_type=BotMessageType.CategoryChooser).first()

            if not role_picker or role_picker.channel_id != self.bot.role_picker_channel_id:
                # Nothing in database
                await self.create_category_choosing_message()
                return

            channel = self.bot.get_channel(role_picker.channel_id)
            try:
                await channel.fetch_message(role_picker.message_id)
            except discord.NotFound:
                await self.create_category_choosing_message()

    async def create_category_choosing_message(self):
        with self.bot.db.dp_session() as session:
            role_picker = session.query(BotMessage).filter_by(message_type=BotMessageType.CategoryChooser).first()
            if role_picker:
                session.delete(role_picker)

            embed = await self.create_category_embed()
            channel = self.bot.get_channel(self.bot.role_picker_channel_id)
            message = await channel.send(embed=embed)

            categories = session.query(Category).all()
            for category in categories:
                await message.add_reaction(category.emoji)

            bot_message = BotMessage(
                channel_id=channel.id, message_id=message.id, message_type=BotMessageType.CategoryChooser
            )
            session.add(bot_message)

    async def on_reaction_role_picker(self, payload: discord.RawReactionActionEvent):
        with self.bot.db.dp_session() as session:
            category = self.get_category_by_emoji(session, str(payload.emoji))
            if not category:
                return

            if category.is_public:
                await self.handle_public_category(payload, category)
            else:
                await self.handle_private_category(payload, category, session)

    async def handle_public_category(self, payload: discord.RawReactionActionEvent, category: Category):
        category_channel = self.bot.get_channel(category.channel_id)
        await category_channel.set_permissions(payload.member, view_channel=True)
        self.bot.logger.info(f"User {payload.user_id} joined category {category.name}")

    async def handle_private_category(
        self, payload: discord.RawReactionActionEvent, category: Category, session: Session
    ):
        user_category = (
            session.query(UserCategory).filter_by(user_id=payload.user_id, category_id=category.id).one_or_none()
        )

        if user_category:
            await self.remove_reaction(payload)
            return

        await self.create_category_request(payload, category, session)

    async def create_category_request(
        self, payload: discord.RawReactionActionEvent, category: Category, session: Session
    ):
        admin_channel = self.bot.get_channel(self.bot.admin_channel_id)
        admin_embed = await self.create_admin_embed(payload.member, category)
        admin_message = await admin_channel.send(embed=admin_embed)

        new_request = CategoryRequest(
            user_id=payload.user_id, category_id=category.id, request_message_id=admin_message.id
        )
        session.add(new_request)

        accept_emoji = self.get_config_emoji(session, "accept")
        decline_emoji = self.get_config_emoji(session, "decline")
        await admin_message.add_reaction(accept_emoji.emoji_id)
        await admin_message.add_reaction(decline_emoji.emoji_id)

        await self.remove_reaction(payload)

    async def remove_reaction(self, payload: discord.RawReactionActionEvent):
        channel = self.bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        reaction = discord.utils.get(message.reactions, emoji=payload.emoji.name)
        await reaction.remove(payload.member)

    async def on_reaction_decline(self, payload: discord.RawReactionActionEvent, session: Session) -> None:
        request = self.get_category_request(session, payload.message_id)
        if not request:
            return

        request.status = "declined"
        category = self.get_category_by_id(session, request.category_id)

        user = self.bot.get_user(request.user_id)
        await user.send(f"Your request to join the category '{category.name}' has been denied.")

        await self.update_admin_message(payload, "Denied")
        self.bot.logger.info(
            f"Admin {payload.member.name} denied category request for user {request.user_id} to join category {category.name}"
        )

    async def on_reaction_accept(self, payload: discord.RawReactionActionEvent, session: Session) -> None:
        request = self.get_category_request(session, payload.message_id)
        if not request:
            return

        request.status = "approved"
        category = self.get_category_by_id(session, request.category_id)

        user = self.bot.get_user(request.user_id)
        await user.send(f"Your request to join the category '{category.name}' has been approved.")

        category_channel = self.bot.get_channel(category.channel_id)
        await category_channel.set_permissions(payload.member, view_channel=True)

        await self.update_admin_message(payload, "Approved")
        self.bot.logger.info(
            f"Admin {payload.member.name} accepted category request for user {request.user_id} to join category {category.name}"
        )

    async def handle_request(self, payload: discord.RawReactionActionEvent) -> None:
        with self.bot.db.dp_session() as session:
            accept_emoji = session.query(ConfigEmoji).filter_by(purpose="accept").first()
            decline_emoji = session.query(ConfigEmoji).filter_by(purpose="decline").first()

            if payload.emoji.name == accept_emoji.emoji_id:
                await self.on_reaction_accept(payload, session)
            elif payload.emoji.name == decline_emoji.emoji_id:
                await self.on_reaction_decline(payload, session)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent) -> None:
        if payload.user_id == self.bot.user.id:
            return

        with self.bot.db.dp_session() as session:
            chooser_message = (
                session.query(BotMessage)
                .filter_by(
                    channel_id=payload.channel_id,
                    message_id=payload.message_id,
                    message_type=BotMessageType.CategoryChooser,
                )
                .one_or_none()
            )

            if chooser_message:
                session.close()
                await self.on_reaction_role_picker(payload)
                return

            request_message = (
                session.query(CategoryRequest).filter_by(request_message_id=payload.message_id, status="pending")
            ).one_or_none()

            if request_message:
                await self.handle_request(payload)

    async def create_admin_embed(self, user: discord.User, category: Category) -> discord.Embed:
        embed = discord.Embed(
            title="Category Join Request", description=f"{user.mention} wants to join {category.name}"
        )
        embed.add_field(name="User", value=user.name, inline=True)
        embed.add_field(name="Category", value=category.name, inline=True)
        return embed

    async def update_category_message(self) -> None:
        with self.bot.db.dp_session() as session:
            bot_message = session.query(BotMessage).filter_by(message_type=BotMessageType.CategoryChooser).one_or_none()

            if bot_message:
                channel = self.bot.get_channel(bot_message.channel_id)
                message = await channel.fetch_message(bot_message.message_id)

                new_embed = await self.create_category_embed()
                await message.edit(embed=new_embed)

                await message.clear_reactions()
                categories = session.query(Category).all()
                for category in categories:
                    await message.add_reaction(category.emoji)

    async def create_category_embed(self) -> discord.Embed:
        embed = discord.Embed(title="Category Selection", description="React to join a category!")
        with self.bot.db.dp_session() as session:
            categories = session.query(Category).all()
            for category in categories.scalars():
                embed.add_field(name=f"{category.emoji} {category.name}", value="\u200b", inline=False)

        return embed

    async def update_admin_message(self, payload: discord.RawReactionActionEvent, status: str) -> None:
        channel = self.bot.get_channel(payload.channel_id)
        admin_message = await channel.fetch_message(payload.message_id)
        embed = admin_message.embeds[0]
        embed.add_field(name="Status", value=status, inline=False)
        embed.add_field(name="Processed by", value=payload.member.name, inline=False)
        await admin_message.edit(embed=embed)
        await admin_message.clear_reactions()

    def get_category(self, session: Session, name: str) -> Optional[Category]:
        return session.query(Category).filter_by(name=name).one_or_none()

    def get_category_by_emoji(self, session: Session, emoji: str) -> Optional[Category]:
        return session.query(Category).filter_by(emoji=emoji).one_or_none()

    def get_category_by_id(self, session: Session, category_id: int) -> Optional[Category]:
        return session.query(Category).filter_by(id=category_id).one_or_none()

    def get_config_emoji(self, session: Session, purpose: str) -> Optional[ConfigEmoji]:
        return session.query(ConfigEmoji).filter_by(purpose=purpose).one_or_none()

    def get_category_request(self, session: Session, message_id: int) -> Optional[CategoryRequest]:
        return session.query(CategoryRequest).filter_by(request_message_id=message_id).one_or_none()


async def setup(bot):
    await bot.add_cog(CategorySelection(bot))
