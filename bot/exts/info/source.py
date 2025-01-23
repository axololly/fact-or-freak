import re
from bot import MyBot
from discord import Colour, Embed, Interaction
from discord.app_commands import command as app_command, Choice, describe
from discord.ext.commands import Cog, Command
from discord.ui import Button, View
from exts.utils.converters import CleanSymbol
from inspect import getsourcelines, getsourcefile
from pathlib import Path
from typing import Annotated

type CommandSourceData = tuple[str, int, int]

class LinkButton(Button):
    def __init__(self, url: str, label: str, /) -> None:
        super().__init__(
            label = label,
            url = url
        )

def add_link_button(url: str, label: str, /) -> View:
    "Return a `View` instance with a single `LinkButton`."
    return View().add_item(LinkButton(url, label))

class SourceCode(Cog):
    _github_url_cache: str

    def __init__(self, bot: MyBot) -> None:
        self.bot = bot
        self.pool = bot.pool

        self.github_repo_url = self.get_repo_url()
        self.github_code_url = self.build_github_url()

    @staticmethod
    def get_repo_url() -> str:
        "Get the URL of the repository."

        with open(".git/config") as f:
            text = f.read()
            m = re.search(r"(https:\/\/github\.com\/axololly\/[\w-]+)", text)

            if not m:
                raise ValueError(f"Couldn't understand config file:\n\n{text}\n")
        
            return m.group(1)
    
    def build_github_url(self) -> str:
        "Builds the GitHub URL of the repository using the files `.git/HEAD` and `.git/config`."

        with open(".git/HEAD") as f:
            text = f.read()
            m = re.match(r"ref\: refs\/heads\/(.+)", text)

            if not m:
                raise ValueError(f"Couldn't understand HEAD file:\n\n{text}\n")
            
            branch = m.group(1)
        
        return f"{self.get_repo_url()}/tree/{branch}"


    async def get_code_attributes(self, command: Command) -> CommandSourceData:
        """
        Gets attributes of the internal source code of a given command.

        This returns a tuple of:

        1. the file it's in, relative to the current working directory.

        2. the starting line of the command.

        3. the ending line of the command.
        """
        
        lines, start = getsourcelines(command.callback)
        file = getsourcefile(command.callback)

        if not file:
            raise ValueError(f"source file for command '{command.name}' returned None.")

        path = Path(file).relative_to(Path.cwd())

        return str(path).replace('\\', '/'), start, start + len(lines) - 1
    

    async def build_embed(self, command: Command) -> Embed:
        is_slash_command = self.bot.tree.get_command(command.name) is not None

        if is_slash_command:
            mention = await self.bot.tree.find_mention_for(command.name)

            if not mention:
                raise LookupError(f"cannot find command mention for command '{command.name}'.")
        else:
            mention = f"`{self.bot.command_prefix}{command.name}`"

        return Embed(
            title = "🔍  Gotcha!",
            description = f"Click the link below to see the source code for {mention}.",
            colour = MyBot.EMBED_COLOUR
        )

    @describe(name = "The command to get the source code of.")
    @app_command(name = "source", description = "Get a GitHub link to the source code of one of the bot's commands.")
    async def get_source_code(self, interaction: Interaction, name: Annotated[str, CleanSymbol] | None = None):
        if not name:
            return await interaction.response.send_message(
                embed = Embed(
                    title = "My Source Code",
                    description = "Come and see how I'm even possible in the first place!",
                    colour = MyBot.EMBED_COLOUR
                ),
                view = add_link_button(self.github_repo_url, "Go to GitHub")
            )

        if not (command := self.bot._commands.get(name)):
            return await interaction.response.send_message(
                embed = Embed(
                    title = "\"Hmm, I could've sworn it was here...\"",
                    description = f"Looks like I don't seem to have a command called `{name}` - are you _sure_ that's a command?",
                    colour = Colour.brand_red()
                ),
                delete_after = 3
            )
        
        path, start, end = await self.get_code_attributes(command)

        url = f"{self.github_code_url}/{path}#L{start}-L{end}"
        
        await interaction.response.send_message(
            embed = await self.build_embed(command), # type: ignore
            view = add_link_button(url, "Go to GitHub")
        )

    @get_source_code.autocomplete('name')
    async def autocomplete_commands(self, interaction: Interaction, current: str):
        commands: dict[str, Command] = interaction.client._commands # type: ignore

        return [
            Choice(name = cmd_name, value = cmd_name)
            for cmd_name in commands
            if current in cmd_name
        ]


async def setup(bot: MyBot) -> None:
    await bot.add_cog(SourceCode(bot))