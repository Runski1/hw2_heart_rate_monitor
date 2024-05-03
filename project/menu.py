import time, framebuf, micropython
from machine import UART, Pin, I2C, Timer, ADC
from ssd1306 import SSD1306_I2C
from fifo import Fifo

# Classes from other files need to be imported here if they're used
from data_processor import record_heart_rate
from hrv_analysis import basic_hrv_analysis
from cloudconnection import connect_to_kubios
from history import History

micropython.alloc_emergency_exception_buf(200)


class Screen:
    def __init__(self):
        self.i2c = I2C(1, scl=Pin(15), sda=Pin(14), freq=400000)
        self.width = 128
        self.height = 64
        self.display = SSD1306_I2C(self.width, self.height, self.i2c)

    def draw_menu(self, sector):
        self.display.fill(0)
        self.display.ellipse(
            int(self.width / 2), int(self.height / 2), 30, 30, 1, True, sector
        )  # white quadrant
        self.display.ellipse(
            int(self.width / 2), int(self.height / 2), 25, 25, 0, True
        )  # black small sircle
        self.display.ellipse(
            int(self.width / 2), int(self.height / 2), 30, 30, 1
        )  # outer white circle (outlines)
        self.display.ellipse(
            int(self.width / 2), int(self.height / 2), 25, 25, 1
        )  # inner white circle (outlines)

    def display_icon(self, framebuffer, x, y):
        self.display.blit(framebuffer, x, y)

    def kubios_icon(self):
        kubwifi = bytearray(
            [  # monovlsb : 35 : 30 : 35
                0x00,
                0xF8,
                0x20,
                0x50,
                0x88,
                0x00,
                0x00,
                0x1E,
                0xA0,
                0xA0,
                0xA0,
                0x9E,
                0xC0,
                0xC0,
                0xDF,
                0xD5,
                0xD5,
                0xCA,
                0xC0,
                0xC0,
                0xC0,
                0xDF,
                0xC0,
                0x80,
                0x9C,
                0xA2,
                0xA2,
                0x22,
                0x1C,
                0x40,
                0x90,
                0x28,
                0x48,
                0x90,
                0x20,
                0x70,
                0x78,
                0x3C,
                0x1C,
                0x1E,
                0x0E,
                0x87,
                0xC7,
                0xE7,
                0xE3,
                0xF3,
                0x73,
                0x73,
                0x79,
                0x39,
                0x39,
                0x39,
                0x39,
                0x39,
                0x39,
                0x39,
                0x79,
                0x73,
                0x73,
                0xF3,
                0xE3,
                0xE7,
                0xC7,
                0x87,
                0x0E,
                0x1E,
                0x1D,
                0x3D,
                0x78,
                0x70,
                0x00,
                0x00,
                0x00,
                0x00,
                0x06,
                0x07,
                0x07,
                0x03,
                0x01,
                0xE0,
                0xF8,
                0x7C,
                0x3C,
                0x1E,
                0xCE,
                0xC7,
                0xE7,
                0xE7,
                0xE7,
                0xC7,
                0xCE,
                0x1E,
                0x1C,
                0x7C,
                0xF8,
                0xE0,
                0x01,
                0x03,
                0x07,
                0x07,
                0x06,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x07,
                0x1F,
                0x1F,
                0x3F,
                0x3F,
                0x3F,
                0x1F,
                0x1F,
                0x07,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
            ]
        )
        kubwifi_framebuf = framebuf.FrameBuffer(kubwifi, 35, 30, framebuf.MONO_VLSB)
        self.display_icon(kubwifi_framebuf, 48, 18)  # aligns icon in center

    def heart_icon(self):
        heartlogo = bytearray(
            [  # monovlsb : 27 : 24 : 27
                0xF0,
                0xF8,
                0xFC,
                0xFE,
                0xFF,
                0xFF,
                0xFF,
                0xFF,
                0xFF,
                0xFF,
                0xFF,
                0xFE,
                0xFC,
                0xF8,
                0xFC,
                0xFE,
                0xFE,
                0xFF,
                0xFF,
                0xFF,
                0xFF,
                0xFF,
                0xFF,
                0xFE,
                0xFC,
                0xFC,
                0xF0,
                0x1F,
                0x3F,
                0xFF,
                0xFF,
                0xFF,
                0xFF,
                0xFF,
                0xFF,
                0xFF,
                0xFF,
                0xFF,
                0xFF,
                0xFF,
                0xFF,
                0xFF,
                0xFF,
                0xFF,
                0xFF,
                0xFF,
                0xFF,
                0xFF,
                0xFF,
                0xFF,
                0xFF,
                0xFF,
                0x7F,
                0x1F,
                0x00,
                0x00,
                0x00,
                0x01,
                0x03,
                0x07,
                0x0F,
                0x1F,
                0x3F,
                0x7F,
                0x7F,
                0xFF,
                0xFF,
                0xFF,
                0xFF,
                0xFF,
                0x7F,
                0x7F,
                0x3F,
                0x1F,
                0x0F,
                0x0F,
                0x07,
                0x03,
                0x00,
                0x00,
                0x00,
            ]
        )
        heart_framebuf = framebuf.FrameBuffer(heartlogo, 27, 24, framebuf.MONO_VLSB)
        self.display_icon(heart_framebuf, 51, 21)

    def hrv_icon(self):
        hrv = bytearray(
            [  # monovlsb : 39 : 16 : 39
                0xFF,
                0xFF,
                0xC0,
                0xC0,
                0xC0,
                0xC0,
                0xC0,
                0xC0,
                0xC0,
                0xC0,
                0xFF,
                0xFF,
                0x00,
                0x00,
                0xFF,
                0xFF,
                0x83,
                0x83,
                0x83,
                0x83,
                0x83,
                0xE6,
                0x7C,
                0x38,
                0x00,
                0x00,
                0x07,
                0x3F,
                0xFC,
                0xE0,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0xE0,
                0xFC,
                0x1F,
                0x03,
                0xFF,
                0xFF,
                0x01,
                0x01,
                0x01,
                0x01,
                0x01,
                0x01,
                0x01,
                0x01,
                0xFF,
                0xFF,
                0x00,
                0x00,
                0xFF,
                0xFF,
                0x01,
                0x01,
                0x01,
                0x01,
                0x07,
                0x1E,
                0x78,
                0xE0,
                0x80,
                0x00,
                0x00,
                0x00,
                0x01,
                0x0F,
                0x3F,
                0xF8,
                0xE0,
                0xF8,
                0x3F,
                0x07,
                0x00,
                0x00,
                0x00,
            ]
        )
        hrv_framebuf = framebuf.FrameBuffer(hrv, 39, 16, framebuf.MONO_VLSB)
        self.display_icon(hrv_framebuf, 46, 23)

    def history_icon(self):
        his = bytearray(
            [  # monovlsb : 35 : 35 : 35
                0x00,
                0x00,
                0x00,
                0x80,
                0xC0,
                0xE0,
                0xF0,
                0x78,
                0x38,
                0x3C,
                0x1C,
                0x0E,
                0x0E,
                0x0E,
                0x07,
                0x07,
                0xF7,
                0xF7,
                0xF7,
                0x07,
                0x07,
                0x0E,
                0x0E,
                0x0E,
                0x1C,
                0x1C,
                0x38,
                0x78,
                0xF0,
                0xE0,
                0xC0,
                0x80,
                0x00,
                0x00,
                0x00,
                0xC0,
                0xF8,
                0xFE,
                0x3F,
                0x07,
                0x03,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0xFF,
                0xFF,
                0xFF,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x01,
                0x07,
                0x3F,
                0xFE,
                0xFC,
                0xE0,
                0x1F,
                0xFF,
                0xFF,
                0xE0,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0xC0,
                0x80,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x1F,
                0x3F,
                0x7F,
                0xF8,
                0xF0,
                0xE0,
                0xC0,
                0x80,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0xE0,
                0xFF,
                0xFF,
                0x3F,
                0x00,
                0x01,
                0x03,
                0x0F,
                0x1F,
                0x3C,
                0x78,
                0xF0,
                0xE0,
                0xFF,
                0xFF,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x01,
                0x83,
                0x87,
                0x8F,
                0xCF,
                0xCE,
                0xE0,
                0xF0,
                0x78,
                0x3C,
                0x1F,
                0x0F,
                0x03,
                0x01,
                0x00,
                0x00,
                0x01,
                0x03,
                0x03,
                0x03,
                0x03,
                0x03,
                0x03,
                0x03,
                0x03,
                0x03,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x01,
                0x01,
                0x01,
                0x01,
                0x01,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
            ]
        )
        his_framebuf = framebuf.FrameBuffer(his, 35, 35, framebuf.MONO_VLSB)
        self.display_icon(his_framebuf, 47, 15)

    def alignment(self, text, value, y_pos):
        text_width = len(text) * 8
        value_str = str(value)
        value_width = len(value_str) * 8

        if not text:  # if empty text or value
            text_width = 0
        if not value:
            value = ""
            value_width = 0

        text_x = self.padding
        value_x = self.width - value_width - self.padding

        self.display.text(text, text_x, y_pos, 1)
        self.display.text(value_str, value_x, y_pos, 1)

    def display_data(self, data):
        self.display.fill(0)
        y_pos = self.padding

        for text, value in data:
            self.alignment(text, value, y_pos)
            y_pos += self.gap  # adds Y position for the next line

        self.display.show()

    def bpm(self, bpm_val):
        data = [("BPM:", bpm_val)]
        self.display.show()

    def hrv_dis(self, mean_hr, mean_ppi, rmssd, sdnn):
        data = [
            ("MEAN HR:", mean_hr),
            ("MEAN PPI:", mean_ppi),
            ("RMSSD:", rmssd),
            ("SDNN:", sdnn),
        ]
        self.display_data(data)

    def kubios_dis(self, mean_hr, mean_ppi, rmssd, sdnn, sns, pns):
        data = [
            ("MEAN HR:", mean_hr),
            ("MEAN PPI:", mean_ppi),
            ("RMSSD:", rmssd),
            ("SDNN:", sdnn),
            ("SNS:", sns),
            ("PNS:", pns),
        ]
        self.display_data(data)

    def history_dis(self, history_data):
        self.display_data(history_data)


