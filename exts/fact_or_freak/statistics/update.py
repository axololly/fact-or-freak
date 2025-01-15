from asqlite import Pool
from ..enums import CategorySelectionResponse
from sqlite3 import Row
from typing import overload

class UpdateStatistics:
    pool: Pool

    @classmethod
    async def create_new_user(cls, user_id: int) -> None:
        """
        Creates a new user to view the statistics of.
        
        If the user already exists, then no action is taken.
        """

        async with cls.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO statistics (user_id) VALUES (?)
                ON CONFLICT (user_id) DO NOTHING
                """,
                user_id
            )
        
    @classmethod
    async def user_is_present(cls, user_id: int) -> bool:
        "Returns `True` if the user ID given exists in the `statistics` table."

        async with cls.pool.acquire() as conn:
            req = await conn.execute(
                """
                SELECT EXISTS(
                    SELECT 1 FROM statistics
                    WHERE user_id = ?
                )
                AS "x"
                """,
                user_id
            )

            row = await req.fetchone()
        
        return bool(row["x"]) # type: ignore

    @classmethod
    async def _increment(cls, column_name: str, user_id: int) -> None:
        async with cls.pool.acquire() as conn:
            await conn.execute(f"UPDATE statistics SET {column_name} = {column_name} + 1 WHERE user_id = ?", user_id)

    @classmethod
    async def update_on_category_choice(cls, response: CategorySelectionResponse, user_id: int) -> None:
        "Increments either `truths_selected` or `dares_selected` for the `user_id`, depending on the `response` given."

        match response:
            case CategorySelectionResponse.ChoseTruth:
                column = "truths_selected"
            
            case CategorySelectionResponse.ChoseDare:
                column = "dares_selected"
            
            case _:
                raise ValueError(f"Invalid CategorySelectionResponse: '{response}'")
        
        await cls._increment(column, user_id)

    @classmethod
    async def update_on_completion(cls, response: CategorySelectionResponse, user_id: int) -> None:
        "Increments either `truths_answered` or `dares_completed` for the `user_id`, depending on the `response` given."

        match response:
            case CategorySelectionResponse.ChoseTruth:
                column = "truths_answered"
            
            case CategorySelectionResponse.ChoseDare:
                column = "dares_completed"
            
            case _:
                raise ValueError(f"Invalid CategorySelectionResponse: '{response}'")
        
        await cls._increment(column, user_id)
    
    @classmethod
    async def update_on_pass(cls, user_id: int) -> None:
        "Increments `passes_made` for the `user_id` given."

        await cls._increment("passes_made", user_id)
    
    @classmethod
    async def update_on_lobby_creation(cls, user_id: int) -> None:
        "Increments `lobbies_made` for the `user_id` given."

        await cls._increment("lobbies_made", user_id)
    
    @classmethod
    async def update_on_lobby_start(cls, player_ids: list[int]) -> None:
        "Increments `games_played` for all `player_ids` given."

        async with cls.pool.acquire() as conn:
            await conn.executemany(
                """
                UPDATE statistics
                SET games_played = games_played + 1
                WHERE user_id = ?
                """,
                map(tuple, player_ids) # type: ignore
            )
    
    @classmethod
    async def update_on_death(cls, user_id: int) -> None:
        "Increments `games_lost` for the `user_id` given."

        await cls._increment("games_lost", user_id)
    
    @classmethod
    async def update_on_win(cls, user_id: int) -> None:
        "Increments `games_won` for the `user_id` given."

        await cls._increment("games_won", user_id)
    
    @classmethod
    async def update_on_game_end(cls, player_ids: list[int], closing_timestamp: int, runtime: int) -> None:
        "Updates `when_last_played` and `play_time` for all the `player_ids` given."

        async with cls.pool.acquire() as conn:
            await conn.executemany(
                """
                UPDATE statistics
                SET
                    when_last_played = ?,
                    play_time = play_time + ?
                WHERE user_id = ?
                """,
                map(lambda ID: (closing_timestamp, runtime, ID), player_ids)
            )
    
    @overload
    @classmethod
    async def fetch(cls, user_id: int) -> Row:
        "Fetch an entire row from the database, corresponding to the `user_id` given."
    
    @overload
    @classmethod
    async def fetch(cls, user_id: int, column: str) -> Row:
        "Fetch one column of data from the database, corresponding to the `user_id` given."
    
    @overload
    @classmethod
    async def fetch(cls, user_id: int, columns: list[str]) -> Row:
        "Fetch data for all the column names given in `columns`."
    
    @classmethod
    async def fetch( # type: ignore
        cls,
        user_id: int,
        column: str | None = None,
        columns: str | list[str] = "*"
    ) -> Row | None:
        if column and columns or not column and not columns:
            raise ValueError("you must provide an argument for either 'column' or 'columns'.")
            
        columns_to_search = column or ', '.join(columns)
    
        async with cls.pool.acquire() as conn:
            req = await conn.execute(
                f"""
                SELECT {columns_to_search} FROM statistics
                WHERE user_id = ?
                """,
                user_id
            )

            return await req.fetchone()