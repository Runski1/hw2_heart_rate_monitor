# Code written by Andrei Vlassenko

import time
from machine import UART, Pin, I2C, Timer, ADC
from ssd1306 import SSD1306_I2C
import framebuf

i2c = I2C(1, scl=Pin(15), sda=Pin(14), freq=400000)
oled_width = 128
oled_height = 64
oled = SSD1306_I2C(oled_width, oled_height, i2c)


class Button:
    def __init__(self, id):
        self.button = Pin(id, Pin.IN, Pin.PULL_UP)

    def pressed(self):
        if self.button.value() == 0:
            time.sleep(0.1)
            if self.button.value() == 0:
                return True

        return False


sw0 = Button(7)
sw2 = Button(9)

x = 56
y = 56

while True:
    oled.fill(0)
    oled.text("<=>", x, y)
    oled.show()
    if sw0.pressed() and x != 104:
        x += 24
    if sw2.pressed() and x != 8:
        x -= 24