class Encoder:
    def __init__(self, rot_a, rot_b):
        self.a = Pin(rot_a, mode=Pin.IN, pull=Pin.PULL_UP)
        self.b = Pin(rot_b, mode=Pin.IN, pull=Pin.PULL_UP)

        self.but = Pin(12, mode=Pin.IN, pull=Pin.PULL_UP)
        self.last_rotation = time.ticks_ms()
        self.knob_fifo = Fifo(30, typecode="i")
        self.last_pressed = 0  # last time the button was pressed
        self.debounce = 500
        self.pressed = False

        self.fifo = Fifo(30, typecode="i")
        self.a.irq(handler=self.rot_handler, trigger=Pin.IRQ_RISING, hard=True)
        self.but.irq(handler=self.but_handler, trigger=Pin.IRQ_FALLING, hard=True)

    def rot_handler(self, pin):
        if self.b():
            self.fifo.put(-1)
        else:
            self.fifo.put(1)

    def but_handler(self, pin):
        button_press = time.ticks_ms()  # Get button pressed time in milliseconds
        if button_press - self.last_pressed > self.debounce:
            self.knob_fifo.put(1)
            self.last_pressed = button_press


oled = Screen()
encoder = Encoder(10, 11)
enc_value = 0b0001  # b0 for Q1
rotval = 0
rri_list = []  # Init rri list here just in case kubios is called before hrv analysis
# so that this works as an error catch

