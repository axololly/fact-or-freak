from __future__ import annotations
import asyncio
from bot import MyBot
from decals import OWNER_CROWN, CROSS, CHECK, DEVELOPER, GOLD, SILVER, BRONZE, HEART
from discord import ButtonStyle as BS, Colour, Embed, Interaction, InteractionMessage, Member, TextStyle, WebhookMessage
from discord.app_commands import command as app_command
from discord.ext.commands import Cog, CommandInvokeError
from discord.ui import button, Button, Modal, View, TextInput
from enum import Enum
from .lobby import Lobby, LobbyExitCodes, in_lobbies
from random import choice
from sqlite3 import Row
from time import time

# ----------------------------------------------------------------------------------------------------------------------------------------------

class UserOptionButton(Button):
    view: PassOnTurnUI

    def __init__(self, deciding_member: Member, user_as_option: Member) -> None:
        super().__init__(
            label = user_as_option.name,
            style = BS.blurple
        )

        self.user_as_option = user_as_option
        self.deciding_member = deciding_member
    
    async def callback(self, interaction: Interaction) -> None:
        if interaction.user != self.deciding_member:
            return await interaction.response.send_message(
                "This is not your interaction.",
                ephemeral = True
            )
        
        for child in self.view.children:
            child.disabled = True
            child.style = BS.grey
        
        self.style = BS.green
        
        self.view.selected_member = self.user_as_option

        await interaction.response.edit_message(
            embed = Embed(
                title = f"{CHECK}  Chosen!",
                description = f"You have selected {self.user_as_option.mention} to continue the game.",
                colour = Colour.brand_green()
            ),
            view = self.view
        )

        self.view.stop()

class PassOnTurnUI(View):
    def __init__(self, member_to_decide: Member, all_members: list[Member]) -> None:
        super().__init__()

        self.selected_member: Member | None = None

        self.member_to_decide = member_to_decide
        self.all_members = all_members

        for opponent in self.all_members:
            if opponent == self.member_to_decide:
                continue

            self.add_item(UserOptionButton(self.member_to_decide, opponent))

# ----------------------------------------------------------------------------------------------------------------------------------------------

class CategorySelectionResponse(Enum):
    NoResponse = 0
    ChoseTruth = 1
    ChoseDare  = 2

class CategorySelectionUI(View):
    def __init__(self, deciding_member: Member) -> None:
        super().__init__(timeout = 20.0)

        self.deciding_member = deciding_member
        self.response = CategorySelectionResponse.NoResponse
    
    async def interaction_check(self, interaction: Interaction) -> bool:
        if interaction.user != self.deciding_member:
            await interaction.response.send_message("This is not your interaction.", ephemeral = True)
            return False
        
        return True
    
    @button(label = "Truth", style = BS.blurple)
    async def selected_truth(self, interaction: Interaction, this: Button):
        self.response = CategorySelectionResponse.ChoseTruth
        
        for child in self.children:
            child.style = BS.grey
            child.disabled = True
        
        this.style = BS.green
        
        await interaction.response.edit_message(view = self)
        
        self.stop()
    
    @button(label = "Dare", style = BS.red)
    async def selected_dare(self, interaction: Interaction, this: Button):
        self.response = CategorySelectionResponse.ChoseDare
        
        for child in self.children:
            child.style = BS.grey
            child.disabled = True
        
        this.style = BS.green
        
        await interaction.response.edit_message(view = self)

        self.stop()

# ----------------------------------------------------------------------------------------------------------------------------------------------

class QuestionType(Enum):
    Truth = 1
    Dare = 2

class PromptExitCode(Enum):
    Normal = 0
    TimedOut = 1
    Passed = 2

class ResponseBoxModal(Modal):
    def __init__(self) -> None:
        super().__init__(
            title = "Response Box",
            timeout = 45
        )
    
    response = TextInput(
        label = "You have 45 seconds to write a response.",
        style = TextStyle.paragraph,
        min_length = 10,
        placeholder = "Don't be afraid to speak your mind."
    )

    async def on_submit(self, interaction: Interaction):
        await interaction.response.defer()

class ConfirmPassUI(View):
    def __init__(self) -> None:
        super().__init__(timeout = 10)

        self.response = True
    
    @button(label = "Confirm", style = BS.green)
    async def confirm(self, interaction: Interaction, _):
        await interaction.response.defer()
        self.stop()
    
    @button(label = "Cancel", style = BS.red)
    async def cancel(self, interaction: Interaction, _):
        self.response = False
        
        await interaction.response.defer()
        self.stop()

