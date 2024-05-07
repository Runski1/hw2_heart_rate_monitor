# Code modified from https://github.com/kevinmcaleer/pico_ssd1306/blob/master/display.py

from machine import Pin, I2C
from ssd1306 import SSD1306_I2C
import framebuf, time

i2c = I2C(1, scl=Pin(15), sda=Pin(14), freq=400000)
oled_width = 128
oled_height = 64
oled = SSD1306_I2C(oled_width, oled_height, i2c)

for n in range(1, 22):
    with open('/logo/img%s.pbm' % n, 'rb') as f:
        f.readline()  # Magic number
        f.readline()  # Creator comment
        dimensions = f.readline().split()  # Read dimensions
        width, height = int(dimensions[0]), int(dimensions[1])
        logo = bytearray(f.read())
    
    fbuf = framebuf.FrameBuffer(logo, width, height, framebuf.MONO_HLSB)
    oled.blit(fbuf, (oled_width - width) // 2, (oled_height - height) // 2)
    oled.show()
    
    if n == 17:  # logo file
        time.sleep(1)
    else:
        time.sleep(0.02)
