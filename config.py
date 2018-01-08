#!/usr/bin/python

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
set_temp = 35.

# Default alarm time
snooze = '07:00'

# Main loop sample rate in seconds
sample_time = 0.1

# PID Proportional, Integral, and Derivative values
Pc = 3.4
Ic = 0.3
Dc = 40.0

Pw = 2.9
Iw = 0.3
Dw = 40.0

#Web/REST Server Options
port = 8080

#kivy options
refresh_rate = 1./5.
fps = 1./refresh_rate
seconds_to_display = 10
