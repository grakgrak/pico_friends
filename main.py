import captive
import gc
import machine
import mqtt
import time
import uasyncio as asyncio
from button import Button
from reboot_button import RebootButton
from lib.neopixel import Neopixel
from machine import Pin
from lib.mqtt_as import MQTTClient

BRIGHTNESS = 200
FADE_SECONDS = 60

colours = {
    'yellow' : (255, 100, 0),
    'orange' : (255, 50, 0),
    'green' : (0, 255, 0),
    'blue' : (0, 0, 255),
    'red' : (255, 0, 0),
    'magenta' : (220, 0, 220),
    'white' : (255, 255, 255),
}

client: MQTTClient = None  # type: ignore
pixels: Neopixel = None  # type: ignore
button: Button = None  # type: ignore
reboot_button: RebootButton = None  # type: ignore

def message_handler(topic: bytearray, msg: bytearray, retained: int):
    print(topic.decode(), msg.decode())
    if topic == mqtt.MQTT_TOPIC:
        rgb_str = msg.split()[0].decode()
        rgb = tuple(map(int, rgb_str.split(',')))
        button.setRGB(rgb)
    if topic == mqtt.MQTT_TOPIC + '/reset':
        machine.reset()

async def button_check():
    while True:
        await asyncio.sleep_ms(10)
        await button.loop()

async def reboot_button_check():
    while True:
        await asyncio.sleep_ms(10)
        await reboot_button.loop()

async def rotate_pixels():
    while True:
        await asyncio.sleep_ms(100)
        pixels.rotate_left()
        pixels.show()
        
async def flash(colour: str, count: int):
    pixels.brightness(20)
    for i in range(count):
        pixels.fill(colours[colour])
        pixels.show()
        await asyncio.sleep_ms(500)
        pixels.clear()
        pixels.show()
        await asyncio.sleep_ms(500)

def publish_cb(rgb: tuple):
    asyncio.create_task(client.publish(mqtt.MQTT_TOPIC, '{} {} {}'.format(','.join(map(str, rgb)), mqtt.mac, time.time()), qos = 1))

async def main():
    global button
    await flash('green', 3)

    button = Button(pixels, publish_cb)
    for task in [button_check]:
        asyncio.create_task(task())
        
    while True:
        gc.collect()
        print("RAM free {} alloc {}".format(gc.mem_free(), gc.mem_alloc()))
        await asyncio.sleep(60)

try:
    pixels = Neopixel(16, 0, 28, "GRB")
    pixels.set_pixel_line_gradient(0, 15, (255,0,255), (0,255,0), BRIGHTNESS)
    pixels.show()
    t = asyncio.create_task(rotate_pixels())
    
    client = asyncio.run(mqtt.init(message_handler))
    
    t.cancel()
    
    if client and client.isconnected():
        asyncio.run(main())
    else:
        print("captive portal")
        reboot_button = RebootButton(27, pixels)
        asyncio.create_task(flash('red', 8))
        asyncio.create_task(reboot_button_check())
        captive.portal()
    
except OSError:
    print( "OSError - restart")
    machine.reset()
    
except KeyboardInterrupt:
    if pixels:
        pixels.clear()
        pixels.show()
    print("Main Finished")
    
finally:  # Prevent LmacRxBlk:1 errors.
    if client:
        client.close()
    asyncio.new_event_loop()
    print('MQTT Finished')
        
