import sys
from time import sleep, time
from math import isnan
import Adafruit_GPIO.SPI as SPI
import Adafruit_MAX31855.MAX31855 as MAX31855
import PID as PID
import config as conf

def c_to_f(c):
  return c * 9.0 / 5.0 + 32.0

def f_to_c(f):
  return (f-32) * 5. / 9.

print dir(conf)

class Sensor(object):
  def __init__(self, state):
    self._sensor = MAX31855.MAX31855(conf.SCK, conf.CS, conf.SO)
    self._state = state
    print self._sensor.readState()
    self._pid = PID.PID(conf.Pc,conf.Ic,conf.Dc, conf.Sc)
    self._pid.SetPoint = self._state['settemp']
    self._pid.setSampleTime(1)
    self._pid.setWindup(conf.windup)

    self._nan_count = 0
    self._i=0
    self._pidhist = [0.,0.,0.,0.,0.,0.,0.,0.,0.,0.]
    self._avgpid = 0.
    self._temphist = [0.,0.,0.,0.,0.]
    self._avgtemp = 0.
    self._lastsettemp = state['settemp']
    self._lasttime = time()
    self._sleeptime = 0

  def run(self, verbose=False):
    while True:
      self._state['sensor'] = self._sensor.readState()
      tempc = self._sensor.readTempC()
      if not self.validate_temp(tempc):
        continue

      temp = self.convert_if_needed(tempc)
      self.update_temp_hist_and_average(temp)
      self.update_target_temp()
      self.update_pid()
      self.update_state(temp)
      if verbose:
        print self._state
      self.sleep()

  def validate_temp(self, tempc):
    if isnan(tempc):
      self._nan_count += 1
      if self._nan_count > 100000:
        raise Exception("100 000 consecutive NaN values from sensor")
      return False
    else:
      self._nan_count = 0
      return True

  def convert_if_needed(self, tempc):
    if conf.celsius:
      temp = tempc
    else:
      temp = c_to_f(tempc)
    return temp

  def update_temp_hist_and_average(self, temp):
    self._temphist[self._i%len(self._temphist)] = temp
    self._avgtemp = sum(self._temphist)/float(len(self._temphist))

  def update_target_temp(self):
    if self._state['settemp'] != self._lastsettemp:
      self._pid.SetPoint = self._state['settemp']
      self._lastsettemp = self._state['settemp']

  def update_pid(self):
    self._pid.update(self._avgtemp)
    hist_length = len(self._pidhist)
    self._pidhist[self._i/hist_length % hist_length] = self._pid.output
    self._avgpid = sum(self._pidhist) / hist_length

  def update_state(self, temp):
    self._state['i'] = self._i
    self._state['temp'] = round(temp, 2)
    self._state['avgtemp'] = round(self._avgtemp, 2)
    diff = self._lastsettemp - self._avgtemp

    # Be aggressive on machine startup
    if diff > 10.0:
      self._state['boost'] = time() + 1

    self._state['pidval'] = round(self._pid.output, 2)
    self._state['avgpid'] = round(self._avgpid, 2)
    self._state['pterm'] = round(self._pid.PTerm, 2)
    self._state['iterm'] = round(self._pid.ITerm * conf.Ic, 2)
    self._state['dterm'] = round(self._pid.DTerm * conf.Dc, 2)
    self._state['sterm'] = round(self._pid.STerm, 2)
  def sleep(self):
    sleeptime = max(self._lasttime+conf.sample_time-time(), 0)
    sleep(sleeptime)
    self._i += 1
    self._lasttime = time()

  def cleanup(self):
    self._pid.cleanup()


if __name__ == "__main__":
  pid = Sensor({ 'settemp': conf.set_temp })
  pid.run(verbose=True)
