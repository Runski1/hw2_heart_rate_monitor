from piotimer import Piotimer
from fifo import Fifo
from filefifo import Filefifo
from machine import Pin, ADC
from led import Led
import micropython
import time

micropython.alloc_emergency_exception_buf(200)

leds = [Led(20), Led(21), Led(22)]


class DataProcessor:
    def __init__(self, fifosize, polling_rate):
        self.polling_rate = polling_rate
        self.sensor = ADC(27)  # HR sensor
        self.rri_arr = []  # array('I') # Final data, filtered RRI's, unsigned longs
        self.fifo = Fifo(fifosize, typecode="i")
        self.tmr = Piotimer(
            period=polling_rate, mode=Piotimer.PERIODIC, callback=self.read_sensor
        )
        self.last_val = 0
        self.ms_count = 0
        self.min = 0xFFFF  # these track the min and max values for dynamic threshold
        self.max = 0x0000
        self.threshold = (
            0x8000  # arbitrary starting value in the middle of sensor's range
        )
        self.last_peak_ms = 0
        # low-pass filter
        self.lpf_lastvals = []  # array('I') # for running average, unsigned integers
        # variance filter
        self.variance_avg = []  # array('H') # for running average, unsigned shorts
        # Filefifo for testing
        # self.file = Filefifo(100, name='capture03_250Hz.txt')
        self.draw_mode_rris = []

    def read_sensor(self, _):
        self.fifo.put(self.sensor.read_u16())

    def detect_slope(self, value, topweight=0.7):
        rri = False
        self.ms_count += self.polling_rate  # tracking time
        # Dynamic threshold
        self.min = min(value, self.min)  # tracking highest and lowest
        self.max = max(value, self.max)
        if (
            self.ms_count != 0 and self.ms_count % 4000 == 0
        ):  # Calculates new threshold every 4 seconds
            self.threshold = (
                self.min * (1 - topweight) + self.max * topweight
            )  # weighted arithmetic mean with 70% top, 30% bottom
            self.min = 0xFFFF  # reset min and max for dynamic threshold
            self.max = 0x0000

        if (  # slope detection
            self.last_val < self.threshold <= value
        ):  # do this stuff if new peak is detected
            rri = self.ms_count - self.last_peak_ms  # Distance (ms) between two peaks
            self.last_peak_ms = self.ms_count  # detected peak to memory
        return rri

    def get_valid_rris(self, draw_mode=False):
        while self.fifo.has_data():
            value = self.fifo.get()
            value = self.lpf(value)
            if not value:
                self.last_val = value
                break
            rri = self.detect_slope(value)
            if not rri:
                self.last_val = value
                break
            if draw_mode:
                self.last_val = value
                self.draw_mode_rris.append(rri)
                break
            range_filtered_rri = self.range_filter(rri)
            if not range_filtered_rri:
                self.last_val = value
                break
            variance_filtered_rri = self.variance_filter(range_filtered_rri)
            if not variance_filtered_rri:
                self.last_val = value
                break
            self.rri_arr.append(variance_filtered_rri)
            self.last_val = value

    def lpf(self, value, amount=10):  # low pass filter
        if len(self.lpf_lastvals) < amount:
            self.lpf_lastvals.append(value)
            return False
        else:
            self.lpf_lastvals.pop(0)
            self.lpf_lastvals.append(value)
            return int(sum(self.lpf_lastvals) / len(self.lpf_lastvals))

    def range_filter(
        self, value, min_rri=400, max_rri=1200
    ):  # Filter out RRIs that are not between 50-150 BPM
        if min_rri <= value <= max_rri:
            return value
        else:
            return False

    def variance_filter(
        self, value, difference_ms=80, length=4
    ):  # Filter out RRIs that vary 60ms or more from previous average
        if len(self.variance_avg) < length:
            self.variance_avg.append(value)
            return False
        else:
            self.variance_avg.pop(0)
            self.variance_avg.append(value)
            avg = sum(self.variance_avg) / len(self.variance_avg)
            if abs(value - avg) < difference_ms:
                return value
            else:
                return False


def record_heart_rate(encoder, oled):
    heart_rate = DataProcessor(100, 4)
    rri_arr_len = 0
    print("Recording")
    while len(heart_rate.rri_arr) < 50:
        while encoder.fifo.has_data():
            encoder.fifo.get()
        while encoder.knob_fifo.has_data():
            encoder.knob_fifo.get()
            heart_rate.tmr.deinit()
            return False
        heart_rate.get_valid_rris()
        if len(heart_rate.rri_arr) > rri_arr_len:
            for led in leds:
                led.toggle()
                time.sleep(0.1)
            oled.show_progress(len(heart_rate.rri_arr) * 2)
            rri_arr_len = len(heart_rate.rri_arr)
    print("Data collected")
    # Kill piotimer
    heart_rate.tmr.deinit()
    return heart_rate.rri_arr


if __name__ == "__main__":
    record_heart_rate()
