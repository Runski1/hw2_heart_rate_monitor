from ssd1306 import SSD1306_I2C
from machine import I2C, Pin
import json
from fifo import Fifo
import time

i2c = I2C(1, scl=Pin(15), sda=Pin(14), freq=400000)
oled_width = 128
oled_height = 64
char_height = 8
oled = SSD1306_I2C(oled_width, oled_height, i2c)

# data = "2024-04-28T18:58:19.061917+00:00"
# timestamp = data.split(".")[0].replace("T", " ")
# print(timestamp)


class Encoder:
    def __init__(self):
        self.a = Pin(10, mode=Pin.IN, pull=Pin.PULL_UP)
        self.b = Pin(11, mode=Pin.IN, pull=Pin.PULL_UP)
        self.fifo = Fifo(30, typecode="i")
        self.a.irq(handler=self.rot_handler, trigger=Pin.IRQ_RISING, hard=True)
        self.but = Pin(12, mode=Pin.IN, pull=Pin.PULL_UP)
        self.but.irq(handler=self.but_handler, trigger=Pin.IRQ_FALLING, hard=True)
        self.button_press = time.ticks_ms()
        self.knob_fifo = Fifo(30, typecode="i")

    def rot_handler(self, pin):
        if self.b():
            self.fifo.put(-1)
        else:
            self.fifo.put(1)

    def but_handler(self, pin):
        if time.ticks_diff(time.ticks_ms(), self.button_press) > 500:
            self.button_press = time.ticks_ms()
            self.knob_fifo.put(1)


results = {
    "mean_hr": "60",
    "mean_ppi": "70",
    "rmssd": "50",
    "sdnn": "40",
    "sns": "30",
    "pns": "20",
    "timestamp": "TEST-28T18:58:19.061917+00:00",
}


class History:
    def __init__(self, oled):
        self.file = "history.txt"
        self.results = results
        self.list = []
        self.menu_lowest = 1
        self.menu_highest = 8
        self.oled = oled
        self.selection_pos = 0
        self.selection = SSD1306_I2C(oled_width, oled_height, i2c)
        self.selection.rect(0, 0, oled_width, 10, 1)

    def selection_up(self):
        if self.selection_pos > 0:
            self.selection_pos -= char_height + 1
        elif self.menu_lowest > 1:
            self.menu_highest -= 1
            self.menu_lowest -= 1

    def selection_down(self):
        if self.selection_pos < 54 and self.selection_pos / 9 + 1 < len(self.list):
            self.selection_pos += char_height + 1
        elif self.menu_highest <= len(self.list):
            self.menu_highest += 1
            self.menu_lowest += 1

    def load_history(self):
        with open(self.file, "r") as history:
            lines = history.readlines()
            if len(lines) == 0:
                print("no recorded history")
                return False
            else:
                with open(self.file, "r") as history:
                    for line in history:
                        record = json.loads(line.strip())
                        self.list.append(record)
                    return True

    def draw_menu(self):
        y = 0
        char_height = 8
        self.oled.fill(0)
        for i in range(self.menu_lowest, min(self.menu_highest, len(self.list) + 1)):
            self.oled.text(self.list[len(self.list) - i]["timestamp"], 2, 2 + y, 1)
            y += char_height + 1
        self.oled.blit(self.selection, 0, self.selection_pos, 0)
        self.oled.show()

    def draw_selection(self):
        self.oled.rect()

    def display_history(self):
        y = 0
        oled.fill(0)
        record_json = self.list[
            (int(len(self.list) - (self.selection_pos / 9)) - self.menu_lowest)
        ]
        for item, value in record_json.items():
            if item != "timestamp":
                oled.text(item + ":", 0, y, 1)
                oled.text(str(value), oled_width - len(str(value)) * 8, y, 1)
                y += 8
        oled.text("Press to exit >", 8, 56, 1)
        oled.show()

    def print_selected_item(
        self,
    ):  # Prints the timestamp that is currently selected to console
        print(
            self.list[
                (int(len(self.list) - (self.selection_pos / 9)) - self.menu_lowest)
            ]
        )


def save_to_history(results):
    with open("history.txt", "a") as history:
        json.dump(results, history)
        history.write("\n")


def history_mode(encoder, menu):
    rot = encoder
    his = History(oled)
    history_exists = his.load_history()  # we can catch true/false here if needed
    if history_exists:
        his.print_selected_item()
        his.draw_menu()
        while True:
            while rot.fifo.has_data():
                val = rot.fifo.get()
                if val == 1:
                    his.selection_down()
                    his.print_selected_item()
                else:
                    his.selection_up()
                    his.print_selected_item()
            his.draw_menu()
            if menu.fifo.has_data():
                while menu.fifo.has_data():
                    menu.fifo.get()
                return
            # Press knob to show history, press again to go back to browsing
            # There must be prettier way to accomplish this but cba for now
            if rot.knob_fifo.has_data():
                # This gets very ugly
                while rot.knob_fifo.has_data():  # empty knob press fifo...
                    rot.knob_fifo.get()
                while rot.knob_fifo.empty():  # ... to keep on displaying history
                    his.display_history()
                    while rot.fifo.has_data():  # ignore knob turns meanwhile
                        rot.fifo.get()  # and make sure fifo doesnt fill up
                while (
                    rot.knob_fifo.has_data()
                ):  # go back to browsing history entries with knob press
                    rot.knob_fifo.get()  # empty fifo


if __name__ == "__main__":
    rot = Encoder()
    his = History(oled)
    history_exists = his.load_history()  # we can catch true/false here if needed
    if history_exists:
        his.print_selected_item()
        his.draw_menu()
        while True:
            while rot.fifo.has_data():
                val = rot.fifo.get()
                if val == 1:
                    his.selection_down()
                    his.print_selected_item()
                else:
                    his.selection_up()
                    his.print_selected_item()
            his.draw_menu()
            # Press knob to show history, press again to go back to browsing
            # There must be prettier way to accomplish this but cba for now
            if rot.knob_fifo.has_data():
                # This gets very ugly
                while rot.knob_fifo.has_data():  # empty knob press fifo...
                    rot.knob_fifo.get()
                while rot.knob_fifo.empty():  # ... to keep on displaying history
                    his.display_history()
                    while rot.fifo.has_data():  # ignore knob turns meanwhile
                        rot.fifo.get()  # and make sure fifo doesnt fill up
                while (
                    rot.knob_fifo.has_data()
                ):  # go back to browsing history entries with knob press
                    rot.knob_fifo.get()  # empty fifo
