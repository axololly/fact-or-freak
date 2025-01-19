from bot import MyBot
from discord import Colour, Embed, Interaction
from discord.app_commands import allowed_contexts, allowed_installs
from discord.ext.commands import Cog, Context, hybrid_command
from frontmatter import Frontmatter
from os.path import exists as path_exists
from logging import getLogger

logger = getLogger(__name__)

class Guides(Cog):
    def __init__(self, bot: MyBot) -> None:
        self.bot = bot
        self.fm = Frontmatter()

    @staticmethod
    def build_embed(fm: Frontmatter, name: str) -> Embed | None:
        file_data = fm.read_file(f"guides/{name}.md")
        metadata = file_data["attributes"].get('embed')

        if not metadata:
            return logger.error(f"No embed metadata found in the file: 'guides/{name}.md'")

        description = file_data.get('body')

        if not description:
            return logger.error(f"No text was found in the file: 'guides/{name}.md'")
        
        embed = Embed.from_dict(metadata)

        embed.description = description
        embed.colour = MyBot.EMBED_COLOUR

        return embed

    @allowed_installs(guilds = True, users = True)
    @allowed_contexts(guilds = True, dms = True, private_channels = True)
    @hybrid_command(name = "guide", description = "Get the guide of a given game.")
    async def get_guide(self, ctx: Context, name: str, *, _):
        if not path_exists(f"guides/{name}.md"):
            return await ctx.reply(
                embed = Embed(
                    title = "Nope.",
                    description = f"Looks like there isn't a guide by the name `{name}`.\n\nAre you sure that's right?",
                    colour = Colour.brand_red()
                ),
                ephemeral = True
            )
        
        embed = self.build_embed(self.fm, name)

        if not embed:
            return await ctx.reply(
                embed = Embed(
                    description = "Hmm, looks like something went wrong. Try again later.",
                    colour = Colour.brand_red()
                )
            )

        await ctx.reply(embed = embed)