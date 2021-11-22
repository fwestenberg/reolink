import aiounittest
import asyncio
import os
import time

from reolink.camera_api import Api
from reolink.subscription_manager import Manager

USER = "Test"
PASSWORD = "12345678"
HOST = "192.168.80.43"
PORT = 80


class TestLogin(aiounittest.AsyncTestCase):
    def setUp(self):
        self._loop = asyncio.new_event_loop()
        self.addCleanup(self._loop.close)
        self._user = USER
        self._password = PASSWORD
        self._host = HOST
        self._port = PORT

    def tearDown(self):
        self._loop.close()

    def test_succes(self):
        api = Api(
            host=self._host,
            port=self._port,
            username=self._user,
            password=self._password,
        )
        assert self._loop.run_until_complete(api.login())
        assert api.session_active
        self._loop.run_until_complete(api.logout())

    def test_wrong_password(self):
        api = Api(
            host=self._host, port=self._port, username=self._user, password="wrongpass"
        )
        assert not self._loop.run_until_complete(api.login())
        assert not api.session_active
        assert not self._loop.run_until_complete(api.get_states())
        assert not self._loop.run_until_complete(api.get_settings())
        assert not self._loop.run_until_complete(api.get_motion_state())
        assert not self._loop.run_until_complete(api.get_stream_source())
        assert not self._loop.run_until_complete(api.set_ftp(True))

    def test_wrong_user(self):
        api = Api(
            host=self._host,
            port=self._port,
            username="wronguser",
            password=self._password,
        )
        assert not self._loop.run_until_complete(api.login())
        assert not api.session_active

    def test_wrong_host(self):
        api = Api(
            host="192.168.1.0",
            port=self._port,
            username=self._user,
            password=self._password,
        )
        assert not self._loop.run_until_complete(api.login())
        assert not api.session_active


