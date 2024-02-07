import disnake as discord
from disnake.ext import commands
from disnake.ext.commands import has_permissions


class Admin(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command(aliases=['clean', 'delete', 'smaz', 'smaž', 'vymaz', 'vymaž'])
    @has_permissions(manage_messages=True)
    async def purge(self, ctx: discord.ext.commands.Context, limit: int = 0) -> None:
        assert isinstance(ctx.channel, (discord.TextChannel, discord.Thread))
        await ctx.channel.purge(limit=limit + 1)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Admin(bot))
