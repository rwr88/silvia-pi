#!/usr/bin/python

def he_control_loop(lock,state):
  from time import sleep
  from datetime import datetime, timedelta
  import RPi.GPIO as GPIO
  import config as conf
  from config import he_pins

  GPIO.setmode(GPIO.BCM)
  for pin in he_pins:
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, 0)

  heating = False

  try:
    while True:
      if state['snoozeon'] == True :
        now = datetime.now()
        dt = datetime.strptime(state['snooze'],'%H:%M')
        if dt.hour == now.hour and dt.minute == now.minute :
          state['snoozeon'] = False

      avgpid = state['avgpid']

      if state['snoozeon']:
        state['heating'] = False
        for pin in he_pins:
          GPIO.output(pin,0)
        sleep(1)
      else:
        if avgpid >= 100 :
          state['heating'] = True
          for pin in he_pins:
            GPIO.output(pin, 1)
          sleep(1)
        elif avgpid > 0 and avgpid < 100:
          state['heating'] = True
          for pin in he_pins:
            GPIO.output(pin, 1)
          sleep(avgpid/100.)
          for pin in he_pins:
            GPIO.output(pin, 0)
          sleep(1-(avgpid/100.))
          state['heating'] = False
        else:
          for pin in he_pins:
            GPIO.output(pin, 0)
          state['heating'] = False
          sleep(1)

  finally:
    for pin in he_pins:
      GPIO.output(pin, 0)
    GPIO.cleanup()


def pid_loop(lock,state):
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
  print conf.SCK, conf.CS, conf.SO

  sensor = MAX31855.MAX31855(conf.SCK, conf.CS, conf.SO)
  print sensor.readState()
  pid = PID.PID(conf.Pc,conf.Ic,conf.Dc)
  with lock:
    pid.SetPoint = state['settemp']
  pid.setSampleTime(conf.sample_time*5)

  nanct=0
  i=0
  j=0
  pidhist = [0.,0.,0.,0.,0.,0.,0.,0.,0.,0.]
  avgpid = 0.
  temphist = [0.,0.,0.,0.,0.,0.,0.,0.,0.,0.]
  avgtemp = 0.
  with lock:
    lastsettemp = state['settemp']
  lasttime = time()
  sleeptime = 0
  iscold = True
  iswarm = False
  lastcold = 0
  lastwarm = 0

  cold = 100
  hot = 200
  if conf.celsius:
    cold = f_to_c(cold)
    hot = f_to_c(hot)

  try:
    while True : # Loops 10x/second
      tempc = sensor.readTempC()
      if isnan(tempc) :
        nanct += 1
        if nanct > 100000 :
          sys.exit
        continue
      else:
        nanct = 0
      with lock:
        state['curtemp'] = tempc
      if conf.celsius:
        temp = tempc
      else:
        temp = c_to_f(tempc)

      diff = avgtemp - temp
      if i > len(temphist) and abs(diff) > 20 and avgtemp > 10:
        temp = avgtemp # elimitate outliers

      temphist[i%len(temphist)] = temp
      avgtemp = sum(temphist)/float(len(temphist))

      if avgtemp < cold :
        lastcold = i

      if avgtemp > hot :
        lastwarm = i

      if iscold and (i-lastcold)*conf.sample_time > 60*15 :
        pid = PID.PID(conf.Pw,conf.Iw,conf.Dw)
        with lock:
          pid.SetPoint = state['settemp']
        pid.setSampleTime(conf.sample_time*5)
        iscold = False

      if iswarm and (i-lastwarm)*conf.sample_time > 60*15 :
        pid = PID.PID(conf.Pc,conf.Ic,conf.Dc)
        with lock:
          pid.SetPoint = state['settemp']
        pid.setSampleTime(conf.sample_time*5)
        iscold = True

      with lock:
        if state['settemp'] != lastsettemp :
          pid.SetPoint = state['settemp']
          lastsettemp = state['settemp']

      if i%10 == 0 :
        pid.update(avgtemp)
        pidout = pid.output
        pidhist[i/10%10] = pidout
        avgpid = sum(pidhist)/len(pidhist)

      with lock:
        state['i'] = i
        state['temp'] = round(temp,2)
        state['avgtemp'] = round(avgtemp,2)
        state['pidval'] = round(pidout,2)
        state['avgpid'] = round(avgpid,2)
        state['pterm'] = round(pid.PTerm,2)
        if iscold :
          state['iterm'] = round(pid.ITerm * conf.Ic,2)
          state['dterm'] = round(pid.DTerm * conf.Dc,2)
        else :
          state['iterm'] = round(pid.ITerm * conf.Iw,2)
          state['dterm'] = round(pid.DTerm * conf.Dw,2)
        state['iscold'] = iscold

      # print time(), state

      sleeptime = lasttime+conf.sample_time-time()
      if sleeptime < 0 :
        sleeptime = 0
      sleep(sleeptime)
      i += 1
      lasttime = time()

  finally:
    pid.clear


