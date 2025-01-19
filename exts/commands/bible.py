import re
from aiohttp import ClientSession as CS
from bot import MyBot
from discord import Colour, Embed
from discord.ext.commands import Cog, Context, command, hybrid_command
from logging import getLogger

logger = getLogger(__name__)

type Verse = str
type Scripture = str

class BibleLookup(Cog):
    def __init__(self, bot: MyBot) -> None:
        self.bot = bot

        self.bible_text: str = ''

    async def cog_load(self) -> None:
        if not self.bible_text:
            async with CS() as cs:
                async with cs.get("https://openbible.com/textfiles/kjv.txt") as response:
                    self.bible_text = await response.text()
    
    def find(self, verse: Verse) -> Scripture:
        """
        Find a Bible verse from the King James Version of
        the Bible from a plain-text descriptor.
        You can search for a verse in one of two ways:
        - `{book} {chapter}:{verse}`
            
            This fetches a single verse.
        - `{book} {chapter}:{starting_verse}-{ending_verse}`
            This fetches a string of multiple verses.
        
        Parameters
        ----------
        verse: `str`
            the descriptor used to locate the verse.
        
        Returns
        -------
        `str`
            the desired scripture.
        
        Raises
        ------
        `ValueError`
            the verse descriptor was not understood by
            the function.
        `IndexError`
            the `ending_verse` value was equal to, or
            less than, the `starting_verse` value
        `LookupError`
            the verse currently being searched for, could
            not be found.
        """
        
        # Check to see if the descriptor is valid, eg. 'Romans 12:17-21'.
        # The neat part about this regex is its groups: it produces either
        # 3 or 4 groups, depending on if a range is specified, meaning we
        # don't need to do any extra processing after unpacking.
        result = re.match(r"^([\w ]+) (\d+):(\d+)(?:-(\d+))?$", verse)

        if not result:
            raise ValueError("'verse' string did not match the provided regex.")

        # 1st group = book, 2nd = chapter,
        # 3rd = start, 4th = optional stop - if left
        # out, then just grab 1
        book, chapter, start, stop = result.groups()

        if stop:
            # A range of verses like '13-9' is clearly invalid,
            # so we need to watch out for that.
            if int(stop) <= int(start):
                raise IndexError("'stop' value must be greater than 'start'.")

            # Convert the `verses` list to a range
            # of verses that the range specifier
            # asks for.
            verses = list(range(int(start), int(stop) + 1))
        else:
            verses = [int(start)]
        
        # Get the whole KJV Bible from the web
        retrieved: list[str] = []

        for v in verses:
            # Build custom regex that allows us to both see if the verse exists,
            # and also retrieve its relevant text.
            result = re.search(fr"^(?:{book} {chapter}:{v})\t(.+)", self.bible_text, re.MULTILINE)

            if not result:
                logger.warning(f"could not find verse {v} for chapter {chapter} of book '{book}'.")

                raise LookupError(f"could not find verse {v} for chapter {chapter} of book '{book}'.")
            
            # Add this to the list of scriptures extracted.
            retrieved.append(f"{self.to_superscript(v)}{result.group(1)}")
        
        # Join the scriptures together,
        # separated by spaces if needed.
        return '  '.join(retrieved)
    

    @staticmethod
    def to_superscript(n: int | str, /) -> str:
        "Convert text with numbers into superscript."

        conv = dict(zip("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹"))

        return ''.join(conv[c] for c in str(n))

    
    @hybrid_command(name = "bible", description = "Get a Bible verse or verses from the KJV Bible.")
    async def bible_lookup(self, ctx: Context, *, verse: str):
        try:
            scripture = self.find(verse)
        except ValueError:
            await ctx.reply(
                embed = Embed(
                    title = "Formatting error!",
                    description = "Looks like you didn't write a valid verse descriptor. To jog your brain, here are a few examples:\n- `Romans 12:17-21`\n- `Genesis 1:1`\n- `Exodus 2:23-25`",
                    colour = Colour.brand_green()
                )
            )
        except IndexError:
            await ctx.reply(
                embed = Embed(
                    title = "Formatting error!",
                    description = "Looks like your desired range of verses is invalid. You'll need to verify those are real elsewhere; _we don't sell that here._",
                    colour = Colour.brand_red()
                )
            )
        except LookupError:
            await ctx.reply(
                embed = Embed(
                    title = "We DON'T sell that here.",
                    description = "Looks like that isn't a valid Bible verse. You'll need to verify those are real elsewhere; _we don't sell that here._",
                    colour = Colour.brand_red()
                )
            )

        else:
            escaped = verse.replace(' ', '%20').replace(':', '%3A')
            bible_gateway_url = f"https://www.biblegateway.com/passage/?search={escaped}&version=KJV"

            await ctx.reply(
                embed = Embed(
                    title = verse,
                    url = bible_gateway_url,
                    description = scripture,
                    colour = self.bot.EMBED_COLOUR
                )
            )


async def setup(bot: MyBot) -> None:
    await bot.add_cog(BibleLookup(bot))