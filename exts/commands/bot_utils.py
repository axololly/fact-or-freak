from aiofiles import open as aopen
from asyncio import sleep as wait
from bot import MyBot
from discord import Embed
from discord.ext.commands import check, command, errors, group, Cog, Context
from frontmatter import Frontmatter
from .guide import Guides
from logging import getLogger

logger = getLogger(__name__)

def is_owner():
    async def predicate(ctx: Context) -> bool:
        if ctx.author.id == 566653183774949395:
            return True
        else:
            await ctx.reply("This is for the owner only.")
            return False

    return check(predicate)

# For clarity in typehints
type Alias = str
type ExtensionName = str

BLUE_ARROW_RIGHT = "<a:blue_arrow_right:1330550362410848317>"

class BotUtils(Cog):
    reload_aliases: dict[Alias, ExtensionName]

    def __init__(self, bot: MyBot) -> None:
        self.bot = bot
        self.pool = bot.pool
        
        self.fm = Frontmatter()

    async def cog_load(self) -> None:
        self.reload_aliases = {}

        async with aopen("exts/commands/aliases.txt") as f:
            for pos, line in enumerate((await f.read()).split('\n')):
                if not line:
                    continue
                
                parts = line.split('\x00')

                if len(parts) != 2:
                    logger.critical(f"'aliases.txt' file contains an invalid format on line {pos + 1}. Please examine now.")

                    return
                
                alias, ext = parts

                self.reload_aliases[alias] = ext
    
    async def cog_unload(self) -> None:
        async with aopen("exts/commands/aliases.txt", "w") as f:
            await f.write(
                '\n'.join(
                    f"{alias}\x00{ext}"
                    for alias, ext in self.reload_aliases.items()
                )
            )

    @is_owner()
    @command()
    async def load(self, ctx: Context, extension: str):
        await self.bot.load_extension(extension)

        await ctx.reply(f"Loaded the `{extension}` extension.")
    
    @load.error
    async def load_EH(self, ctx: Context, error: errors.CommandError):
        if isinstance(error, errors.NoEntryPointError):
            return await ctx.reply("That file doesn't have a `setup()` function.")
        
        elif isinstance(error, errors.ExtensionAlreadyLoaded):
            return await ctx.reply("That extension is already loaded.")

        elif isinstance(error, errors.ExtensionNotFound):
            return await ctx.reply("That's not a valid extension path. You sure that's right?")
        
        else:
            raise error
    
    @is_owner()
    @group(name = 'reload', invoke_without_command = True)
    async def reload(self, ctx: Context, extension: str):
        if not ctx.guild:
            await ctx.reply("You can only run this in a guild!")
            return
        
        if extension == "all":
            for ext in self.bot._extensions:
                await self.bot.reload_extension(ext)
            
            return await ctx.reply("Reloaded `all` extensions.")
        
        # If extension is an alias, correct it to the default name
        extension = self.reload_aliases.get(extension, extension)

        if extension not in self.bot._extensions:
            return await ctx.reply("That's not a valid extension.", delete_after = 2.0)

        await self.bot.reload_extension(extension)
        await ctx.reply(f"Reloaded the `{extension}` extension.", delete_after = 2.0)
        
        await wait(2.0)
        
        await ctx.message.delete()

    @is_owner()
    @reload.command(name = "alias")
    async def add_alias(self, ctx: Context, extension: str, alias: str):
        if extension not in self.bot._extensions:
            return await ctx.reply("That's not a valid extension.", delete_after = 2.0)
        
        existing = self.reload_aliases.get(alias)
        existing_text = f"from `{existing}` " if existing else ''

        self.reload_aliases[alias] = extension

        await ctx.reply(f"Changed the alias `{alias}` to point {existing_text}to the extension `{extension}`")

    @reload.command(name = "aliases")
    async def show_aliases(self, ctx: Context):
        await ctx.reply(
            embed = Embed(
                title = "Current Aliases",
                description = '\n'.join(
                    f"- `{alias}` {BLUE_ARROW_RIGHT} `{ext}`"
                    for alias, ext in self.reload_aliases.items()
                ) or "Hmm, there's nothing here.",
                colour = self.bot.EMBED_COLOUR
            )
        )

    @command(name = 'sync')
    async def sync(self, ctx: Context):
        synced = await self.bot.tree.sync()

        await ctx.reply(f"Synced {len(synced)} commands:\n{'\n'.join(f"{x}. `/{cmd}`" for x, cmd in enumerate(synced))}")
    

    @command(name = 'prefix')
    async def set_prefix(self, ctx: Context, prefix: str | None = None):
        if not prefix:
            embed = Guides.build_embed(self.fm, "guides/set-prefix.md")

            if embed:
                await ctx.reply(embed = embed)
            
            return
        
        async with self.pool.acquire() as conn:
            req = await conn.execute("SELECT prefix FROM custom_prefixes WHERE user_id = ?", ctx.author.id)
            row = await req.fetchone()

            current_prefix = row["prefix"] if row else self.bot.command_prefix

            if prefix == current_prefix:
                await ctx.reply("You already have that as your default prefix!")
                return
            
            if prefix == "reset":
                await conn.execute("DELETE FROM custom_prefixes WHERE user_id = ?", ctx.author.id)

                await ctx.reply(f"Your prefix has been reset to the default `{self.bot.command_prefix}`")

                return
            
            await conn.execute(
                """
                INSERT INTO custom_prefixes (user_id, prefix) VALUES (:user_id, :prefix)
                
                ON CONFLICT (user_id) DO

                UPDATE SET prefix = :prefix WHERE user_id = :user_id
                """,
                {
                    "user_id": ctx.author.id,
                    "prefix": prefix
                }
            )

            await ctx.reply(f"Your prefix has been changed from `{current_prefix}` to `{prefix}`")

            return


async def setup(bot: MyBot) -> None:
    await bot.add_cog(BotUtils(bot))