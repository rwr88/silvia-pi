#!/usr/bin/python
import simplejson

filename = '/home/pi/silvia-pi/conf.json'

class Config:
    def __init__(self):
        # Raspberry Pi SPI Port and Device
        '''spi_port = 0
        spi_dev = 0'''
        SCK = 13
        SO = 19
        CS = 26

        # Pin # for relay connected to heating element
        he_pins = [21, 20]

        # Default goal temperature
        celsius = True
        set_temp = 96.

        # Default alarm time
        snooze = '07:00'

        # Main loop sample rate in seconds
        sample_time = 0.3

        # PID Proportional, Integral, and Derivative values
        Pc = 4
        Ic = 0.3
        Dc = 60.0
        Sc = 0.5
        windup = 20.0

        #Web/REST Server Options
        port = 8080

        #kivy options
        refresh_rate = 1./5.
        fps = 1./refresh_rate
        seconds_to_display = 10

    def save(self):
        with open(filename, 'w') as f:
            simplejson.dump(self, f)

config = None

try:
    with open(filename, 'r') as f:
        config = simplejson.load(f)
except:
    config = Config()
