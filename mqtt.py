import machine
import time
import uasyncio as asyncio
import ubinascii as binascii
from mqtt_as import MQTTClient, config
from phew import ntp
from credentials import Creds

TEST_TOPIC = 'first-test'
MQTT_TOPIC = 'friends/amelia'
MQTT_USERNAME = b'friends'
MQTT_PASSWORD = b'Fr13nds.'
MQTT_BROKER = b'799fc682e5d548da9335ee48f79b2986.s2.eu.hivemq.cloud'

creds = Creds()
creds.load()

# Define configuration
config['ssid'] = creds.ssid
config['wifi_pw'] = creds.password
config['will'] = (TEST_TOPIC, 'Goodbye cruel world!', False, 0)
config["queue_len"] = 1  # Use event interface with default queue
config['server'] = MQTT_BROKER
config['user'] = MQTT_USERNAME
config['password'] = MQTT_PASSWORD
config['port'] = 8883
config['keepalive'] = 60
config['ssl'] = True
config['ssl_params'] = {'server_side': False, 'server_hostname': MQTT_BROKER}

# Set up client. Enable optional debug statements.
MQTTClient.DEBUG = False
client = MQTTClient(config)
_handle_message = None
outages = 0
mac = ''

async def messages(client):  # Respond to incoming messages
    async for topic, msg, retained in client.queue:
        if _handle_message:
            _handle_message(topic, msg, retained)
        else:
            print((topic, msg, retained))

async def up(client):  # Respond to connectivity being (re)established
    global mac
    while True:
        await client.up.wait()  # Wait on an Event
        client.up.clear()
        mac = binascii.hexlify(client._sta_if.config('mac'),':').decode()
        ntp.fetch() # get the current time from NTP
        await client.subscribe(MQTT_TOPIC, 1)  # renew subscriptions
        await client.subscribe(TEST_TOPIC, 1)  # renew subscriptions
        
async def down(client):
    global outages
    while True:
        await client.down.wait()  # Pause until connectivity changes
        client.down.clear()
        outages += 1
        print('WiFi or broker is down.')
        
async def init(message_handler):
    global _handle_message
    _handle_message = message_handler

    try:
        if not creds.is_valid():
            return None
        
        await client.connect()
        if not client.isconnected():
            return None
        
        for task in (up, down, messages):
            asyncio.create_task(task(client))
        return client
    
    except OSError:
        print("client is None")
        return None
