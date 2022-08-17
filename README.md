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
