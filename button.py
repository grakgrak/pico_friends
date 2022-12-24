import mqtt
import time
from machine import Pin
from lib.neopixel import Neopixel
from statemachine import StateMachine

BRIGHTNESS = 128
BUTTON_PIN = 27
FADE_MS = 30000
DOUBLE_CLICK_MS = 400

_pixels: Neopixel

class Button(StateMachine):
    def __init__(self, pixels: Neopixel, publish_cb):
        global _pixels
        _pixels = pixels

        StateMachine.__init__(self, 'IDLE')
        
        self.publish = publish_cb
        self.button = Pin(BUTTON_PIN, Pin.IN, Pin.PULL_DOWN)
        self.pressed: int | None = self.button.value()
        self.pressed_at: int = 0
        self.released_at: int = 0
        self.brightness: int = 0
        self.waiting_start: int = 0
        self.rgb: tuple = (0,0,0)
    
    def setRGB(self, rgb: tuple):
        self.brightness = BRIGHTNESS
        self.rgb = rgb
        
    def refresh_pixels(self):
        if self.brightness > 0:
            if self.ms_since(self.waiting_start) > FADE_MS // BRIGHTNESS:
                self.waiting_start = time.ticks_ms()
                self.brightness -= 1
            _pixels.brightness(self.brightness)
            _pixels.fill(self.rgb)
        else:
            _pixels.clear()
        _pixels.show()
    
    def IDLE(self, stateChanged: bool) -> str:
        if self.released_at:
            if self.ms_since(self.released_at) > DOUBLE_CLICK_MS:
                self.publish(self.rgb)
                self.released_at = 0

        if self.pressed != self.button.value():
            self.pressed = self.button.value()
            return 'BUTTON_PRESSED' if self.pressed else 'BUTTON_RELEASED'

        self.refresh_pixels()
        return 'IDLE'

    def DOUBLE_CLICK(self, stateChanged: bool) -> str:
        self.brightness = 0
        _pixels.clear()
        return 'IDLE'

    def BUTTON_PRESSED(self, stateChanged: bool) -> str:
        if stateChanged:
            self.pressed_at = time.ticks_ms()
            return 'BUTTON_PRESSED'
            
        diff = self.ms_since(self.pressed_at)
        self.rgb = _pixels.colorHSV((diff * 7) % 65535, 255, 255)
        
        _pixels.fill(self.rgb, BRIGHTNESS)
        _pixels.show()

        return 'BUTTON_PRESSED' if self.button.value() else 'IDLE'

    def BUTTON_RELEASED(self, stateChanged: bool) -> str:
        if self.released_at:
            self.released_at = 0
            return 'DOUBLE_CLICK'
        
        self.brightness = BRIGHTNESS
        self.released_at = time.ticks_ms()
        return 'IDLE'

