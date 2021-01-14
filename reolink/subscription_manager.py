"""
Reolink Camera subscription
"""
from datetime import datetime, timedelta
import base64
import hashlib
import logging
import re
import uuid

import aiohttp
import asyncio
from . import templates

TERMINATION_TIME = 15
DEFAULT_TIMEOUT = 30

_LOGGER = logging.getLogger(__name__)


class Manager:
    """Initialize the Reolink event class."""
    def __init__(self, host, port, username, password, timeout=DEFAULT_TIMEOUT):
        self._host = host
        self._username = username
        self._password = password[:31]
        self._timeout = aiohttp.ClientTimeout(total=timeout)
        self._subscribe_url = f"http://{host}:{port}/onvif/event_service"
        self._manager_url = None
        self._termination_time = None
        self._time_difference = None

    @property
    def renewtimer(self):
        """Return the renew time in seconds."""
        if self._time_difference is None or self._termination_time is None:
            return 0

        remote_time = datetime.utcnow()
        remote_time += timedelta(seconds=self._time_difference)

        diff = self._termination_time - remote_time
        _LOGGER.debug("Host %s should renew in: %i seconds...",
            self._host, diff.seconds
        )

        return diff.seconds

    async def convert_time(self, time):
        """Convert time object to printable."""
        try:
            return datetime.strptime(time, "%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            return

    async def calc_time_difference(self, local_time, remote_time):
        """Calculate the time difference between local and remote."""
        return remote_time.timestamp() - local_time.timestamp()

    async def get_digest(self):
        """Get the authorisation digest."""
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
        """Send data to the camera."""

        try:
            async with aiohttp.ClientSession(timeout=self._timeout) as session:
                async with session.post(
                    url=self._subscribe_url, data=data, headers=headers
                ) as response:
                    response_xml = await response.text()

                    _LOGGER.debug(
                        "Reolink host %s got response status: %s. Payload: {%s}",
                        self._host, response.status, response_xml
                    )
                    if response.status == 200:
                        return response_xml

                    return

        except aiohttp.ClientConnectorError as conn_err:
            _LOGGER.debug('Host %s: Connection error %s', self._host, str(conn_err))
        except asyncio.TimeoutError:
            _LOGGER.debug('Host %s: connection timeout exception. Please check the connection to this camera.', self._host)
        except: #pylint: disable=bare-except
            _LOGGER.debug('Host %s: Unknown exception occurred.', self._host)
        return

    async def extract_value(self, data, element):
        """Extract a value from the XML file. Most efficient way"""
        matches = re.findall(rf"{element}>(.+?)<", data)
        if not matches:
            return

        return matches[0]

    async def subscribe(self, webhook_url):
        """Subscribe to events."""
        headers = templates.HEADERS
        headers.update(templates.SUBSCRIBE_ACTION)
        template = templates.SUBSCRIBE_XML

        parameters = {
            "Address": webhook_url,
            "InitialTerminationTime": f"PT{TERMINATION_TIME}M",
        }

        parameters.update(await self.get_digest())
        local_time = datetime.utcnow()

        xml = template.format(**parameters)

        response = await self.send(headers, xml)
        if response is None:
            return False

        self._manager_url = await self.extract_value(response, "Address")

        current_time = await self.extract_value(response, "CurrentTime")
        remote_time = await self.convert_time(current_time)

        termination_time = await self.extract_value(response, "TerminationTime")
        self._termination_time = await self.convert_time(termination_time)

        if (
            self._manager_url is None
            or remote_time is None
            or self._termination_time is None
        ):
            _LOGGER.error(
                "Host: %s failed to subscribe. Required response parameters not available.",
                self._host
            )
            return False

        self._time_difference = await self.calc_time_difference(local_time, remote_time)

        _LOGGER.debug(
            "Local time: %s, camera time: %s (difference: %s), termination time: %s",
            local_time.strftime('%Y-%m-%d %H:%M'), remote_time.strftime('%Y-%m-%d %H:%M'),
            self._time_difference, self._termination_time.strftime('%Y-%m-%d %H:%M')
        )

        return True

    async def renew(self):
        """Renew the event subscription.
        The Reolink renew function has a bug, so it always returns the initial Termination Time.
        By adding the duration to this parameter, the new termination time can be calculated.

        So this will not work now:
            terminationTime = await self.extract_value(response, 'TerminationTime')
            self._termination_time = await self.convertTime(terminationTime)
        """
        headers = templates.HEADERS
        headers.update(templates.RENEW_ACTION)
        template = templates.RENEW_XML

        parameters = {
            "To": self._manager_url,
            "TerminationTime": f"PT{TERMINATION_TIME}M",
        }

        parameters.update(await self.get_digest())
        local_time = datetime.utcnow()

        xml = template.format(**parameters)

        response = await self.send(headers, xml)
        if response is None:
            await self.unsubscribe()
            return False

        current_time = await self.extract_value(response, "CurrentTime")
        remote_time = await self.convert_time(current_time)

        if remote_time is None:
            _LOGGER.error(
                "Host: %s failed to renew subscription. Expected response not available.",
                self._host
            )
            await self.unsubscribe()
            return False

        self._time_difference = await self.calc_time_difference(local_time, remote_time)
        self._termination_time += timedelta(minutes=TERMINATION_TIME)

        _LOGGER.debug(
            "Local time: %s, camera time: %s (difference: %s), termination time: %s",
            local_time.strftime('%Y-%m-%d %H:%M'), remote_time.strftime('%Y-%m-%d %H:%M'),
            self._time_difference, self._termination_time.strftime('%Y-%m-%d %H:%M')
        )

        return True

    async def unsubscribe(self):
        """Unsubscribe from events."""
        headers = templates.HEADERS
        headers.update(templates.UNSUBSCRIBE_ACTION)
        template = templates.UNSUBSCRIBE_XML

        parameters = {"To": self._manager_url}
        parameters.update(await self.get_digest())

        xml = template.format(**parameters)

        await self.send(headers, xml)

        self._termination_time = None
        self._time_difference = 0
        self._manager_url = None
        return True
