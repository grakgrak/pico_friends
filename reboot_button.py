import time
import machine
from machine import Pin
from lib.neopixel import Neopixel

BRIGHTNESS = 128

_pixels: Neopixel

class RebootButton():
    def __init__(self, pin, pixels: Neopixel):
        global _pixels
        _pixels = pixels
        self.button = Pin(pin, Pin.IN, Pin.PULL_DOWN)
        self.pressed = self.button.value()
        self.pressed_at = None
        
    async def loop(self):
        if self.pressed_at:
            diff = time.ticks_diff(time.ticks_ms(), self.pressed_at)
            if diff > 3000:
                machine.reset()

        # The button state has changed
        if self.pressed != self.button.value():
            self.pressed = self.button.value()
            self.pressed_at = time.ticks_ms()
            if self.pressed:
                _pixels.fill((255,0,0), BRIGHTNESS)
            else:
                _pixels.clear()
            _pixels.show()

