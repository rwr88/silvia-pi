import time
import pygame
from pygame.locals import *
import os
import sys
import signal

import matplotlib
matplotlib.use("Agg")
import matplotlib.backends.backend_agg as agg
import pylab

LCD_WIDTH = 320
LCD_HEIGHT = 240
LCD_SIZE = (LCD_WIDTH, LCD_HEIGHT)
 
os.putenv('SDL_FBDEV', '/dev/fb1')
#os.putenv('SDL_MOUSEDRV', 'TSLIB')
#os.putenv('SDL_MOUSEDEV', '/dev/input/touchscreen')

pygame.init()
pygame.display.set_mode(LCD_SIZE, DOUBLEBUF)

#pygame.mouse.set_visible(False)

class Chart(object):
    def __init__(self, refresh_rate, span, state):
        self._data = []
        self._len = span / refresh_rate
        self._refresh_rate = refresh_rate
        self._state = state

    def set_data(self, data):
        self._data = data

    def add_temp(self, temp):
        self._data.append(temp)
        if len(self._data) > self._len:
            del SELF._data[0]
        print "Added temp:", temp
        self.plot()

    def plot(self):
        print "Plotting:", self._data
        fig = pylab.figure(figsize=[4, 3], dpi=80)
        ax = fig.gca()
        ax.plot(self._data)

        canvas = agg.FigureCanvasAgg(fig)
        canvas.draw()
        size = canvas.get_width_height()
        renderer = canvas.get_renderer()
        raw_data = renderer.tostring_rgb()
        surf = pygame.image.fromstring(raw_data, size, "RGB")
        pygame.display.get_surface().blit(surf, (0,0))
        pygame.display.flip()
        print "Plotting done"

    def run(self):
        crashed = False
        while not crashed:
            self.add_temp(self._state['avgtemp'])
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    crashed = True
            time.sleep(self._refresh_rate)

if __name__ == "__main__":
    chart = Chart(1, 10, {'avgtemp': 18})
    chart.set_data([18, 17.5, 18, 18, 18, 18.5, 18])
    chart.plot()
    while True:
        time.sleep(1)
