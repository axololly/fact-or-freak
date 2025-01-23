from bot import MyBot
from discord.ext.commands import Cog

class OneSentenceEachGame(Cog):
    def __init__(self, bot: MyBot) -> None:
        self.bot = bot
        self.pool = bot.pool


async def setup(bot: MyBot) -> None:
    await bot.add_cog(OneSentenceEachGame(bot))