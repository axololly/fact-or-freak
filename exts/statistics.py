from bot import MyBot
from discord import Interaction, Member
# from discord.app_commands import command as app_command
from discord.ext.commands import Cog, Context, command
from discord.ui import button, Button
from .bases import FixedTimeView
from time import time

class Example(FixedTimeView):
    def __init__(self):
        super().__init__(timeout = 15)
    
    @button(label = "0")
    async def test(self, interaction: Interaction, this: Button):
        this.label = str(int(this.label) + 1)
        await interaction.response.edit_message(view = self)

class Statistics(Cog):
    def __init__(self, bot: MyBot) -> None:
        self.bot = bot
        self.pool = bot.pool

    @command(name = "test")
    async def test(self, ctx: Context):
        view = Example()

        await ctx.reply(view = view)

        t0 = time()

        await view.wait()

        time_taken = time() - t0

        await ctx.reply(f"View closed. Time taken: {time_taken}")


async def setup(bot: MyBot) -> None:
    await bot.add_cog(Statistics(bot))