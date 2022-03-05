import os
import sys
from dotenv import load_dotenv
load_dotenv()

import pytest
from unittest.mock import AsyncMock, MagicMock, Mock, PropertyMock, patch
from typing import List, Dict, Union, Optional, Any
from cogs.teacherfeedback import TeacherFeedback

from tests.models.discord_models import DiscordRole
from extra.utils import get_timestamp

from .conftest import (
    DatabaseDriver,
    Query,
    Result,
    get_users,
    _INSERT,
    createConnection,
    DiscordMember
)
from contextlib import suppress
import asyncio

DNK_ID: int = 647452832852869120

# SLC: Sloth Language Class
# RUN: pytest --asyncio-mode=auto --capture=no

class TestSlothLanguageClass:
    """ Class for testing the features inside Sloth's
    Language Class system. """

    def setup(self) -> None:
        """ Setup of the test class, which creates a database connection, cache etc. """

        cursor, connection = createConnection()

        refer = DatabaseDriver.execute

        def execute(self: DatabaseDriver, query: Union[str, Query]) -> Result:
            """ Executes a query using the database driver. """

            print("execute", query)

            assert isinstance(query, Query), \
                "Unexpected raw query execution"

            result = refer(self, query)

            if query.kind == _INSERT and result.commited:
                model = result.asdict()

            return result

        DatabaseDriver.execute = execute
        self.driver = DatabaseDriver(cursor, connection)

        self.users: List[Dict[str, Any]] = get_users()

    def teardown(self) -> None:
        """ Closes the database connection after tests. """
        self.driver.close()

    def get_user(
        self,
        user_id: int,
    ) -> Optional[DiscordMember]:
        """ Gets a vendor for the product creation.
        :param vendor: The vendor to get. """

        with suppress(Exception):
            return next(x
                for x in self.users
                if x.id == user_id)
        return

    @pytest.mark.asyncio
    async def test_start_classroom(self) -> None:
        """ Tests the creation of a classroom. """

        # Imports the teacherfeedback's cog
        from cogs import teacherfeedback

        # Gets basic required data
        current_time = int(await get_timestamp())
        member: DiscordMember = self.get_user(user_id=DNK_ID)
        
        # Mocks DB connector
        teacherfbdb = teacherfeedback.TeacherFeedbackDatabase
        teacherfb = teacherfeedback.TeacherFeedback

        # Mocks the TeacherFeedback class methods and properties
        teacherfb.cache = {}
        teacherfb.teacher_cache = {}
        teacherfb.db = Mock(return_value=self.driver)
        teacherfb.db.get_active_teacher_class_by_teacher_id = AsyncMock(return_value=[])
        teacherfb.db.get_teacher_saved_classes = AsyncMock(return_value=[])

        # Mocks class creation questions
        class_info: Dict[str, str] = {
            'language': 'Portuguese', 'type': 'Pronunciation', 'desc': "Beginner's class", 'taught_in': 'English'}
        teacherfb.ask_class_creation_questions = AsyncMock(return_value=class_info)

        # Inserts Active Class
        inserted_class = teacherfb.start_class = AsyncMock(
            return_value=self.driver.insert_active_teacher_class(
                teacher_id=member.id, language=class_info['language'], 
                class_type=class_info['type'], vc_timestamp=current_time,
                class_desc=class_info['desc'], taught_in=class_info['taught_in']
            )
        )
        result = await inserted_class()
        # Checks whether Active Class was indeed inserted into the database
        assert (result["teacher_id"], result["language"]) == (member.id, class_info["language"])
        
        # Mocks Channel creation
        await teacherfb.create_class(teacherfb, member)
        # Deletes Active Class from the database
        await teacherfbdb.delete_active_teacher_class_by_teacher_and_vc_id(
            object,
            teacher_id=member.id, vc_id=result["vc_id"], 
        )

    @pytest.mark.skip(reason="Not implemented.")
    def test_end_classroom(self) -> None: pass

    @pytest.mark.skip(reason="Not implemented.")
    def test_reward_people(self) -> None: pass

