import ssd1306
from machine import Pin, I2C
import utime


led = Pin("LED", Pin.OUT)
OLED_SDA = 14  # Data
OLED_SCL = 15  # Clock

# Initialize I2C to use OLED
i2c = I2C(1, scl=Pin(OLED_SCL), sda=Pin(OLED_SDA), freq=3200000)
OLED_WIDTH = 128
OLED_HEIGHT = 64
oled = ssd1306.SSD1306_I2C(OLED_WIDTH, OLED_HEIGHT, i2c)
# Wait for a second
utime.sleep(1)

oled.poweroff()
machine.idle()