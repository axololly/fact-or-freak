from discord import Interaction, ButtonStyle as BS
from discord.ui import View, button

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