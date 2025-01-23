from __future__ import annotations
from bot import MyBot, OWNER_ID
from .decals import CROSS, OWNER_CROWN, DEVELOPER
from discord import ButtonStyle as BS, Colour, Interaction, Embed
from discord.app_commands import command as app_command, rename as arg_rename, describe as arg_describe, allowed_contexts, allowed_installs
from discord.ext.commands import Cog, CommandInvokeError
from .enums import LobbyExitCodes
from .views.game_ui import GameUI
from bot.utils.lobby import Lobby
from .statistics import UpdateStatistics as Stats

class FactOrFreakGame(Cog):
    def __init__(self, bot: MyBot) -> None:
        self.bot = bot
        self.pool = bot.pool
    
    @allowed_installs(guilds = True, users = False)
    @allowed_contexts(guilds = True, dms = False, private_channels = False)
    @app_command(name = "play", description = "Play a game of Fact-or-Freak.")
    @arg_rename(lobby_name = "name")
    @arg_describe(lobby_name = "Set a custom name for the lobby you're about to create.")
    async def play_game(self, interaction: Interaction, lobby_name: str | None = None):
        if interaction.user in Lobby.in_lobbies:
            return await interaction.response.send_message(
                embed = Embed(
                    title = f"{CROSS}  Not so fast!",
                    description = "You're already inside a lobby, so you can't create one. Leave it to join this one.",
                    colour = Colour.brand_red()
                ),
                ephemeral = True
            )
    
        lobby_name = (lobby_name or f"🤫") + " [Players Waiting]"
        
        lobby = Lobby(
            timeout = 30.0,
            leader = interaction.user, # type: ignore
            name = lobby_name
        )
        
        await interaction.response.send_message(
            embed = Embed(
                title = lobby_name,
                description = f"1. {interaction.user.mention}  {OWNER_CROWN}{f" {DEVELOPER}" if interaction.user.id == OWNER_ID else ""}\n\n-# Do you even _have_ friends to be playing this?",
                colour = Colour.brand_red()
            ),
            view = lobby
        )

        await lobby.wait()

        if len(lobby.members) == 1 and lobby.exit_code != LobbyExitCodes.LeaderLeft:
            for sibling in lobby.children:
                sibling.style = BS.grey
                sibling.disabled = True
            
            try:
                return await interaction.edit_original_response(
                    embed = Embed(
                        title = "Lobby Failed",
                        description = f"~~1. {lobby.leader.mention}~~\n-# Get some friends, loser.",
                        colour = Colour.brand_red()
                    ),

                    view = None
                )

            # The message was deleted beforehand.
            except CommandInvokeError:
                return

        match lobby.exit_code:
            case LobbyExitCodes.Normal:
                for sibling in lobby.children:
                    sibling.style = BS.grey
                    sibling.disabled = True
                
                await interaction.edit_original_response(
                    embed = Embed(
                        title = f"Lobby Commencing...",
                        description = '\n'.join(
                            [ f"1. {lobby.leader.mention}  {OWNER_CROWN}{f" {DEVELOPER}" if lobby.leader.id == OWNER_ID else ""}" ]
                          + [
                                f"- {member.mention}{f"  {DEVELOPER}" if member.id == OWNER_ID else ""}"
                                for member in lobby.members
                                if member != lobby.leader
                            ]
                        ) + '\n\n' + f'-# {len(lobby.members)} member{'s' if len(lobby.members) > 1 else ''}.',
                        colour = Colour.brand_green(),
                    ),

                    view = None
                )
            
            case LobbyExitCodes.LeaderLeft:
                return

        game = GameUI(
            members = lobby.members,
            bot = self.bot
        )

        player_ids = [m.id for m in lobby.members]

        await Stats.create_new_users(player_ids)
        
        await Stats.update_on_lobby_start(player_ids)

        await game.run(interaction.channel) # type: ignore

        await Stats.update_on_game_end(
            player_ids,
            game._end_time, # type: ignore
            game.runtime
        )


async def setup(bot):
    await bot.add_cog(FactOrFreakGame(bot))