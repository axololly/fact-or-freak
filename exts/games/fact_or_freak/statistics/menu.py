from ..decals import BRONZE, SILVER, GOLD, DIAMOND, DEVELOPER, PURPLE_BADGE
from discord import Embed, Interaction, Member, SelectOption
from discord.ui import Select
from ...utils.bases import OwnedView
from .update import UpdateStatistics as Stats

def format_seconds(seconds: int) -> str:
    if seconds == 0:
        return "0s"
    
    units = {
        1: 'seconds',
        60: 'minutes',
        3600: 'hours',
        86400: 'days'
    }

    vals = []

    while units:
        place_value = max(units)
        str_unit = units.pop(place_value)

        value, seconds = divmod(seconds, place_value)

        if value:
            vals.append(f"{value} {str_unit}")
    
    return ', '.join(vals[:-1]) + f' and {vals[-1]}'


class StatisticSelection(Select):
    view: 'StatisticsPageMenu' # type: ignore

    def __init__(self) -> None:
        super().__init__(
            placeholder = "Select a category...",
            options = [
                SelectOption(
                    label = "Special",
                    description = "Shows winrate, playtime, etc.",
                    value = 1,
                    emoji = "⭐"
                ),
                SelectOption(
                    label = "Games",
                    description = "Shows lobbies joined, games won, etc.",
                    value = 2,
                    emoji = "🎮"
                ),
                SelectOption(
                    label = "Interactions",
                    description = "Shows truths chosen, dares completed, etc.",
                    value = 3,
                    emoji = "📲"
                ),
                SelectOption(
                    label = "Badges",
                    description = "See all the badges you can get from this bot.",
                    value = 4,
                    emoji = PURPLE_BADGE
                )
            ]
        )
    
    async def callback(self, interaction: Interaction) -> None:
        option = int(self.values[0])

        for x in self.options:
            x.default = False
        
        self.options[option - 1].default = True

        await interaction.response.edit_message(
            embed = self.view.pages[option],
            view = self.view
        )

