"""
Reolink Camera API
"""
import json
import logging
from datetime import datetime, timedelta

import requests

import aiohttp

MANUFACTURER = 'Reolink'
DEFAULT_STREAM = "main"
DEFAULT_PROTOCOL = "rtmp"
DEFAULT_CHANNEL = 0

_LOGGER = logging.getLogger(__name__)

class api(object):
    def __init__(self, host, port, username, password):
        self._url = f"http://{host}:{port}/cgi-bin/api.cgi"
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._channel = 0
        self._token = None
        self._leaseTime = None
        self._motion_state = False
        self._last_motion = 0
        self._device_info = None
        self._ftp_state = None
        self._email_state = None
        self._ir_state = None
        self._dayNight_state = None
        self._recording_state = None
        self._audio_state = None
        self._rtspport = None
        self._rtmpport = None
        self._onvifport = None
        self._ptzpresets = dict()
        self._motion_detection_state = None
        self._isp_settings = None
        self._ftp_settings = None
        self._enc_settings = None
        self._ptzpresets_settings = None
        self._users = None
        self._local_link = None
        self._stream = DEFAULT_STREAM
        self._protocol = DEFAULT_PROTOCOL
        self._channel = DEFAULT_CHANNEL

    @property
    def host(self):
        return self._host

    @property
    def port(self):
        return self._port

    @property
    def onvif_port(self):
        return self._onvifport

    @property
    def mac_address(self):
        return self._local_link["value"]["LocalLink"]["mac"]

    @property
    def serial(self):
        return self._device_info["value"]["DevInfo"]["serial"]

    @property
    def name(self):
        return self._device_info["value"]["DevInfo"]["name"]

    @property
    def sw_version(self):
        return self._device_info["value"]["DevInfo"]["firmVer"]

    @property
    def model(self):
        return self._device_info["value"]["DevInfo"]["model"]

    @property
    def manufacturer(self):
        return MANUFACTURER

    @property
    def motion_state(self):
        return self._motion_state

    @property
    def ftp_state(self):
        return self._ftp_state

    @property
    def email_state(self):
        return self._email_state

    @property
    def ir_state(self):
        return self._ir_state

    @property
    def dayNight_state(self):
        return self._dayNight_state

    @property
    def recording_state(self):
        return self._recording_state

    @property
    def audio_state(self):
        return self._audio_state

    @property
    def rtmpport(self):
        return self._rtmpport

    @property
    def rtspport(self):
        return self._rtspport

    @property
    def last_motion(self):
        return self._last_motion

    @property
    def ptzpresets(self):
        return self._ptzpresets

    @property
    def device_info(self):
        return self._device_info

    @property
    def stream(self):
        return self._stream

    @property
    def protocol(self):
        return self._protocol

    @property
    def channel(self):
        return self._channel

    @property
    def motion_detection_state(self):
        """Camera motion detection setting status."""
        return self._motion_detection_state

    @property
    def session_active(self):
        if (self._token is not None 
        and self._leaseTime > datetime.now()):
            return True
        else:
            self._token = None
            self._leaseTime = None
            return False

    async def clear_token(self):
        self._token = None
        self._leaseTime = None
    
    async def get_switchCapabilities(self):
        capabilities = []
        if len(self._ptzpresets) != 0:
            capabilities.append("ptzPresets")

        if self._ftp_state is not None:
            capabilities.append("ftp")

        if self._ir_state is not None:
            capabilities.append("irLights")

        if self._recording_state is not None:
            capabilities.append("recording")   

        if self._motion_detection_state is not None:
            capabilities.append("motionDetection")

        if self._dayNight_state is not None:
            capabilities.append("dayNight")   

        if self._email_state is not None:
            capabilities.append("email")

        if self._audio_state is not None:
            capabilities.append("audio")

        if self._ptzpresets_settings is not None:
            capabilities.append("PTZpresets")

        return capabilities

    async def get_states(self):
        body = [{"cmd": "GetFtp", "action": 1, "param": {"channel": self._channel}},
            {"cmd": "GetEnc", "action": 1, "param": {"channel": self._channel}},
            {"cmd": "GetEmail", "action": 1, "param": {"channel": self._channel}},
            {"cmd": "GetIsp", "action": 1, "param": {"channel": self._channel}},
            {"cmd": "GetIrLights", "action": 1, "param": {"channel": self._channel}},
            {"cmd": "GetRec", "action": 1, "param": {"channel": self._channel}},
            {"cmd": "GetPtzPreset", "action": 1, "param": {"channel": self._channel}},
            {"cmd": "GetAlarm","action":1,"param":{"Alarm":{"channel": self._channel ,"type":"md"}}}]

        response = await self.send(body)

        try:
            json_data = json.loads(response)
            await self.map_json_response(json_data)
            return True
        except:
            _LOGGER.error(f"Error translating Reolink state response")
            await self.clear_token()
            return False

    async def get_settings(self):
        body = [{"cmd": "GetDevInfo", "action":1, "param": {"channel": self._channel}},
            {"cmd": "GetLocalLink", "action": 1, "param": {"channel": self._channel}},
            {"cmd": "GetNetPort", "action": 1, "param": {"channel": self._channel}},
            {"cmd": "GetUser", "action": 1, "param": {"channel": self._channel}}]

        response = await self.send(body)

        try:
            json_data = json.loads(response)
            await self.map_json_response(json_data)
            return True
        except:
            _LOGGER.error(f"Error translating Reolink settings response")
            await self.clear_token()
            return False

    async def get_motion_state(self):
        body = [{"cmd": "GetMdState", "action": 0, "param":{"channel":self._channel}}]

        response = await self.send(body)

        try:
            json_data = json.loads(response)

            if json_data is None:
                _LOGGER.error(f"Unable to get Motion detection state at IP {self._host}")
                self._motion_state = False
                return self._motion_state

            await self.map_json_response(json_data)
        except:
            await self.clear_token()
            self._motion_state = False

        return self._motion_state

    async def get_still_image(self):
        param = {"cmd": "Snap", "channel": self._channel}
        response = await self.send(None, param)
        # response = await self.send(None, f"?cmd=Snap&channel={self._channel}&token={self._token}")
        if response is None:
            return

        return response

    async def get_snapshot(self):
        return await self.get_still_image()

    async def get_stream_source(self):
        if not await self.login():
            return

        if self.protocol == "rtsp":
            stream_source = f"rtsp://{self._host}:{self._rtspport}/h264Preview_{self._channel+1:02d}_{self._stream}&token={self._token}"
        else:
            stream_source = f"rtmp://{self._host}:{self._rtmpport}/bcs/channel{self._channel}_{self._stream}.bcs?channel={self._channel}&stream=0&token={self._token}"
        
        return stream_source

    async def update_streaming_options(self, stream, protocol, channel):
        _LOGGER.error(f"Stream: {stream} Protocol:{protocol} Channel:{channel}")
        self._stream = stream
        self._protocol = protocol
        self._channel = channel

    async def map_json_response(self, json_data):

        for data in json_data:
            try:
                if data["code"] == 1: # -->Error, like "ability error"
                    continue

                if data["cmd"] == "GetDevInfo":
                    self._device_info = data

                if data["cmd"] == "GetLocalLink":
                    self._local_link = data

                elif data["cmd"] == "GetNetPort":
                    self._netport_settings = data
                    self._rtspport = data["value"]["NetPort"]["rtspPort"]
                    self._rtmpport = data["value"]["NetPort"]["rtmpPort"]
                    self._onvifport = data["value"]["NetPort"]["onvifPort"]

                if data["cmd"] == "GetUser":
                    self._users = data["value"]["User"]

                elif data["cmd"] == "GetFtp":
                    self._ftp_settings = data
                    self._ftp_state = (data["value"]["Ftp"]["schedule"]["enable"] == 1)

                elif data["cmd"] == "GetEnc":
                    self._enc_settings = data
                    self._audio_state = (data["value"]["Enc"]["audio"] == 1)

                elif data["cmd"] == "GetEmail":
                    self._email_settings = data
                    self._email_state = (data["value"]["Email"]["schedule"]["enable"] == 1)

                elif data["cmd"] == "GetIsp":
                    self._isp_settings = data
                    self._dayNight_state = (data["value"]["Isp"]["dayNight"] == "Auto")

                elif data["cmd"] == "GetIrLights":
                    self._ir_settings = data
                    self._ir_state = (data["value"]["IrLights"]["state"] == "Auto")

                elif data["cmd"] == "GetRec":
                    self._recording_settings = data
                    self._recording_state = (data["value"]["Rec"]["schedule"]["enable"] == 1)

                elif data["cmd"] == "GetPtzPreset":
                    self._ptzpresets_settings = data
                    for preset in data["value"]["PtzPreset"]:
                        if int(preset["enable"]) == 1:
                            preset_name = preset["name"]
                            preset_id = int(preset["id"])
                            self._ptzpresets[preset_name] = preset_id
                            _LOGGER.debug(f"Got preset {preset_name} with ID {preset_id}")
                        else:
                            _LOGGER.debug(f"Preset is not enabled: {preset}")

                elif data["cmd"] == "GetAlarm":
                    self._motion_detection_settings = data
                    self._motion_detection_state = (data["value"]["Alarm"]["enable"] == 1)

                elif data["cmd"] == "GetMdState":
                    self._motion_state = json_data[0]["value"]["state"] == 1
            except:
                continue

    async def login(self):

        if self.session_active:
            return True

        _LOGGER.info(f"Reolink camera with host {self._host}:{self._port} trying to login with user {self._username}")

        body = [{"cmd": "Login", "action": 0, "param": {"User": {"userName": self._username, "password": self._password}}}]
        param = {"cmd": "Login", "token": "null"}

        response = await self.send(body, param)

        try:
            json_data = json.loads(response)
            _LOGGER.debug(f"Get response from {self._host}: {json_data}")
        except:
            _LOGGER.error(f"Error translating login response to json")
            return False

        if json_data is not None:
            if json_data[0]["code"] == 0:
                self._token = json_data[0]["value"]["Token"]["name"]
                leaseTime = json_data[0]["value"]["Token"]["leaseTime"]
                self._leaseTime = (datetime.now()+timedelta(seconds=leaseTime))

                _LOGGER.info(f"Reolink camera logged in at IP {self._host}. Leasetime {self._leaseTime:%d-%m-%Y %H:%M}, token {self._token}")
                return True
            else:
                _LOGGER.error(f"Failed to login at IP {self._host}. No token available")
                return False
        else:
            _LOGGER.error(f"Failed to login at IP {self._host}. Connection error.")
            return False

    async def isAdmin(self):
        for user in self._users:
            if user['userName'] == self._username:
                if (user['level'] == 'admin'):
                    _LOGGER.info(f"User {self._username} has authorisation level {user['level']}")
                else: 
                    _LOGGER.info(f"User {self._username} has authorisation level {user['level']}. Only admin users can change camera settings! Switches will not work.")

    async def logout(self):
        body = [{"cmd":"Logout","action":0,"param":{}}]
        param = {"cmd": "Logout"}

        await self.send(body, param)

    async def set_ftp(self, enable):
        if not await self.get_states() or not self._ftp_settings:
            _LOGGER.error("Error while fetching current FTP settings")
            return

        if enable == True:
            newValue = 1
        else:
            newValue = 0

        body = [{"cmd":"SetFtp","action":0,"param": self._ftp_settings["value"] }]
        body[0]["param"]["Ftp"]["schedule"]["enable"] = newValue

        return await self.send_setting(body)

    async def set_audio(self, enable):
        if not await self.get_states() or not self._enc_settings:
            _LOGGER.error("Error while fetching current audio settings")
            return

        if enable == True:
            newValue = 1
        else:
            newValue = 0

        body = [{"cmd":"SetEnc","action":0,"param": self._enc_settings["value"] }]
        body[0]["param"]["Enc"]["audio"] = newValue

        return await self.send_setting(body)

    async def set_email(self, enable):
        if not await self.get_states() or not self._email_settings:
            _LOGGER.error("Error while fetching current email settings")
            return

        if enable == True:
            newValue = 1
        else:
            newValue = 0

        body = [{"cmd":"SetEmail","action":0,"param": self._email_settings["value"] }]
        body[0]["param"]["Email"]["schedule"]["enable"] = newValue

        return await self.send_setting(body)

    async def set_ir_lights(self, enable):
        if not await self.get_states() or not self._ir_settings:
            _LOGGER.error("Error while fetching current IR light settings")
            return

        if enable == True:
            newValue = "Auto"
        else:
            newValue = "Off"

        body = [{"cmd":"SetIrLights","action":0,"param": self._ir_settings["value"] }]
        body[0]["param"]["IrLights"]["state"] = newValue

        return await self.send_setting(body)

    async def set_dayNight(self, value):
        if not await self.get_states() or not self._isp_settings:
            _LOGGER.error("Error while fetching current ISP settings")
            return

        if value in [ "Auto", "Color", "Black&White" ]:
            newValue = value

        body = [{"cmd":"SetIsp","action":0,"param": self._ir_settings["value"] }]
        body[0]["param"]["Isp"]["dayNight"] = newValue

        return await self.send_setting(body)

    async def set_recording(self, enable):
        if not await self.get_states() or not self._recording_settings:
            _LOGGER.error("Error while fetching current recording settings")
            return

        if enable == True:
            newValue = 1
        else:
            newValue = 0

        body = [{"cmd":"SetRec","action":0,"param": self._recording_settings["value"] }]
        body[0]["param"]["Rec"]["schedule"]["enable"] = newValue

        return await self.send_setting(body)

    async def set_motion_detection(self, enable):
        if not await self.get_states() or not self._motion_detection_settings:
            _LOGGER.error("Error while fetching current motion detection settings")
            return

        if enable == True:
            newValue = 1
        else:
            newValue = 0

        body = [{"cmd":"SetAlarm","action":0,"param": self._motion_detection_settings["value"] }]
        body[0]["param"]["Alarm"]["enable"] = newValue
        return await self.send_setting(body)

    async def send_setting(self, body):
        command = body[0]["cmd"]
        _LOGGER.debug(f"Sending command: {command} to: {self._host} with body: {body}")
        response = await self.send(body, {"cmd": command})
        try:
            json_data = json.loads(response)
            _LOGGER.debug(f"Get response from {self._host}: {json_data}")

            if json_data[0]["value"]["rspCode"] == 200:
                await self.get_states()
                return True
            else:
                return False
        except:
            _LOGGER.error(f"Error translating {command} response to json")
            return False

    async def send(self, body, param={}):
        if (body is None 
        or (body[0]["cmd"] != "Login" and body[0]["cmd"] != "Logout")):
            if not await self.login():
                return False

        if self._token is not None:
            param["token"]=self._token

        timeout = aiohttp.ClientTimeout(total=10)

        if body is None:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url=self._url, params=param) as response:
                    return await response.read()
        else:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url=self._url, json=body, params=param) as response:
                    json_data = await response.text()
                    return json_data
