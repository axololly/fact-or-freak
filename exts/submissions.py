from bot import MyBot
from datetime import datetime as dt
from decals import CHECK, CROSS
from discord import ButtonStyle as BS, Colour, Embed, Interaction, Member, TextStyle
from discord.app_commands import command as app_command, Group
from discord.ext.commands import Cog
from discord.ui import View, button, Modal, TextInput
from enum import Enum
from re import match
from sqlite3 import IntegrityError

class Category(Enum):
    Empty = 0
    Truth = 1
    Dare = 2

class BulkSubmissionModal(Modal):
    field = TextInput(
        label = "Questions",
        placeholder = "Each question should be on it's own line...",
        min_length = 20,
        style = TextStyle.paragraph
    )
    
    def __init__(self) -> None:
        super().__init__(
            title = "Submission",
            timeout = 45.0
        )

    async def on_submit(self, interaction: Interaction):
        now = dt.now()
        is_pm, hour = divmod(now.hour, 12)
        formatted_datetime = f"{hour}:{now.minute:0>2}{['a', 'p'][is_pm]}m"

        async with interaction.client.pool.acquire() as conn:
            for position, question in enumerate(self.field.value.split('\n')):
                result = match(r"(truth|dare) - .+", question)

                if not result:
                    return await interaction.response.send_message(
                        embed = Embed(
                            title = f"{CROSS}  Already taken!",
                            description = f"This wasn't written in the correct format. It should be `[truth|dare] - [question]`, like `truth - How many times in a day do you go outside?`" '\n\n'
                                          f"The question at fault was on line {position + 1}:\n```yml\n{question}\n```",
                            colour = Colour.brand_red(),
                        ).set_footer(
                            text = f'When was it submitted, you ask? It was {formatted_datetime}.'
                        ),
                        ephemeral = True
                    )
                
                category = 1 if question.split(' ')[0] == "truth" else 2
                question = question.split(' - ')[1]

                try:
                    await conn.execute(
                        "INSERT INTO questions (submitter_id, when_submitted, category, content) VALUES (?, ?, ?, ?)",
                        interaction.user.id, int(now.timestamp()), category, question
                    )
                
                # Found a duplicate question
                except IntegrityError:
                    req = await conn.execute("SELECT submitter_id, when_submitted FROM questions WHERE content = ?", question)
                    row = await req.fetchone()

                    user_who_submitted = interaction.client.get_user(row['submitter_id']) or await interaction.client.fetch_user(row['submitter_id'])
                    
                    when_question_was_submitted = dt.fromtimestamp(row['when_submitted'])
                    time_since = when_question_was_submitted.date() - dt.now().date()
                    
                    is_pm, hour = divmod(when_question_was_submitted.hour, 12)
                    formatted_datetime = f"{hour}:{when_question_was_submitted.minute:0>2}{['a', 'p'][is_pm]}m"
                    
                    # If it's not the same day, add the date at the start.
                    if time_since.days > 0:
                        _date = f"{when_question_was_submitted.day}/{when_question_was_submitted.month}/{when_question_was_submitted.year:0>4}"
                    else:
                        _date = "today"
                    
                    formatted_datetime = f"{_date} at {formatted_datetime}"

                    return await interaction.response.send_message(
                        embed = Embed(
                            title = f"{CROSS}  Already taken!",
                            description = f"Looks like {user_who_submitted.mention} got there first! You'll need another question to submit because this one is already there." '\n\n'
                                          f"The question at fault was on line {position + 1}:\n```yml\n{question}\n```",
                            colour = Colour.brand_red(),
                        ).set_footer(
                            text = f'When was it submitted, you ask? It was {formatted_datetime}.'
                        ),
                        ephemeral = True,
                        delete_after = 5.0
                    )
        
        await interaction.response.send_message(
            embed = Embed(
                title = f"{CHECK}  All done!",
                description = "Your question went through perfectly fine! You'll see it in future rounds.",
                colour = Colour.brand_green()
            ).set_footer(
                text = f"Submission time: {formatted_datetime}"
            ),
            ephemeral = True,
            delete_after = 5.0
        )

        self.stop()

# ------------------------------------------------------------------------------------------------------------------------

