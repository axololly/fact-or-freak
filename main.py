from asyncio import sleep
from bot import MyBot
from discord.ext.commands import Context

bot = MyBot()

@bot.command(name = 'reload')
async def reload(ctx: Context, extension: str):
    if ctx.author.id != 566653183774949395:
        await ctx.reply("This is for the owner only.")
    
    if extension == "all":
        for ext in bot._extensions:
            await bot.reload_extension(ext)
        
        await ctx.reply("Reloaded `all` extensions.", delete_after = 2.0)
        await sleep(2.0)
        await ctx.message.delete()
    
    else:
        await bot.reload_extension(extension)
        await ctx.reply(f"Reloaded the `{extension}` extension.", delete_after = 2.0)
        await sleep(2.0)
        await ctx.message.delete()

@bot.command(name = 'sync')
async def sync(ctx: Context):
    if ctx.author.id != 566653183774949395:
        await ctx.reply("This is for the owner only.")
    
    synced = await bot.tree.sync()

    await ctx.reply(f"Synced {len(synced)} commands.")

bot.run(open('token.txt').read())