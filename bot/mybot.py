from aiohttp import ClientSession
from asqlite import create_pool, Pool
from discord.ext.commands import Bot
from discord import Activity, ActivityType, Colour, Embed, Forbidden, HTTPException, Member, Message, Intents, User
from discord.app_commands import Group
from discord.ext.commands import Command, Context, errors
from bot.exts.fun.games.fact_or_freak.statistics.update import UpdateStatistics
from bot.utils.mentionable_tree import MentionableTree
from glob import glob as find
from gidgethub.aiohttp import GitHubAPI
from .log import get_handler
from typing import Generator

OWNER_ID = 566653183774949395

class MyBot(Bot):
    pool: Pool
    tree: MentionableTree # type: ignore
    owner: User
    github_api: GitHubAPI

    _extensions: list[str]
    "A list of module paths for extensions loaded by the bot."

    _commands: dict[str, Command]
    "A dictionary mapping names to their `Command` instances."

    EMBED_COLOUR = 0x2c89c9
    
    def __init__(self) -> None:
        super().__init__(
            command_prefix = '?',
            help_command = None,
            intents = Intents.all(),
            tree_cls = MentionableTree
        )
        
        self._extensions = []
    
    async def get_prefix(self, message: Message, /) -> str:
        async with self.pool.acquire() as conn:
            req = await conn.execute(
                "SELECT prefix FROM custom_prefixes WHERE user_id = ?",
                message.author.id
            )
            row = await req.fetchone()
        
        return row["prefix"] if row else str(self.command_prefix)
    
    async def setup_hook(self) -> None:
        self._cs = ClientSession()
        self.github_api = GitHubAPI(self._cs, "")

        self.pool = await create_pool('main-database.sql')
        UpdateStatistics.pool = self.pool

        self.docs_db_pool = await create_pool('exts/utils/documentation.sql')

        for path in find('bot/exts/**/*.py', recursive = True):
            if 'async def setup' in open(path, errors = "ignore").read():
                await self.load_extension(path.replace('.py', '').replace('\\', '.'))

        self._commands = {
            cmd.qualified_name: cmd
            for cmd in self.get_all_commands()
        }

        self.owner = self.get_user(566653183774949395) or await self.fetch_user(566653183774949395)
        
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

    async def load_extension(self, name: str, /): # type: ignore
        await super().load_extension(name)
        
        if name not in self._extensions:
            self._extensions.append(name)

    async def can_dm(self, person: User | Member, /) -> bool: # type: ignore
        "Check to see if a user can be directly messaged."
        
        try:
            await person.send()
        except Forbidden:
            return False
        except HTTPException:
            return True
    
    async def on_ready(self) -> None:
        await self.change_presence(
            activity = Activity(
                type = ActivityType.watching,
                name = "Joelle's gorgeous boobs glistening in maple syrup."
            )
        )

    async def on_command_error(self, ctx: Context, error: errors.CommandError):
        if isinstance(error, errors.CommandNotFound):
            await ctx.reply(
                embed = Embed(
                    title = "Nuh uh.",
                    description = "Looks like that's not a real command. If you wanna suggest it, send me a DM to talk to my owner, and maybe we can discuss something.",
                    colour = Colour.brand_red()
                ),
                delete_after = 5.0
            )
            return

        else:
            raise error

    async def close(self) -> None:
        await super().close()

        await self.docs_db_pool.close()
        await self.pool.close()

        await self._cs.close()
    
    def run(self) -> None: # type: ignore
        super().run(
            open("token.txt").read(),

            log_handler = get_handler(),
            root_logger = True
        )