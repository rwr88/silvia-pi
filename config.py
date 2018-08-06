#!/usr/bin/python
import jsonpickle

filename = '/home/pi/silvia-pi/conf.json'

class Config:
    def __init__(self):
        pass

    def set_defaults(self):
        # Raspberry Pi SPI Port and Device
        '''spi_port = 0
        spi_dev = 0'''
        self.SCK = 13
        self.SO = 19
        self.CS = 26

        # Pin # for relay connected to heating element
        self.he_pins = [21, 20]

        # Default goal temperature
        self.celsius = True
        self.set_temp = 96.

        # Default alarm time
        self.snooze = '07:00'

        # Main loop sample rate in seconds
        self.sample_time = 0.3

        # PID Proportional, Integral, and Derivative values
        self.Pc = 4
        self.Ic = 0.3
        self.Dc = 60.0
        self.Sc = 0.5
        self.windup = 20.0

        #Web/REST Server Options
        self.port = 8080

        #kivy options
        self.refresh_rate = 1./5.
        self.fps = 1./self.refresh_rate
        self.seconds_to_display = 10

    def save(self):
        with open(filename, 'w') as f:
            f.write(jsonpickle.encode(self))

config = None

try:
    with open(filename, 'r') as f:
        config = jsonpickle.decode(f.read())
except Exception as e:
    print(e)
    config = Config()
    config.set_defaults()
