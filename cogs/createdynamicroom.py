import discord
from discord import channel
from discord.ext.menus import Position
from extra import utils
from discord.ext import commands, tasks
from datetime import datetime
import asyncio
from PIL import Image, ImageFont, ImageDraw
import os
from cogs.slothcurrency import SlothCurrency
from mysqldb import *
from typing import List, Union, Any, Optional
from extra.menu import ConfirmSkill
from extra.select import LanguageRoomSelect
import json

class DynRoomUserVCstamp:
    def __init__(self, user_id: int, user_vc_ts: int):
        self.user_id = user_id
        self.user_vc_ts = user_vc_ts

    @staticmethod
    def instance_from_dict(attr_dict):
        return DynRoomUserVCstamp(attr_dict['user_id'], attr_dict['user_vc_ts'])

class DynRoomUserVCstampDatabase:
    def __init__(self, client):
        pass

    # ===== DynRoomUserVCstamp related functions =====

    @commands.has_permissions(administrator=True)
    @commands.command(hidden=True)
    async def create_table_user_dr_vc_ts(self, ctx) -> None:
        """ (ADM) Creates the DynRoomUserVCstamp table. """

        await ctx.message.delete()
        if await self.table_user_dr_vc_ts_exists():
            return await ctx.send("**Table __DynRoomUserVCstamp__ already exists!**")
        mycursor, db = await the_database()
        await mycursor.execute("CREATE TABLE DynRoomUserVCstamp (user_id bigint, user_vc_ts bigint)")
        await db.commit()
        await mycursor.close()

        return await ctx.send("**Table __DynRoomUserVCstamp__ created!**", delete_after=5)

    @commands.has_permissions(administrator=True)
    @commands.command(hidden=True)
    async def drop_table_user_vc_ts(self, ctx) -> None:
        """ (ADM) Drops the DynRoomUserVCstamp table. """

        await ctx.message.delete()
        if not await self.table_user_dr_vc_ts_exists():
            return await ctx.send("**Table __DynRoomUserVCstamp__ doesn't exist!**")
        mycursor, db = await the_database()
        await mycursor.execute("DROP TABLE DynRoomUserVCstamp")
        await db.commit()
        await mycursor.close()

        return await ctx.send("**Table __DynRoomUserVCstamp__ dropped!**", delete_after=5)

    @commands.has_permissions(administrator=True)
    @commands.command(hidden=True)
    async def reset_table_user_dr_vc_ts(self, ctx) -> None:
        """ (ADM) Resets the DynRoomUserVCstamp table. """

        await ctx.message.delete()
        if not await self.table_user_dr_vc_ts_exists():
            return await ctx.send("**Table __DynRoomUserVCstamp__ doesn't exist yet!**")
        mycursor, db = await the_database()
        await mycursor.execute("DELETE FROM DynRoomUserVCstamp")
        await db.commit()
        await mycursor.close()

        return await ctx.send("**Table __DynRoomUserVCstamp__ reset!**", delete_after=5)

    async def table_user_dr_vc_ts_exists(self) -> bool:
        """ Checks whether the DynRoomUserVCstamp table exists. """

        mycursor, db = await the_database()
        await mycursor.execute("SHOW TABLE STATUS LIKE 'DynRoomUserVCstamp'")
        table_info = await mycursor.fetchall()
        await mycursor.close()

        return len(table_info) != 0

    async def update_user_dr_vc_ts(self, user_id: int, new_ts: int) -> None:
        """ Updates the user's DynamicRoom voice channel join timestamp.
        :param user_id: The ID of the user.
        :param new_ts: The new/current timestamp. """

        mycursor, db = await the_database()
        await mycursor.execute("UPDATE DynRoomUserVCstamp SET user_vc_ts = %s WHERE user_id = %s", (new_ts, user_id))
        await db.commit()
        await mycursor.close()

    async def insert_user_dr_vc(self, user_id: int, the_time: int) -> None:
        """ Updates the user's DynamicRoom voice channel join timestamp.
        :param user_id: The ID of the user.
        :param the_time: The current time. """

        mycursor, db = await the_database()
        await mycursor.execute("INSERT INTO DynRoomUserVCstamp (user_id, user_vc_ts) VALUES (%s, %s)", (user_id, the_time - 61))
        await db.commit()
        await mycursor.close()

    async def upsert_user_dr_vc_ts(self, user_id: int, the_time: int, object_form: bool=False) -> Union[List[List[object]], DynRoomUserVCstamp]:
        """ Gets the user voice channel timestamp, and insert them into the database
        in case they are not there yet.
        :param user_id: The ID of the user.
        :param the_time: The current time.
        :param object_form: If the result should be in object form. """

        mycursor, db = await the_database()
        await mycursor.execute("SELECT * FROM DynRoomUserVCstamp WHERE user_id = %s", (user_id,))
        row = await mycursor.fetchall()
        await mycursor.close()

        if not row:
            await self.insert_user_dr_vc(user_id, the_time)
            return await self.upsert_user_dr_vc_ts(user_id, the_time, object_form)

        if object_form:
            # this will extract row headers
            row_headers = [x[0] for x in mycursor.description]
            json_data = []
            for result in row:
                json_data.append(dict(zip(row_headers, result)))
            if not json_data:
                return None
            return DynRoomUserVCstamp.instance_from_dict(json_data[0])

        return row

