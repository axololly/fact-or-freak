import logging, re
from bot import MyBot
from discord import Colour, Embed
from discord.app_commands import allowed_contexts, allowed_installs, describe
from discord.ext.commands import Cog, Context, hybrid_command

logger = logging.getLogger(__name__)

class RTFM(Cog):
    def __init__(self, bot: MyBot) -> None:
        self.bot = bot
        self.docs_db_pool = bot.docs_db_pool

        # TODO: dynamically build a regex query based on the prefixes to strip.
        # self.discord_py_docs_prefixes = ["discord", "discord.ext", "discord.ui", "discord.ext.commands"]

        self.discord_py_docs_regex = re.compile(r"^(?:discord\.)?(?:(?:ext\.(?:commands\.))|(?:ui\.))?(.+)")
    
    @allowed_installs(guilds = True, users = True)
    @allowed_contexts(guilds = True, dms = True, private_channels = True)
    @describe(query = "the Python or discord.py object to search for.")
    @hybrid_command(
        name = "docs",
        aliases = ['d', 'rtfm', 'rtfd'],
        description = "Get documentation for a specified Python or discord.py object - standard library included.",
    )
    async def get_documentation(self, ctx: Context, query: str):
        async with self.docs_db_pool.acquire() as conn:
            req = await conn.execute("SELECT name, link, usage, description, module_name FROM 'sphinx-symbols' WHERE name = ?", query)
            row = await req.fetchone()

        if not row:
            return await ctx.reply(
                embed = Embed(
                    title = "Nope.",
                    description = "Unfortunately, we don't have that here. If this is a legimite module, message my owner <@566653183774949395> (or use the postbox when it's made) and tell him to add it.",
                    colour = Colour.brand_red()
                ),
                ephemeral = True
            )
        
        obj_name = row["name"]

        if row["module_name"] == "discord.py":
            obj_name = re.sub(self.discord_py_docs_regex, r'\1', obj_name)

        await ctx.reply(
            embed = Embed(
                title = obj_name,
                url = row["link"],

                # If there are no usages, add the description.
                # If there ARE usages, separate with two newlines.
                description = '\n\n'.join([
                    row["usage"], row["description"]
                ]),

                colour = MyBot.EMBED_COLOUR
            ).set_footer(
                text = f"This is a {row["module_name"]} object."
            )
        )


async def setup(bot: MyBot) -> None:
    await bot.add_cog(RTFM(bot))