class SingleSubmissionModal(Modal):
    field = TextInput(
        label = "Question",
        placeholder = "Write your question here...",
        min_length = 20
    )
    
    def __init__(self, category: Category) -> None:
        super().__init__(
            title = "Submission",
            timeout = 45.0
        )

        self.category = category

    async def on_submit(self, interaction: Interaction):
        now = dt.now()
        is_pm, hour = divmod(now.hour, 12)
        formatted_datetime = f"{hour}:{now.minute:0>2}{['a', 'p'][is_pm]}m"

        async with interaction.client.pool.acquire() as conn:
            try:
                await conn.execute(
                    "INSERT INTO questions (submitter_id, when_submitted, category, content) VALUES (?, ?, ?, ?)",
                    interaction.user.id, int(now.timestamp()), self.category.value, self.field.value
                )
            except IntegrityError:
                req = await conn.execute("SELECT submitter_id, when_submitted FROM questions WHERE content = ?", self.field.value)
                row = await req.fetchone()

                user_who_submitted = interaction.client.get_user(row['submitter_id']) or await interaction.client.fetch_user(row['submitter_id'])
                
                return await interaction.response.send_message(
                    embed = Embed(
                        title = f"{CROSS}  Already taken!",
                        description = f"Looks like {user_who_submitted.mention} got there first! You'll need another question to submit because this one is already there.",
                        colour = Colour.brand_red(),
                    ).set_footer(
                        text = f'When was it submitted, you ask? It was {formatted_datetime}.'
                    ),
                    ephemeral = True,
                    delete_after = 5.0
                )
        
        await interaction.response.send_message(
            embed = Embed(
                title = f"{CHECK}  All done!",
                description = "Your question went through perfectly fine! You'll see it in future rounds.",
                colour = Colour.brand_green()
            ).set_footer(
                text = f"Submission time: {formatted_datetime}"
            ),
            ephemeral = True,
            delete_after = 5.0
        )

        self.stop()

# ------------------------------------------------------------------------------------------------------------------------

class CategorySelectionView(View):
    def __init__(self, member: Member) -> None:
        super().__init__(timeout = 30)
        self.member = member
        self.selection = Category.Empty
    
    async def interaction_check(self, interaction: Interaction) -> bool:
        if interaction.user != self.member:
            await interaction.response.send_message("This isn't your interaction.")
            return False
        
        return True
    
    async def after_selection(self, interaction: Interaction) -> None:
        modal = SingleSubmissionModal(self.selection)

        await interaction.response.send_modal(modal)

        for child in self.children:
            child.disabled = True
            child.style = BS.grey
        
        if self.selection == Category.Truth:
            self.truth.style = BS.green
        
        elif self.selection == Category.Dare:
            self.dare.style = BS.green

        await interaction.followup.edit_message(
            interaction.message.id,
            view = self
        )

        if await modal.wait():
            await interaction.followup.send("You didn't submit any questions.")

        self.stop()
    
    @button(label = "Truth", style = BS.green)
    async def truth(self, interaction: Interaction, _):
        self.selection = Category.Truth
        
        await self.after_selection(interaction)

    @button(label = "Dare", style = BS.red)
    async def dare(self, interaction: Interaction, _):
        self.selection = Category.Dare

        await self.after_selection(interaction)

# ------------------------------------------------------------------------------------------------------------------------

class TruthOrDare(Cog):
    def __init__(self, bot: MyBot) -> None:
        self.bot = bot
        self.pool = bot.pool
    
    submit = Group(name = 'submit', description = "...")

    @submit.command(name = "single", description = "Submit one question that can be asked in certain rounds.")
    async def single(self, interaction: Interaction):
        view = CategorySelectionView(interaction.user)

        await interaction.response.send_message(
            embed = Embed(
                description = "Select which type of phrase you want to contribute:",
                colour = Colour.dark_embed()
            ),
            view = view,
            ephemeral = True
        )

        await view.wait()

        await interaction.delete_original_response()
    
    @submit.command(name = "multiple", description = "Submit multiple questions, separated by newlines, to be asked in certain rounds.")
    async def multiple(self, interaction: Interaction):
        modal = BulkSubmissionModal()

        await interaction.response.send_modal(modal)

        if await modal.wait():
            await interaction.followup.send(
                "You didn't provide any questions!",
                ephemeral = True
            )

async def setup(bot: MyBot):
    await bot.add_cog(TruthOrDare(bot))