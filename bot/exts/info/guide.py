from aiofiles import open as aopen
from bot import MyBot
from discord import Colour, Embed
from discord.app_commands import allowed_contexts, allowed_installs
from discord.ext.commands import Cog, Context, hybrid_command
from exts.utils.converters import CleanSymbol
from frontmatter import Frontmatter
from glob import glob as find
from os.path import exists as path_exists
from logging import getLogger
from typing import Annotated

logger = getLogger(__name__)

class Guides(Cog):
    def __init__(self, bot: MyBot) -> None:
        self.bot = bot

        self.fm = Frontmatter()
        self.guide_aliases = {}

        for path in find("guides/*.md"):
            name = path.removeprefix("guides\\").removesuffix(".md")

            data = self.fm.read_file(path)["attributes"]

            if 'aliases' in data:
                for alias in data["aliases"]:
                    if alias in self.guide_aliases:
                        raise RuntimeError(f"the alias 'alias' in path '{path}' is already taken in path 'guides/{self.guide_aliases[alias]}.md'")

                    self.guide_aliases[alias] = name

    @staticmethod
    def build_embed(fm: Frontmatter, path: str) -> Embed | None:
        file_data = fm.read_file(path)
        metadata = file_data["attributes"].get('embed')

        if not metadata:
            return logger.error(f"No embed metadata found in the file: '{path}'")

        description = file_data.get('body')

        if not description:
            return logger.error(f"No text was found in the file: '{path}'")
        
        embed = Embed.from_dict(metadata)

        embed.description = description
        embed.colour = MyBot.EMBED_COLOUR

        return embed

    @allowed_installs(guilds = True, users = True)
    @allowed_contexts(guilds = True, dms = True, private_channels = True)
    @hybrid_command(name = "guide", description = "Get a given guide to something about the bot.")
    async def get_guide(self, ctx: Context, name: Annotated[str, CleanSymbol]):
        name = self.guide_aliases.get(name, name)

        if not path_exists(f"guides/{name}.md"):
            return await ctx.reply(
                embed = Embed(
                    title = "Nope.",
                    description = f"Looks like there isn't a guide by the name `{name}`.\n\nAre you sure that's right?",
                    colour = Colour.brand_red()
                ),
                ephemeral = True
            )
        
        embed = self.build_embed(self.fm, f"guides/{name}.md")

        if not embed:
            return await ctx.reply(
                embed = Embed(
                    description = "Hmm, looks like something went wrong. Try again later.",
                    colour = Colour.brand_red()
                )
            )

        await ctx.reply(embed = embed)

async def setup(bot: MyBot) -> None:
    await bot.add_cog(Guides(bot))