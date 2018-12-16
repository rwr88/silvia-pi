#!/usr/bin/python

import time
import pygame
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.style.use("dark_background")
import matplotlib.backends.backend_agg as agg

import logging
logger = logging.getLogger('silvia.gui')

LCD_WIDTH = 320
LCD_HEIGHT = 240
LCD_SIZE = (LCD_WIDTH, LCD_HEIGHT)

class Chart(object):
  def __init__(self, refresh_rate, span, state):
    self._last_on_state = None
    logger.info('GUI constructor')
    self._state = state
    self._len = int(span / refresh_rate)
    #while self._state['temp'] == 0.0:
    #  time.sleep(0.1)
    self._data = [self._state['temp'] for x in xrange(self._len)]
    self._target = [self._state['settemp'] for x in xrange(self._len)]
    self._refresh_rate = refresh_rate

    self._figure = plt.figure(figsize=[4,3], dpi=80)
    self._axes = self._figure.add_subplot(111)
    self._axes.grid(linestyle='dotted')

    logger.info('Plotting initial data')
    self._data_plot, = self._axes.plot(self._data)
    self._target_plot, = self._axes.plot(self._target)
    self._figure.gca().get_xaxis().set_visible(False)
    logger.info('Constructor done')
    state['gui_on'] = True

  @staticmethod
  def start_pygame():
    os.putenv('SDL_FBDEV', '/dev/fb1')
    #os.putenv('SDL_MOUSEDRV', 'TSLIB')
    #os.putenv('SDL_MOUSEDEV', '/dev/input/touchscreen')
    pygame.init()
    pygame.display.set_mode(LCD_SIZE, pygame.DOUBLEBUF)
    pygame.mouse.set_visible(False)

  @staticmethod
  def stop_pygame():
    pygame.quit()

  def set_data(self, data):
    self._data = data

  def add_temp(self, temp):
    self._data.append(temp)
    self._target.append(self._state['settemp'])
    if len(self._data) > self._len:
      del self._data[0]
      del self._target[0]
    self.plot()

  def plot(self):
    self._data_plot.set_ydata(self._data)
    self._target_plot.set_ydata(self._target)
    avgtemp = self._state['avgtemp']
    settemp = self._state['settemp']
    self._axes.set_ylim(min(self._data+self._target)-3, max(self._data+self._target)+3)
    self._axes.autoscale_view()
    canvas = agg.FigureCanvasAgg(self._figure)
    canvas.draw()
    size = canvas.get_width_height()
    renderer = canvas.get_renderer()
    raw_data = renderer.tostring_rgb()
    surf = pygame.image.fromstring(raw_data, size, "RGB")
    pygame.display.get_surface().blit(surf, (0,0))
    pygame.display.flip()

  def run(self):
    crashed = False
    try:
      while not crashed:
        if self._last_on_state != self._state['on']:
          color = 'green' if self._state['on'] else 'red'
          self._target_plot.set_color(color)
          self._last_on_state = self._state['on']
        temp = self._state['temp']
        self.add_temp(temp)
        for event in pygame.event.get():
          if event.type == pygame.QUIT:
            crashed = True
          time.sleep(self._refresh_rate)
    except Exception as e:
      logger.error(e)
    except KeyboardInterrupt:
      logger.info('User interrupted process, exiting GUI')
    logger.info('GUI exiting run() loop')
