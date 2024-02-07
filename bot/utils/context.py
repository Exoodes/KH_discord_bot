from typing import Any, Optional, Union

import disnake as discord
from disnake.ext import commands
from disnake.utils import get


class Context(commands.Context):
    """
    custom Context object passed in every ctx variable
    in your commands. provides some useful getter shortcuts
    """

    def get_category(self, name: Optional[str] = None, **kwargs: Any) -> Optional[discord.CategoryChannel]:
        assert self.guild, "this method can only be run for guild events"
        if name is not None:
            kwargs.update({"name": name})
        return get(self.guild.categories, **kwargs)

    def get_channel(self, name: Optional[str] = None, **kwargs: Any) -> Optional[discord.abc.GuildChannel]:
        assert self.guild, "this method can only be run for guild events"
        if name is not None:
            kwargs.update({"name": name})
        return get(self.guild.channels, **kwargs)

    def get_role(self, name: Optional[str] = None, **kwargs: Any) -> Optional[discord.Role]:
        assert self.guild, "this method can only be run for guild events"
        if name is not None:
            kwargs.update({"name": name})
        return get(self.guild.roles, **kwargs)

    def get_emoji(self, name: Optional[str] = None, **kwargs: Any) -> Optional[discord.Emoji]:
        if name is not None:
            kwargs.update({"name": name})
        return get(self.bot.emojis, **kwargs)

    def get_member(self, name: Optional[str] = None, **kwargs: Any) -> Optional[discord.Member]:
        assert self.guild, "this method can only be run for guild events"
        if name is not None:
            kwargs.update({"name": name})
        return get(self.guild.members, **kwargs)
