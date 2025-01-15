from discord.ui import Modal, TextInput
from discord import Interaction, TextStyle

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