class DynamicRoom:
    def __init__(self, guild_id, room_id, vc_id, room_ts, is_perma_room):
        self.guild_id = guild_id
        self.room_id = room_id
        self.vc_id = vc_id
        self.room_ts = room_ts
        self.is_perma_room = is_perma_room
    
    @staticmethod
    def instance_from_dict(attr_dict):
        return DynamicRoom(attr_dict['guild_id'], attr_dict['room_id'], attr_dict['vc_id'], attr_dict['room_ts'], attr_dict['is_perma_room'])

class DynamicRoomDatabase:
    def __init__(self):
        pass

    # ===== Dynamic Rooms related functions =====

    async def get_dynamic_room_vc_id(self, vc_id: int, object_form: bool=False) -> Union[List[List[object]], DynamicRoom]:
        """ Gets a Dynamic Room by voice channel ID.
        :param vc_id: The voice channel ID.
        :param object_form: If the result should be in object form. """

        mycursor, db = await the_database()
        await mycursor.execute("SELECT * FROM DynamicRoom WHERE vc_id = %s", (vc_id,))
        dynamic_rooms = await mycursor.fetchall()
        await mycursor.close()

        if object_form:
            # this will extract row headers
            row_headers = [x[0] for x in mycursor.description]
            json_data = []
            for result in dynamic_rooms:
                json_data.append(dict(zip(row_headers, result)))
            
            if not json_data:
                return None

            return DynamicRoom.instance_from_dict(json_data[0])
            
        return dynamic_rooms

    async def get_all_dynamic_rooms(self, object_form: bool=False) -> Union[List[List[object]], List[DynamicRoom]]:
        """ Get all rows from DynamicRoom table.
        :param object_form: If the result should be in object form. """

        mycursor, db = await the_database()
        await mycursor.execute("SELECT * FROM DynamicRoom")
        rooms = await mycursor.fetchall()
        await mycursor.close()

        if object_form:
            # this will extract row headers
            row_headers = [x[0] for x in mycursor.description]
            json_data = []
            for result in rooms:
                json_data.append(dict(zip(row_headers, result)))
            return [DynamicRoom.instance_from_dict(room_dict) for room_dict in json_data]

        return rooms

    async def insert_dynamic_rooms(self, guild_id: int, room_id: int, vc_id: int, room_ts: int, is_perma_room: bool=False) -> None:
        """ Inserts a Dynamic Room.
        :param user_id: The Language Room ID.
        :param user_vc: The voice channel ID.
        :param user_txt: The voice channel timestamp. """

        mycursor, db = await the_database()
        await mycursor.execute("INSERT INTO DynamicRoom (guild_id, room_id, vc_id, room_ts, is_perma_room) VALUES (%s, %s, %s, %s, %s)", (guild_id, room_id, vc_id, room_ts, is_perma_room))
        await db.commit()
        await mycursor.close()

    async def table_dynamic_rooms_exists(self) -> bool:
        """ Checks whether the DynamicRoom table exists. """

        mycursor, db = await the_database()
        await mycursor.execute("SHOW TABLE STATUS LIKE 'DynamicRoom'")
        table_info = await mycursor.fetchall()
        await mycursor.close()

        return len(table_info) != 0

    @commands.command(hidden=True)
    @commands.has_permissions(administrator=True)
    async def create_table_dynamic_rooms(self, ctx) -> None:
        """ (ADM) Creates the DynamicRoom table. """

        if await self.table_dynamic_rooms_exists():
            return await ctx.send("**Table __DynamicRoom__ already exists!**")

        mycursor, db = await the_database()
        await mycursor.execute("CREATE TABLE DynamicRoom (room_id BIGINT, vc_id BIGINT, room_ts BIGINT)")
        await db.commit()
        await mycursor.close()

        return await ctx.send("**Table __DynamicRoom__ created!**")

    @commands.command(hidden=True)
    @commands.has_permissions(administrator=True)
    async def drop_table_dynamic_rooms(self, ctx) -> None:
        """ (ADM) Drops the DynamicRoom table. """

        if not await self.table_dynamic_rooms_exists():
            return await ctx.send("**Table __DynamicRoom__ doesn't exist!**")

        mycursor, db = await the_database()
        await mycursor.execute("DROP TABLE DynamicRoom")
        await db.commit()
        await mycursor.close()

        return await ctx.send("**Table __DynamicRoom__ dropped!**")

    @commands.command(hidden=True)
    @commands.has_permissions(administrator=True)
    async def reset_table_dynamic_rooms(self, ctx) -> None:
        """ (ADM) Resets the DynamicRoom table. """

        if not await self.table_dynamic_rooms_exists():
            return await ctx.send("**Table __DynamicRoom__ doesn't exist yet!**")

        mycursor, db = await the_database()
        await mycursor.execute("DELETE FROM DynamicRoom")
        await db.commit()
        await mycursor.close()

        return await ctx.send("**Table __DynamicRoom__ reset!**")

    async def make_perma_dynamic_room(self, vc_id: int) -> None:
        query = ""
        if vc_id != 0:
            query = ""
        
        mycursor, db = await the_database()
        await mycursor.execute("UPDATE DynamicRoom SET is_perma_room = true WHERE vc_id = %s", (vc_id,))
        await db.commit()
        await mycursor.close()

