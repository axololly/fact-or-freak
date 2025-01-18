from bot import MyBot
from discord import Colour, Embed, Interaction
from discord.app_commands import allowed_contexts, allowed_installs, command as app_command
from discord.ext.commands import Cog
from frontmatter import Frontmatter
from os.path import exists as path_exists
from logging import getLogger

logger = getLogger(__name__)

class Guides(Cog):
    def __init__(self, bot: MyBot) -> None:
        self.bot = bot
        self.fm = Frontmatter()

    @allowed_installs(guilds = True, users = True)
    @allowed_contexts(guilds = True, dms = True, private_channels = True)
    @app_command(name = "guide", description = "Get the guide of a given game.")
    async def get_guide(self, interaction: Interaction, name: str):
        if not path_exists(f"guides/{name}.md"):
            return await interaction.response.send_message(
                embed = Embed(
                    title = "Nope.",
                    description = f"Looks like there isn't a guide by the name `{name}`.\n\nAre you sure that's right?",
                    colour = Colour.brand_red()
                ),
                ephemeral = True
            )
        
        file_data = self.fm.read_file(f"guides/{name}.md")
        metadata = file_data.get('attributes')

        if not metadata:
            return logger.error(f"No metadata found in the file: \x1b[1mguides/{name}.md\x1b[0m")

        description = file_data.get('body')

        if not description:
            return logger.error(f"No text was found in the file: \x1b[1mguides/{name}.md\x1b[0m")
        
        embed = Embed.from_dict(metadata)

        embed.description = description

        await interaction.response.send_message(embed = embed)