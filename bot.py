from asqlite import create_pool, Pool
from discord.ext.commands import Bot
from discord import Intents, Activity, ActivityType
from glob import glob
from exts.statistics.update import UpdateStatistics

OWNER_ID = 566653183774949395

class MyBot(Bot):
    pool: Pool
    _extensions: list[str]
    
    def __init__(self) -> None:
        super().__init__(
            command_prefix = '?',
            intents = Intents.all()
        )
        self._extensions = []
    
    async def setup_hook(self) -> None:
        self.pool = await create_pool('data.sql')
        UpdateStatistics.pool = self.pool

        for path in glob('exts/**/*.py', recursive = True):
            if 'async def setup' in open(path, errors = "ignore").read():
                path = path.replace('.py', '').replace('\\', '.')
                
                self._extensions.append(path)

                await self.load_extension(path)
        
        await self.tree.sync()
    
    async def on_ready(self) -> None:
        await self.change_presence(
            activity = Activity(
                type = ActivityType.watching,
                name = "Joelle's gorgeous boobs glistening in maple syrup."
            )
        )