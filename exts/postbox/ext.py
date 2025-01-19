from bot import MyBot
from discord import Embed, File, Member, Message, User, utils
from discord.ext.commands import Cog
from ..commands.guide import Guides
from frontmatter import Frontmatter
from logging import getLogger

logger = getLogger(__name__)

class Postbox(Cog):
    def __init__(self, bot: MyBot) -> None:
        self.bot = bot
        
        self.making_requests: set[int] = set()
        self.author_from_response: dict[int, User | Member] = {}

    @Cog.listener('on_message')
    async def dm_handler(self, message: Message):
        # Ensure this is only in DMs and not messages from the bot
        if message.guild or message.author.bot:
            return
        
        # Owner speaking to bot - pass on message to person
        if await self.bot.is_owner(message.author):
            # Ignore any messages with no replies
            if not message.reference:
                return
            
            if not message.reference.message_id:
                logger.warning(f"Message reference was found to have no message ID attached to it. This postbox request has been aborted for that reason.")
                return
            
            person_replied_to = self.author_from_response[message.reference.message_id]
            
            # If the user isn't making a request anymore, ignore this
            if person_replied_to.id not in self.making_requests:
                return
            
            # If we can't DM the user, drop an X on our message and terminate their request
            if not await self.bot.can_dm(person_replied_to):
                self.making_requests.remove(person_replied_to.id)
                
                await message.add_reaction('❌')
                
                return
            
            # Pass on message to person
            await person_replied_to.send(
                embed = Embed(
                    description = message.content,
                    colour = self.bot.EMBED_COLOUR,
                    timestamp = utils.utcnow()
                ).set_author(
                    name = f"From {message.author.name}",
                    icon_url = message.author.display_avatar.url
                ),
                files = [
                    File(await atch.read(), atch.filename)
                    for atch in message.attachments
                ]
            )

            await message.add_reaction('✅')

        # Person speaking to bot - pass on message to owner
        else:
            if message.author.id not in self.making_requests:
                readme = Guides.build_embed(
                    Frontmatter(),
                    "guides/postbox-intro.md"
                )

                if not readme:
                    logger.error("The file 'guides/postbox-intro.md' encountered issues when being built with Guides.build_embed().")
                    return
                
                await message.reply(embed = readme)
                
                self.making_requests.add(message.author.id)
            
            forwarded_message = await self.bot.owner.send(
                embed = Embed(
                    description = message.content,
                    colour = self.bot.EMBED_COLOUR,
                    timestamp = utils.utcnow()
                ).set_author(
                    name = f"From {message.author.name}",
                    icon_url = message.author.display_avatar.url
                )
            )

            self.author_from_response[forwarded_message.id] = message.author

            await message.add_reaction('✅')


async def setup(bot: MyBot) -> None:
    await bot.add_cog(Postbox(bot))