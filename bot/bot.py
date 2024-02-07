import logging
from typing import Any

from disnake import Activity, ActivityType
from disnake.ext import commands
from utils.context import Context

log = logging.getLogger(__name__)


class KH_BOT(commands.Bot):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.activity = self.activity or Activity(
            type=ActivityType.listening, name="Napiš /pomoc")

    async def on_ready(self) -> None:
        log.info("Bot is now all ready to go")

    async def on_command(self, ctx: Context) -> None:
        if ctx.message.content:
            command = ctx.message.content
            log.info(
                f'in #{ctx.channel} @{ctx.author} used command: {command}')
        else:
            params = ' '.join(map(str, ctx.kwargs.values()))
            command = f"{ctx.prefix}{ctx.command} {params}"
            log.info(
                f'in #{ctx.channel} @{ctx.author} used slash command: {command}')

    async def on_error(self, event_method: str, *args: Any, **kwargs: Any) -> None:
        """ reimplement on_error method to print to a log file instead of sys.stderr"""
        log.error(f'Ignoring exception in %s' % (event_method,), exc_info=True)

    def add_cog(self, cog: commands.Cog, *, override: bool = False) -> None:
        log.info("loading cog: %s", cog.qualified_name)
        super().add_cog(cog, override=override)

    def remove_cog(self, name: str) -> None:
        log.info("unloading cog: %s", name)
        super().remove_cog(name)
