import logging
from typing import Any

from disnake import Activity, ActivityType
from disnake.ext import commands

log = logging.getLogger(__name__)

class KH_BOT(commands.Bot):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.activity = self.activity or Activity(
            type=ActivityType.listening, name="!help")

    async def on_ready(self) -> None:
        log.info("Bot is now all ready to go")