def pygame_gui(lock, state):
  import time
  import pygame
  import os

  import matplotlib
  matplotlib.use("Agg")
  import matplotlib.pyplot as plt
  plt.style.use("dark_background")
  import matplotlib.backends.backend_agg as agg

  LCD_WIDTH = 320
  LCD_HEIGHT = 240
  LCD_SIZE = (LCD_WIDTH, LCD_HEIGHT)

  os.putenv('SDL_FBDEV', '/dev/fb1')
  #os.putenv('SDL_MOUSEDRV', 'TSLIB')
  #os.putenv('SDL_MOUSEDEV', '/dev/input/touchscreen')

  pygame.init()
  pygame.display.set_mode(LCD_SIZE, pygame.DOUBLEBUF)

  pygame.mouse.set_visible(False)

  class Chart(object):
    def __init__(self, refresh_rate, span, state):
      self._state = state
      self._len = int(span / refresh_rate)
      with lock:
        self._data = [self._state['curtemp'] for x in xrange(self._len)]
        self._target = [self._state['settemp'] for x in xrange(self._len)]
      self._refresh_rate = refresh_rate

      self._figure = plt.figure(figsize=[4,3], dpi=80)
      self._axes = self._figure.add_subplot(111)
      self._data_plot, = self._axes.plot(self._data)
      self._target_plot, = self._axes.plot(self._target)
      self._figure.gca().get_xaxis().set_visible(False)

    def set_data(self, data):
      self._data = data

    def add_temp(self, temp):
      self._data.append(temp)
      with lock:
        self._target.append(self._state['settemp'])
      if len(self._data) > self._len:
        del self._data[0]
        del self._target[0]
      #print "Added temp:", temp
      self.plot()

    def plot(self):
      #print "Plotting:", self._data
      self._data_plot.set_ydata(self._data)
      self._target_plot.set_ydata(self._target)
      with lock:
        avgtemp = self._state['avgtemp']
        settemp = self._state['settemp']
      self._axes.set_ylim(min(avgtemp-5, settemp-5), max(avgtemp+5, settemp+5))
      self._axes.autoscale_view()
      canvas = agg.FigureCanvasAgg(self._figure)
      canvas.draw()
      size = canvas.get_width_height()
      renderer = canvas.get_renderer()
      raw_data = renderer.tostring_rgb()
      surf = pygame.image.fromstring(raw_data, size, "RGB")
      pygame.display.get_surface().blit(surf, (0,0))
      pygame.display.flip()
      #print "Plotting done"

    def run(self):
      crashed = False
      while not crashed:
        with lock:
          temp = self._state['avgtemp']
        self.add_temp(temp)
        for event in pygame.event.get():
          if event.type == pygame.QUIT:
            crashed = True
          time.sleep(self._refresh_rate)

  try:
    c = Chart(0.5, 15, state)
    c.run()
  finally:
    import sys
    pygame.quit()
    sys.exit()

def gpio_temp_control(lock, state):
  from gpiozero import Button

  def increase():
    print "increase"
    state['settemp'] += 0.1

  def decrease():
    print "decrease"
    state['settemp'] -= 0.1

  up = Button(17)
  up.when_pressed = increase
  down = Button(22)
  down.when_pressed = decrease

  return up, down


if __name__ == '__main__':
  from multiprocessing import Process, Manager, Lock
  from time import sleep
  from urllib2 import urlopen
  import config as conf

  lock = Lock()
  manager = Manager()
  pidstate = manager.dict()
  pidstate['snooze'] = conf.snooze
  pidstate['snoozeon'] = False
  pidstate['i'] = 0
  pidstate['settemp'] = conf.set_temp
  pidstate['avgpid'] = 0.
  pidstate['curtemp'] = 0.
  pidstate['heating'] = False
  pidstate['avgtemp'] = None

  up, down = gpio_temp_control(lock, pidstate)

  p = Process(target=pid_loop,args=(lock, pidstate))
  p.daemon = True
  p.start()

  h = Process(target=he_control_loop,args=(lock, pidstate))
  h.daemon = True
  h.start()

  gui = Process(target=pygame_gui, args=(lock, pidstate))
  gui.daemon = True
  gui.start()

  while p.is_alive and gui.is_alive and h.is_alive:
    try:
      with lock:
        print pidstate
      sleep(10)
    except:
      break

  p.terminate()
  h.terminate()
  gui.terminate()

  #pygame_gui(lock, pidstate) #Blocking
