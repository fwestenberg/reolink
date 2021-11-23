from unittest import TestCase

import unittest
import aiounittest
import asyncio
import os
import time
import logging

from reolink.camera_api import Api
from reolink.subscription_manager import Manager

DO_DEBUG = False

USER = "Test"
PASSWORD = "12345678"
HOST = "192.168.80.43"
PORT = 80


class TestApi(TestCase):


    def test_login(self):
        # logging.debug("setting up")
        self.setup()
        loop = asyncio.get_event_loop()
        assert loop.run_until_complete(self.do_login())

    async def do_login(self):
        # logging.debug("in do login")

        api = Api(
            host=self._host,
            port=self._port,
            username=self._user,
            password=self._password,
        )

        if await api.login():
            await api.logout()
            self.tearDown()
            return True
        else:
            return False

    def test_get_states(self):
        # logging.debug("setting up get settings")
        self.setup()
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.do_get_settings())
        loop.run_until_complete(self.do_get_states())

    async def do_get_states(self):
        api = Api(
            host=self._host,
            port=self._port,
            username=self._user,
            password=self._password,
        )
        await api.get_settings()
        # logging.debug("in do get states ", await api.get_states())

        if await api.get_states():
            await api.logout()
            return True
        else:
            await api.logout()
            return False

    def test_get_settings(self):
        # logging.debug("setting up get settings")
        self.setup()
        loop = asyncio.get_event_loop()
        assert loop.run_until_complete(self.do_get_settings())

    async def do_get_settings(self):
        api = Api(
            host=self._host,
            port=self._port,
            username=self._user,
            password=self._password,
        )
        # logging.debug("in do get settings ", await api.get_settings())

        if await api.get_settings():
            await api.logout()
            return True
        else:
            await api.logout()
            return False


    def test_set_ir_lights(self):
        # logging.debug("setting up ir lights settings")
        self.setup()
        loop = asyncio.get_event_loop()
        assert loop.run_until_complete(self.do_set_ir(False))
        assert loop.run_until_complete(self.do_set_ir(True))

    async def do_set_ir(self, state):
        api = Api(
            host=self._host,
            port=self._port,
            username=self._user,
            password=self._password,
        )

        await api.get_settings()
        await api.get_states()
        # logging.debug("in do set ir ", await api.set_ir_lights(state))
        #await api.logout()

        if await api.set_ir_lights(state):
            await api.logout()
            return True
        else:
            await api.logout()
            return False


    def test_set_whiteled(self):
    # White Led State (Spotlight )
    # required tests listed inline

        # logging.debug("setting up spotlight settings")
        self.setup()
        loop = asyncio.get_event_loop()
        #   turn off , night mode off """
        assert self._loop.run_until_complete(self.do_set_whiteled(False, 50, 0))
        #   turn on, night mode off """
        assert self._loop.run_until_complete(self.do_set_whiteled(True, 50, 0))
        #   turn off, , night mode on """
        assert self._loop.run_until_complete(self.do_set_whiteled(False, 50, 1))
        #   turn on, night mode on , auto mode """
        assert self._loop.run_until_complete(self.do_set_whiteled(True, 50, 1))
        #   turn off, night mode on, scheduled """
        assert self._loop.run_until_complete(self.do_set_whiteled(False, 50, 3))
        #   turn on,  night mode on, scheduled mode """
        assert self._loop.run_until_complete(self.do_set_whiteled(True, 50, 3))
        # so that effect can be seen on spotlight wait 2 seconds between changes """
        time.sleep(2)
        #   Turn on, NM on, auto Bright = 0 """
        assert self._loop.run_until_complete(self.do_set_whiteled(True, 0, 1))
        time.sleep(2)
        #   Turn on, NM on, auto Bright = 100 """
        assert self._loop.run_until_complete(self.do_set_whiteled(True, 100, 1))
        # now turn off light - does not require an assert """
        self._loop.run_until_complete(self.do_set_whiteled(False, 50, 0))
        # with incorrect values the routine should return a False """
        #   incorrect mode not 0,1,3 """
        assert not self._loop.run_until_complete(self.do_set_whiteled(True, 100, 2))
        #   incorrect brightness < 0 """
        assert not self._loop.run_until_complete(self.do_set_whiteled(False, -10, 1))
        #  incorrect brightness > 100
        assert not self._loop.run_until_complete(self.do_set_whiteled(False, 1000, 1))
        #
        # now the lighting schedule
        #
        # get and print the existing settings

        self._loop.run_until_complete(self.do_get_schedule())
        assert self._loop.run_until_complete(self.do_set_spotlight_lighting_schedule(5,30,17,30))
        self._loop.run_until_complete(self.do_get_schedule())
        assert self._loop.run_until_complete(self.do_set_spotlight_lighting_schedule(7, 30, 19, 30))
        self._loop.run_until_complete(self.do_get_schedule())
        # invalid parameters
        assert not self._loop.run_until_complete(self.do_set_spotlight_lighting_schedule(-1, 0, 18, 0))
        assert not self._loop.run_until_complete(self.do_set_spotlight_lighting_schedule(24, 0, 18, 0))
        assert not self._loop.run_until_complete(self.do_set_spotlight_lighting_schedule(6, -2, 18, 0))
        assert not self._loop.run_until_complete(self.do_set_spotlight_lighting_schedule(6, 60, 18, 0))
        assert not self._loop.run_until_complete(self.do_set_spotlight_lighting_schedule(6, 0, -3, 0))
        assert not self._loop.run_until_complete(self.do_set_spotlight_lighting_schedule(6, 0, 24, 0))
        assert not self._loop.run_until_complete(self.do_set_spotlight_lighting_schedule(6, 0, 18, -4))
        assert not self._loop.run_until_complete(self.do_set_spotlight_lighting_schedule(18, 59, 19, 0))
        assert not self._loop.run_until_complete(self.do_set_spotlight_lighting_schedule(18, 29, 18, 30))
    #  query should end time equals start time be an error
        assert not self._loop.run_until_complete(self.do_set_spotlight_lighting_schedule(6, 0, 6, 0))

    async def do_get_schedule(self):
        api = Api(
            host=self._host,
            port=self._port,
            username=self._user,
            password=self._password,
        )

        await api.get_settings()
        await api.get_states()
        print(api._whiteled_settings["value"]["WhiteLed"]["LightingSchedule"])
        await api.logout()
        return

    async def do_set_whiteled(self,new_enable,new_bright, new_mode):
        api = Api(
            host=self._host,
            port=self._port,
            username=self._user,
            password=self._password,
        )

        await api.get_settings()
        await api.get_states()
        # logging.debug("in do set whiteled ", await api.set_whiteled(new_enable,new_bright,new_mode))

        if await api.set_whiteled(new_enable,new_bright,new_mode):
            await api.logout()
            return True
        else:
            await api.logout()
            return False

    async def do_set_spotlight_lighting_schedule(self, endhour,endmin,starthour,startmin):
        api = Api(
            host=self._host,
            port=self._port,
            username=self._user,
            password=self._password,
        )

        await api.get_settings()
        await api.get_states()

        if await api.set_spotlight_lighting_schedule(endhour,endmin,starthour,startmin):
            await api.logout()
            return True
        else:
            await api.logout()
            return False

    def test_spotlight(self):
        self.setup()
        loop = asyncio.get_event_loop()

        assert self._loop.run_until_complete(self.do_set_spotlight(True))
        time.sleep(5)
        assert self._loop.run_until_complete(self.do_set_spotlight(False))

    async def do_set_spotlight(self,enable):
        api = Api(
            host=self._host,
            port=self._port,
            username=self._user,
            password=self._password,
        )

        await api.get_settings()
        await api.get_states()

        if await api.set_spotlight(enable):
            await api.logout()
            return True
        else:
            await api.logout()
            return False

    def test_siren(self):
        self.setup()
        loop = asyncio.get_event_loop()

        assert self._loop.run_until_complete(self.do_set_siren(True))
        time.sleep(10)
        assert self._loop.run_until_complete(self.do_set_siren(False))
        time.sleep(10)
        assert self._loop.run_until_complete(self.do_set_siren(True))
        time.sleep(10)
        assert self._loop.run_until_complete(self.do_set_siren(False))

    async def do_set_siren(self,enable):
        api = Api(
            host=self._host,
            port=self._port,
            username=self._user,
            password=self._password,
        )

        await api.get_settings()
        await api.get_states()

        if await api.set_siren(enable):
            await api.logout()
            return True
        else:
            await api.logout()
            return False



    def setup(self):
        self._loop = asyncio.new_event_loop()
        self.addCleanup(self._loop.close)
        self._user = USER
        self._password = PASSWORD
        self._host = HOST
        self._port = PORT




    def tearDown(self):
        self._loop.close()