class GetResponseUI(View):
    def __init__(self, deciding_member: Member, member_lives_left: int) -> None:
        super().__init__(timeout = 45)

        self.deciding_member = deciding_member
        self._lives_left = member_lives_left

        self.response = None
        self.exit_code = PromptExitCode.TimedOut
    
    async def interaction_check(self, interaction: Interaction) -> bool:
        if interaction.user != self.deciding_member:
            await interaction.response.send_message("This is not your interaction.", ephemeral = True)
            return False
        
        return True
    
    @button(label = "Submit", style = BS.blurple)
    async def submit(self, interaction: Interaction, _):
        modal = ResponseBoxModal()

        await interaction.response.send_modal(modal)
        
        if await modal.wait():
            return
        
        self.response = modal.response.value
        self.exit_code = PromptExitCode.Normal

        self.stop()
    
    @button(label = "Pass", style = BS.red)
    async def pass_turn(self, interaction: Interaction, _):
        confirmation_menu = ConfirmPassUI()

        await interaction.response.send_message(
            embed = Embed(
                description = f"> Passing on a question or failing to respond 3 times in this game will cause you to forfeit your turn.\n\nAre you sure you want to pass with **{self._lives_left}** {"lives" if self._lives_left != 1 else "life"} left?\n\nYou have to respond: <t:{int(time()) + 11}:R>\n\n-# Note: this will answer with `Yes` by default.",
                colour = Colour.dark_embed()
            ),
            view = confirmation_menu,
            ephemeral = True
        )

        # View timed out (answer Yes by default) or they agreed to pass
        if await confirmation_menu.wait() or confirmation_menu.response:
            await interaction.edit_original_response(
                embed = Embed(
                    title = f"{CHECK}  All done!",
                    description = f"You passed on this question, leaving you with **{self._lives_left - 1}** {"lives" if self._lives_left - 1 != 1 else "life"} left.\n\n-# Good luck!",
                    colour = Colour.brand_green()
                ),
                view = None
            )
            
            self.exit_code = PromptExitCode.Passed

            self.stop()
            
            return
        
        await interaction.edit_original_response(
            embed = Embed(
                title = f"{CROSS}  Not happening.",
                description = "You cancelled passing - good for you. Now it's time to answer the question, dummy.",
                colour = Colour.brand_red()
            ),
            view = None
        )

        self.exit_code = PromptExitCode.Passed

        self.stop()
    

