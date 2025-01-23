from __future__ import annotations
from aiohttp import ClientSession as CS
from bot import MyBot
from discord import Colour, Embed
from discord.ext.commands import check, Context, Cog, hybrid_command
from dataclasses import dataclass
from datetime import datetime
from exts.utils.converters import CleanSymbol
from typing import Annotated, overload

def is_owner():
    async def predicate(ctx: Context):
        if ctx.author.id == 566653183774949395:
            return True
        else:
            await ctx.reply("This is for the owner only.")
            return False

    return check(predicate)

PYPI_LOGO_URL = "https://cdn.discordapp.com/emojis/766274397257334814.png"

@dataclass
class Package:
    """
    A dataclass representing a package on the PyPI website.
    This contains information about its name, version, summary
    and creation.
    To find a package on the PyPI website, use the `.find()`
    static method on this class.
    """
    
    __slots__ = ("name", "version", "summary", "created")
    
    name: str
    "The name of the package."

    version: str
    "The version of the package."

    summary: str
    "The author-given summary of the package."

    created: datetime
    "The creation time of the package."
    

    @property
    def url(self) -> str:
        "The URL of the project, on the `pypi` website."
        
        return f"https://pypi.org/package/{self.name}"

    @property
    def timestamp(self) -> str:
        "The Discord-formatted timestamp of when this package was created."

        return f"<t:{int(self.created.timestamp())}:R>"
    

    def __repr__(self) -> str:
        return f"<PackageData name={ascii(self.name)} version={ascii(self.version)} created='{self.created.strftime("%d/%m/%Y %I:%M %p")}'>"
    

    @overload
    @staticmethod
    async def find(package: str, /) -> Package | None:
        "Find a package on the PyPI website."
    
    @overload
    @staticmethod
    async def find(package: str, version: str, /) -> Package | None:
        "Find the specific version of a package on the PyPI website."
    
    @staticmethod
    async def find(package: str, version: str | None = None, /) -> Package | None:
        """
        Find a package under a specific version on the PyPI website.
        If no version is given, the latest version is selected.
        Parameters
        ----------
        package: `str`
            the name of the package to look for.
        version: `str | None`
            the specific version to look for. If left out,
            information on the latest version is retrieved.
        
        Returns
        -------
        `Package`
            relevant data about the package retrieved.
        `None`
            the package (or version on the package) cannot be found.
        """
        
        async with CS() as cs:
            async with cs.get(f"https://pypi.org/pypi/{package}/json") as response:
                reply = await response.json()

        if reply == {"message": "Not Found"}:
            return None
            
        info = reply["info"]
        releases = reply["releases"]

        if version:
            if version not in releases:
                return None
                
            release = releases[version][0]
            
        else:
            release = releases[info["version"]][0]
            
        upload_time = datetime.strptime(
            release["upload_time"],
            "%Y-%m-%dT%H:%M:%S"
        )
            
        return Package(
            name = info["name"],
            version = version or info["version"],
            summary = info["summary"],
            created = upload_time
        )

class LookupPyPI(Cog):
    def __init__(self, bot: MyBot) -> None:
        self.bot = bot
    
    @hybrid_command(name = 'pypi', aliases = ['pip'])
    async def pypi_lookup(self, ctx: Context, name: Annotated[str, CleanSymbol]):
        """
        Fetches data about a package on the Python Packaging Index (PyPI).

        Parameters
        ----------
        name: str
            the name of the package.
        """
        
        package = await Package.find(name)

        if not package:
            embed = Embed(
                title = "Sadly not.",
                description = "Looks like that isn't a valid module name. Double-check your spelling and come back to me with a valid module.",
                colour = Colour.brand_red()
            )
        else:
            embed = Embed(
                title = package.name,
                url = package.url,
                description = f"{package.summary}\n\nReleased on <t:{package.timestamp}:D>",
                colour = self.bot.EMBED_COLOUR
            )
        
        embed.set_thumbnail(url = PYPI_LOGO_URL)
        
        return await ctx.reply(embed = embed)


async def setup(bot: MyBot) -> None:
    await bot.add_cog(LookupPyPI(bot))