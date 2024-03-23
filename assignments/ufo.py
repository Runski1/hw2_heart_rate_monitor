# Code written by Andrei Vlassenko

import time
from machine import UART, Pin, I2C, Timer, ADC
from ssd1306 import SSD1306_I2C

# i2c bus and display init
i2c = I2C(1, scl=Pin(15), sda=Pin(14), freq=400000)
oled_width = 128
oled_height = 64
oled = SSD1306_I2C(oled_width, oled_height, i2c)

# Button class with rebound filter
class Button:
    def __init__(self, id):
        self.button = Pin(id, Pin.IN, Pin.PULL_UP)

    def pressed(self):
        if self.button.value() == 0:
            time.sleep(0.05)
            if self.button.value() == 0:
                return True
        return False


sw0 = Button(7)
sw2 = Button(9)

# Vector UFO
sides = [
            [-10, 0, -6, 2],
            [-6, 2, 6, 2],
            [6, 2, 10, 0],
            [10, 0, 6, -2],
            [6, -2, -6, -2],
            [-6, -2, -10, 0],
            [-4, 2, -2, 4],
            [-2, 4, 2, 4],
            [2, 4, 4, 2]
            ]

x = 64 # This should be 52 for <=> and 64 for vector ufo
y = 60 # This should be 56 for <=> and 60 for vector ufo

while True:
    oled.fill(0)
    for side in sides: # Comment this out for <=> ufo
        oled.line(side[0] + x, (-1)*side[1] + y, side[2] + x, (-1)*side[3] + y, 1) # Comment this out for <=> ufo
#    oled.text("<=>", x, y)
    oled.show()
    if sw0.pressed() and x < 114: # This should be 104 for <=> and 114 for vector ufo
        x += 4
    if sw2.pressed() and x > 14: # This should be 0 for <=> and 14 for vector ufo
        x -= 4
