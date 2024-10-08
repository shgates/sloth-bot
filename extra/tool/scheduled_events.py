# import.standard
from typing import List, Union

# import.thirdparty
from discord.ext import commands

# import.local
from mysqldb import DatabaseCore

class ScheduledEventsTable(commands.Cog):
    """ Class for managing the ScheduledEvents table in the database. """

    def __init__(self, client: commands.Bot) -> None:
        """ Class init method. """

        self.client = client
        self.db = DatabaseCore()

    @commands.command(hidden=True)
    @commands.has_permissions(administrator=True)
    async def create_table_scheduled_events(self, ctx: commands.Context) -> None:
        """ Creates the ScheduledEvents table. """

        member = ctx.author

        if await self.check_scheduled_events_exists():
            return await ctx.send(f"**Table `ScheduledEvents` already exists, {member.mention}!**")
        
        await self.db.execute_query("""
            CREATE TABLE ScheduledEvents (
                event_label VARCHAR(100) NOT NULL,
                event_ts BIGINT NOT NULL,
                PRIMARY KEY (event_label)
            )""")

        await ctx.send(f"**Table `ScheduledEvents` created, {member.mention}!**")

    @commands.command(hidden=True)
    @commands.has_permissions(administrator=True)
    async def drop_table_scheduled_events(self, ctx: commands.Context) -> None:
        """ Creates the ScheduledEvents table. """

        member = ctx.author
        
        if not await self.check_scheduled_events_exists():
            return await ctx.send(f"**Table `ScheduledEvents` doesn't exist, {member.mention}!**")

        await self.db.execute_query("DROP TABLE ScheduledEvents")

        await ctx.send(f"**Table `ScheduledEvents` dropped, {member.mention}!**")

    @commands.command(hidden=True)
    @commands.has_permissions(administrator=True)
    async def reset_table_scheduled_events(self, ctx: commands.Context) -> None:
        """ Creates the ScheduledEvents table. """

        member = ctx.author
        
        if not await self.check_scheduled_events_exists():
            return await ctx.send(f"**Table `ScheduledEvents` doesn't exist yet, {member.mention}!**")

        await self.db.execute_query("DELETE FROM ScheduledEvents")

        await ctx.send(f"**Table `ScheduledEvents` reset, {member.mention}!**")

    async def check_scheduled_events_exists(self) -> bool:
        """ Checks whether the ScheduledEvents table exists. """

        return await self.db.table_exists("ScheduledEvents")

    async def insert_advertising_event(self, event_label: str, current_ts: int) -> None:
        """ Inserts an advertising event.
        :param event_label: The label of the advertising event.
        :param current_ts: The timestamp in which it was inserted. """

        await self.db.execute_query("INSERT INTO ScheduledEvents (event_label, event_ts) VALUES (%s, %s)", (event_label, current_ts))

    async def check_advertising_time(self, current_ts: int, event_label: str, ad_time: int) -> bool:
        """ Checks whether the advertising time is due.
        :param current_ts: The current timestamp.
        :param event_label: The label of the event
        :param ad_time: Advertising time cooldown. """

        return await self.db.execute_query("""
            SELECT * from ScheduledEvents
            WHERE event_label = %s AND %s - event_ts >= %s
        """, (event_label, current_ts, ad_time), fetch="one")

    async def get_advertising_event(self, event_label: str) -> List[Union[str, int]]:
        """ Gets an advertising event.
        :param event_label: The label of the advertising event. """

        return await self.db.execute_query("SELECT * FROM ScheduledEvents WHERE event_label = %s", (event_label,), fetch="one")

    async def update_advertising_time(self, event_label: str, current_ts: int) -> None:
        """ Updates the timestamp of the advertising event.
        :param event_label: The label of the advertising event.
        :param current_ts: The timestamp to update the event to. """

        await self.db.execute_query("UPDATE ScheduledEvents SET event_ts = %s WHERE event_label = %s", (current_ts, event_label))
