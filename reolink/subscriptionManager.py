"""
Reolink Camera subscription
"""
import re
import logging
import aiohttp
import hashlib
import base64
from datetime import datetime, timedelta
import uuid
from . import templates

TERMINATION_TIME = 15

_LOGGER = logging.getLogger(__name__)


class manager(object):
    def __init__(self, host, port, username, password):
        self._host = host
        self._username = username
        self._password = password
        self._subscribe_url = f"http://{host}:{port}"
        self._manager_url = None
        self._terminationTime = None
        self._timeDifference = None

    @property
    def renewTimer(self):
        if self._timeDifference is None or self._terminationTime is None:
            return 0

        remoteTime = datetime.utcnow()
        remoteTime += timedelta(seconds=self._timeDifference)

        diff = self._terminationTime - remoteTime
        _LOGGER.debug(f"Host {self._host} should renew in: {diff.seconds} seconds...")

        return diff.seconds

    async def convertTime(self, time):
        try:
            return datetime.strptime(time, "%Y-%m-%dT%H:%M:%SZ")
        except:
            return

    async def calcTimeDifference(self, localTime, remoteTime):
        return remoteTime.timestamp() - localTime.timestamp()

    async def getDigest(self):
        created = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000Z")

        raw_nonce = uuid.uuid4().bytes
        nonce = base64.b64encode(raw_nonce)

        sha1 = hashlib.sha1()
        sha1.update(raw_nonce + created.encode("utf8") + self._password.encode("utf8"))
        raw_digest = sha1.digest()
        digest_pwd = base64.b64encode(raw_digest)

        return {
            "UsernameToken": str(uuid.uuid4()),
            "Username": self._username,
            "PasswordDigest": digest_pwd.decode("utf8"),
            "Nonce": nonce.decode("utf8"),
            "Created": created,
        }

    async def send(self, headers, data):
        timeout = aiohttp.ClientTimeout(total=10)

        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    url=self._subscribe_url, data=data, headers=headers
                ) as response:
                    response_xml = await response.text()

                    _LOGGER.debug(
                        f"Reolink host {self._host} got response status: {response.status}. Payload: {response_xml}"
                    )
                    if response.status == 200:
                        return response_xml
                    else:
                        return None

        except aiohttp.client_exceptions.ServerDisconnectedError:
            return None
        except aiohttp.client_exceptions.ClientConnectorError:
            return None

    async def extract_value(self, data, element):
        matches = re.findall(rf"{element}>(.+?)<", data)
        if not (len(matches)):
            return

        return matches[0]

    async def subscribe(self, webhook_url):
        headers = templates.HEADERS
        headers.update(templates.SUBSCRIBE_ACTION)
        template = templates.SUBSCRIBE_XML

        parameters = {
            "Address": webhook_url,
            "InitialTerminationTime": f"PT{TERMINATION_TIME}M",
        }

        parameters.update(await self.getDigest())
        localTime = datetime.utcnow()

        xml = template.format(**parameters)

        response = await self.send(headers, xml)
        if response is None:
            return False

        self._manager_url = await self.extract_value(response, "Address")

        currentTime = await self.extract_value(response, "CurrentTime")
        remoteTime = await self.convertTime(currentTime)

        terminationTime = await self.extract_value(response, "TerminationTime")
        self._terminationTime = await self.convertTime(terminationTime)

        if (
            self._manager_url is None
            or remoteTime is None
            or self._terminationTime is None
        ):
            _LOGGER.error(
                f"Host: {self._host} failed to subscribe. Required response parameters not available."
            )
            return False

        self._timeDifference = await self.calcTimeDifference(localTime, remoteTime)

        _LOGGER.debug(
            f"Local time: {localTime:%Y-%m-%d %H:%M}, camera time: {remoteTime:%Y-%m-%d %H:%M} (difference: {self._timeDifference}), termination time: {self._terminationTime:%Y-%m-%d %H:%M:%S}"
        )

        return True

    async def renew(self):
        headers = templates.HEADERS
        headers.update(templates.RENEW_ACTION)
        template = templates.RENEW_XML

        parameters = {
            "To": self._manager_url,
            "TerminationTime": f"PT{TERMINATION_TIME}M",
        }

        parameters.update(await self.getDigest())
        localTime = datetime.utcnow()

        xml = template.format(**parameters)

        response = await self.send(headers, xml)
        if response is None:
            await self.unsubscribe()
            return False

        currentTime = await self.extract_value(response, "CurrentTime")
        remoteTime = await self.convertTime(currentTime)

        if remoteTime is None:
            _LOGGER.error(
                f"Host: {self._host} failed to renew subscription. Required response parameters not available."
            )
            await self.unsubscribe()
            return False

        self._timeDifference = await self.calcTimeDifference(localTime, remoteTime)

        """ 
        The Reolink renew function has a bug, so it always returns the initial Termination Time. 
        By adding the duration to this parameter, the new termination time can be calculated.
        
        So this will not work now:
            terminationTime = await self.extract_value(response, 'TerminationTime')
            self._terminationTime = await self.convertTime(terminationTime)
        """

        self._terminationTime += timedelta(minutes=TERMINATION_TIME)

        _LOGGER.debug(
            f"Local time: {localTime:%Y-%m-%d %H:%M}, camera time: {remoteTime:%Y-%m-%d %H:%M} (difference: {self._timeDifference}), termination time: {self._terminationTime:%Y-%m-%d %H:%M:%S}"
        )

        return True

    async def unsubscribe(self):
        headers = templates.HEADERS
        headers.update(templates.UNSUBSCRIBE_ACTION)
        template = templates.UNSUBSCRIBE_XML

        parameters = {"To": self._manager_url}
        parameters.update(await self.getDigest())

        xml = template.format(**parameters)

        response = await self.send(headers, xml)
        if response is None:
            return False

        self._terminationTime = None
        self._timeDifference = 0
        self._manager_url = None
        return True