while True:
    # sphere graphics
    while encoder.fifo.has_data():
        rotval += encoder.fifo.get()
        if not encoder.pressed:  # This check here to not change menus when inside one
            print(rotval)
            if rotval > 3:  # so that Q doesn't change with minor knob movement
                rotval = 0
                enc_value >>= 1  # changing Q
                if enc_value == 0b0000:  # from Q1 to Q4
                    enc_value = 0b1000
            elif rotval < -3:
                rotval = 0
                enc_value <<= 1  # changing Q
                if enc_value == 0b10000:  # from Q4 to Q1
                    enc_value = 0b0001

    # displays menu
    oled.draw_menu(enc_value)
    if enc_value == 0b0001:
        oled.heart_icon()
    elif enc_value == 0b1000:  # 2nd selection
        oled.hrv_icon()
    elif enc_value == 0b0100:  # 3rd selection
        oled.kubios_icon()
    elif enc_value == 0b0010:
        oled.history_icon()
    if encoder.knob_fifo.has_data():
        encoder.pressed = True
        if enc_value == 0b0001:
            while encoder.knob_fifo.has_data():
                encoder.knob_fifo.get()
            encoder.pressed = False
            print("BPM selected")
            # BPM and heart curve
            # init Andrei's code
            pass
        elif enc_value == 0b1000:
            while (
                encoder.knob_fifo.has_data()
            ):  # Emptying the fifo if multiple presses are recognized
                encoder.knob_fifo.get()
            encoder.pressed = False
            print("HRV selected")
            rri_list = record_heart_rate()
            print("Calculating basic HRV analysis")
            results_dict = basic_hrv_analysis(rri_list)
            print(results_dict)
            # Call for the display function here with results-dictionary
            pass
        elif enc_value == 0b0100:
            while encoder.knob_fifo.has_data():
                encoder.knob_fifo.get()
            encoder.pressed = False
            # Kubios
            # pass list of RRIs (caught previously) to Andrei's kubios stuff. If empty,
            # prompt user or do nothing
            # Returns analysis results as json, I think the drawing should be called here
            # and not directly from the Kubios code, but idk. its WIP
            print("Kubios selected")
            if len(rri_list) == 0:
                print("Use HRV mode first")
            else:
                kubios_results = connect_to_kubios(rri_list)
                his = History(kubios_results, _)
                his.save_results()
                del his
        elif enc_value == 0b0010:
            while encoder.knob_fifo.has_data():
                encoder.knob_fifo.get()
            encoder.pressed = False
            print("History selected")
            # History
            # Call for history drawing things here. It handles it's own display
            pass

    oled.display.show()