class GameUI(View):
    message: InteractionMessage

    def __init__(self, members: list[Member]) -> None:
        super().__init__()

        self.players = {member: 3 for member in members}
        self.dead_players: list[Member] = []
        self.current_player: Member = choice(members)

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
        
        if interaction.user not in self.members:
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
        interaction: Interaction,
        person_to_prompt: Member
    ) -> tuple[WebhookMessage, Row, str] | PromptExitCode:
        """
        Prompt a user for a response, returning a tuple of the message
        sent, the question data from the database and the prompted user's
        response, or a `PromptExitCode` if no response was given.
        """

        category_select = CategorySelectionUI(person_to_prompt)

        # Ask to select between `Truth` or `Dare`
        category_selection_message = await interaction.followup.send(
            content = person_to_prompt.mention,
            embed = Embed(
                title = "Category Selection",
                description = f"Select a category of questions from the options below.\n\nYou must answer: <t:{int(time()) + 22}:R>",
                colour = Colour.blurple()
            ),
            view = category_select,
            wait = True
        )

        # If the user did not respond, abort
        try:
            await asyncio.wait_for(category_select.wait(), timeout = category_select.timeout)
        except asyncio.TimeoutError:
            return PromptExitCode.TimedOut

        # Get question data from database
        async with interaction.client.pool.acquire() as conn:
            req = await conn.execute(
                """
                SELECT submitter_id, when_submitted, category, content
                FROM questions WHERE category = ?
                ORDER BY random() LIMIT 1
                """,
                category_select.response.value
            )

            question_data = await req.fetchone()

        # Find the user who made the question
        submitter = interaction.client.get_user(question_data["submitter_id"])

        # Prepare a method to get a response from the user
        get_response_menu = GetResponseUI(person_to_prompt, self.players[person_to_prompt])

        question = question_data["content"]

        # Show selected question and ask for response
        await category_selection_message.delete()

        question_message = await interaction.followup.send(
            content = self.current_player.mention,

            embed = Embed(
                title = f"{category_select.response.name.removeprefix("Chose")}: {question[0].lower()}{question[1:]}",
                description = f"Respond to this by:\n- clicking the `Submit` button to submit an answer.\n- passing on the question using the `Pass` button.\n\nYou have to respond: <t:{int(time()) + 46}:R>"
            ).set_author(
                name = f"From {submitter.name}",
                icon_url = submitter.display_avatar.url
            ),
            
            view = get_response_menu,

            wait = True
        )

        try:
            await asyncio.wait_for(get_response_menu.wait(), timeout = get_response_menu.timeout)
        except asyncio.TimeoutError:
            pass

        # View timed out or the user didn't respond normally
        if get_response_menu.exit_code != PromptExitCode.Normal:
            match get_response_menu.exit_code:
                case PromptExitCode.Passed:
                    await question_message.edit(
                        embed = Embed(
                            title = f"{CROSS}  Pass the salt.",
                            description = f"Looks like {self.current_player.mention} passed on such an amazing question:\n\n> **{category_select.response.name.removeprefix("Chose")}**: {question[0].lower()}{question[1:]}\n\nAnother life lost, like in the tragic events of 2001 when Al Qaeda-",
                            colour = Colour.brand_red()
                        ),

                        view = None
                    )

                case PromptExitCode.TimedOut:
                    await question_message.edit(
                        embed = Embed(
                            title = f"{CROSS}  Got aired in a game I made.",
                            description = f"Looks like {self.current_player.mention} couldn't come up with a response to the question:\n\n> **{category_select.response.name.removeprefix("Chose")}**: {question[0].lower()}{question[1:]}\n\nWhat a fucking retard.",
                            colour = Colour.brand_red()
                        ),

                        view = None
                    )
            
            return get_response_menu.exit_code

        answer = get_response_menu.response

        return question_message, question_data, answer
    
    async def get_next_player(self, interaction: Interaction) -> Member:
        """
        Get the next player to continue the game. If the user doesn't
        respond in time, another player will be randomly chosen.
        """

        view = PassOnTurnUI(self.current_player, self.players)

        message = await interaction.followup.send(
            self.current_player.mention,

            embed = Embed(
                title = "Choose a Player",
                description = f"{'\n'.join(f"{n + 1}. {p.mention}  {' '.join(HEART for _ in range(self.players[p]))}" for n, p in enumerate(self.players))}\n\nSelect the person you want to pass the turn onto.\nThis must be done: <t:{int(time()) + 46}:R>",
                colour = Colour.blurple()
            ),
            view = view,

            wait = True
        )

        if await view.wait():
            randomly_chosen_player = choice([m for m in self.players if m != self.current_player])

            await message.edit(
                embed = Embed(
                    title = f"{CROSS}  Silence is not consent.",
                    description = f"{self.current_player.mention}, because you didn't choose a member, one of your lives has been deducted. You now have **{self.players[self.current_player]}** {"lives" if self.players[self.current_player] != 1 else "life"} remaining.\n\n{randomly_chosen_player.mention} has been chosen to continue the game instead.",
                    colour = Colour.brand_red()
                )
            )
        
            return randomly_chosen_player
        
        return view.selected_member
    
    async def run(self, interaction: Interaction) -> None:
        # Chuck out the first response - everything uses `.followup.`
        if not interaction.response.is_done():
            await interaction.response.defer()

        while True:
            # Prompt for a response from the current player
            response = await self.prompt_for_response(interaction, self.current_player)

            # Timed out or passed on the question - take away a life
            if isinstance(response, PromptExitCode) and response != PromptExitCode.Normal:                
                self.players[self.current_player] -= 1

                if self.players[self.current_player] == 0:
                    await interaction.followup.send(
                        self.current_player.mention,

                        embed = Embed(
                            title = f"{CROSS}  Get out!",
                            description = f"Looks like you ran out of lives, meaning you cannot participate in this game anymore.\n\nTough luck and do better!",
                            colour = Colour.brand_red()
                        )
                    )

                    self.dead_players.append(
                        self.players.pop(self.current_player)
                    )

                    # Last man standing, end game
                    if len(self.players) == 1:
                        return await self.game_over(interaction)

                self.current_player = choice(list(self.players))
                
                continue

            qmsg, qdata, qreply = response
            question = qdata["content"]
            submitter = interaction.client.get_user(qdata["submitter_id"])

            # Delete the other message
            await qmsg.delete()

            # Send what the user put in the chat
            await interaction.followup.send(
                embed = Embed(
                    title = f"{"Dare" if qdata["category"] else "Truth"}: {question[0].lower()}{question[1:]}",
                    description = "> " + qreply.replace('\n', '\n> '),
                    colour = Colour.brand_green()
                ).set_author(
                    name = f"Answered by {self.current_player}",
                    icon_url = self.current_player.display_avatar.url
                ).set_footer(
                    text = f"Submitted by {submitter.name}",
                    icon_url = submitter.display_avatar.url
                )
            )

            # Get the next member to participate
            self.current_player = await self.get_next_player(interaction)

    async def game_over(self, interaction: Interaction) -> None:
        "End the game and announce the winners."

        players_who_need_awards = self.dead_players[::-1][:2]
        award_emojis = [SILVER, BRONZE]

        awards = {
            x + 2: players_who_need_awards[x]
            for x in range(players_who_need_awards)
        }

        # Give the developer badge
        if self.current_player.id == 566653183774949395:
            winner = f"{GOLD} {DEVELOPER}  {self.current_player.mention}"
        else:
            winner = f"{GOLD}  {self.current_player.mention}"
        
        scores_embed = Embed(
            title = "🏆  Winner!",
            description = f"The winner of this round was:\n# {winner} {' '.join(HEART for _ in range(self.players[self.current_player]))}\n\n{'\n'.join(f"{n}. {award_emojis[n - 2]}  ~~{p.mention}~~" for n, p in awards.items())}",
            colour = 0xffcc4d
        )

        if len(self.players) > 3:
            other_dead_players = self.dead_players[::-1][2:]

            scores_embed.add_field(
                name = "Other Dead Players",
                value = '\n'.join(f"{n + 4}. ~~{other_dead_players[n].mention}~~" for n in range(len(other_dead_players)))
            )

        await interaction.followup.send(
            content = ' '.join(p.mention for p in list(self.players) + self.dead_players),
            embed = scores_embed
        )

        self.stop()

