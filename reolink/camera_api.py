"""
Reolink Camera API
"""
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from . import typings
from .software_version import SoftwareVersion
import traceback

import asyncio
import aiohttp
import urllib.parse as parse

MANUFACTURER = "Reolink"
DEFAULT_STREAM = "main"
DEFAULT_PROTOCOL = "rtmp"
DEFAULT_CHANNEL = 0
DEFAULT_TIMEOUT = 30
DEFAULT_STREAM_FORMAT = "h264"
DEFAULT_RTMP_AUTH_METHOD = 'PASSWORD'

_LOGGER = logging.getLogger(__name__)
_LOGGER_DATA = logging.getLogger(__name__+".data")


ref_sw_version_3_0_0_0_0 = SoftwareVersion("v3.0.0.0_0")


class Api:  # pylint: disable=too-many-instance-attributes disable=too-many-public-methods
    """Reolink API class."""

    def __init__(
        self,
        host,
        port,
        username,
        password,
        channel=DEFAULT_CHANNEL,
        protocol=DEFAULT_PROTOCOL,
        stream=DEFAULT_STREAM,
        timeout=DEFAULT_TIMEOUT,
        stream_format=DEFAULT_STREAM_FORMAT,
        rtmp_auth_method=DEFAULT_RTMP_AUTH_METHOD,
    ):
        """Initialize the API class."""
        self._url = f"http://{host}:{port}/cgi-bin/api.cgi"
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
        self._daynight_state = None
        self._backlight_state = None
        self._recording_state = None
        self._audio_state = None
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

        self._isp_settings = None
        self._ftp_settings = None
        self._push_settings = None
        self._enc_settings = None
        self._ptz_presets_settings = None
        self._ability_settings = None
        self._netport_settings = None
        self._email_settings = None
        self._ir_settings = None
        self._recording_settings = None
        self._alarm_settings = None

        self._users = None
        self._local_link = None
        self._ptz_support = False

    @property
    def host(self):
        """Return the host."""
        return self._host

    @property
    def port(self):
        """Return the port."""
        return self._port

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

    async def clear_token(self):
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
            {"cmd": "GetRec", "action": 1, "param": {"channel": self._channel}},
            {"cmd": "GetPtzPreset", "action": 1, "param": {"channel": self._channel}},
            {"cmd": "GetHddInfo", "action": 1, "param": {}},
            {
                "cmd": "GetAlarm",
                "action": 1,
                "param": {"Alarm": {"channel": self._channel, "type": "md"}},
            },
            {"cmd": "GetPushV20", "action": 1, "param": {"channel": self._channel}},
            {"cmd": "GetPush", "action": 1, "param": {"channel": self._channel}},
        ]

        if cmd_list is not None:
            for x, line in enumerate(body):
                if line["cmd"] not in cmd_list:
                    body.pop(x)

        response = await self.send(body)
        if response is None:
            return False

        try:
            json_data = json.loads(response)
            await self.map_json_response(json_data)
            return True
        except (TypeError, json.JSONDecodeError):
            _LOGGER.debug(
                "Host: %s: Error translating Reolink state response", self._host
            )
            await self.clear_token()
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
        ]

        response = await self.send(body)
        if response is None:
            return False

        try:
            json_data = json.loads(response)
            await self.map_json_response(json_data)
            return True
        except (TypeError, json.JSONDecodeError):
            _LOGGER.debug(
                "Host %s: Error translating Reolink settings response", self._host
            )
            await self.clear_token()
            return False

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

            await self.map_json_response(json_data)
        except (TypeError, json.JSONDecodeError):
            await self.clear_token()
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

            await self.map_json_response(json_data)
        except (TypeError, json.JSONDecodeError):
            await self.clear_token()

        return self._ai_state

    async def get_still_image(self):
        """Get the still image."""
        param = {"cmd": "Snap", "channel": self._channel}

        response = await self.send(None, param)
        if response is None or response == b"":
            return

        return response

    async def get_snapshot(self):
        """Get a snapshot."""
        return await self.get_still_image()

    async def get_stream_source(self):
        """Return the stream source url."""
        if not await self.login():
            return

        if self.protocol == DEFAULT_PROTOCOL:
            if self._rtmp_auth_method == DEFAULT_RTMP_AUTH_METHOD:
                stream_source = f"rtmp://{self._host}:{self._rtmp_port}/bcs/channel{self._channel}_{self._stream}.bcs?channel={self._channel}&stream=0&user={self._username}&password={self._password}"
            else:
                stream_source = f"rtmp://{self._host}:{self._rtmp_port}/bcs/channel{self._channel}_{self._stream}.bcs?channel={self._channel}&stream=0&token={self._token}"
        else:
            password = parse.quote(self._password)
            channel = "{:02d}".format(self._channel + 1)
            stream_source = f"rtsp://{self._username}:{password}@{self._host}:{self._rtsp_port}/{self._stream_format}Preview_{channel}_{self._stream}"

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
        stream_source = f"rtmp://{self._host}:{self._rtmp_port}/vod/{filename.replace('/', '%20')}?channel={self._channel}&stream=0&token={self._token}"

        return stream_source

    async def map_json_response(self, json_data):  # pylint: disable=too-many-branches
        """Map the JSON objects to internal objects and store for later use."""

        push_data = None
        pushv20_data = None

        for data in json_data:
            try:
                if data["code"] == 1:  # -->Error, like "ability error"
                    continue

                if data["cmd"] == "GetMdState":
                    self._motion_state = json_data[0]["value"]["state"] == 1

                elif data["cmd"] == "GetAiState":
                    self._ai_state = json_data[0]["value"]

                elif data["cmd"] == "GetDevInfo":
                    self._device_info = data
                    self._serial = data["value"]["DevInfo"]["serial"]
                    self._name = data["value"]["DevInfo"]["name"]
                    self._sw_version = data["value"]["DevInfo"]["firmVer"]
                    self._model = data["value"]["DevInfo"]["model"]
                    self._channels = data["value"]["DevInfo"]["channelNum"]
                    self._sw_version_object = SoftwareVersion(self._sw_version)

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

                elif data["cmd"] == "GetPush":
                    push_data = data

                elif data["cmd"] == "GetPushV20":
                    pushv20_data = data

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

                elif data["cmd"] == "GetRec":
                    self._recording_settings = data
                    self._recording_state = (
                        data["value"]["Rec"]["schedule"]["enable"] == 1
                    )

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

                elif data["cmd"] == "GetAbility":
                    for ability in data["value"]["Ability"]["abilityChn"]:
                        self._ptz_support = ability["ptzCtrl"]["permit"] != 0

            except:  # pylint: disable=bare-except
                _LOGGER.error(traceback.format_exc())
                continue

        if pushv20_data is not None:
            self._push_settings = pushv20_data
            self._push_state = pushv20_data["value"]["Push"]["enable"] == 1
        elif push_data is not None:
            self._push_settings = push_data
            self._push_state = push_data["value"]["Push"]["schedule"]["enable"] == 1

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
        await self.clear_token()

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

    async def set_ftp(self, enable):
        """Set the FTP parameter."""
        if not self._ftp_settings:
            _LOGGER.error("Actual FTP settings not available")
            return False

        if enable:
            new_value = 1
        else:
            new_value = 0

        body = [{"cmd": "SetFtp", "action": 0, "param": self._ftp_settings["value"]}]
        body[0]["param"]["Ftp"]["schedule"]["enable"] = new_value

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

        if self._sw_version_object is not None and self._sw_version_object > ref_sw_version_3_0_0_0_0:
            body = [{"cmd": "SetPushV20", "action": 0, "param": self._push_settings["value"]}]
            body[0]["param"]["Push"]["enable"] = new_value
        else:
            body = [{"cmd": "SetPush", "action": 0, "param": self._push_settings["value"]}]
            body[0]["param"]["Push"]["schedule"]["enable"] = new_value

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
            {"cmd": "SetIrLights", "action": 0, "param": self._ir_settings["value"]}
        ]
        body[0]["param"]["IrLights"]["state"] = new_value

        return await self.send_setting(body)

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

        body = [
            {"cmd": "SetRec", "action": 0, "param": self._recording_settings["value"]}
        ]
        body[0]["param"]["Rec"]["schedule"]["enable"] = new_value

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
            _LOGGER.debug("Response from %s: %s", self._host, json_data)
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
                    return search_result["Status"], None

                return search_result["Status"], search_result["File"]

        _LOGGER.debug("Host: %s: Failed to get results for %s", self._host, command)
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

    async def send(self, body, param=None):
        """Generic send method."""
        if body is None or (body[0]["cmd"] != "Login" and body[0]["cmd"] != "Logout"):
            if not await self.login():
                return False

        if not param:
            param = {}
        if self._token is not None:
            param["token"] = self._token

        try:
            if body is None:
                async with aiohttp.ClientSession(timeout=self._timeout) as session:
                    async with session.get(url=self._url, params=param) as response:
                        _LOGGER.debug("send()= HTTP Request params =%s", str(param).replace(self._password, "<password>"))
                        json_data = await response.read()
                        _LOGGER.debug("send HTTP Response status=%s", str(response.status))
                        _LOGGER_DATA.debug("send() HTTP Response data: %s", str(json_data))

                        return json_data
            else:
                async with aiohttp.ClientSession(timeout=self._timeout) as session:
                    async with session.post(
                        url=self._url, json=body, params=param
                    ) as response:
                        _LOGGER.debug("send() HTTP Request params =%s", str(param).replace(self._password, "<password>"))
                        _LOGGER.debug("send() HTTP Request body =%s", str(body).replace(self._password, "<password>"))
                        json_data = await response.text()
                        _LOGGER.debug("send() HTTP Response status=%s", str(response.status))
                        _LOGGER_DATA.debug("send() HTTP Response data: %s", str(json_data))
                        return json_data

        except aiohttp.ClientConnectorError as conn_err:
            _LOGGER.debug("Host %s: Connection error %s", self._host, str(conn_err))
        except asyncio.TimeoutError:
            _LOGGER.debug(
                "Host %s: connection timeout exception. Please check the connection to this camera.",
                self._host,
            )
        except:  # pylint: disable=bare-except
            _LOGGER.debug("Host %s: Unknown exception occurred.", self._host)
        return
