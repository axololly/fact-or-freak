from .bases import OwnedView
from .confirm_pass import ConfirmPassUI
from decals import CHECK, CROSS
from discord import ButtonStyle as BS, Colour, Embed, Interaction, Member
from discord.ui import button
from ..enums import PromptExitCode
from ..modals.response_box import ResponseBoxModal
from time import time

class GetResponseUI(OwnedView):
    def __init__(self, question: str, deciding_member: Member, member_lives_left: int) -> None:
        super().__init__(deciding_member)
        
        self._lives_left = member_lives_left

        self.question = question

        self.response = None
        self.exit_code = PromptExitCode.TimedOut
    
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