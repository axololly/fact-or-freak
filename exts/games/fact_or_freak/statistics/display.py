from bot import MyBot
from discord import Interaction, Member
from discord.app_commands import command as app_command
from discord.ext.commands import Cog
from .menu import StatisticsPageMenu
from .update import UpdateStatistics as Stats

class DisplayStatistics(Cog):
    def __init__(self, bot: MyBot) -> None:
        self.bot = bot
        self.pool = bot.pool
    
    @app_command(name = "statistics", description = "View all your statistics on Fact-or-Freak.")
    async def show_statistics(self, interaction: Interaction, member: Member | None = None):
        if member:
            if not await Stats.user_is_present(member.id):
                return await interaction.response.send_message(
                    "The person you chose doesn't have any statistics!",
                    ephemeral = True
                )
        
        else:
            if not await Stats.user_is_present(interaction.user.id):
                return await interaction.response.send_message(
                    "You don't have any statistics!",
                    ephemeral = True
                )
        
        menu = StatisticsPageMenu(
            owner = interaction.user, # type: ignore
            target = member or interaction.user # type: ignore
        )
        
        await menu.create_pages()

        await interaction.response.send_message(
            embed = menu.pages[0],
            view = menu
        )

        if await menu.wait():
            await interaction.delete_original_response()
    
    @app_command(name = "badges", description = "See a list of badges you can achieve in this bot.")
    async def show_badges(self, interaction: Interaction):
        await interaction.response.send_message(
            embed = StatisticsPageMenu.BADGES_EMBED,
            delete_after = 60.0
        )


async def setup(bot: MyBot) -> None:
    await bot.add_cog(DisplayStatistics(bot))