class LanguageRoom:
    def __init__(self, room_id: int, english_name: str, room_name: str, room_quant: int, room_capacity: int):
        self.room_id = room_id
        self.english_name = english_name
        self.room_name = room_name
        self.room_quant = room_quant
        self.room_capacity = room_capacity

    @staticmethod
    def instance_from_dict(attr_dict):
        return LanguageRoom(attr_dict['room_id'], attr_dict['english_name'], attr_dict['room_name'], attr_dict['room_quant'], attr_dict['room_capacity'])

class LanguageRoomDatabase:
    def __init__(self):
        pass

    # ===== LanguageRoom related functions =====

    async def table_language_room_exists(self) -> bool:
        """ Checks whether the LanguageRoom table exists. """

        mycursor, db = await the_database()
        await mycursor.execute("SHOW TABLE STATUS LIKE 'LanguageRoom'")
        table_info = await mycursor.fetchall()
        await mycursor.close()

        return len(table_info) != 0

    @commands.command(hidden=True)
    @commands.has_permissions(administrator=True)
    async def create_table_language_room(self, ctx) -> None:
        """ (ADM) Creates the LanguageRoom table. """

        if await self.table_language_room_exists():
            return await ctx.send("**Table __LanguageRoom__ already exists!**")

        mycursor, db = await the_database()
        await mycursor.execute("CREATE TABLE LanguageRoom (room_id SERIAL, english_name VARCHAR(32), room_name BLOB, room_quant INT, room_capacity INT)")
        await db.commit()
        await mycursor.close()

        return await ctx.send("**Table __LanguageRoom__ created!**")

    @commands.command(hidden=True)
    @commands.has_permissions(administrator=True)
    async def drop_table_language_room(self, ctx) -> None:
        """ (ADM) Drops the LanguageRoom table. """

        if not await self.table_language_room_exists():
            return await ctx.send("**Table __LanguageRoom__ doesn't exist!**")

        mycursor, db = await the_database()
        await mycursor.execute("DROP TABLE LanguageRoom")
        await db.commit()
        await mycursor.close()

        return await ctx.send("**Table __LanguageRoom__ dropped!**")

    async def insert_language_room(self, english_name: str, room_name: str, room_quant: str = None, room_capacity: str = None) -> None:
        """ Inserts a Language Room entry.
        :param room_name: The room name. """

        mycursor, db = await the_database()
        await mycursor.execute("INSERT INTO LanguageRoom (room_id, role_id, permission_name, permission_value) VALUES (%s, %s, %s, %s)", (room_id, role_id, permission_name, permission_value))
        await db.commit()
        await mycursor.close()

    async def table_language_room_exists(self) -> bool:
        """ Checks whether the LanguageRoom table exists. """

        mycursor, db = await the_database()
        await mycursor.execute("SHOW TABLE STATUS LIKE 'LanguageRoom'")
        table_info = await mycursor.fetchall()
        await mycursor.close()

        return len(table_info) != 0

    async def get_rooms_by_ids(self, ids, object_form: bool=False) -> Union[List[List[object]], List[DynamicRoom]]:
        """ Returns room data from given ids.
        :param ids: The room name.
        :param object_form: If the result should be in object form. """

        mycursor, db = await the_database()
        await mycursor.execute("SELECT * FROM LanguageRoom WHERE room_id IN %s", (ids,))
        rooms = await mycursor.fetchall()
        await mycursor.close()

        if object_form:
            # this will extract row headers
            row_headers = [x[0] for x in mycursor.description]
            json_data = []
            for result in rooms:
                json_data.append(dict(zip(row_headers, result)))
            return [LanguageRoom.instance_from_dict(room_dict) for room_dict in json_data]

        return rooms

    async def delete_dynamic_rooms(self, room_id: int) -> None:
        """ Deletes a a Dynamic Room by room ID.
        :param user_id: The user ID.
        :param user_vc: The voice channel ID. """

        mycursor, db = await the_database()
        await mycursor.execute("DELETE FROM DynamicRoom WHERE room_id = %s", (room_id,))
        await db.commit()
        await mycursor.close()

    async def get_language_room_by_id(self, room_id: int, object_form: bool=False) -> Union[List[List[object]], LanguageRoom]:
        """ Get room id in LanguageRoom table. """

        mycursor, db = await the_database()
        await mycursor.execute("SELECT * FROM LanguageRoom WHERE room_id = %s", (room_id,))
        row = await mycursor.fetchall()
        await mycursor.close()

        if object_form:
            # this will extract row headers
            row_headers = [x[0] for x in mycursor.description]
            json_data = []
            for result in rooms:
                json_data.append(dict(zip(row_headers, result)))
            return [LanguageRoom.instance_from_dict(room_dict) for room_dict in json_data]

        # room_id, room_name
        return row

    async def get_all_language_room(self, object_form: bool=False) -> Union[List[List[object]], List[DynamicRoom]]:
        """ Get room id in LanguageRoom table. """

        mycursor, db = await the_database()
        await mycursor.execute("SELECT * FROM LanguageRoom")
        row = await mycursor.fetchall()
        await mycursor.close()

        if object_form:
            # this will extract row headers
            row_headers = [x[0] for x in mycursor.description]
            json_data = []
            for result in row:
                json_data.append(dict(zip(row_headers, result)))
            return [LanguageRoom.instance_from_dict(room_dict) for room_dict in json_data]

        return row

