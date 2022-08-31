Reolink Python package
======================

### Description

This is a package implementing the Reolink IP camera API. Also it’s providing a way to subscribe to Reolink events, so real-time events can be received on a webhook.

### Prerequisites

- python3

### Installation

````
git clone https://github.com/fwestenberg/reolink
cd reolink/
pip3 install .
````

### Usage

````
api = camera_api.Api('192.168.1.10', 80, 'user', 'mypassword')

# get settings, like ports etc.:
await api.get_settings()

# Store the subscribe port
subscribe_port =  api.onvif_port

# get the states:
await api.get_states()

# print some state value:
print(api.ir_state)

# enable the infrared lights:
await api.set_ir_lights(True)

# enable the spotlight:
await api.set_spotlight(True)

# enable the siron:
await api.set_sirenTrue)

# logout
await api.logout()

# Now subscribe to events, suppose our webhook url is http://192.168.1.11/webhook123

sman = subscription_manager.Manager('192.168.1.10', subscribePort, ' user', 'mypassword')
await sman.subscribe('http://192.168.1.11/webhook123')

# After some minutes check the renew timer (keep the eventing alive):
if (sman.renewTimer <= 100):
    await sman.renew()

# Unsubscribe
await sman.unsubscribe()
````

### Example

This is an example of the usage of the API. In this case we want to retrive and print the Mac Address of the NVR.
````
from reolink.camera_api import Api
import asyncio

async def print_mac_address():
    # initialize the api
    api = Api('192.168.1.109', 80, 'admin', 'admin1234')
    # get settings
    await api.get_settings()
    # print mac address
    print(api._mac_address)
    # close the api
    await api.logout()

if __name__ == "__main__":
    asyncio.run(print_mac_address())
````
