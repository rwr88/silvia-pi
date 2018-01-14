#!/usr/bin/python

from time import sleep
from datetime import datetime, timedelta
import RPi.GPIO as GPIO
import config as conf
from config import he_pins


class Heat(object):
  def __init__(self, state):
    self._state = state
    self.setup()

  def setup(self):
    GPIO.setmode(GPIO.BCM)
    for pin in he_pins:
      GPIO.setup(pin, GPIO.OUT)
      GPIO.output(pin, 0)

  def cleanup(self):
    for pin in he_pins:
      GPIO.output(pin, 0)
    GPIO.cleanup()

  def run(self):
    heating = False

    while True:
      # Check if snooze is over
      if self._state['snoozeon'] == True :
        now = datetime.now()
        dt = datetime.strptime(self._state['snooze'],'%H:%M')
        if dt.hour == now.hour and dt.minute == now.minute :
          self._state['snoozeon'] = False

      # Sleep if snoozing
      if self._state['snoozeon']:
        self._state['heating'] = False
        for pin in he_pins:
          GPIO.output(pin,0)
        sleep(1)
      else:
        avgpid = self._state['avgpid']

        # Full heat
        if avgpid >= 100 :
          self._state['heating'] = True
          for pin in he_pins:
            GPIO.output(pin, 1)
          sleep(1)
        # Heat for avgpid/100 seconds, sleep the rest of the second
        elif avgpid > 0 and avgpid < 100:
          self._state['heating'] = True
          for pin in he_pins:
            GPIO.output(pin, 1)
          sleep(avgpid/100.)
          for pin in he_pins:
            GPIO.output(pin, 0)
          sleep(1-(avgpid/100.))
          self._state['heating'] = False
        # Don't heat
        else:
          for pin in he_pins:
            GPIO.output(pin, 0)
          self._state['heating'] = False
          sleep(1)
