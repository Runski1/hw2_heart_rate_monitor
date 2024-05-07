# Written by Andrei Vlassenko
from machine import Pin, ADC
from time import sleep
from piotimer import Piotimer
from fifo import Fifo


class HeartLine:
    
    
    def __init__(self, pin, oled):
        self.sensor = ADC(pin)  # Sensor pin
        self.oled = oled.display  # Nichakon's oled != SSD1306 object
        self.oled.fill(0)    # empty screen before first line drawing
        self.minval = 0      # needed for scaling
        self.maxval = 65535  # needed for scaling
        self.scale_factor = 200 # sensitivity
        self.offset = 114       # offset needed to turn peaks upside down
        self.pixel_range = 64  # resolution (Recommended 128 or 64)
        self.x_add = round(128 / self.pixel_range) # next x is relative to drawing resolution
        self.last_y = 20 # make the new line start from previous height
    
    def read_raw(self):
        return self.sensor.read_u16() # raw value

    
    def scale_data(self):
        value = self.read_raw()  # get raw value
        # dynamic range needed for scaling
        self.maxval = max(self.maxval, value)
        self.minval = min(self.minval, value)
        # calculating scaled value
        scaled = round(((value - self.minval) / (self.maxval - self.minval)) * self.scale_factor)
        return scaled
    
        
    def display(self):
        #self.oled.text(str(self.scale_factor),104,24,1)
        x = 0 # resetting line start position to beggining
        y1 = self.last_y # resetting line height
        for _ in range(self.pixel_range): # amount of values per pixel. (Max 1 value per pixel) 
            y2 = self.offset - self.scale_data() # turning upside down the scaled value
            y2 = min(max(y2, 2), 20)  # Ensure y2 is within the valid range
            self.oled.line(x, y1, x + self.x_add, y2, 1) # drawing a line from value to value
            self.oled.show() 
            x += self.x_add # next position of x is relative to drawing resolution
            y1 = y2  # Update y1 for the next line
        self.last_y = y1
        self.oled.fill(0)
        
        
class bpmCalc:
    
    
    def __init__(self,oled):
        self.sensor = ADC(27) # HR sensor
        self.oled = oled.display # Nichakon's oled != SSD1306 object
        
        self.bpm_list = [] # used for averages
        self.minbpm = 1200 # 1200 ms PPI equals 50 BPM 
        self.maxbpm = 375 # 375 ms PPI is about 160 BPM 
        self.lastbpm = 75 # used to filter out unnatural fluctuations
        
        self.bpm_fifo = Fifo(30, typecode='i')
        self.average_bpm = 0 # used for displaying average bpm
        self.last_average_bpm = 0 # used to update average bpm
        self.reset_counter = 0
        
        self.lastval = 99999 # used for peak detection and average
        self.ms_counter = 0  # used for calculating PPI
        self.maxval = 0 # maximum value for a period
        self.minval = 99999 # minimum value for a period
        self.threshold = 33600 # register peaks over this value
        self.threshold_offset = 200 # Offset threshold so it is above middle
        self.readcount = 0 # used to update threshold
        
        # timer adds 1 to a counter every 4 ms and puts raw value into fifo
        self.fifo = Fifo(1000, typecode='i')
        self.tmr = Piotimer(period=4, mode=Piotimer.PERIODIC, callback=self.counter)
        
        
    def counter(self, _):
        self.fifo.put(self.sensor.read_u16()) # Put raw value in fifo
      
      
    def SLPF(self, value): # Simple LowPass Filter for Dummies
        new_val = (value + self.lastval) // 2
        return new_val
    
    
    def detect(self, average): # main algorythm
        
        while self.fifo.has_data(): # Run only when fifo not empty. 
            # Get raw value from fifo and average it with the previous
            raw = self.fifo.get()
            self.ms_counter += 4 # adding one each 4 ms
            newval = self.SLPF(raw)
            
            # Update min and max values for dynamic threshold
            self.maxval = max(self.maxval, newval)
            self.minval = min(self.minval, newval)
            
            # Recalculate new threshold every 500 values and reset values.
            self.readcount += 1 # for threshold update
            if self.readcount > 500:
                self.threshold = ((self.minval + self.maxval) // 2) + self.threshold_offset
                self.minval = 99999
                self.maxval = 0
                self.readcount = 0
                
            # Check if new value is bigger that previous value and is above thershold
            if self.lastval < self.threshold <= newval: # basic rising edge peak detection 
                if self.minbpm > self.ms_counter > self.maxbpm: # skip values outside human heart rate. 
                    seconds = self.ms_counter / 1000 # caclulate seconds between peaks
                    bpm = 60 // seconds # calculate BPM
                    if abs(self.lastbpm - bpm) < 20: # Ignore fluctuations of more than 10 BPM between beats
                        self.last_bpm = bpm
                        self.bpm_list.append(bpm) # add BPM to a list 
                self.ms_counter = 0 # Reset counter after rising edge was detected 
            self.lastval = newval # save current value as lastvalue for filtering
            
            # List for averages
            if len(self.bpm_list) > average: # Check if list has enough values
                self.bpm_fifo.put(int(sum(self.bpm_list) / (average + 1)))
                
                self.bpm_list = [] # empty the list
        self.bpm_show() # call show BPM show method 
                
    
    def bpm_show(self):
        while self.bpm_fifo.has_data(): # Reading if buffer has BPM average 
            self.average_bpm = self.bpm_fifo.get() # Getting BPM average.
            self.reset_counter = 0
        # Checking if average wasn't reset
        if self.average_bpm != 0: 
            self.oled.text(f"{self.average_bpm}", 56,40,1) # Show average BPM
        else: self.oled.text("--", 56,38,1) # Show two lines when no BPM data available
        # Check if last average BPM is same as previous
        if self.last_average_bpm == self.average_bpm:
            self.reset_counter += 1
            if self.reset_counter > 2: # If average BPM same for more than 5 times, reset values
                self.average_bpm = 0  # zero indicates that no data available
                self.reset_counter = 0 # resetting counter
        
        self.last_average_bpm = self.average_bpm # Update last average 
        self.oled.text("Press to exit >", 8,56,1)
        self.oled.show()
                

def display_bpm(encoder,oled):
    bpm = bpmCalc(oled)
    heartline = HeartLine(27,oled) # 27 for sensor pin

    while True:
        heartline.display()
        bpm.detect(4) # average of 5 PPIs (In BPM)
        while encoder.fifo.has_data():
            encoder.fifo.get()
        if encoder.knob_fifo.has_data():
            while encoder.knob_fifo.has_data():
                encoder.knob_fifo.get()
            bpm.tmr.deinit()
            return

