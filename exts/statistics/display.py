from bot import MyBot, OWNER_ID
from decals import DEVELOPER, BRONZE, SILVER, GOLD, DIAMOND
from discord import Colour, Embed, Interaction, Member
from discord.app_commands import command as app_command
from discord.ext.commands import Cog
from .update import UpdateStatistics as Stats

EMBED_COLOURS = {
        BRONZE: 0xA8682A,
        SILVER: 0xABACAA,
          GOLD: 0xE9CF65,
       DIAMOND: 0x6EDDDD,
     DEVELOPER: 0x713C62
}

def format_seconds(seconds: int) -> str:
    units = {
        1: 's',
        60: 'm',
        3600: 'h',
        86400: 'd'
    }

    vals = []

    while units:
        place_value = max(units)
        str_unit = units.pop(place_value)

        value, seconds = divmod(seconds, place_value)

        if value:
            vals.append(f"{value}{str_unit}")
    
    return ' '.join(vals)

class DisplayStatistics(Cog):
    def __init__(self, bot: MyBot) -> None:
        self.bot = bot
        self.pool = bot.pool
    
    @app_command(name = "statistics", description = "View all your statistics on Fact-or-Freak.")
    async def show_statistics(self, interaction: Interaction, member: Member = None):
        if member:
            if not await Stats.user_is_present(member.id):
                return await interaction.response.send_message(
                    "That user has no statistics! "
                    "They need to `/play` games before you can view their statistics.",
                    ephemeral = True
                )
        else:
            if not await Stats.user_is_present(interaction.user.id):
                return await interaction.response.send_message(
                    "That user has no statistics! "
                    "They need to `/play` games before you can view their statistics.",
                    ephemeral = True
                )
        
        person = member or interaction.user
      
      # --------------------------------------------------------------------------------------

        data = await Stats.fetch(person.id)
        
        wins_award = ""

        match 1:
            # Diamond for winning 50+ games
            case 1 if data["games_won"] >= 50:
                wins_awards = DIAMOND
            
            # Gold for winning 25+ games
            case 1 if data["games_won"] >= 25:
                wins_awards = GOLD
            
            # Silver for winning 10+ games
            case 1 if data["games_won"] >= 10:
                wins_awards = SILVER
            
            # Bronze for winning 1+ game
            case 1 if data["games_won"] >= 1:
                wins_awards = BRONZE
            
            # No wins = no medals
        
        playtime_award = ""

        match 1:
            # Diamond for playing 24+ hours
            case 1 if data["play_time"] >= 24 * 60 * 60:
                playtime_award = DIAMOND
            
            # Gold for playing 12+ hours
            case 1 if data["play_time"] >= 12 * 60 * 60:
                playtime_award = GOLD
            
            # Silver for playing 6+ hours
            case 1 if data["play_time"] >= 6 * 60 * 60:
                playtime_award = SILVER

            # Bronze for playing 3+ hours
            case 1 if data["play_time"] >= 3 * 60 * 60:
                playtime_award = BRONZE
    
      # --------------------------------------------------------------------------------------
        
        stats_page = Embed(
            colour = EMBED_COLOURS.get(
                DEVELOPER if person.id == OWNER_ID else (wins_award or playtime_award),
                Colour.dark_embed()
            )
        )

        stats_page.set_author(
            name = f"{person.name}'s Statistics",
            icon_url = person.display_avatar
        )

        stats_page.add_field(
            name = "⭐ Special",
            value = '\n'.join([
                f"Time played: **{format_seconds(data["play_time"])}**  {playtime_award}",
                f"Games won: {data["games_won"]} {wins_award}",
                f"_Winrate: {f'{round(data["games_won"] / data["games_lost"], 2)}%' if data["games_lost"] > 0 else "Unbound"}_",
            ])
        )

        stats_page.add_field(
            name = "🎮 Games",
            value = '\n'.join([
                f"Lobbies made: {data["lobbies_made"]}",
                f"Games played: **{data["games_played"]}**\n",

                f"Games won: {data["games_won"]} {wins_award}",
                f"Games lost: {data["games_lost"]}\n",

                f"_Winrate: {f'{round(data["games_won"] / data["games_lost"], 2)}%' if data["games_lost"] > 0 else "Unbound"}%_",
            ])
        )

        stats_page.add_field(
            name = "📲 Interactions",
            value = '\n'.join([
                f"Truths chosen: {data["truths_selected"]}",
                f"Truths answered: {data["truths_answered"]}",
                f"_Completion rate: {data["truths_answered"] / data["truths_selected"]:.2f}%_\n"

                f"Dares chosen: {data["dares_selected"]}",
                f"Dares answered: {data["dares_completed"]}",
                f"_Completion rate: {data["dares_completed"] / data["dares_selected"]:.2f}%\n_"

                f"Passes made: {data["passes_made"]}",
                f"_Pass rate: {data["passes_made"] / (data["truths_selected"] + data["dares_selected"])}%_"
            ])
        )


async def setup(bot: MyBot) -> None:
    await bot.add_cog(DisplayStatistics(bot))