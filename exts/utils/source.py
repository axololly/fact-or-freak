from bot import MyBot
from discord import ButtonStyle as BS, Colour, Embed, Interaction, User
from discord.app_commands import command as app_command, describe
from discord.ext.commands import Cog, Command
from discord.ui import Button, View
from inspect import getsourcelines, getsourcefile
from pathlib import Path
import re

type CommandSourceData = tuple[str, int, int]

class LinkButton(Button):
    def __init__(self, url: str, /) -> None:
        super().__init__(
            style = BS.url,
            url = url
        )

def add_link_button(url: str, /) -> View:
    return View().add_item(LinkButton(url))

class SourceCode(Cog):
    _github_url_cache: str

    def __init__(self, bot: MyBot) -> None:
        self.bot = bot
        self.pool = bot.pool

        self.github_url = self.construct_url()

    @staticmethod
    def construct_url() -> str:
        with open(".git/HEAD") as f:
            text = f.read()
            m = re.match(r"ref\: refs\/heads\/(.+)", text)

            if not m:
                raise ValueError(f"Couldn't understand HEAD file:\n\n{text}\n")
            
            branch = m.group(1)

        with open(".git/config") as f:
            text = f.read()
            m = re.search(r"(https:\/\/github\.com\/axololly\/[\w-]+)", text)

            if not m:
                raise ValueError(f"Couldn't understand config file:\n\n{text}\n")
        
            url = m.group(1)
        
        return f"{url}/tree/{branch}"


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
    

    async def build_embed(self, user: User, command: Command) -> Embed:
        is_slash_command = self.bot.tree.get_command(command.name) is not None

        if is_slash_command:
            mention = await self.bot.tree.find_mention_for(command.name)

            if not mention:
                raise LookupError(f"cannot find command mention for command '{command.name}'.")
        else:
            mention = f"`{self.bot.command_prefix}{command.name}`"

        embed = Embed(
            title = f"Source for {command.name}",
            description = f"Here's the source code for {mention}.\n\nLet me know what you think!",
            colour = Colour.brand_green()
        )
        
        embed.set_footer(
            text = f"Requested by {user.display_name}",
            icon_url = user.display_avatar.url
        )

        return embed


    @describe(name = "The command to get the source code of.")
    @app_command(name = "source", description = "Get a GitHub link to the source code of one of the bot's commands.")
    async def get_source_code(self, interaction: Interaction, name: str):
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

        url = f"{self.github_url}/{path}#L{start}-L{end}"
        
        await interaction.response.send_message(
            embed = await self.build_embed(interaction.user, command), # type: ignore
            view = add_link_button(url)
        )


async def setup(bot: MyBot) -> None:
    await bot.add_cog(SourceCode(bot))