# ----------------------------------------------------------------------------------------------------------------------------------------------

class Game(Cog):
    def __init__(self, bot: MyBot) -> None:
        self.bot = bot
        self.pool = bot.pool
    
    @app_command(name = "play", description = "Play a game of Truth or Dare.")
    async def play_game(self, interaction: Interaction):
        if interaction.user in in_lobbies:
            return await interaction.response.send_message(
                embed = Embed(
                    title = f"{CROSS}  Not so fast!",
                    description = "You're already inside a lobby, so you can't create one. Leave it to join this one.",
                    colour = Colour.brand_red()
                ),
                ephemeral = True
            )
        
        lobby = Lobby(interaction.user)
        
        await interaction.response.send_message(
            embed = Embed(
                title = "Players Waiting",
                description = f"1. {interaction.user.mention}  {OWNER_CROWN}{f" {DEVELOPER}" if interaction.user.id == 566653183774949395 else ""}\n\n-# Do you even _have_ friends to be playing this?",
                colour = Colour.brand_red()
            ),
            view = lobby
        )

        try:
            await asyncio.wait_for(lobby.wait(), timeout = 30.0)
        
        # Lobby closed
        except asyncio.TimeoutError:
            pass

        if len(lobby.members) == 1 and lobby.exit_code != LobbyExitCodes.LeaderLeft:
            for sibling in lobby.children:
                sibling.style = BS.grey
                sibling.disabled = True
            
            try:
                return await interaction.edit_original_response(
                    embed = Embed(
                        title = "Lobby Failed",
                        description = f"~~1. {lobby.leader.mention}~~\n-# Get some friends, loser.",
                        colour = Colour.brand_red()
                    ),

                    view = None
                )

            # The message was deleted beforehand.
            except CommandInvokeError:
                return

        match lobby.exit_code:
            case LobbyExitCodes.Normal:
                for sibling in lobby.children:
                    sibling.style = BS.grey
                    sibling.disabled = True
                
                await interaction.edit_original_response(
                    embed = Embed(
                        title = "Lobby Commencing...",
                        description = '\n'.join(
                            [ f"1. {lobby.leader.mention}  {OWNER_CROWN}{f" {DEVELOPER}" if lobby.leader.id == 566653183774949395 else ""}" ]
                          + [
                                f"- {member.mention}{f"  {DEVELOPER}" if member.id == 566653183774949395 else ""}"
                                for member in lobby.members
                                if member != lobby.leader
                            ]
                        ) + '\n\n' + f'-# {len(lobby.members)} member{'s' if len(lobby.members) > 1 else ''}.',
                        colour = Colour.brand_green(),
                    ),

                    view = None
                )
            
            case LobbyExitCodes.LeaderLeft:
                return

        game = GameUI(lobby.members)

        await game.run(interaction)

async def setup(bot):
    await bot.add_cog(Game(bot))