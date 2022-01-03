"""
Reolink Camera API
"""
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from . import typings
from .software_version import SoftwareVersion
from .exceptions import CredentialsInvalidError, SnapshotIsNotValidFileTypeError, InvalidContentTypeError
import traceback
import re

import asyncio
import aiohttp
import urllib.parse as parse

MANUFACTURER = "Reolink"
DEFAULT_USE_SSL = False
DEFAULT_STREAM = "main"
DEFAULT_PROTOCOL = "rtmp"
DEFAULT_CHANNEL = 0
DEFAULT_TIMEOUT = 30
DEFAULT_STREAM_FORMAT = "h264"
DEFAULT_RTMP_AUTH_METHOD = 'PASSWORD'

_LOGGER = logging.getLogger(__name__)
_LOGGER_DATA = logging.getLogger(__name__+".data")


ref_sw_version_3_0_0_0_0 = SoftwareVersion("v3.0.0.0_0")
ref_sw_version_3_1_0_0_0 = SoftwareVersion("v3.1.0.0_0")


class Api:  # pylint: disable=too-many-instance-attributes disable=too-many-public-methods
    """Reolink API class."""

    def __init__(
        self,
        host,
        port,
        username,
        password,
        use_https=DEFAULT_USE_SSL,
        channel=DEFAULT_CHANNEL,
        protocol=DEFAULT_PROTOCOL,
        stream=DEFAULT_STREAM,
        timeout=DEFAULT_TIMEOUT,
        stream_format=DEFAULT_STREAM_FORMAT,
        rtmp_auth_method=DEFAULT_RTMP_AUTH_METHOD,
    ):
        """Initialize the API class."""
        self._url = ""
        self._host = host
        self._port = port
        self._username = username
        self._password = password[:31]
        self._channel = channel
        self._stream = stream
        self._protocol = protocol
        self._stream_format = stream_format
        self._rtmp_auth_method = rtmp_auth_method
        self._timeout = aiohttp.ClientTimeout(total=timeout)
        self._use_https = use_https

        self._token = None
        self._lease_time = None
        self._motion_state = False
        self._ai_state = None
        self._device_info = None
        self._hdd_info = None
        self._ftp_state = None
        self._push_state = None
        self._email_state = None
        self._ir_state = None
        self._whiteled_state = None
        self._whiteled_mode = None
        self._daynight_state = None
        self._backlight_state = None
        self._recording_state = None
        self._audio_state = None
        self._audio_alarm_state = None
        self._rtsp_port = None
        self._rtmp_port = None
        self._onvifport = None
        self._mac_address = None
        self._serial = None
        self._name = None
        self._sw_version = None
        self._sw_version_object: Optional[SoftwareVersion] = None
        self._model = None
        self._channels = None
        self._ptz_presets = dict()
        self._sensitivity_presets = dict()
        self._motion_detection_state = None

        self._auto_focus_settings = None
        self._time_settings = None
        self._ntp_settings = None
        self._isp_settings = None
        self._ftp_settings = None
        self._osd_settings = None
        self._push_settings = None
        self._enc_settings = None
        self._ptz_presets_settings = None
        self._ability_settings = None
        self._netport_settings = None
        self._email_settings = None
        self._ir_settings = None
        self._whiteled_settings = None
        self._recording_settings = None
        self._alarm_settings = None
        self._audio_alarm_settings = None
        self._users = None
        self._local_link = None
        self._ptz_support = False

        self._is_nvr = False
        self._is_ia_enabled = False

        self._aiohttp_session: aiohttp.ClientSession = aiohttp.ClientSession(timeout=self._timeout,
                                                                    connector=aiohttp.TCPConnector(ssl=False))

        self._api_version_getrec: int = 0
        self._api_version_getftp: int = 0
        self._api_version_getpush: int = 0
        self._api_version_getalarm: int = 0

        self.refresh_base_url()

    def enable_https(self, enable: bool):
        self._use_https = enable
        self.refresh_base_url()

    def refresh_base_url(self):
        if self._use_https:
            self._url = f"https://{self._host}:{self._port}/cgi-bin/api.cgi"
        else:
            self._url = f"http://{self._host}:{self._port}/cgi-bin/api.cgi"

    @property
    def host(self):
        """Return the host."""
        return self._host

    @property
    def port(self):
        """Return the port."""
        return self._port

    @property
    def is_ia_enabled(self):
        """Wether or not the camera support IA"""
        return self._is_ia_enabled

    @property
    def onvif_port(self):
        """Return the onvif port for subscription."""
        return self._onvifport

    @property
    def mac_address(self):
        """Return the mac address."""
        return self._mac_address

    @property
    def serial(self):
        """Return the serial."""
        return self._serial

    @property
    def name(self):
        """Return the camera name."""
        return self._name

    @property
    def sw_version(self):
        """Return the software version."""
        return self._sw_version

    @property
    def model(self):
        """Return the model."""
        return self._model

    @property
    def manufacturer(self):
        """Return the manufacturer name (Reolink)."""
        return MANUFACTURER

    @property
    def channels(self):
        """Return the number of channels."""
        return self._channels

    @property
    def motion_state(self):
        """Return the motion state (polling)."""
        return self._motion_state

    @property
    def ai_state(self):
        """Return the AI state."""
        return self._ai_state

    @property
    def ftp_state(self):
        """Return the FTP state."""
        return self._ftp_state

    @property
    def push_state(self):
        """Return the PUSH (notifications) state."""
        return self._push_state

    @property
    def email_state(self):
        """Return the email state."""
        return self._email_state

    @property
    def ir_state(self):
        """Return the infrared state."""
        return self._ir_state

    @property
    def whiteled_state(self):
        """Return the spotlight state."""
        if self._whiteled_state == 1:
            return True
        else:
            return False

    @property
    def whiteled_mode(self):
        """Return the spotlight state."""
        return self._whiteled_mode

    @property
    def whiteled_schedule(self):
        """Return the spotlight state."""
        return self._whiteled_settings["value"]["WhiteLed"]["LightingSchedule"]

    @property
    def whiteled_settings(self):
        """Return the spotlight state."""
        return self._whiteled_settings

    @property
    def daynight_state(self):
        """Return the daynight state."""
        return self._daynight_state

    @property
    def backlight_state(self):
        """Return the backlight state."""
        return self._backlight_state

    @property
    def recording_state(self):
        """Return the recording state."""
        return self._recording_state

    @property
    def audio_state(self):
        """Return the audio state."""
        return self._audio_state

    @property
    def audio_alarm_settings(self):
        """Return the audio state."""
        return self._audio_alarm_settings

    @property
    def audio_alarm_state(self):
        """Return the audio state."""
        if self._audio_alarm_state == 1:
            return True
        else:
            return False

    @property
    def rtmp_port(self):
        """Return the RTMP port."""
        return self._rtmp_port

    @property
    def rtsp_port(self):
        """Return the RTSP port."""
        return self._rtsp_port

    @property
    def ptz_presets(self):
        """Return the PTZ presets."""
        return self._ptz_presets

    @property
    def sensitivity_presets(self):
        """Return the sensitivity presets."""
        return self._sensitivity_presets

    @property
    def device_info(self):
        """Return the device info."""
        return self._device_info

    @property
    def hdd_info(self):
        """Return the HDD info."""
        return self._hdd_info

    @property
    def stream(self):
        """Return the stream."""
        return self._stream

    @property
    def protocol(self):
        """Return the protocol."""
        return self._protocol

    @property
    def stream_format(self):
        """Return the stream format."""
        return self._stream_format

    @property
    def channel(self):
        """Return the channel number."""
        return self._channel

    @property
    def ptz_support(self):
        """Return if PTZ is supported."""
        return self._ptz_support

    @property
    def motion_detection_state(self):
        """Return the motion detection state."""
        return self._motion_detection_state

    @property
    def session_active(self):
        """Return if the session is active."""
        if self._token is not None and self._lease_time > datetime.now():
            return True

        self._token = None
        self._lease_time = None
        return False

    @property
    def api_version_getrec(self):
        return self._api_version_getrec

    def clear_token(self):
        """Initialize the token and lease time."""
        self._token = None
        self._lease_time = None

    async def get_switch_capabilities(self):
        """Return the capabilities of the camera."""
        capabilities = []

        if self._ftp_state is not None:
            capabilities.append("ftp")

        if self._push_state is not None:
            capabilities.append("push")

        if self._ir_state is not None:
            capabilities.append("irLights")

        if self._whiteled_state is not None:
            capabilities.append("spotlight")

        if self._audio_alarm_state is not None:
            capabilities.append("siren")

        if self._recording_state is not None:
            capabilities.append("recording")

        if self._motion_detection_state is not None:
            capabilities.append("motionDetection")

        if self._daynight_state is not None:
            capabilities.append("dayNight")

        if self._backlight_state is not None:
            capabilities.append("backLight")

        if self._email_state is not None:
            capabilities.append("email")

        if self._audio_state is not None:
            capabilities.append("audio")

        if self._ptz_support:
            capabilities.append("ptzControl")

        if len(self._ptz_presets) != 0:
            capabilities.append("ptzPresets")

        if len(self._sensitivity_presets) != 0:
            capabilities.append("sensitivityPresets")

        return capabilities

    async def get_states(self, cmd_list=None):
        """Fetch the state objects."""
        body = [
            {"cmd": "GetFtp", "action": 1, "param": {"channel": self._channel}},
            {"cmd": "GetEnc", "action": 1, "param": {"channel": self._channel}},
            {"cmd": "GetEmail", "action": 1, "param": {"channel": self._channel}},
            {"cmd": "GetIsp", "action": 1, "param": {"channel": self._channel}},
            {"cmd": "GetIrLights", "action": 1, "param": {"channel": self._channel}},
            {"cmd": "GetWhiteLed", "action": 0, "param": {"channel": self._channel}},
            {"cmd": "GetPtzPreset", "action": 1, "param": {"channel": self._channel}},
            {"cmd": "GetHddInfo", "action": 1, "param": {}},
            {
                "cmd": "GetAlarm",
                "action": 1,
                "param": {"Alarm": {"channel": self._channel, "type": "md"}},
            },
        ]

        if self._api_version_getpush == 0:
            body.append({"cmd": "GetPush", "action": 1, "param": {"channel": self._channel}})
        else:
            body.append({"cmd": "GetPushV20", "action": 1, "param": {"channel": self._channel}})

        if self._api_version_getftp == 0:
            body.append({"cmd": "GetFtp", "action": 1, "param": {"channel": self._channel}})
        else:
            body.append({"cmd": "GetFtpV20", "action": 1, "param": {"channel": self._channel}})

        if self._api_version_getrec == 0:
            body.append({"cmd": "GetRec", "action": 1, "param": {"channel": self._channel}})
        else:
            body.append({"cmd": "GetRecV20", "action": 1, "param": {"channel": self._channel}})

        if self._api_version_getalarm == 0:
            body.append({"cmd": "GetAudioAlarm", "action": 1, "param": {"channel": self._channel}})
        else:
            body.append({"cmd": "GetAudioAlarmV20", "action": 1, "param": {"channel": self._channel}})

        if cmd_list is not None:
            for x, line in enumerate(body):
                if line["cmd"] not in cmd_list:
                    body.pop(x)

        response = await self.send(body)
        if response is None:
            print("states none")
            return False

        try:
            json_data = json.loads(response)
            self.map_json_response(json_data)
            return True
        except (TypeError, json.JSONDecodeError) as e:
            _LOGGER.debug(
                "Host: %s: Error translating Reolink state response: e", self._host, e
            )
            self.clear_token()
            return False

    async def get_settings(self):
        """Fetch the settings."""
        body = [
            {"cmd": "GetDevInfo", "action": 1, "param": {"channel": self._channel}},
            {"cmd": "GetLocalLink", "action": 1, "param": {"channel": self._channel}},
            {"cmd": "GetNetPort", "action": 1, "param": {"channel": self._channel}},
            {"cmd": "GetUser", "action": 1, "param": {"channel": self._channel}},
            {"cmd": "GetOsd", "action": 1, "param": {"channel": self._channel}},
            {
                "cmd": "GetAbility",
                "action": 1,
                "param": {"User": {"userName": self._username}},
            },
            {"cmd": "GetAiState", "action": 0, "param": {"channel": self._channel}},  # to capture AI capabilities
            {"cmd": "GetNtp", "action": 0, "param": {}},
            {"cmd": "GetTime", "action": 0, "param": {}},
            {"cmd": "GetAutoFocus", "action": 0, "param": {"channel": self._channel}},
        ]

        response = await self.send(body)
        if response is None:
            return False

        try:
            json_data = json.loads(response)
            self.map_json_response(json_data)
        except (TypeError, json.JSONDecodeError):
            _LOGGER.debug(
                "Host %s: Error translating Reolink settings response", self._host
            )
            self.clear_token()
            return False

        # checking API versions (because Reolink dev quality sucks big time we cannot fully trust GetAbility)
        body = []
        if self._api_version_getpush == 1:
            body.append({"cmd": "GetPushV20", "action": 1, "param": {"channel": self._channel}})
        if self._api_version_getftp == 1:
            body.append({"cmd": "GetFtpV20", "action": 1, "param": {"channel": self._channel}})
        if self._api_version_getrec == 1:
            body.append({"cmd": "GetRecV20", "action": 1, "param": {"channel": self._channel}})
        if self._api_version_getalarm == 1:
            body.append({"cmd": "GetAudioAlarmV20", "action": 1, "param": {"channel": self._channel}})

        response = await self.send(body)
        try:
            json_data = json.loads(response)
        except (TypeError, json.JSONDecodeError):
            _LOGGER.debug(
                "Host %s: Error translating Reolink settings response", self._host
            )
            self.clear_token()
            return False

        def check_command_exists(cmd: str):
            for x in json_data:
                if x["cmd"] == cmd:
                    return True
            return False

        if self._api_version_getpush == 1:
            if not check_command_exists("GetPushV20"):
                self._api_version_getpush = 0

        if self._api_version_getftp == 1:
            if not check_command_exists("GetFtpV20"):
                self._api_version_getftp = 0

        if self._api_version_getrec == 1:
            if not check_command_exists("GetRecV20"):
                self._api_version_getrec = 0

        if self._api_version_getalarm == 1:
            if not check_command_exists("GetAudioAlarmV20"):
                self._api_version_getalarm = 0

        return True

    async def get_motion_state(self):
        """Fetch the motion state."""
        body = [{"cmd": "GetMdState", "action": 0, "param": {"channel": self._channel}}]

        response = await self.send(body)
        if response is None:
            return False

        try:
            json_data = json.loads(response)

            if json_data is None:
                _LOGGER.error(
                    "Unable to get Motion detection state at IP %s", self._host
                )
                self._motion_state = False
                return self._motion_state

            self.map_json_response(json_data)
        except (TypeError, json.JSONDecodeError):
            self.clear_token()
            self._motion_state = False

        return self._motion_state

    async def get_ai_state(self):
        """Fetch the AI state."""
        body = [{"cmd": "GetAiState", "action": 0, "param": {"channel": self._channel}}]

        response = await self.send(body)
        if response is None:
            return False

        try:
            json_data = json.loads(response)

            if json_data is None:
                _LOGGER.error(
                    "Unable to get AI detection state at IP %s", self._host
                )            
                return self._ai_state

            self.map_json_response(json_data)
        except (TypeError, json.JSONDecodeError):
            self.clear_token()

        return self._ai_state

    async def get_all_motion_states(self):
        """Fetch All motions states at once (regular + AI)."""
        body = [{"cmd": "GetMdState", "action": 0, "param": {"channel": self._channel}},
                {"cmd": "GetAiState", "action": 0, "param": {"channel": self._channel}}]

        response = await self.send(body)
        json_data = json.loads(response)

        if json_data is None:
            _LOGGER.error(
                "Unable to get All Motion States at IP %s", self._host
            )
            self._motion_state = False
            return self._motion_state

        self.map_json_response(json_data)

    async def get_still_image(self):
        """Get the still image."""
        param = {"cmd": "Snap", "channel": self._channel}

        response = await self.send(None, param, expected_content_type='image/jpeg')
        if response is None or response == b"":
            return

        return response

    async def get_snapshot(self):
        """Get a snapshot."""
        return await self.get_still_image()

    def get_rtmp_stream_source(self) -> str:
        if self._rtmp_auth_method == DEFAULT_RTMP_AUTH_METHOD:
            return f"rtmp://{self._host}:{self._rtmp_port}/bcs/channel{self._channel}_{self._stream}.bcs?channel=" \
                   f"{self._channel}&stream=0&user={self._username}&password={self._password}"

        return f"rtmp://{self._host}:{self._rtmp_port}/bcs/channel{self._channel}_{self._stream}.bcs?channel=" \
               f"{self._channel}&stream=0&token={self._token}"

    def get_rtsp_stream_source(self) -> str:
        password = parse.quote(self._password)
        channel = "{:02d}".format(self._channel + 1)
        return f"rtsp://{self._username}:{password}@{self._host}:{self._rtsp_port}/" \
               f"{self._stream_format}Preview_{channel}_{self._stream}"

    async def get_stream_source(self):
        """Return the stream source url."""
        if not await self.login():
            return

        if self.protocol == "rtmp":
            stream_source = self.get_rtmp_stream_source()
        else:
            stream_source = self.get_rtsp_stream_source()

        return stream_source

    async def get_vod_source(self, filename: str):
        """Return the vod source url."""
        if not await self.login():
            return

        """
        REOLink uses an odd encoding, if the camera provides a / in the filename it needs
        to be encoded with %20
        """
        # VoDs are only available over rtmp, rtsp is not an option
        stream_source = f"rtmp://{self._host}:{self._rtmp_port}/vod/{filename.replace('/', '%20')}?" \
                        f"channel={self._channel}&stream=0&token={self._token}"

        return stream_source

    def map_json_response(self, json_data):  # pylint: disable=too-many-branches
        """Map the JSON objects to internal objects and store for later use."""

        for data in json_data:
            try:
                if data["code"] == 1:  # -->Error, like "ability error"
                    continue

                if data["cmd"] == "GetMdState":
                    self._motion_state = data["value"]["state"] == 1

                elif data["cmd"] == "GetAiState":
                    self._ai_state = data["value"]
                    self._is_ia_enabled = True

                elif data["cmd"] == "GetDevInfo":
                    self._device_info = data
                    self._serial = data["value"]["DevInfo"]["serial"]
                    self._name = data["value"]["DevInfo"]["name"]
                    self._sw_version = data["value"]["DevInfo"]["firmVer"]
                    self._model = data["value"]["DevInfo"]["model"]
                    self._channels = data["value"]["DevInfo"]["channelNum"]
                    self._sw_version_object = SoftwareVersion(self._sw_version)
                    self._is_nvr = data["value"]["DevInfo"].get("exactType", "CAM") == "NVR"

                elif data["cmd"] == "GetHddInfo":
                    self._hdd_info = data["value"]["HddInfo"]

                elif data["cmd"] == "GetLocalLink":
                    self._local_link = data
                    self._mac_address = data["value"]["LocalLink"]["mac"]

                elif data["cmd"] == "GetNetPort":
                    self._netport_settings = data
                    self._rtsp_port = data["value"]["NetPort"]["rtspPort"]
                    self._rtmp_port = data["value"]["NetPort"]["rtmpPort"]
                    self._onvifport = data["value"]["NetPort"]["onvifPort"]

                elif data["cmd"] == "GetOsd":
                    self._osd_settings = data
                    self._name = data["value"]["Osd"]["osdChannel"]["name"]

                elif data["cmd"] == "GetUser":
                    self._users = data["value"]["User"]

                elif data["cmd"] == "GetFtp":
                    self._ftp_settings = data
                    self._ftp_state = data["value"]["Ftp"]["schedule"]["enable"] == 1

                elif data["cmd"] == "GetFtpV20":
                    self._ftp_settings = data
                    self._ftp_state = data["value"]["Ftp"]["enable"] == 1

                elif data["cmd"] == "GetPush":
                    self._push_settings = data
                    self._push_state = data["value"]["Push"]["schedule"]["enable"] == 1

                elif data["cmd"] == "GetPushV20":
                    self._push_settings = data
                    self._push_state = data["value"]["Push"]["enable"] == 1

                elif data["cmd"] == "GetEnc":
                    self._enc_settings = data
                    self._audio_state = data["value"]["Enc"]["audio"] == 1

                elif data["cmd"] == "GetEmail":
                    self._email_settings = data
                    self._email_state = (
                        data["value"]["Email"]["schedule"]["enable"] == 1
                    )

                elif data["cmd"] == "GetIsp":
                    self._isp_settings = data
                    self._daynight_state = data["value"]["Isp"]["dayNight"]
                    self._backlight_state = data["value"]["Isp"]["backLight"]

                elif data["cmd"] == "GetIrLights":
                    self._ir_settings = data
                    self._ir_state = data["value"]["IrLights"]["state"] == "Auto"

                elif data["cmd"] == "GetWhiteLed":
                    self._whiteled_settings = data
                    self._whiteled_state = data["value"]["WhiteLed"]["state"]
                    self._whiteled_mode = data["value"]["WhiteLed"]["mode"]

                elif data["cmd"] == "GetRec":
                    self._recording_settings = data
                    self._recording_state = (data["value"]["Rec"]["schedule"]["enable"] == 1)
                elif data["cmd"] == "GetRecV20":
                    self._recording_settings = data
                    self._recording_state = (data["value"]["Rec"]["enable"] == 1)
                elif data["cmd"] == "GetPtzPreset":
                    self._ptz_presets_settings = data
                    for preset in data["value"]["PtzPreset"]:
                        if int(preset["enable"]) == 1:
                            preset_name = preset["name"]
                            preset_id = int(preset["id"])
                            self._ptz_presets[preset_name] = preset_id

                elif data["cmd"] == "GetAlarm":
                    self._alarm_settings = data
                    self._motion_detection_state = data["value"]["Alarm"]["enable"] == 1
                    self._sensitivity_presets = data["value"]["Alarm"]["sens"]

                elif data["cmd"] == "GetAudioAlarm":
                    self._audio_alarm_settings = data
                    self._audio_alarm_state = data["value"]["Audio"]["schedule"]["enable"]

                elif data["cmd"] == "GetAudioAlarmV20":
                    self._audio_alarm_settings = data
                    self._audio_alarm_state = data["value"]["Audio"]["enable"]

                elif data["cmd"] == "GetAbility":
                    for ability in data["value"]["Ability"]["abilityChn"]:
                        self._ptz_support = ability["ptzCtrl"]["permit"] != 0

                    abilities: Dict[str, Any] = data["value"]["Ability"]

                    for ability, details in abilities.items():
                        if ability == 'push':
                            self._api_version_getpush = details['ver']
                        elif ability == 'supportRecordEnable':
                            self._api_version_getrec = details['ver']
                        elif ability == 'scheduleVersion':
                            self._api_version_getalarm = details['ver']
                        elif ability == 'supportFtpEnable':
                            self._api_version_getftp = details['ver']

                elif data["cmd"] == "GetNtp":
                    self._ntp_settings = data

                elif data["cmd"] == "GetTime":
                    self._time_settings = data

                elif data["cmd"] == "GetAutoFocus":
                    self._auto_focus_settings = data

            except Exception as e:  # pylint: disable=bare-except
                _LOGGER.error(traceback.format_exc())
                continue

    async def login(self):
        """Login and store the session ."""
        if self.session_active:
            return True

        _LOGGER.debug(
            "Reolink camera with host %s:%s trying to login with user %s",
            self._host,
            self._port,
            self._username,
        )

        body = [
            {
                "cmd": "Login",
                "action": 0,
                "param": {
                    "User": {
                        "userName": self._username,
                        "password": self._password,
                    }
                },
            }
        ]
        param = {"cmd": "Login", "token": "null"}

        response = await self.send(body, param)
        if response is None:
            return False

        try:
            json_data = json.loads(response)
            _LOGGER.debug("Get response from %s: %s", self._host, json_data)
        except (TypeError, json.JSONDecodeError):
            _LOGGER.debug(
                "Host %s: Error translating login response to json", self._host
            )
            return False

        if json_data is not None:
            if json_data[0]["code"] == 0:
                self._token = json_data[0]["value"]["Token"]["name"]
                lease_time = json_data[0]["value"]["Token"]["leaseTime"]
                self._lease_time = datetime.now() + timedelta(seconds=lease_time)

                _LOGGER.debug(
                    "Reolink camera logged in at IP %s. Leasetime %s, token %s",
                    self._host,
                    self._lease_time.strftime("%d-%m-%Y %H:%M"),
                    self._token,
                )
                return True

        _LOGGER.debug("Failed to login at IP %s.", self._host)
        return False

    async def is_admin(self):
        """Check if the user has admin authorisation."""
        for user in self._users:
            if user["userName"] == self._username:
                if user["level"] == "admin":
                    _LOGGER.debug(
                        "User %s has authorisation level %s",
                        self._username,
                        user["level"],
                    )
                else:
                    _LOGGER.warning(
                        """User %s has authorisation level %s. Only admin users can change
                        camera settings! Switches will not work.""",
                        self._username,
                        user["level"],
                    )

    async def logout(self):
        """Logout from the API."""
        body = [{"cmd": "Logout", "action": 0, "param": {}}]
        param = {"cmd": "Logout"}

        await self.send(body, param)
        self.clear_token()
        await self._aiohttp_session.close()

    async def set_channel(self, channel):
        """Update the channel property."""
        self._channel = channel

    async def set_stream(self, stream):
        """Update the stream property."""
        self._stream = stream

    async def set_protocol(self, protocol):
        """Update the protocol property."""
        self._protocol = protocol

    async def set_stream_format(self, stream_format):
        """Update the stream format property."""
        self._stream_format = stream_format

    async def set_timeout(self, timeout):
        """Update the timeout property."""
        self._timeout = aiohttp.ClientTimeout(total=timeout)

    async def set_time(self, dateFmt=None, hours24=None, tzOffset=None):
        """Set time parameters."""
        """Arguments:"""
        """dateFmt (string) Format of the date in the OSD timestamp"""
        """hours24 (boolean) True selects 24h format, False selects 12h format"""
        """tzoffset (int) Timezone offset versus UTC in seconds"""

        """ Always get current time first """
        ret = await self.get_settings()
        if not ret:
            return ret
        if not self._time_settings:
            _LOGGER.error("Actual time settings not available")
            return False
        body = [{"cmd": "SetTime", "action": 0, "param": self._time_settings["value"]}]

        if dateFmt is not None:
            if dateFmt == 'DD/MM/YYYY' or dateFmt == 'MM/DD/YYYY' or dateFmt == 'YYYY/MM/DD':
                body[0]["param"]["Time"]["timeFmt"] = dateFmt
            else:
                _LOGGER.error("Invalid dateFmt specified")
                return False

        if hours24 is not None:
            if hours24:
                body[0]["param"]["Time"]["hourFmt"] = 0
            else:
                body[0]["param"]["Time"]["hourFmt"] = 1

        if tzOffset is not None:
            if type(tzOffset) is not int:
                _LOGGER.error("Invalid time zone offset specified, type is not int")
                return False
            if tzOffset < -43200 or tzOffset > 50400:
                _LOGGER.error("Invalid time zone offset specified")
                return False
            body[0]["param"]["Time"]["timeZone"] = tzOffset

        return await self.send_setting(body)

    async def set_ntp(self, enable=None, server=None, port=None, interval=None):
        """Set NTP parameters."""
        """Arguments:"""
        """enable (boolean) Enable synchronization"""
        """server (string) Name or IP-Address of time server (or pool)"""
        """port (int) Port number in range of (1..65535)"""
        """interval (int) Interval of synchronization in minutes in range of (60-65535)"""
        if not self._ntp_settings:
            _LOGGER.error("Actual NTP settings not available")
            return False

        body = [{"cmd": "SetNtp", "action": 0, "param": self._ntp_settings["value"]}]

        if enable is not None:
            if enable:
                body[0]["param"]["Ntp"]["enable"] = 1
            else:
                body[0]["param"]["Ntp"]["enable"] = 0

        if server is not None:
            body[0]["param"]["Ntp"]["server"] = server

        if port is not None:
            if type(port) is not int:
                _LOGGER.error("Invalid NTP port specified, type is not int")
                return False
            if port < 1 or port > 65535:
                _LOGGER.error("Invalid NTP port with invalid range specified")
                return False
            body[0]["param"]["Ntp"]["port"] = port

        if interval is not None:
            if type(interval) is not int:
                _LOGGER.error("Invalid NTP interval specified, type is not int")
                return False
            if port < 60 or port > 65535:
                _LOGGER.error("Invalid NTP interval with invalid range specified")
                return False
            body[0]["param"]["Ntp"]["interval"] = interval

        return await self.send_setting(body)

    async def sync_ntp(self):
        """Sync date and time via NTP now."""
        if not self._ntp_settings:
            _LOGGER.error("Actual NTP settings not available")
            return False

        body = [{"cmd": "SetNtp", "action": 0, "param": self._ntp_settings["value"]}]
        body[0]["param"]["Ntp"]["interval"] = 0

        return await self.send_setting(body)

    async def set_autofocus(self, enable: bool):
        """Enable/Disable AutoFocus."""
        """Parameters:"""
        """enable (boolean) enables/disables AutoFocus if supported"""
        if not self._auto_focus_settings:
            _LOGGER.error("AutoFocus not available")
            return False

        if enable:
            new_disable = 0
        else:
            new_disable = 1

        body = [{"cmd": "SetAutoFocus", "action": 0, "param": self._auto_focus_settings["value"]}]
        body[0]["param"]["AutoFocus"]["disable"] = new_disable

        return await self.send_setting(body)

    def validate_osd_pos(self, pos):
        """Helper function for validating an OSD position"""
        """Returns True, if a valid position is specified"""
        return (
            pos == "Upper Left" or pos == "Upper Right"
            or pos == "Top Center" or pos == "Bottom Center"
            or pos == "Lower Left" or pos == "Lower Right"
            )

    async def set_osd(self, namePos=None, datePos=None, enableWaterMark=None):
        """Set OSD parameters."""
        """Parameters:"""
        """namePos (string) specifies the position of the camera name - "Off" disables this OSD"""
        """datePos (string) specifies the position of the date - "Off" disables this OSD"""
        """enableWaterMark (boolean) enables/disables the Logo (WaterMark) if supported"""
        if not self._osd_settings:
            _LOGGER.error("Actual OSD settings not available")
            return False

        body = [{"cmd": "SetOsd", "action": 0, "param": self._osd_settings["value"]}]

        if namePos is not None:
            if "Off" == namePos:
                body[0]["param"]["Osd"]["osdChannel"]["enable"] = 0
            else:
                if not self.validate_osd_pos(namePos):
                    _LOGGER.error("Invalid OSD position specified: namePos = %s", namePos)
                    return False
                body[0]["param"]["Osd"]["osdChannel"]["enable"] = 1
                body[0]["param"]["Osd"]["osdChannel"]["pos"] = namePos

        if datePos is not None:
            if "Off" == datePos:
                body[0]["param"]["Osd"]["osdTime"]["enable"] = 0
            else:
                if not self.validate_osd_pos(datePos):
                    _LOGGER.error("Invalid OSD position specified: datePos = %s", datePos)
                    return False
                body[0]["param"]["Osd"]["osdTime"]["enable"] = 1
                body[0]["param"]["Osd"]["osdTime"]["pos"] = datePos

        if enableWaterMark is not None:
            if "watermark" in  body[0]["param"]["Osd"]:
                if enableWaterMark:
                    body[0]["param"]["Osd"]["watermark"] = 1
                else:
                    body[0]["param"]["Osd"]["watermark"] = 0
            else:
                _LOGGER.debug("Ignoring enableWaterMark. Not supported by this device")

        return await self.send_setting(body)

    async def set_push(self, enable: bool):
        """Set the PUSH (notifications) parameter."""
        if not self._push_settings:
            _LOGGER.error("Actual PUSH settings not available")
            return False

        if enable:
            new_value = 1
        else:
            new_value = 0

        if self._api_version_getpush == 0:
            body = [{"cmd": "SetPush", "action": 0, "param": self._push_settings["value"]}]
            body[0]["param"]["Push"]["schedule"]["enable"] = new_value
        else:
            body = [{"cmd": "SetPushV20", "action": 0, "param": self._push_settings["value"]}]
            body[0]["param"]["Push"]["enable"] = new_value

        return await self.send_setting(body)

    async def set_ftp(self, enable: bool):
        """Set the FTP (notifications) parameter."""
        if not self._ftp_settings:
            _LOGGER.error("Actual FTP settings not available")
            return False

        if enable:
            new_value = 1
        else:
            new_value = 0

        if self._api_version_getftp == 0:
            body = [{"cmd": "SetFtp", "action": 0, "param": self._ftp_settings["value"]}]
            body[0]["param"]["Ftp"]["schedule"]["enable"] = new_value
        else:
            body = [{"cmd": "SetFtpV20", "action": 0, "param": self._ftp_settings["value"]}]
            body[0]["param"]["Ftp"]["enable"] = new_value

        return await self.send_setting(body)

    async def set_audio(self, enable):
        """Set the audio parameter."""
        if not self._enc_settings:
            _LOGGER.error("Actual audio settings not available")
            return False

        if enable:
            new_value = 1
        else:
            new_value = 0

        body = [{"cmd": "SetEnc", "action": 0, "param": self._enc_settings["value"]}]
        body[0]["param"]["Enc"]["audio"] = new_value

        return await self.send_setting(body)

    async def set_email(self, enable):
        """Set the email parameter."""
        if not self._email_settings:
            _LOGGER.error("Actual email settings not available")
            return False

        if enable:
            new_value = 1
        else:
            new_value = 0

        body = [
            {"cmd": "SetEmail", "action": 0, "param": self._email_settings["value"]}
        ]
        body[0]["param"]["Email"]["schedule"]["enable"] = new_value

        return await self.send_setting(body)

    async def set_ir_lights(self, enable):
        """Set the IR lights parameter."""
        if not self._ir_settings:
            _LOGGER.error("Actual IR light settings not available")
            return False

        if enable:
            new_value = "Auto"
        else:
            new_value = "Off"
        body = [
            {"cmd": "SetIrLights", "action": 0, "param": {"IrLights": {"channel": 0, "state": "dummy"}}}
        ]
        body[0]["param"]["IrLights"]["state"] = new_value

        return await self.send_setting(body)

    async def set_whiteled(self, enable, new_bright, new_mode=None):
        """Set the WhiteLed parameter."""
        """ with Reolink Duo GetWhiteLed returns an error state """
        """ SetWhiteLed appears to require 4 parameters """
        """  state - two values 0/1 possibly OFF/ON """
        """  channel - appears to default to 0 """ 
        """  mode - three values I think """
        """    0  Night Mode Off """
        """    1  Night Mode On , AUTO on """
        """    3  Night Mode On, Set Time On """
        """  bright - brigtness level range 0 to 100 """ 
        """                                              """ 
        """   TO BE CONFIRMED """
        """   There may be an extra set of parameters with Duo - dont know with others """
        """   LightingSchedule : { EndHour , EndMin, StartHour,StartMin  }    """
        """                                                                            """
        if not self._whiteled_settings:
            _LOGGER.error("Actual White Led settings not available")
            return False
        if new_mode is None:
            new_mode = 1
        if (
            (new_bright < 0 or new_bright > 100)
            or
            (not (new_mode == 0 or new_mode == 1 or new_mode == 3))
                ):
            _LOGGER.error("Incorrect parameters supplied to SetWhiteLed \n Bright = %s\n Mode = %s",
                                    new_bright, new_mode)
            return False

        if enable:
            new_enable = 1
        else:
            new_enable = 0

        body = [
            {'cmd': 'SetWhiteLed',
                'param': {'WhiteLed':
                              {'state': new_enable, 'channel': 0, 'mode': new_mode, 'bright': new_bright}
                          }
            }
        ]

        _LOGGER.debug(" whiteled body  ", body,await self.send_setting(body))

        if not await self.send_setting(body):
            return False
        else:
            return await self.get_states()


    async def set_spotlight_lighting_schedule(self, endhour =6, endmin =0, starthour =18, startmin=0):
    # stub to handle setting the time period where spotlight (WhiteLed)
    # will be on when NightMode set and AUTO is off
    # time is 24 hour
    #

        if not self._whiteled_settings:
            _LOGGER.error("Actual White Led settings not available")
            return False


        # sensibility checks

        if (endhour < 0 or endhour > 23
                or endmin < 0 or endmin > 59
                or starthour < 0 or starthour > 23
                or startmin < 0  or startmin > 59
                or (endhour == starthour and endmin <= startmin)
                or (not (endhour < 12 and starthour > 16) and (endhour < starthour))
                ):
            _LOGGER.error("Parameter Error in setting Lighting schedule\n"
                          "Start Time %s:%s\nEndTime %s:%s",
                          starthour,startmin,endhour,endmin)
            return False

        body = [
            {"cmd": "SetWhiteLed",
             "param": {
                 "WhiteLed": {
                     "LightingSchedule": {
                         "EndHour": endhour, "EndMin": endmin, "StartHour": starthour, "StartMin": startmin},"channel": 0, "mode": 3
                 }
             }
             }
        ]

        if not await self.send_setting(body):
            return False
        else:
            # update the state of the spotlight
            return await self.get_states()

    async def set_spotlight(self, enable):
        # simply calls set_whiteled with brightness 100, mode 3
        # after setting lightning schedule to on all the time 0000 to 2359

        if enable:
            if not await self.set_spotlight_lighting_schedule(23, 59, 0, 0):
                return False
            return await self.set_whiteled(enable, 100, 3)
        else:
            return await self.set_whiteled(enable, 100, 1)

    async def set_audio_alarm(self,enable, *args):
        # fairly basic only either turns it off or on
        # called in its simple form by set_siren
        # future version might have more parameters related to MD, AI etc
        # this information will be passed in *args or should it be a **kwargs??

        if not self._audio_alarm_settings:
            _LOGGER.error("Actual AudioAlarm settings not available")
            return False

        if enable:
            on_off = 1
        else:
            on_off = 0

        if self._api_version_getalarm == 0:
            body = [
                {'cmd': 'SetAudioAlarm',
                 'param': {"Audio":
                               {"schedule": {"enable": on_off}}
                           }
                 }
            ]
        else:
            body = [
                {'cmd': 'SetAudioAlarmV20',
                 'param': {"Audio":
                               {"enable": on_off, "channel": 0}
                           }
                 }
            ]

        _LOGGER.debug(" audio_alarm body  ", body, await self.send_setting(body))
        if not await self.send_setting(body):
            return False
        else:
            return self.get_settings()

    async def set_siren(self,enable):
        # Uses API AudioAlarmPlay with manual switch
        # uncertain if there may be a glitch - dont know if there is API I have yet to find
        # which sets AudioLevel
        if enable:
            man_switch = 1
        else:
            man_switch = 0

        # this is overkill but to get state set right necessary to call set_audio_alarm

        if not await self.set_audio_alarm(enable):
            return False

        body = [
            {'cmd': 'AudioAlarmPlay',
              'action': 0,
             'param': {
                 "alarm_mode": 'manul',
                 'manual_switch': man_switch,
                 'times': 2,
                 "channel": 0
                       }
             }
        ]

        if not await self.send_setting(body):
            return False
        else:
            return self.get_settings()

    async def set_daynight(self, value):
        """Set the daynight parameter."""
        if not self._isp_settings:
            _LOGGER.error("Actual ISP settings not available")
            return False

        if value not in ["Auto", "Color", "Black&White"]:
            _LOGGER.error("Invalid input: %s", value)
            return False

        new_value = value

        body = [{"cmd": "SetIsp", "action": 0, "param": self._isp_settings["value"]}]
        body[0]["param"]["Isp"]["dayNight"] = new_value

        return await self.send_setting(body)

    async def set_backlight(self, value):
        """Set the backlight parameter."""
        if not self._isp_settings:
            _LOGGER.error("Actual ISP settings not available")
            return False

        if value not in ["BackLightControl", "DynamicRangeControl", "Off"]:
            _LOGGER.error("Invalid input: %s", value)
            return False

        new_value = value

        body = [{"cmd": "SetIsp", "action": 0, "param": self._isp_settings["value"]}]
        body[0]["param"]["Isp"]["backLight"] = new_value

        return await self.send_setting(body)

    async def set_recording(self, enable):
        """Set the recording parameter."""
        if not self._recording_settings:
            _LOGGER.error("Actual recording settings not available")
            return False

        if enable:
            new_value = 1
        else:
            new_value = 0

        if self._api_version_getrec == 0:
            body = [
                {"cmd": "SetRec", "action": 0, "param": self._recording_settings["value"]}
            ]
            body[0]["param"]["Rec"]["schedule"]["enable"] = new_value

        else:
            body = [
                {"cmd": "SetRecV20", "action": 0, "param": self._recording_settings["value"]}
            ]
            body[0]["param"]["Rec"]["enable"] = new_value

        return await self.send_setting(body)

    async def set_motion_detection(self, enable):
        """Set the motion detection parameter."""
        if not self._alarm_settings:
            _LOGGER.error("Actual alarm settings not available")
            return False

        if enable:
            new_value = 1
        else:
            new_value = 0

        body = [
            {
                "cmd": "SetAlarm",
                "action": 0,
                "param": self._alarm_settings["value"],
            }
        ]
        body[0]["param"]["Alarm"]["enable"] = new_value
        return await self.send_setting(body)

    async def set_sensitivity(self, value: int, preset=None):
        """Set motion detection sensitivity.
        Here the camera web and windows application
        show a completely different value than set.
        So the calculation 51-value makes the "real"
        value.
        """
        if not self._alarm_settings:
            _LOGGER.error("Actual alarm settings not available")
            return False

        body = [
            {
                "cmd": "SetAlarm",
                "action": 1,
                "param": {
                    "Alarm": {
                        "channel": 0,
                        "type": "md",
                        "sens": self._alarm_settings["value"]["Alarm"]["sens"],
                    }
                },
            }
        ]
        for setting in body[0]["param"]["Alarm"]["sens"]:
            if preset is None or preset == setting["id"]:
                setting["sensitivity"] = int(51 - value)

        return await self.send_setting(body)

    async def set_ptz_command(self, command, preset=None, speed=None):
        """Send PTZ command to the camera.

        List of possible commands
        --------------------------
        Command     Speed   Preset
        --------------------------
        Right       X
        RightUp     X
        RightDown   X
        Left        X
        LeftUp      X
        LeftDown    X
        Up          X
        Down        X
        ZoomInc     X
        ZoomDec     X
        FocusInc    X
        FocusDec    X
        ToPos       X       X
        Auto
        Stop
        """

        body = [
            {
                "cmd": "PtzCtrl",
                "action": 0,
                "param": {"channel": self._channel, "op": command},
            }
        ]

        if speed:
            body[0]["param"]["speed"] = speed
        if preset:
            body[0]["param"]["id"] = preset
        return await self.send_setting(body)

    async def send_search(
        self, start: datetime, end: datetime, only_status: bool = False
    ) -> Tuple[List[typings.SearchStatus], Optional[List[typings.SearchFile]]]:
        """Send search command."""
        body = [
            {
                "cmd": "Search",
                "action": 0,
                "param": {
                    "Search": {
                        "channel": self._channel,
                        "onlyStatus": 0 if not only_status else 1,
                        "streamType": self._stream,
                        "StartTime": {
                            "year": start.year,
                            "mon": start.month,
                            "day": start.day,
                            "hour": start.hour,
                            "min": start.minute,
                            "sec": start.second,
                        },
                        "EndTime": {
                            "year": end.year,
                            "mon": end.month,
                            "day": end.day,
                            "hour": end.hour,
                            "min": end.minute,
                            "sec": end.second,
                        },
                    }
                },
            }
        ]

        command = body[0]["cmd"]
        _LOGGER.debug(
            "Sending command: %s to: %s with body: %s", command, self._host, body
        )
        response = await self.send(body, {"cmd": command})
        if response is None:
            return None, None

        try:
            json_data = json.loads(response)
        except (TypeError, json.JSONDecodeError):
            _LOGGER.debug(
                "Host %s: Error translating %s response to json", self._host, command
            )
            return None, None
        except KeyError as key_error:
            _LOGGER.debug(
                "Host %s: Received an unexpected response while sending command: %s, %s",
                self._host,
                command,
                key_error,
            )
            return None, None

        if json_data is not None:
            if json_data[0]["code"] == 0:
                search_result = json_data[0]["value"]["SearchResult"]
                if only_status or "File" not in search_result:
                    if "Status" in search_result:
                        return search_result["Status"], None
                else:
                    return search_result["Status"], search_result["File"]

        _LOGGER.warning("Host: %s: Failed to get results for %s, JSON data was was empty?", self._host, command)
        return None, None

    async def send_setting(self, body):
        """Send a setting."""
        command = body[0]["cmd"]
        _LOGGER.debug(
            "Sending command: %s to: %s with body: %s", command, self._host, body
        )
        response = await self.send(body, {"cmd": command})
        if response is None:
            return False

        try:
            json_data = json.loads(response)
            _LOGGER.debug("Response from %s: %s", self._host, json_data)

            if json_data[0]["value"]["rspCode"] == 200:
                getcmd = command.replace("Set", "Get")
                await self.get_states(cmd_list=[getcmd])
                return True

            return False
        except (TypeError, json.JSONDecodeError):
            _LOGGER.debug(
                "Host %s: Error translating %s response to json", self._host, command
            )
            return False
        except KeyError:
            _LOGGER.debug(
                "Host %s: Received an unexpected response while sending command: %s",
                self._host,
                command,
            )
            return False

    def is_nvr(self):
        return self._is_nvr

    async def send(self, body, param=None, expected_content_type: Optional[str] = None):
        """Generic send method."""

        if self._aiohttp_session.closed:
            self._aiohttp_session = aiohttp.ClientSession(timeout=self._timeout,
                                                            connector=aiohttp.TCPConnector(ssl=False))

        if body is None or (body[0]["cmd"] != "Login" and body[0]["cmd"] != "Logout"):
            if not await self.login():
                return False

        if not param:
            param = {}
        if self._token is not None:
            param["token"] = self._token

        try:
            if body is None:
                async with self._aiohttp_session.get(url=self._url, params=param, allow_redirects=False) as response:
                    _LOGGER.debug("send() HTTP Request params =%s", str(param).replace(self._password, "<password>"))
                    json_data = await response.read()
                    _LOGGER.debug("send() HTTP Response status=%s content-type=(%s)",
                                  response.status, response.content_type)

                    if param.get("cmd") == "Snap":
                        _LOGGER_DATA.debug("send() HTTP Response data scrapped because it's too large")
                    else:
                        _LOGGER_DATA.debug("send() HTTP Response data: %s", json_data)

                    if len(json_data) < 500 and response.content_type == 'text/html':
                        if b'"detail" : "invalid user"' in json_data or \
                                b'"detail" : "login failed"' in json_data \
                                or b'detail" : "please login first' in json_data:
                            self.clear_token()
                            raise CredentialsInvalidError()

                    if expected_content_type is not None and response.content_type != expected_content_type:
                        raise InvalidContentTypeError("expected '{}' but received '{}'".format(expected_content_type,
                                                                                               response.content_type))

                    return json_data
            else:
                async with self._aiohttp_session.post(
                        url=self._url, json=body, params=param, allow_redirects=False
                ) as response:
                    _LOGGER.debug("send() HTTP Request params =%s", str(param).replace(self._password, "<password>"))
                    _LOGGER.debug("send() HTTP Request body =%s", str(body).replace(self._password, "<password>"))
                    json_data = await response.text()
                    _LOGGER.debug("send() HTTP Response status=%s content-type=(%s)",
                                  response.status, response.content_type)
                    if param.get("cmd") == "Search" and len(json_data) > 500:
                        _LOGGER_DATA.debug("send() HTTP Response data scrapped because it's too large")
                    else:
                        _LOGGER_DATA.debug("send() HTTP Response data: %s", json_data)

                    if len(json_data) < 500 and response.content_type == 'text/html':
                        if 'detail" : "invalid user' in json_data or 'detail" : "login failed' in json_data \
                                or 'detail" : "please login first' in json_data:
                            self.clear_token()
                            raise CredentialsInvalidError()

                    return json_data

        except aiohttp.ClientConnectorError as conn_err:
            _LOGGER.debug("Host %s: Connection error %s", self._host, str(conn_err))
            raise
        except asyncio.TimeoutError:
            _LOGGER.debug(
                "Host %s: connection timeout exception. Please check the connection to this camera.",
                self._host,
            )
            raise
        except Exception as e:  # pylint: disable=bare-except
            _LOGGER.debug("Host %s: Unknown exception occurred: %s", self._host, traceback.format_exc())
            raise
        return
