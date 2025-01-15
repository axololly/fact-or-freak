from asqlite import create_pool, Pool
from discord.ext.commands import Bot
from discord import Intents, Activity, ActivityType
from discord.ext.commands import Command
from exts.fact_or_freak.statistics.update import UpdateStatistics
from exts.utils.mentionable_tree import MentionableTree
from glob import glob as find

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
            intents = Intents.all()
        )
        
        self._extensions: list[str] = []
        "A list of module paths for extensions loaded by the bot."
    
    async def setup_hook(self) -> None:
        self.pool = await create_pool('data.sql')
        UpdateStatistics.pool = self.pool

        for path in find('exts/**/*.py', recursive = True):
            if 'async def setup' in open(path, errors = "ignore").read():
                path = path.replace('.py', '').replace('\\', '.')
                
                self._extensions.append(path)

                await self.load_extension(path)

        self._commands = {
            cmd.name: cmd
            for cmd in self.walk_commands()
        }
        
        # await self.tree.sync()
    
    async def on_ready(self) -> None:
        await self.change_presence(
            activity = Activity(
                type = ActivityType.watching,
                name = "Joelle's gorgeous boobs glistening in maple syrup."
            )
        )