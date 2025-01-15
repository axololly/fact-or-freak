from asyncio import wait_for, TimeoutError as _TimeoutError
from discord import Interaction, Member
from discord.ui import View

class FixedTimeView(View):
    """
    An abstract base subclass of `View` that allows you to set
    a hard limit on the amount of time it takes for a view to
    finish.

    This is useful for something like a lobby system where
    you don't want the timer to refresh after every button
    press or interaction made to the view.
    """

    def __init__(self, timeout: float = 60.0) -> None:
        """
        Initiate a view with a fixed-length timeout.

        Default is 60 seconds - can be as long as desired.
        """

        super().__init__(timeout = timeout)

    async def wait(self) -> bool:
        """
        Operates the same as `View.wait` by pausing the logic until
        the view closes, but uses `asyncio.wait_for` instead to enforce
        a fixed time limit.
        
        This automatically stops itself with `.stop()` and calls
        `.on_timeout()` like usual.
        """
        
        try:
            await wait_for(super().wait(), timeout = self.timeout)
            return False
        
        except _TimeoutError:
            await self.on_timeout()
            self.stop()
            
            return True
    
    def __repr__(self) -> str:
        return f"<FixedTimeView timeout={self.timeout}>"


class OwnedView(View):
    """
    An abstract base subclass of `View` that allows you to
    make a view's interactions accessible by only one person.

    This is useful for something like a paginator, where only
    one person is meant to be interacting with the view.
    """

    def __init__(self, owner: Member, message: str = "This is not your interaction.") -> None:
        """
        Create an `OwnedView` that only the `owner` can interact with.

        Optionally, you can also specify a `message` to be displayed when
        someone, who is **not** the owner, tries to interact with the view.
        """

        super().__init__()
        
        self.owner = owner
        self._message = message
    
    async def interaction_check(self, interaction: Interaction) -> bool:
        if interaction.user != self.owner:
            await interaction.response.send_message(self._message, ephemeral = True)
            return False

        return True

    def __repr__(self) -> str:
        return f"<OwnedView owner={self.owner}>"