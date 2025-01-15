from bot import MyBot, OWNER_ID
from .category_select import CategorySelectionUI
from ..decals import GOLD, SILVER, BRONZE, DEVELOPER, CROSS, HEART_SHINE, HEART_BREAK
from discord import Colour, Embed, Interaction, Member, Message, TextChannel
from discord.ui import View
from ..enums import PromptExitCode
from .get_response import GetResponseUI
from .pass_on_turn import PassOnTurnUI
from random import choice
from sqlite3 import Row
from ..statistics.update import UpdateStatistics as Stats
from time import time

def get_current_timestamp() -> int:
    return int(time())

class GameUI(View):
    _start_time: int | None
    _end_time: int | None

    message: Message

    def __init__(self, members: list[Member], bot: MyBot) -> None:
        super().__init__()

        self.bot = bot
        self.pool = bot.pool

        self.players = {member: 3 for member in members}
        self.dead_players: list[Member] = []
        self.current_player: Member = choice(members)

        self._start_time = None
        self._end_time = None
    
    @property
    def runtime(self) -> int:
        "Return the number of seconds since the game started running."

        if not self._start_time:
            raise ReferenceError(
                "cannot determine runtime before the game has begun. "
                "Start the round using .run() before calling this property."
            )
        
        return (self._end_time or get_current_timestamp()) - self._start_time

    async def interaction_check(self, interaction: Interaction) -> bool:
        if interaction.user in self.dead_players:
            await interaction.response.send_message(
                embed = Embed(
                    title = "Not so fast!",
                    description = "Wouldn't be much of a fun game if you could come back from the dead and keep pestering your friends, would it?\n\n-# Now go and do something more meaningful with your life - don't waste it.",
                    colour = Colour.brand_red()
                ),
                ephemeral = True
            )
            return False
        
        if interaction.user not in self.players:
            await interaction.response.send_message(
                embed = Embed(
                    title = "Not so fast!",
                    description = "This isn't your lobby to be playing in.\n\nFor this game, you need _friends_. Don't have any? Go find some then.\n\n-# Loser.",
                    colour = Colour.brand_red()
                ),
                ephemeral = True
            )
            return False

        return True
    
    async def prompt_for_response(
        self,
        channel: TextChannel,
        person_to_prompt: Member
    ) -> tuple[Message, Row, str] | PromptExitCode:
        """
        Prompt a user for a response, returning a tuple of the message
        sent, the question data from the database and the prompted user's
        response, or a `PromptExitCode` if no response was given.
        """

        category_select = CategorySelectionUI(person_to_prompt)

        # Ask to select between `Truth` or `Dare`
        category_selection_message = await channel.send(
            person_to_prompt.mention,
            embed = Embed(
                title = "Category Selection",
                description = f"Select a category of questions from the options below.\n\nYou must answer: <t:{int(get_current_timestamp()) + 22}:R>",
                colour = Colour.blurple()
            ),
            view = category_select
        )

        if await category_select.wait():
            return PromptExitCode.TimedOut

        await Stats.update_on_category_choice(
            response = category_select.response,
            user_id = self.current_player.id
        )

        # Get question data from database
        async with self.pool.acquire() as conn:
            req = await conn.execute(
                """
                SELECT
                    submitter_id,
                    when_submitted,
                    category,
                    content
                FROM questions
                WHERE category = ?
                AND (addressed_to = -1 OR addressed_to = ?)
                ORDER BY random() LIMIT 1
                """,
                category_select.response.value,
                self.current_player.id
            )

            question_data = await req.fetchone()

        # Find the user who made the question
        submitter = self.bot.get_user(question_data["submitter_id"]) # type: ignore

        question = question_data["content"] # type: ignore

        # Prepare a method to get a response from the user
        get_response_menu = GetResponseUI(question, person_to_prompt, self.players[person_to_prompt])

        # Show selected question and ask for response
        await category_selection_message.delete()

        question_message = await channel.send(
            self.current_player.mention,

            embed = Embed(
                title = f"{category_select.response.name.removeprefix("Chose")}: {question[0].lower()}{question[1:]}",
                description = f"Respond to this by:\n- clicking the `Submit` button to submit an answer.\n- passing on the question using the `Pass` button.\n\nYou have to respond: <t:{int(get_current_timestamp()) + 46}:R>"
            ).set_author(
                name = f"From {submitter.name}", # type: ignore
                icon_url = submitter.display_avatar.url # type: ignore
            ),
            
            view = get_response_menu
        )

        await get_response_menu.wait()

        # View timed out or the user didn't respond normally
        if get_response_menu.exit_code != PromptExitCode.Normal:
            match get_response_menu.exit_code:
                case PromptExitCode.Passed:
                    await question_message.edit(
                        embed = Embed(
                            title = f"{HEART_BREAK}  Passed away.",
                            description = f"Looks like {self.current_player.mention} passed on such an amazing question:\n\n> **{category_select.response.name.removeprefix("Chose")}**: {question[0].lower()}{question[1:]}\n\nAnother life lost, like in the tragic events of 2001 when Al Qaeda-",
                            colour = Colour.brand_red()
                        ),

                        view = None
                    )

                    await Stats.update_on_pass(self.current_player.id)

                case PromptExitCode.TimedOut:
                    await question_message.edit(
                        embed = Embed(
                            title = f"{HEART_BREAK}  Got aired in a game I made.",
                            description = f"Looks like {self.current_player.mention} couldn't come up with a response to the question:\n\n> **{category_select.response.name.removeprefix("Chose")}**: {question[0].lower()}{question[1:]}\n\nWhat a fucking retard.",
                            colour = Colour.brand_red()
                        ),

                        view = None
                    )
            
            return get_response_menu.exit_code

        answer = get_response_menu.response

        return question_message, question_data, answer # type: ignore
    
    async def get_next_player(self, channel: TextChannel) -> Member:
        """
        Get the next player to continue the game. If the user doesn't
        respond in time, another player will be randomly chosen.
        """

        view = PassOnTurnUI(self.current_player, [p for p in self.players])

        message = await channel.send(
            self.current_player.mention,

            embed = Embed(
                title = "Choose a Player",
                description = f"{'\n'.join(f"{n + 1}. {p.mention}  {' '.join(HEART_SHINE for _ in range(self.players[p]))}" for n, p in enumerate(self.players))}\n\nSelect the person you want to pass the turn onto.\nThis must be done: <t:{int(get_current_timestamp()) + 22}:R>",
                colour = Colour.blurple()
            ),
            view = view
        )

        if await view.wait():
            randomly_chosen_player = choice([m for m in self.players if m != self.current_player])

            await message.edit(
                embed = Embed(
                    title = f"{CROSS}  Silence is not consent.",
                    description = f"{self.current_player.mention}, because you didn't choose a member, one of your lives has been deducted. You now have **{self.players[self.current_player] - 1}** {"lives" if self.players[self.current_player] - 1 != 1 else "life"} remaining.\n\n{randomly_chosen_player.mention} has been chosen to continue the game instead.",
                    colour = Colour.brand_red()
                ),
                view = None
            )
        
            return randomly_chosen_player
        
        return view.selected_member # type: ignore
    
    async def run(self, channel: TextChannel) -> None:
        self._start_time = int(get_current_timestamp())

        while True:
            # Prompt for a response from the current player
            response = await self.prompt_for_response(channel, self.current_player)

            # Timed out or passed on the question - take away a life
            if isinstance(response, PromptExitCode) and response != PromptExitCode.Normal:                
                self.players[self.current_player] -= 1

                if self.players[self.current_player] == 0:
                    await channel.send(
                        self.current_player.mention,

                        embed = Embed(
                            title = f"{HEART_BREAK}  \"break my heart - oh no, she didn't\"",
                            description = f"Looks like you ran out of lives, meaning you cannot participate in this game anymore.\n\nTough luck and do better!",
                            colour = Colour.brand_red()
                        )
                    )

                    await Stats.update_on_death(self.current_player.id)

                    self.dead_players.append(self.current_player)
                    self.players.pop(self.current_player)

                    # Last man standing, end game
                    if len(self.players) == 1:
                        return await self.game_over(channel)

                self.current_player = choice(list(self.players))
                
                continue

            qmsg, qdata, qreply = response # type: ignore
            question = qdata["content"]
            submitter = self.bot.get_user(qdata["submitter_id"])

            # Delete the other message
            await qmsg.delete()

            # Send what the user put in the chat
            await channel.send(
                embed = Embed(
                    title = f"{"Dare" if qdata["category"] else "Truth"}: {question[0].lower()}{question[1:]}",
                    description = "> " + qreply.replace('\n', '\n> '),
                    colour = Colour.brand_green()
                ).set_author(
                    name = f"Answered by {self.current_player}",
                    icon_url = self.current_player.display_avatar.url
                ).set_footer(
                    text = f"Asked by {submitter.name}", # type: ignore
                    icon_url = submitter.display_avatar.url # type: ignore
                )
            )

            # Get the next member to participate
            self.current_player = await self.get_next_player(channel)

    async def game_over(self, channel: TextChannel) -> None:
        "End the game and announce the winners."

        self._end_time = int(get_current_timestamp())

        await Stats.update_on_win(self.current_player.id)

        players_who_need_awards = self.dead_players[::-1][:2]
        award_emojis = [SILVER, BRONZE]

        awards = {
            x + 2: players_who_need_awards[x]
            for x in range(len(players_who_need_awards))
        }

        # Give the developer badge if the developer won the game
        if self.current_player.id == OWNER_ID:
            winner = f"{GOLD} {DEVELOPER}  {self.current_player.mention}"
        else:
            winner = f"{GOLD}  {self.current_player.mention}"
        
        scores_embed = Embed(
            title = "🏆  Winner!",
            description = f"The winner of this round was:\n# {winner} {' '.join(HEART_SHINE for _ in range(self.players[self.current_player]))}\n\n{'\n'.join(f"{n}. {award_emojis[n - 2]}  ~~{p.mention}~~{f"  {DEVELOPER}" if p.id == OWNER_ID else ""}" for n, p in awards.items())}",
            colour = 0xffcc4d
        )

        if len(self.players) > 3:
            other_dead_players = self.dead_players[::-1][2:]

            scores_embed.add_field(
                name = "Other Dead Players",
                value = '\n'.join(f"{n + 4}. ~~{other_dead_players[n].mention}~~" for n in range(len(other_dead_players)))
            )

        await channel.send(
            ' '.join(p.mention for p in list(self.players) + self.dead_players),
            embed = scores_embed
        )

        self.stop()