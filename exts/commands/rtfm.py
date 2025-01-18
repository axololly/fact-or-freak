import logging, re
from bot import MyBot
from discord import Colour, Embed, Interaction
from discord.app_commands import allowed_contexts, allowed_installs, command as app_command, describe, Choice
from discord.ext.commands import Cog

logger = logging.getLogger(__name__)

class RTFM(Cog):
    def __init__(self, bot: MyBot) -> None:
        self.bot = bot
        self.docs_db_pool = bot.docs_db_pool

        self.names: dict[str, list[str]] = {}

        self.discord_py_docs_prefixes = ["discord", "discord.ext", "discord.ui", "discord.ext.commands"]
        self.discord_py_docs_regex = r"^(?:discord\.)?(?:(?:ext\.(?:commands\.))|(?:ui\.))?(.+)"
    
    async def cog_load(self):
        async with self.docs_db_pool.acquire() as conn:
            req = await conn.execute("SELECT tbl_name FROM sqlite_master")
            table_name_data = await req.fetchall()

            for row in table_name_data:
                table_name = row["tbl_name"]

                req = await conn.execute(f"SELECT name FROM '{table_name}'")
                
                self.names[table_name] = [
                    row["name"] for row in
                    await req.fetchall()
                ]
    
    @allowed_installs(guilds = True, users = True)
    @allowed_contexts(guilds = True, dms = True, private_channels = True)
    @describe(query = "the Python object to search for.")
    @app_command(name = "python-docs", description = "Get documentation for a specified Python object - standard library included.")
    async def python_docs(self, interaction: Interaction, query: str):
        if query not in self.names["python"]:
            return await interaction.response.send_message(
                embed = Embed(
                    title = "Nothing to see here!",
                    description = f"Looks like nothing could be found for the query `{query}`.",
                    colour = Colour.brand_red()
                ),
                ephemeral = True
            )
        
        async with self.docs_db_pool.acquire() as conn:
            req = await conn.execute("SELECT name, link, usage, description FROM 'python' WHERE name = ?", query)
            row = await req.fetchone()

            if not row:
                logger.error(f"No data was found in the database for the query '{query}' (python) - perhaps a deleted record?")
                return
        
        await interaction.response.send_message(
            embed = Embed(
                title = row["name"],
                url = row["link"],
                description = '\n\n'.join([
                    row["usage"], row["description"]
                ]),
                colour = Colour.dark_embed()
            )
        )
    
    @python_docs.autocomplete('query')
    async def python_query_autocomplete(self, interaction: Interaction, current: str):
        if not current:
            return []
        
        async with self.docs_db_pool.acquire() as conn:
            req = await conn.execute("SELECT * FROM 'python' WHERE name = ?", current + "%")
            rows = (await req.fetchall())[:8]
        
        return [
            Choice(
                name = row["name"],
                value = row["name"]
            )
            for row in rows
        ]
    
    @allowed_installs(guilds = True, users = True)
    @allowed_contexts(guilds = True, dms = True, private_channels = True)
    @describe(query = "the discord.py object to search for.")
    @app_command(name = "discord-docs", description = "Get documentation for a specified discord.py object.")
    async def discord_py_docs(self, interaction: Interaction, query: str):
        if query not in self.names["discord.py"]:
            return await interaction.response.send_message(
                embed = Embed(
                    title = "Nothing to see here!",
                    description = f"Looks like nothing could be found for the query `{query}`.",
                    colour = Colour.brand_red()
                ),
                ephemeral = True
            )
        
        async with self.docs_db_pool.acquire() as conn:
            req = await conn.execute("SELECT name, link, usage, description FROM 'discord.py' WHERE name = ?", query)
            row = await req.fetchone()

            if not row:
                logger.error(f"No data was found in the database for the query '{query}' (discord.py) - perhaps a deleted record?")
                return
        
        await interaction.response.send_message(
            embed = Embed(
                title = row["name"],
                url = row["link"],
                description = '\n\n'.join([
                    row["usage"], row["description"]
                ]),
                colour = Colour.dark_embed()
            )
        )
    
    @discord_py_docs.autocomplete('query')
    async def discord_py_query_autocomplete(self, interaction: Interaction, current: str):
        if not current:
            return []
        
        def build_query(search_term: str, *, prefixes: list[str], columns: list[str] = ["*"]) -> str:
            search_term = search_term.replace("'", "\\'")
            
            return f"SELECT {', '.join(columns)} FROM 'discord.py'\n" + \
                   f"WHERE name LIKE '{search_term}%'\nOR " + \
                    "\nOR ".join(
                        f"name LIKE '{prefix}.' || '{search_term}%'"
                        for prefix in prefixes
                    )

        def clean_with_regex(text: str) -> str:
            return re.sub(self.discord_py_docs_regex, r"\1", text)

        async with self.docs_db_pool.acquire() as conn:
            req = await conn.execute(
                build_query(
                    search_term = current,
                    prefixes = self.discord_py_docs_prefixes,
                    columns = ["name"]
                )
            )
            rows = (await req.fetchall())[:25]
        
        return [
            Choice(
                name = clean_with_regex(row["name"]),
                value = row["name"]
            )
            for row in rows
        ]


async def setup(bot: MyBot) -> None:
    await bot.add_cog(RTFM(bot))