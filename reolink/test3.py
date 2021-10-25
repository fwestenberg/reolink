from reolink.camera_api import Api
from reolink.subscription_manager import Manager
import asyncio
import os
import time
import logging
import aiohttp

logging.basicConfig(level=logging.DEBUG)
logging.getLogger('chardet.charsetprober').setLevel(logging.DEBUG)



async def do_test():
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
        async with session.get("https://192.168.0.47/cgi-bin/api.cgi",
                                params={"cmd": "Snap", "user": "admin", "password": "ikolpm74"}, allow_redirects=False) as response:
            print("req status={} / len:{}".format(response.status, response.content_length))
            json_data = await response.read()
            if len(json_data) < 500 and response.content_type == 'text/html':
                if b'"detail" : "invalid user"' in json_data or b'"detail" : "login failed"' in json_data:
                    raise Exception("help")
            #print(text)


loop = asyncio.get_event_loop()
loop.run_until_complete(do_test())