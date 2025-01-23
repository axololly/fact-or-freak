from bot import MyBot
from discord import ClientUser, Colour, Embed
from discord.ext.commands import BucketType, Command, Cog, CooldownMapping, Group, HelpCommand
from ..source import SourceCode, add_link_button
from typing import Generator


class Help(HelpCommand):
    def __init__(self) -> None:
        super().__init__()
        
        self.github_repo_url = SourceCode.get_repo_url()

        self.command_attrs = {
            "name": "help",
            "cooldown": CooldownMapping.from_cooldown(2, 5.0, BucketType.user)
        }
    
    async def send_bot_help(self, _) -> None:
        this_bot: ClientUser = self.context.bot.user # type: ignore
        
        embed = Embed(
            title = f"Luna ({this_bot.display_name})",
            description = f"Hi. I'm Luna - a pretty cool Discord bot that got revived with some cool new commands.\n\nOne day this page will look better, but that's for another time.",
            colour = MyBot.EMBED_COLOUR
        )

        embed.set_thumbnail(
            url = this_bot.display_avatar.url
        )
        
        await self.context.reply(
            embed = embed,
            view = add_link_button(self.github_repo_url, "See Source Code")
        )
    
    async def send_command_help(self, command: Command) -> None:
        embed = Embed(
            title = f"Command: {command.qualified_name}",
            description = command.description or "No description provided.",
            colour = MyBot.EMBED_COLOUR
        )

        embed.add_field(
            name = "Usage",
            value = command.usage or "No usage provided.",
            inline = False
        )

        embed.add_field(
            name = "Aliases",
            value = ', '.join([f"`{a}`" for a in command.aliases] or ["No aliases provided."]),
            inline = False
        )

        await self.context.reply(embed = embed)

    async def send_cog_help(self, cog: Cog) -> None: # TODO: add this.
        await self.context.reply("This isn't a feature yet.")

    async def send_group_help(self, group: Group) -> None:
        def unpack_group(group: Group, /) -> Generator[Command, None, None]:
            for sub in group.commands:
                if isinstance(sub, Group):
                    yield from unpack_group(sub)
                else:
                    yield sub
        
        commands = unpack_group(group)

        embed = Embed(
            title = f"Group: {group.name}",
            description = group.description or "No description provided.",
            colour = MyBot.EMBED_COLOUR
        )

        if commands:
            embed.add_field(
                name = "Commands",
                value = '\n'.join(
                    f"- `{self.context.prefix}{cmd.qualified_name}`"
                    f"\n  - {cmd.description or "No description provided."}"
                    for cmd in commands
                )
            )
        
        await self.context.reply(embed = embed)
    
    async def send_error_message(self, error: str) -> None:
        await self.context.reply(
            embed = Embed(
                title = "Nah.",
                description = error,
                colour = Colour.brand_red()
            )
        )


# ======================================================================================================================== #


class HelpCog(Cog):
    def __init__(self, bot: MyBot) -> None:
        help_cmd = Help()
        help_cmd.cog = self
        bot.help_command = help_cmd


async def setup(bot: MyBot) -> None:
    await bot.add_cog(HelpCog(bot))