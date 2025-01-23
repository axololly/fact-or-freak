"""
async def main():
    async with CS() as cs:
        api = GitHubAPI(cs, "")

        user = "axololly"
        repo = "paste"
        
        item = await api.getitem(f"/repos/{user}/{repo}")

        print(dumps(item, indent = 2))
        print(item["html_url"])
"""

import re
from bot import MyBot
from dataclasses import dataclass
from datetime import datetime as dt
from discord import Colour, Embed
from discord.ext.commands import BadArgument, Cog, Context, group
from .source import add_link_button, SourceCode
from bot.utils.converters import CleanSymbol
from gidgethub import BadRequest as BadRequest
from typing import Annotated


@dataclass
class GitHubUser:
    name: str
    bio: str | None
    public_repos: int | None
    public_gists: int | None
    url: str
    avatar_url: str
    created: dt | None
    last_updated: dt | None

    @staticmethod
    def from_kwargs(**kwargs) -> 'GitHubUser':
        def grab(d: dict, e: str) -> ...:
            return d.pop(e) if e in d else None
        
        return GitHubUser(
            name         = kwargs.pop("login"),
            bio          = grab(kwargs, "bio"),
            public_gists = grab(kwargs, "public_gists"),
            public_repos = grab(kwargs, "public_repos"),
            url          = kwargs.pop("url"),
            avatar_url   = kwargs.pop("avatar_url"),
            created      = dt.strptime(kwargs.pop("created_at"), "%Y-%m-%dT%H:%M:%SZ") if "created_at" in kwargs else None,
            last_updated = dt.strptime(kwargs.pop("updated_at"), "%Y-%m-%dT%H:%M:%SZ") if "updated_at" in kwargs else None
        )


@dataclass
class GitHubRepo:
    name: str
    description: str
    url: str
    forks: int
    stars: int
    creation: dt
    last_update: dt
    author: GitHubUser

    @staticmethod
    def from_kwargs(**kwargs) -> 'GitHubRepo':
        unix_dt = "%Y-%m-%dT%H:%M:%SZ"

        return GitHubRepo(
            name        = kwargs.pop("name"),
            description = kwargs.pop("description"),
            url         = kwargs.pop("html_url"),
            forks       = kwargs.pop("forks_count"),
            stars       = kwargs.pop("stargazers_count"),
            creation    = dt.strptime(kwargs.pop("created_at"), unix_dt),
            last_update = dt.strptime(kwargs.pop("updated_at"), unix_dt),
            author      = GitHubUser.from_kwargs(**kwargs.pop("owner"))
        )


class GitHubLookup(Cog):
    def __init__(self, bot: MyBot) -> None:
        self.bot = bot
        self.gh = bot.github_api
        
        self.my_repo_url = SourceCode.get_repo_url()
    
    async def cog_command_error(self, ctx: Context, error: Exception):
        if isinstance(error, BadArgument):
            await ctx.reply(
                embed = Embed(
                    title = "Nope.",
                    description = f"That's an invalid format. Check the help command{f" for `{ctx.prefix}{ctx.command.name}`" if ctx.command else ''} for more details.",
                    colour = Colour.brand_red()
                )
            )
        elif isinstance(error, BadRequest):
            await ctx.reply(
                embed = Embed(
                    title = "\"I could've sworn it was just here.\"",
                    description = "Looks like that doesn't exist. Double-check what you sent and try it again.",
                    colour = Colour.brand_red()
                )
            )
        else:
            raise error

    @group(name = "github", aliases = ['gh'], invoke_without_command = True)
    async def github(self, ctx: Context):
        return await ctx.reply(
            embed = Embed(
                title = "My Source Code",
                description = "Come and see how I'm even possible in the first place!",
                colour = MyBot.EMBED_COLOUR
            ),
            view = add_link_button(self.my_repo_url, "Go to GitHub")
        )
    
    @github.command(name = "user")
    async def show_user(self, ctx: Context, name: Annotated[str, CleanSymbol]):
        item = await self.gh.getitem(f"/users/{name}")

        user = GitHubUser.from_kwargs(**item)

        embed = Embed(
            title = user.name,
            description = user.bio,
            url = user.url
        )

        embed.set_thumbnail(
            url = user.avatar_url
        )

        embed.set_footer(
            text = f"{user}"
        )

    @github.command(name = "repo")
    async def show_repo(self, ctx: Context, repo: str):
        m = re.match(r"([\w\-]+)\/([\w\-\.]+)(?: .+)?", repo)

        if not m:
            raise BadArgument
        
        user, repo = m.groups()
        
        item = await self.gh.getitem(f"/repos/{user}/{repo}")

        repository = GitHubRepo.from_kwargs(**item)

        embed = Embed(
            title = repository.name,
            url = repository.author.url,
            description = '\n\n'.join([
                repository.description or "No description provided.",
                f"Created <t:{int(repository.creation.timestamp())}:D> - Last updated <t:{int(repository.last_update.timestamp())}:D>"
            ]),
            colour = self.bot.EMBED_COLOUR
        )

        embed.add_field(
            name = "<:gitbranch:1331207756845420616> Forks",
            value = repository.forks
        )

        embed.add_field(
            name = "⭐ Stars",
            value = repository.forks
        )

        await ctx.reply(embed = embed)


async def setup(bot: MyBot) -> None:
    await bot.add_cog(GitHubLookup(bot))