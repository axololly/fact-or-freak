from asqlite import create_pool, Pool
from datetime import datetime as dt
from discord.ext.commands import Bot
from discord import Intents, Activity, ActivityType
from discord.app_commands import Group
from discord.ext.commands import Command
from exts.games.fact_or_freak.statistics.update import UpdateStatistics
from exts.utils.mentionable_tree import MentionableTree
from glob import glob as find
from .log import get_handler
from typing import Generator

OWNER_ID = 566653183774949395

class MyBot(Bot):
    pool: Pool
    _extensions: list[str]
    tree: MentionableTree # type: ignore

    _commands: dict[str, Command]
    "A dictionary mapping names to their `Command` instances."
    
    def __init__(self) -> None:
        super().__init__(
            command_prefix = '?',
            intents = Intents.all(),
            tree_cls = MentionableTree
        )
        
        self._extensions = []
        "A list of module paths for extensions loaded by the bot."

        self._commands = {}
    
    async def setup_hook(self) -> None:
        self.pool = await create_pool('data.sql')
        UpdateStatistics.pool = self.pool

        self.docs_db_pool = await create_pool('../exts/utils/docs/index.sql')

        for path in find('exts/**/*.py', recursive = True):
            if 'async def setup' in open(path, errors = "ignore").read():
                path = path.replace('.py', '').replace('\\', '.')
                
                self._extensions.append(path)

                await self.load_extension(path)

        self._commands = {
            cmd.qualified_name: cmd
            for cmd in self.get_all_commands()
        }
        
    def get_all_commands(self) -> Generator[Command, None, None]:
        """
        Returns a generator of all the commands in the bot including
        from loaded cogs, as well as flattening out groups.
        """

        def unpack_group(group: Group, /) -> Generator[Command, None, None]:
            for sub in group.commands:
                if isinstance(sub, Group):
                    yield from unpack_group(sub)
                else:
                    yield sub # type: ignore
            
        yield from self.walk_commands()
        
        for cog in self.cogs.values():
            yield from cog.walk_commands()

            for cmd in cog.walk_app_commands():
                if isinstance(cmd, Group):
                    yield from unpack_group(cmd)
                else:
                    yield cmd # type: ignore
    
    async def on_ready(self) -> None:
        await self.change_presence(
            activity = Activity(
                type = ActivityType.watching,
                name = "Joelle's gorgeous boobs glistening in maple syrup."
            )
        )
    
    def run(self, token: str) -> None: # type: ignore
        super().run(token, log_handler = get_handler())