from machine import Pin, PWM
import utime

class Led:
    def __init__(self, id):
        self.pwm = PWM(Pin(id, Pin.OUT))
        self.pwm.freq(1000)


class Button:
    def __init__(self, id):
        self.button = Pin(id, Pin.IN, Pin.PULL_UP)

    def pressed(self):
        if self.button.value() == 0:
            utime.sleep(0.05)
            if self.button.value() == 0:
                utime.sleep(0.05)
                return True

# Init LEDs and the button
button = Button(12)
led1 = Led(22)
led2 = Led(21)
led3 = Led(20)

count = 0
# Main loop
while True:
    if button.pressed():
        count += 1
        print(count)
    led1brightness = 1000 if count & 1 else 0
    led2brightness = 1000 if count & 2 else 0
    led3brightness = 1000 if count & 4 else 0
    led1.pwm.duty_u16(led1brightness)
    led2.pwm.duty_u16(led2brightness)
    led3.pwm.duty_u16(led3brightness)
    
    utime.sleep(0.05)