class LanguageRoomPermissions:
    def __init__(self, room_id: int, role_id: int, permission_name: str, permission_value: bool):
        self.room_id = room_id
        self.role_id = role_id
        self.permission_name = permission_name
        self.permission_value = permission_value


    @staticmethod
    def instance_from_dict(attr_dict):
        return LanguageRoomPermissions(attr_dict['room_id'], attr_dict['role_id'], attr_dict['permission_name'], attr_dict['permission_value'])

class LanguageRoomPermissionsDatabase:
    def __init__(self, client):
        pass

    # ===== LanguageRoomPermissions related functions =====

    async def get_language_channel_permission(self, room_id, object_form=False):
        """ Gets LanguageChannel Permissions by room ID.
        :param room_id: The room ID. """

        mycursor, db = await the_database()
        await mycursor.execute("SELECT * FROM LanguageRoomPermissions WHERE room_id = %s", (room_id,))
        language_room_permissions = await mycursor.fetchall()
        await mycursor.close()

        if object_form:
            # this will extract row headers
            row_headers = [x[0] for x in mycursor.description]
            json_data = []
            for result in language_room_permissions:
                json_data.append(dict(zip(row_headers, result)))

            if not json_data:
                return None

            return [LanguageRoomPermissions.instance_from_dict(perms_dict) for perms_dict in json_data]

        return language_room_permissions

    async def get_available_rooms(self, roles, see_everything=False, object_form=False):
        """ Gets LanguageChannel Permissions by room ID.
        :param room_id: The room ID. """

        if see_everything:
            query = f"SELECT * FROM LanguageRoomPermissions"
        else:
            query = f"SELECT * FROM LanguageRoomPermissions WHERE role_id IN %s AND permission_name IN ('view', 'speaker') AND permission_value=true" % (
                roles,)

        # print(query)

        mycursor, db = await the_database()
        await mycursor.execute(query)
        available_rooms = await mycursor.fetchall()
        await mycursor.close()

        if object_form:
            # this will extract row headers
            row_headers = [x[0] for x in mycursor.description]
            json_data = []
            for result in available_rooms:
                json_data.append(dict(zip(row_headers, result)))

            if not json_data:
                return None

            return [LanguageRoomPermissions.instance_from_dict(perms_dict) for perms_dict in json_data]

        return available_rooms

