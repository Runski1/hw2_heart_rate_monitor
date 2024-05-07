import time, framebuf, micropython
from machine import UART, Pin, I2C, Timer, ADC
from ssd1306 import SSD1306_I2C
from fifo import Fifo
import ujson


# Classes from other files need to be imported here if they're used
from data_processor import record_heart_rate
from hrv_analysis import basic_hrv_analysis
from cloudconnection import connect_to_kubios
from history import save_to_history, history_mode
from measureHR import display_bpm
import icons, intro

micropython.alloc_emergency_exception_buf(200)

class Screen:
    def __init__(self):
        self.i2c = I2C(1, scl=Pin(15), sda=Pin(14), freq=400000)
        self.width = 128
        self.height = 64
        self.display = SSD1306_I2C(self.width, self.height, self.i2c)
        self.padding = 5
        self.gap = 10
        self.letter_size = 8

    def draw_menu(self, sector):
        self.display.fill(0)
        self.display.ellipse(int(self.width / 2), int(self.height / 2), 30, 30, 1, True, sector) # white quadrant
        self.display.ellipse(int(self.width / 2), int(self.height / 2), 25, 25, 0, True) # black small circle
        self.display.ellipse(int(self.width / 2), int(self.height / 2), 30, 30, 1) # outer white circle (outlines)
        self.display.ellipse(int(self.width / 2), int(self.height / 2), 25, 25, 1) # inner white circle (outlines)
        
    def display_icon(self, framebuffer, x, y):
        self.display.blit(framebuffer, x, y)
        
    def heart_icon(self):
        heart_framebuf = framebuf.FrameBuffer(icons.heartlogo, 27, 24, framebuf.MONO_VLSB)
        self.display_icon(heart_framebuf, 51, 21)  # aligns icon in center
        
    def kubios_icon(self):
        kubwifi_framebuf = framebuf.FrameBuffer(icons.kubwifi, 35, 30, framebuf.MONO_VLSB)
        self.display_icon(kubwifi_framebuf, 48, 18)
        
    def hrv_icon(self):
        hrv_framebuf = framebuf.FrameBuffer(icons.hrv, 39, 16, framebuf.MONO_VLSB)
        self.display_icon(hrv_framebuf, 46, 23)
        
    def history_icon(self):
        his_framebuf = framebuf.FrameBuffer(icons.his, 24, 22, framebuf.MONO_VLSB)
        self.display_icon(his_framebuf, 53, 20)

    def alignment(self, text, results, y_pos):
        text_width = len(text) * self.letter_size
        res_str = str(results)
        res_width = len(res_str) * self.letter_size
        
        if not text:  # if empty text or value
            text_width = 0
        if not results:
            results = "No value"
        
        txt_x_pos = self.padding
        res_x_pos = self.width - len(res_str) * self.letter_size
        
        self.display.text(text, txt_x_pos, y_pos, 1)
        self.display.text(res_str, res_x_pos, y_pos, 1)
        
    def display_data(self, results):
        self.display.fill(0)
        y_pos = self.padding
        for text, value in results.items():
            self.alignment(text, value, y_pos)
            y_pos += self.gap  # Leaves gap between lines
            
        # self.display.text("Press to exit >", 0, self.height - self.letter_size - self.padding, 1)
        self.display.show()
        encoder.empty_fifos()
        while encoder.knob_fifo.empty():
            encoder.fifo.get()
            self.display.show()  # Sorry for hacky way to keep showing the results

    def show_progress(self, percentage):
        self.display.fill(0)
        message = "Measuring... "
        # Displaying and aligning text to center
        self.display.text(message, (self.width - ((len(message) * self.letter_size))) // 2, self.height - (self.gap + self.letter_size), 1)
        self.display.text(str(percentage) + "%", (self.width - ((len(str(percentage)) * self.letter_size))) // 2, self.height - self.letter_size, 1)
        self.display.show()

        
    def hrv_dis(self, mean_hr, mean_ppi, rmssd, sdnn):
        results = {
            "MEAN HR:": round(mean_hr, 1),
            "MEAN PPI:": round(mean_ppi),
            "RMSSD:": round(rmssd, 2),
            "SDNN:": round(sdnn, 2),
        }
        self.display_data(results)
        
    def kubios_dis(self, results, connecting=False):
        if connecting: # Displaying and aligning text to center
            text1 = 'Connecting...'
            self.display.fill(0)
            self.display.text(text1, (self.width - ((len(text1) * self.letter_size))) // 2, (self.height - self.letter_size) // 2, 1)
            self.display.show()  # Connecting message
        else:
            self.display.fill(0)
            y_pos = self.padding
            parsed_results = {"MEAN HR:": results["mean_hr"],
                              "MEAN PPI:": results["mean_ppi"],
                              "RMSSD:": results["rmssd"],
                              "SDNN:": results["sdnn"],
                              "SNS:": results["sns"],
                              "PNS:": results["pns"]}
            self.display_data(parsed_results)

class MenuButton:
    def __init__(self, pin):
        self.button = Pin(pin, Pin.IN, Pin.PULL_UP)
        self.button.irq(handler=self.but_handler, trigger=Pin.IRQ_FALLING, hard=True)
        self.debounce = 500
        self.fifo = Fifo(10, typecode="i")
        self.last_pressed = 0
        self.button_press = 0

    def but_handler(self, pin):
        self.button_press = time.ticks_ms()
        if self.button_press - self.last_pressed > self.debounce:
            self.fifo.put(1)
            self.last_pressed = self.button_press

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

        self.fifo = Fifo(100, typecode="i")
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

    def empty_fifos(self):
        while self.fifo.has_data():
            self.fifo.get()
        while self.knob_fifo.has_data():
            self.knob_fifo.get()


oled = Screen()
menubutton = MenuButton(9)
encoder = Encoder(10, 11)
enc_value = 0b0001  # b0 for Q1
rotval = 0
rri_list = False

while True:
    # sphere graphics
    while encoder.fifo.has_data():
        rotval += encoder.fifo.get()
        if not encoder.pressed:  # This check here to not change menus when inside one
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
            display_bpm(encoder, oled)
        
        elif enc_value == 0b1000:
            while (
                encoder.knob_fifo.has_data()
            ):  # Emptying the fifo if multiple presses are recognized
                encoder.knob_fifo.get()
            encoder.pressed = False
            print("HRV selected")
            oled.show_progress(0)
            rri_list = record_heart_rate(encoder, oled)
            if (
                not rri_list
            ):  # this should be True if recording is interrupted by knob press
                print("recording interrupted")
                pass
            else:
                results_dict = ujson.loads(basic_hrv_analysis(rri_list))
                oled.hrv_dis(
                    results_dict["mean_hr"],
                    results_dict["mean_ppi"],
                    results_dict["rmssd"],
                    results_dict["sdnn"])
                encoder.empty_fifos()
                pass

        elif enc_value == 0b0100:
            while encoder.knob_fifo.has_data():
                encoder.knob_fifo.get()
            encoder.pressed = False
            print("Kubios selected")
            oled.kubios_dis("_", connecting=True)
            kubios_results = connect_to_kubios(rri_list)
            print("saving results to history")
            if kubios_results:
                oled.kubios_dis(kubios_results)
                save_to_history(kubios_results)
                print("Record saved to history")
            else:
                print("Failed to connect to Kubios")  #prompt user if empty
                connected = False
            encoder.empty_fifos()

        elif enc_value == 0b0010:
            while encoder.knob_fifo.has_data():
                encoder.knob_fifo.get()
            encoder.pressed = False
            print("History selected")
            history_mode(encoder, menubutton)
            pass
        
    while menubutton.fifo.has_data():
        menubutton.fifo.get()
        
    oled.display.show()

