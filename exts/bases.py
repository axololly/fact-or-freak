import asyncio
from abc import ABC
from discord.ui import View

class FixedTimeView(View, ABC):
    """
    A subclass of `View` that allows you to set a hard
    limit on the amount of time it takes for a view to finish.

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

    async def wait(self) -> None:
        """
        Operates the same as `View.wait` by pausing the logic until
        the view closes, but uses `asyncio.wait_for` instead to enforce
        a fixed time limit.
        
        This automatically stops itself with `.stop()` and calls
        `.on_timeout()` like usual.
        """
        
        try:
            await asyncio.wait_for(super().wait(), timeout = self.timeout)
        
        except asyncio.TimeoutError:
            await self.on_timeout()
            self.stop()