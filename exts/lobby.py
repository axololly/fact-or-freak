from __future__ import annotations
from decals import CHECK, CROSS, OWNER_CROWN, DEVELOPER
from discord import AllowedMentions, ButtonStyle as BS, Colour, Embed, Interaction, Member
from discord.ui import View, button, Button
from enum import Enum

class LobbyExitCodes(Enum):
    Normal = 0
    LeaderLeft = 1
    LeaderSkipped = 2

class StartEarly(Button):
    view: Lobby

    def __init__(self, leader: Member) -> None:
        super().__init__(
            label = "Start Early",
            style = BS.blurple
        )
        self.leader = leader
    
    async def callback(self, interaction: Interaction) -> None:
        if interaction.user != self.leader:
            return await interaction.response.send_message(
                "You are not the party leader. To start the match early, you'll have to ask "
                f"{self.leader.mention} to start the party first.",
                allowed_mentions = AllowedMentions(users = False),
                ephemeral = True
            )

        self.view.exit_code = LobbyExitCodes.LeaderSkipped

        """
        for sibling in self.view.children:
            sibling.style = BS.grey
            sibling.disabled = True
        
        self.style = BS.green
        """

        await interaction.response.edit_message(
            embed = Embed(
                title = "Lobby Commencing...",
                description = '\n'.join(
                    [ f"1. {self.leader.mention}  {OWNER_CROWN}" ]
                  + [
                        f"- {member.mention}"
                        for member in self.view.members
                        if member != self.leader
                    ]
                ) + '\n\n' + f'-# {len(self.view.members)} member{'s' if len(self.view.members) > 1 else ''}.',
                colour = Colour.brand_green()
            ),
            
            view = None
        )
        self.view.stop()

class Lobby(View):
    # Set of user IDs currently in lobbies
    in_lobbies: set[Member] = set()

    def __init__(self, leader: Member) -> None:
        super().__init__()

        self.members: list[Member] = [leader]
        self.leader = leader
        self.in_lobbies.add(self.leader)
        
        self.start_early_button = StartEarly(leader)

        self.exit_code = LobbyExitCodes.Normal

    # Overrided to release all users from the `in_lobbies` set
    def stop(self) -> None:
        self.in_lobbies -= set(self.members)

        super().stop()

    async def update_player_list(self, interaction: Interaction) -> None:
        if len(self.members) < 2 and self.start_early_button in self.children:
            self.remove_item(self.start_early_button)
        
        if len(self.members) >= 2 and self.start_early_button not in self.children:
            self.add_item(self.start_early_button)

        await interaction.followup.edit_message(
            interaction.message.id,

            embed = Embed(
                title = "Players Waiting",
                description = '\n'.join(
                    [ f"1. {self.leader.mention}  {OWNER_CROWN}{f"  {DEVELOPER}" if self.leader.id == 566653183774949395 else ""}" ]
                  + [
                        f"- {member.mention}{f"  {DEVELOPER}" if member.id == 566653183774949395 else ""}"
                        for member in self.members
                        if member != self.leader
                    ]
                ) + '\n\n' + f'-# {len(self.members)} member{'s' if len(self.members) > 1 else ''}.',
                colour = Colour.blurple()
            ),
            view = self
        )
    
    @button(label = "Join Lobby", style = BS.green)
    async def join_lobby(self, interaction: Interaction, _):
        if interaction.user in self.in_lobbies:
            return await interaction.response.send_message(
                embed = Embed(
                    title = f"{CROSS}  Not so fast!",
                    description = "You're already inside a lobby! You need to leave it before you can join this one.",
                    color = Colour.brand_red()
                ),
                ephemeral = True
            )

        if interaction.user in self.members:
            return await interaction.response.send_message(
                embed = Embed(
                    title = f"{CROSS}  Not so fast!",
                    description = "You're already in this lobby! You need to leave it before you can do anything about lobbies.",
                    colour = Colour.brand_red()
                ),
                ephemeral = True
            )
    
        self.members.append(interaction.user)
        self.in_lobbies.add(interaction.user)

        await interaction.response.send_message(
            embed = Embed(
                title = f"{CHECK}  All done!",
                description = "You've been successfully added to this lobby. Good to have you here.",
                colour = Colour.brand_green()
            ),
            ephemeral = True
        )

        await self.update_player_list(interaction)
    
    @button(label = 'Leave Lobby', style = BS.red)
    async def leave_lobby(self, interaction: Interaction, _):
        if interaction.user == self.leader:
            self.exit_code = LobbyExitCodes.LeaderLeft
            
            for child in self.children:
                child.disabled = True
                child.style = BS.grey
            
            await interaction.response.edit_message(
                embed = Embed(
                    title = "Lobby Closed",
                    description = f"The party leader left his own party, so we decided to close it for him." '\n\n'
                                   "-# Maybe they didn't have friends in the first place.",
                    colour = Colour.brand_red()
                ),
                view = self
            )

            return self.stop()
        
        if interaction.user not in self.in_lobbies:
            return await interaction.response.send_message(
                embed = Embed(
                    title = f"{CROSS}  Not so fast!",
                    description = "You're not even in any lobbies, dude. Go away.",
                    color = Colour.brand_red()
                ),
                ephemeral = True
            )

        if interaction.user not in self.members:
            return await interaction.response.send_message(
                embed = Embed(
                    title = f"{CROSS}  Not so fast!",
                    description = "You're not in this lobby. Either join it or go away.",
                    colour = Colour.brand_red()
                ),
                ephemeral = True
            )
    
        self.members.remove(interaction.user)
        self.in_lobbies.remove(interaction.user)

        await interaction.response.send_message(
            embed = Embed(
                title = f"{CHECK}  All done!",
                description = "You've been successfully removed from this lobby. Good to have you here.",
                colour = Colour.brand_green()
            ),
            ephemeral = True
        )

        await self.update_player_list(interaction)