class StatisticsPageMenu(OwnedView):
    BADGES_EMBED = Embed(
        title = f"{PURPLE_BADGE} Badges",
        description = "When it comes to using this bot, there are a few badges you can earn, and they're listed below:",
        colour = 0x815AB8
    ).add_field(
        name = f"{BRONZE} Bronze",
        value = "This can be obtained after winning at least 1 game, or from playing at least 3 hours, of _Fact-or-Freak._",
        inline = False
    ).add_field(
        name = f"{SILVER} Silver",
        value = "This can be obtained after winning at least 10 games, or from playing at least 6 hours, of _Fact-or-Freak._",
        inline = False
    ).add_field(
        name = f"{GOLD} Gold",
        value = "This can be obtained after winning at least 25 games, or from playing at least 12 hours, of _Fact-or-Freak._",
        inline = False
    ).add_field(
        name = f"{DIAMOND} Diamond",
        value = "This can be obtained after winning 50 games or more, or from playing 24 hours or more, of _Fact-or-Freak._",
        inline = False
    ).add_field(
        name = f"{DEVELOPER} Developer",
        value = "This is reserved only for developers of _Fact-or-Freak_, the people who brought you this experience.",
        inline = False
    ).set_footer(
        text = "Note that you can achieve two of the same badge by completing both requirements."
    )

    def __init__(self, owner: Member, target: Member) -> None:
        super().__init__(owner)
        self.timeout = 30.0
        self.target = target

        self.add_item(StatisticSelection())
    
    async def create_pages(self) -> None:
        data = await Stats.fetch(self.owner.id)

        # =============================
        #         Wins Awards
        # =============================
        # Diamond for winning 50+ games
        # Gold for winning 25+ games
        # Silver for winning 10+ games
        # Bronze for winning 1+ game
        match 1:
            case 1 if data["games_won"] >= 50:  wins_award = DIAMOND
            case 1 if data["games_won"] >= 25:  wins_award =    GOLD
            case 1 if data["games_won"] >= 10:  wins_award =  SILVER
            case 1 if data["games_won"] >=  1:  wins_award =  BRONZE
            case                            _:  wins_award =    None
        
        # =============================
        #       Playtime Awards
        # =============================
        # Diamond for playing 24+ hours
        # Gold for playing 12+ hours
        # Silver for playing 6+ hours
        # Bronze for playing 3+ hours
        match 1:
            case 1 if data["play_time"] >= 24 * 60 * 60:  wins_award = DIAMOND
            case 1 if data["play_time"] >= 12 * 60 * 60:  wins_award =    GOLD
            case 1 if data["play_time"] >=  6 * 60 * 60:  wins_award =  SILVER
            case 1 if data["play_time"] >=  3 * 60 * 60:  wins_award =  BRONZE
            case                                      _:  wins_award =    None

        # Constructing the pages to display
        self.pages = [
            # Home page
            Embed(
                title = "🏠 Home",
                description = "Select an option from the dropdown below to see your statistics.",
                colour = 0xF2F2F2
            ).set_author(
                name = f"{self.target.name}'s Statistics",
                icon_url = self.target.display_avatar.url
            ).add_field(
                name = "Badges",
                value = f"For statistics like win count and play-time, users are awarded badges based on their progress.\n\nSee the `Badges` section for more information.",
                inline = False
            ),

            # Shows special statistics (W/L ratio, time played, etc)
            Embed(
                title = "⭐ Special",
                colour = 0xFFC83D,
            ).set_author(
                name = f"{self.target.name}'s Statistics",
                icon_url = self.target.display_avatar.url
            ).add_field(
                name = "Time Played",
                value = f"You've played for **{format_seconds(data["play_time"])}**.",
                inline = False
            ).add_field(
                name = "Wins",
                value = f"You've won **{data["games_won"]}** game{'s' if data["games_won"] != 1 else ''}{f" {wins_award} " if wins_award else ""} so far.{f"\n\n> That's a winrate of **{data["games_won"] / data["games_played"] * 100:.2f}%**." if data["games_played"] > 0 else ""}",
                inline = False
            ),

            # Shows game statistics (lobbies made and joined, and games won and lost, including winrate)
            Embed(
                title = "🎮 Games",
                colour = 0x383838
            ).set_author(
                name = f"{self.target.name}'s Statistics",
                icon_url = self.target.display_avatar.url
            ).add_field(
                name = "Lobbies",
                value = f"Made: {data["lobbies_made"]}\nJoined: {data["games_played"] - data["lobbies_made"]}",
                inline = False
            ).add_field(
                name = "Wins / Losses",
                value = f"Won: **{data["games_won"]}**{f" {wins_award}" if wins_award else ""}\nLost: **{data["games_lost"]}**\nWinrate: " \
                + (f"**{data["games_won"] / data["games_played"] * 100:.2f}%**." if data["games_played"] > 0 else "N/A"),
                inline = False
            ),

            # Shows interaction statistics (truths chosen and answered, dares chosen and completed, etc)
            Embed(
                title = "📲 Interactions",
                colour = 0x0794BD
            ).set_author(
                name = f"{self.target.name}'s Statistics",
                icon_url = self.target.display_avatar.url
            ).add_field(
                name = "👼 Truths",
                value = f"Chosen: {data["truths_selected"]}\nAnswered: {data["truths_answered"]}{f"\nAnswer rate: **{data["truths_answered"] / data["truths_selected"] * 100:.2f}%**.\n-# After selecting `Truth`." if data["truths_selected"] > 0 else ""}",
                inline = False
            ).add_field(
                name = "😈 Dares",
                value = f"Chosen: {data["dares_selected"]}\nCompleted: {data["dares_completed"]}{f"\nCompletion rate: **{data["dares_completed"] / data["dares_selected"] * 100:.2f}%**.\n-# After selecting `Dare`." if data["dares_selected"] > 0 else ""}",
                inline = False
            ).add_field(
                name = "🙄 Passes (boring)",
                value = f"Passes: {data["passes_made"]}\nPass rate: {data["passes_made"] / (data["truths_selected"] + data['dares_selected']) if data["truths_selected"] + data['dares_selected'] > 0 else "N/A"}",
                inline = False
            ),

            # Shows information on the badges you can get
            self.BADGES_EMBED
        ]