class TestGetData(aiounittest.AsyncTestCase):
    def setUp(self):
        self._loop = asyncio.new_event_loop()
        self.addCleanup(self._loop.close)

        self._user = USER
        self._password = PASSWORD
        self._host = HOST
        self._port = PORT

        self._api = Api(
            host=self._host,
            port=self._port,
            username=self._user,
            password=self._password,
        )
        assert self._loop.run_until_complete(self._api.login())
        assert self._api.session_active

    def test1_settings(self):
        assert self._loop.run_until_complete(self._api.get_settings())
        self._loop.run_until_complete(self._api.is_admin())

        assert self._api.host is not None
        assert self._api.port is not None
        assert self._api.channel is not None
        assert self._api.onvif_port is not None
        assert self._api.mac_address is not None
        assert self._api.serial is not None
        assert self._api.name is not None
        assert self._api.sw_version is not None
        assert self._api.model is not None
        assert self._api.manufacturer is not None
        assert self._api.rtmp_port is not None
        assert self._api.rtsp_port is not None
        assert self._api.stream is not None
        assert self._api.protocol is not None

        assert self._api.device_info is not None
        assert self._api.hdd_info is not None
        assert self._api.ptz_support is not None

        self._api._users.append({"level": "guest", "userName": "guest"})
        self._api._username = "guest"
        assert not self._loop.run_until_complete(self._api.is_admin())

    def test2_states(self):
        assert self._loop.run_until_complete(self._api.get_states())
        assert self._loop.run_until_complete(self._api.get_motion_state()) is not None

        self._api._ptz_support = True
        self._api._ptz_presets["test"] = 123

        assert (
            self._loop.run_until_complete(self._api.get_switch_capabilities())
            is not None
        )

    def test3_images(self):
        assert self._loop.run_until_complete(self._api.get_still_image()) is not None
        self._api._channel = 9
        assert self._loop.run_until_complete(self._api.get_still_image()) is None
        self._api._channel = 0
        assert self._loop.run_until_complete(self._api.get_snapshot()) is not None
        assert self._loop.run_until_complete(self._api.get_stream_source()) is not None

    def test4_properties(self):
        assert self._loop.run_until_complete(self._api.get_states())

        assert self._api.motion_state is not None
        assert self._api.ftp_state is not None
        assert self._api.email_state is not None
        assert self._api.ir_state is not None
        assert self._api.whiteled_state is not None 
        assert self._api.daynight_state is not None
        assert self._api.recording_state is not None
        assert self._api.audio_state is not None
        assert self._api.motion_detection_state is not None
        assert self._api.ptz_presets == {}  # Cam has no ptz
        assert self._api.sensititivy_presets is not None

        get_ptz_response = [
            {
                "cmd": "GetPtzPreset",
                "code": 0,
                "value": {
                    "PtzPreset": [
                        {"enable": 0, "name": "Preset_1", "id": 0},
                        {"enable": 1, "name": "Preset_2", "id": 1},
                    ]
                },
            }
        ]
        self._loop.run_until_complete(self._api.map_json_response(get_ptz_response))
        assert self._api._ptz_presets is not None
        assert self._api._ptz_presets_settings is not None
        assert not self._loop.run_until_complete(
            self._api.send_setting([{"cmd": "wrong_command"}])
        )

        for _ in range(1):
            self._loop.run_until_complete(
                self._api.update_streaming_options("sub", "rtsp", 1)
            )

            self._loop.run_until_complete(
                self._api.update_streaming_options("main", "rtmp", 0)
            )

            """FTP state."""
            assert self._loop.run_until_complete(self._api.set_ftp(True))
            assert self._api.ftp_state
            assert self._loop.run_until_complete(self._api.set_ftp(False))
            assert not self._api.ftp_state

            """Email state."""
            assert self._loop.run_until_complete(self._api.set_email(True))
            assert self._api.email_state
            assert self._loop.run_until_complete(self._api.set_email(False))
            assert not self._api.email_state

            """Audio state."""
            assert self._loop.run_until_complete(self._api.set_audio(True))
            assert self._api.audio_state
            assert self._loop.run_until_complete(self._api.set_audio(False))
            assert not self._api.audio_state

            """ir state."""
            assert self._loop.run_until_complete(self._api.set_ir_lights(True))
            assert self._api.ir_state
            assert self._loop.run_until_complete(self._api.set_ir_lights(False))
            assert not self._api.ir_state

            """Daynight state."""
            assert self._loop.run_until_complete(self._api.set_daynight("Auto"))
            assert self._api.daynight_state
            assert self._loop.run_until_complete(self._api.set_daynight("Color"))
            assert not self._api.daynight_state

            """Recording state."""
            assert self._loop.run_until_complete(self._api.set_recording(True))
            assert self._api.recording_state
            assert self._loop.run_until_complete(self._api.set_recording(False))
            assert not self._api.recording_state

            """Motion detection state."""
            assert self._loop.run_until_complete(self._api.set_motion_detection(True))
            assert self._api.motion_detection_state is not None  # Ignore state
            assert self._loop.run_until_complete(self._api.set_motion_detection(False))

            assert self._loop.run_until_complete(self._api.get_states())

            assert (
                self._loop.run_until_complete(self._api.get_stream_source()) is not None
            )

            assert (
                self._loop.run_until_complete(
                    self._api.set_ptz_command("RIGHT", speed=10)
                )
                == False
            )
            assert (
                self._loop.run_until_complete(
                    self._api.set_ptz_command("GOTO", preset=1)
                )
                == False
            )
            assert (
                self._loop.run_until_complete(self._api.set_ptz_command("STOP"))
                == False
            )

            assert self._loop.run_until_complete(self._api.set_sensitivity(value=10))
            assert self._loop.run_until_complete(
                self._api.set_sensitivity(value=45, preset=0)
            )

            """ White Led State (Spotlight )  """
            """ required tests """
            """    turn off , night mode off """
            """    turn on, night mode off """
            """    turn off, , night mode on """
            """    turn on, night mode on , auto mode """
            """    turn off, night mode on, scheduled """
            """    turn on,  night mode on, scheduled mode """
            """    Turn on, NM on, auto Bright = 0 """
            """    Turn on, NM on, auto Bright = 100 """
            """    incorrect mode not 0,1,3 """
            """    incorrect brightness < 0 """
            """    incorrect brightness > 100 """
            

            assert self._loop.run_until_complete(self._api.set_whiteled(False,50,0))
            assert self._loop.run_until_complete(self._api.set_whiteled(True,50,0))
            assert self._loop.run_until_complete(self._api.set_whiteled(False,50,1))
            assert self._loop.run_until_complete(self._api.set_whiteled(True,50,1))
            assert self._loop.run_until_complete(self._api.set_whiteled(False,50,3))
            assert self._loop.run_until_complete(self._api.set_whiteled(True,50,3))
            """  so that effect can be seen on spotlight wait 2 seconds between changes """
            time.sleep(2)
            assert self._loop.run_until_complete(self._api.set_whiteled(True,0,1))
            time.sleep(2)
            assert self._loop.run_until_complete(self._api.set_whiteled(True,100,1))
            assert self._loop.run_until_complete(self._api.set_whiteled(True,100,2))
            time.sleep(2)
            """ now turn off light - does not require an assert """
            self.loop.run_until_complete(self._api.set_whiteled(False,50,0))
            """ with incorrect values the routine should return a False """
            assert not self._loop.run_until_complete(self._api.set_whiteled(True,-10,1))
            assert not self._loop.run_until_complete(self._api.set_whiteled(True,1000,1))
            """  now tests for setting the schedule for spotlight when night mode non auto"""
            assert self._loop.run_until_complete(self._api.set_spotlight_lighting_schedule(5, 30, 17, 30))
            assert self._loop.run_until_complete(self._api.set_spotlight_lighting_schedule(7, 30, 19, 30))
            # invalid parameters
            assert not self._loop.run_until_complete(self._api.set_spotlight_lighting_schedule(-1, 0, 18, 0))
            assert not self._loop.run_until_complete(self._api.set_spotlight_lighting_schedule(24, 0, 18, 0))
            assert not self._loop.run_until_complete(self._api.set_spotlight_lighting_schedule(6, -2, 18, 0))
            assert not self._loop.run_until_complete(self._api.set_spotlight_lighting_schedule(6, 60, 18, 0))
            assert not self._loop.run_until_complete(self._api.set_spotlight_lighting_schedule(6, 0, -3, 0))
            assert not self._loop.run_until_complete(self._api.set_spotlight_lighting_schedule(6, 0, 24, 0))
            assert not self._loop.run_until_complete(self._api.set_spotlight_lighting_schedule(6, 0, 18, -4))
            assert not self._loop.run_until_complete(self._api.set_spotlight_lighting_schedule(18, 59, 19, 0))
            assert not self._loop.run_until_complete(self._api.set_spotlight_lighting_schedule(18, 29, 18, 30))
            #  query should end time equals start time be an error
            assert not self._loop.run_until_complete(self._api.set_spotlight_lighting_schedule(6, 0, 6, 0))

    def tearDown(self):
        self._loop.run_until_complete(self._api.logout())
        self._loop.close()