# ===== Dynamic Room class =====

class CreateDynamicRoom(commands.Cog, DynRoomUserVCstampDatabase, DynamicRoomDatabase, LanguageRoomDatabase, LanguageRoomPermissionsDatabase):
    """ A cog related to the creation of dynamically instancing voice channels. """

    def __init__(self, client):
        """ Class initializing method. """

        self.client = client
        self.lr_vc_id = int(os.getenv('CREATE_DYNAMIC_ROOM_VC_ID'))
        self.lr_cat_id = int(os.getenv('CREATE_DYNAMIC_ROOM_CAT_ID'))
        self.language_rooms = None

    @commands.Cog.listener()
    async def on_ready(self):
        """ Tells when the cog is ready to be used. """

        print("CreateDynamicRoom cog is online")

        self.check_empty_dynamic_rooms.start()

        await self.prefetch_language_room()

    @tasks.loop(minutes=10)
    async def check_empty_dynamic_rooms(self):
        """ Task that checks Dynamic Rooms expirations. """

        if not await self.table_dynamic_rooms_exists():
            return

        # Looks for empy nonperma rooms to delete
        all_rooms = await self.get_all_dynamic_rooms(object_form=True)
        for room in all_rooms:
            guild = self.client.get_guild(room.guild_id)
            room_id = room.room_id
            channel = discord.utils.get(guild.channels, id=room.vc_id)
            is_perma_room = room.is_perma_room

            if not channel:
                await self.delete_dynamic_rooms(room_id)
                return

            len_users = len(channel.members)

            if not is_perma_room and len_users == 0:
                try:
                    await channel.delete()
                except Exception:
                    pass

                await self.delete_dynamic_rooms(room_id)

    async def prefetch_language_room(self):
        self.language_rooms = await super().get_all_language_room(object_form=True)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after) -> None:
        """ Handler for voice channel activity, that's eventually gonna be used
        for creating a DynamicRoom. """

        # Checks if the user is leaving the vc and whether there still are people in there
        if before.channel and before.channel.category:
            if before.channel.category.id == self.lr_cat_id:
                user_voice_channel = discord.utils.get(
                    member.guild.channels, id=before.channel.id)
                len_users = len(user_voice_channel.members)
                if len_users == 0 and user_voice_channel.id != self.lr_vc_id:
                    room_data = await self.get_dynamic_room_vc_id(user_voice_channel.id, object_form=True)
                    # print(room_data)

                    if not room_data or not room_data.is_perma_room:
                        if room_data:
                            await self.delete_dynamic_rooms(room_data.room_id)
                        await self.delete_things([user_voice_channel])
                    try:
                        pass
                    except Exception as e:
                        print(e)

        # Checks if the user is joining the create a room VC
        if not after.channel:
            return

        if after.channel.id == self.lr_vc_id:
            the_time = await utils.get_timestamp()
            old_time = (await self.upsert_user_dr_vc_ts(member.id, the_time, object_form=True)).user_vc_ts
            if not the_time - old_time >= 60:
                await member.send(
                    f"**You're on a cooldown, try again in {round(60 - (the_time - old_time))} seconds!**",)
                # return await member.move_to(None)
                # return
            if the_time - old_time >= 60:
                await self.update_user_dr_vc_ts(member.id, the_time)

            # create dynamic room and move member
            await self.create_dynamic_room(member)
            # await self.initiate_member_room_interaction(member)

    async def create_dynamic_room(self, member: discord.member) -> None:
        """ Prompts member to create a dynamic room.
        :param member: The member to prompt. """

        # get dynamic room creation data from user
        room_data = await self.initiate_member_room_interaction(member)

        if room_data is None:
            return

        room_id = room_data.room_id
        room_name = room_data.room_name.decode("utf-8")
        room_ts = await utils.get_timestamp()
        room_capacity = room_data.room_capacity

        creations = []
        failed = False

        the_category_test = discord.utils.get(
            member.guild.categories, id=self.lr_cat_id)

        if vc_channel := await self.try_to_create(kind='voice', category=the_category_test, name=room_name, user_limit=room_capacity):
            creations.append(vc_channel)
            await self.set_language_channel_permissions(member.guild, room_id, vc_channel)
        else:
            failed = True

        # Checks whether there are failed creations, if so, delete the channels
        if failed:
            await self.delete_things(creations)
            return await member.send(f"**Channels limit reached, creation cannot be completed, try again later!**")

        # Puts the channels ids in the database
        await self.insert_dynamic_rooms(member.guild.id, room_id, vc_channel.id, room_ts)
        await member.send(f"**🦥 good chatting 🦥**")

        try:
            await member.move_to(vc_channel)
        except discord.errors.HTTPException:
            await member.send("**You cannot be moved because you are not in a Voice-Channel! You have one minute to join the room before it gets deleted.**")
            await asyncio.sleep(60)
            if len(vc_channel.members) == 0:
                await vc_channel.delete()

    async def get_language_room_id(self, room_id) -> List[List[int]]:
        if self.language_rooms:
            for room in self.language_rooms:
                if room.room_id == room_id:
                    return room

        return None

    @commands.command(hidden=True)
    @commands.has_permissions(administrator=True)
    async def insert_language_room(self, ctx, *args) -> None:
        """ Inserts a Language Room entry.
        :param room_name: The room name. """

        await super().insert_language_room(ctx, args)

        await self.prefetch_language_room()

    async def delete_things(self, things: List[Any]) -> None:
        """ Deletes a list of things.
        :param things: The things to delete. """

        for thing in things:
            try:
                await thing.delete()
            except:
                pass

    async def try_to_create(
            self,
            kind: str, category: discord.CategoryChannel = None,
            channel: discord.TextChannel = None, guild: Optional[discord.Guild] = None, owner: Optional[discord.Member] = None, **kwargs: Any
    ) -> Union[bool, discord.TextChannel, discord.VoiceChannel, discord.CategoryChannel, discord.Thread]:
        """ Try to create something.
        :param thing: The thing to try to create.
        :param kind: Kind of creation. (txt, vc, cat, thread)
        :param category: The category in which it will be created. (Optional)
        :param channel: The channel in which the thread be created in. (Optional)(Required for threads)
        :param guild: The guild in which it will be created in. (Optional)(Required for categories)
        :param owner: The owner of the room. (Optional)
        :param kwargs: The arguments to inform the creations. """

        try:
            if kind == 'text':
                the_thing = await category.create_text_channel(**kwargs)
            elif kind == 'voice':
                the_thing = await category.create_voice_channel(**kwargs)
            elif kind == 'category':
                the_thing = await guild.create_category(**kwargs)
            elif kind == 'thread':
                start_message = await channel.send(kwargs['name'])
                await start_message.pin(reason="Galaxy Room's Thread Creation")
                the_thing = await start_message.create_thread(**kwargs)
                if owner:
                    await the_thing.add_user(owner)
        except Exception as e:
            print(e)
            return False
        else:
            return the_thing

    async def set_language_channel_permissions(self, guild, room_id, vc):
        """ set channel permissions given room_id and the voice channel
        :param guild: discord server instance.
        :param room_id: id of the language room.
        :param vc: voice channel to be modified.
        """

        channel_permission = await self.get_language_channel_permission(room_id, object_form=True)
        # print(str(channel_permission))
        await vc.edit(sync_permissions=True)
        await vc.edit(sync_permissions=False)

        for permission in channel_permission:
            m_perm_name = permission.permission_name
            m_perm_value = permission.permission_value
            m_role_id = permission.role_id
            m_member = guild.get_role(m_role_id)

            if m_perm_name == "speaker":
                asyncio.create_task(vc.set_permissions(
                    target=m_member, view_channel=True, connect=True, speak=True))
            else:
                asyncio.create_task(vc.set_permissions(
                    **{"target": m_member, m_perm_name: m_perm_value}))

    async def get_language_rooms_list_member(self, member: discord.Member) -> List[DynamicRoom]:
        roles = [role for role in member.roles]
        roles_tuple = tuple([role.id for role in roles])
        can_see_everything = any([int(os.getenv('SHOW_ME_EVERYTHING_ROLE_ID')) in roles_tuple])

        permissions_rooms = await self.get_available_rooms(roles_tuple, see_everything=can_see_everything, object_form=True)

        available_rooms = await self.get_rooms_by_ids(tuple([permission.room_id for permission in permissions_rooms]), object_form=True)

        return available_rooms

    async def get_capped_rooms(self, room_list: List[DynamicRoom]) -> List[DynamicRoom]:
        
        return room_list

    async def initiate_member_room_interaction(self, member: discord.Member) -> Union[List[DynamicRoom], None]:
        """ initiate interaction with user to create room
        :param member: Member to initiate interaction. """
        available_rooms_list = await self.get_language_rooms_list_member(member)

        available_rooms_list = await self.get_capped_rooms(available_rooms_list)

        def create_option(room, index):
            return discord.SelectOption(label=room.room_name.decode("utf-8"), value=index, description=room.english_name)

        available_options = [create_option(room, str(index)) for index, room in enumerate(available_rooms_list)]

        if len(available_options) == 1:
            return available_options[0]

        # create view with selects with the available languages
        view = discord.ui.View()
        select_limit = 25
        for i in range(0, len(available_options), 25):
            row_num = int((i+1)/25)
            #print(row_num)
            if row_num < 5:
                view.add_item(LanguageRoomSelect(self.client, custom_id="select_lr_"+str(row_num), row=row_num, select_options=available_options[i:i + select_limit]))

        await member.send(f"**Select a Room**", view=view)
        await view.wait()

        # print(available_options[int(view.chosen_room)])

        if hasattr(view, 'chosen_room'):
            return available_rooms_list[int(view.chosen_room)]

        return None

    @commands.command(hidden=True)
    @commands.has_permissions(administrator=True)
    async def make_perma(self, ctx, vc_id):
        await ctx.message.delete()
        await ctx.send("**Done!**", delete_after=3)
        await super().make_perma_dynamic_room(vc_id=vc_id)

def setup(client):
    """ Cog's setup function. """

    client.add_cog(CreateDynamicRoom(client))
