from .bases import FixedTimeView, OwnedView
from discord import Interaction, Member, ButtonStyle as BS
from discord.ui import button, Button
from ..enums import CategorySelectionResponse

class CategorySelectionUI(OwnedView):
    def __init__(self, deciding_member: Member) -> None:
        super().__init__(deciding_member)

        self.timeout = 20.0
        
        self.response = CategorySelectionResponse.NoResponse
    
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