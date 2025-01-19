from asyncio import sleep
from bot import MyBot
from discord import Colour, Embed
from discord.ext.commands import command, Cog, Context
from frontmatter import Frontmatter
from .guide import Guides

class BotUtils(Cog):
    def __init__(self, bot: MyBot) -> None:
        self.bot = bot
        self.pool = bot.pool
        
        self.fm = Frontmatter()
    
    @command(name = 'reload')
    async def reload(self, ctx: Context, extension: str):
        if ctx.author.id != 566653183774949395:
            await ctx.reply("This is for the owner only.")
        
        if extension == "all":
            for ext in self.bot._extensions:
                await self.bot.reload_extension(ext)
            
            await ctx.reply("Reloaded `all` extensions.", delete_after = 2.0)
            await sleep(2.0)
            await ctx.message.delete()
        
        else:
            await self.bot.reload_extension(extension)
            await ctx.reply(f"Reloaded the `{extension}` extension.", delete_after = 2.0)
            await sleep(2.0)
            await ctx.message.delete()

    @command(name = 'sync')
    async def sync(self, ctx: Context):
        if ctx.author.id != 566653183774949395:
            await ctx.reply("This is for the owner only.")
        
        synced = await self.bot.tree.sync()

        await ctx.reply(f"Synced {len(synced)} commands: ```yml\n{tuple(synced)!a}\n```")
    

    @command(name = 'prefix')
    async def set_prefix(self, ctx: Context, prefix: str | None = None):
        if not prefix:
            embed = Guides.build_embed(self.fm, "set-prefix")

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