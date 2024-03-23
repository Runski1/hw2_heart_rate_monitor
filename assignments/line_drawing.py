# Written by Matias Ruonala
# Andrei's ufo-code used as base

import time
from machine import Pin, I2C
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
sw1 = Button(8)
sw2 = Button(9)

x = 0
y = 32

while True:
    if sw0.pressed() and y >= 3:
        y -= 1
    elif sw2.pressed() and y <= 61: # drawing lines down is still slower than drawing up, need to ask Joe
        y += 1 # I also feel like there must be smarter way to do this than an if-else monster
    elif sw1.pressed():
        oled.fill(0)
        x = 0
        y = 32
    else:
        time.sleep(0.05) # This here so it doesnt draw straight lines faster than up or down
    x += 1
    if x > 128:
        x = 0
    oled.pixel(x, y, 1)
    oled.show()
    # Polling rate is actually defined by the rebound filters or the 50ms sleep in else. (max polling rate is 1/50ms = 33.3Hz)
