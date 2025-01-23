import re
from discord import Interaction
from discord.app_commands import Transformer
from discord.ext.commands import Context, Converter

class CleanSymbol(Converter, Transformer):
    """
    Removes any further arguments from the given argument.

    For example, the raw arg `prefix - This is how prefixes work`
    is cleaned to just `prefix` using regex.
    """
    
    def reform(self, arg: str) -> str:
        return re.sub(r"([\w\-\.]+)(?: .+)?", r'\1', arg)

    async def convert(self, ctx: Context, argument: str) -> str:
        return self.reform(argument)

    async def transform(self, interaction: Interaction, value: str) -> str:
        return self.reform(value)