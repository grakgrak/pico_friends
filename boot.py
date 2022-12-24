from credentials import Creds
from lib.neopixel import Neopixel
import ugit
import urequests

pixels = Neopixel(16, 0, 28, "GRB")
pixels.fill((0,0,255))
pixels.show()

creds = Creds()
creds.load()

wlan = ugit.wificonnect(ssid=creds.ssid, password=creds.password)

if wlan.isconnected():
    pixels.fill((0,255,0))
else:
    pixels.fill((255,0, 0))
pixels.show()

# get the current version
with open("./version.info", "r") as f:
    current_version = f.read()

r = urequests.get(ugit.raw + 'version.info')

if r.status_code == 200 and r.text != current_version:
    pixels.fill((255,255,255))
    pixels.show()
    ugit.pull_all(isconnected=True)
