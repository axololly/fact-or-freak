from __future__ import annotations
from .bases import OwnedView
from decals import CHECK
from discord import ButtonStyle as BS, Colour, Embed, Interaction, Member
from discord.ui import View, Button

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

class PassOnTurnUI(OwnedView):
    def __init__(self, member_to_decide: Member, all_members: list[Member]) -> None:
        super().__init__(owner = member_to_decide)
        
        self.timeout = 20.0
        self.selected_member: Member | None = None
        self.all_members = all_members

        for opponent in self.all_members:
            if opponent == self.owner:
                continue

            self.add_item(UserOptionButton(self.owner, opponent))