class TestSubscription(aiounittest.AsyncTestCase):
    def setUp(self):
        self._loop = asyncio.new_event_loop()
        self.addCleanup(self._loop.close)
        self._user = USER
        self._password = PASSWORD
        self._host = HOST
        self._port = PORT

    def tearDown(self):
        self._loop.close()

    def test_succes(self):
        api = Api(
            host=self._host,
            port=self._port,
            username=self._user,
            password=self._password,
        )
        assert self._loop.run_until_complete(api.login())
        assert api.session_active
        assert self._loop.run_until_complete(api.get_settings())
        subscribe_port = api.onvif_port
        self._loop.run_until_complete(api.logout())

        smen = Manager(
            host=self._host,
            port=subscribe_port,
            username=self._user,
            password=self._password,
        )

        assert self._loop.run_until_complete(smen.subscribe("192.168.1.1/fakewebhook"))
        assert self._loop.run_until_complete(smen.renew())
        assert smen.renewtimer > 0
        assert self._loop.run_until_complete(smen.unsubscribe())
        assert smen.renewtimer == 0

        assert not self._loop.run_until_complete(smen.convert_time("no_time"))
        assert not self._loop.run_until_complete(smen.extract_value("test", "<no_xml>"))
        smen._password = "notmypassword"
        assert not self._loop.run_until_complete(
            smen.subscribe("192.168.1.1/fakewebhook")
        )
        smen._host = "192.168.1.1"
        assert not self._loop.run_until_complete(
            smen.subscribe("192.168.1.1/fakewebhook")
        )
