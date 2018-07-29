#!/usr/bin/python

import logging
from datetime import datetime as dt

logger = logging.getLogger('silvia')
logger.setLevel(logging.INFO)
fh = logging.FileHandler('logs/%s.log' % dt.strftime(dt.now(), '%Y-%m-%d'))
fh.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh)

def he_control_loop(lock,state):
  from heat import Heat

  try:
    heat_control = Heat(state)
    heat_control.run()
  except Exception as e:
    logger.error(e)
  finally:
    logger.info("----------------Closing heat control----------------")
    heat_control.cleanup()

def pid_loop(lock,state):
  from sensor import Sensor
  try:
    pid = Sensor(state)
    pid.run()
  except Exception as e:
    logger.error(e)
  finally:
    logger.info("--------------------Closing PID---------------------")
    pid.cleanup()


def pygame_gui(lock, state):
  from chart import Chart

  try:
    Chart.start_pygame()
    c = Chart(0.5, 30, state)
    c.run()
  except Exception as e:
    logger.error(e)
  finally:
    logger.info("--------------------Closing GUI---------------------")
    Chart.stop_pygame()

def gpio_temp_control(lock, state):
  from gpiozero import Button
  from time import time

  def increase():
    logger.info("Increase button pressed")
    state['settemp'] += 0.1

  def decrease():
    logger.info("Decrease button pressed")
    state['settemp'] -= 0.1

  def exit():
    logger.info("Exit button pressed")
    state['exit'] = True

  def set_boost():
    logger.info("Heating for 5 seconds")
    state['boost'] = time() + 5

  up = Button(17)
  up.when_pressed = increase
  down = Button(22)
  down.when_pressed = decrease
  kill = Button(27)
  kill.when_pressed = exit
  boost = Button(23)
  boost.when_pressed = set_boost

  return up, down, kill, boost

def print_exception(*info):
  import traceback
  tb = ''.join(traceback.format_exception(*info))

  logger.error("Uncaught error: ")
  logger.error(tb)


if __name__ == '__main__':
  from multiprocessing import Process, Manager, Lock
  from time import sleep
  from urllib2 import urlopen
  import config as conf
  import sys
  from formatter import PartialFormatter

  sys.excepthook = print_exception
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
  pidstate['exit'] = False
  pidstate['pterm'] = None
  pidstate['iterm'] = None
  pidstate['dterm'] = None
  pidstate['sterm'] = None
  pidstate['pidval'] = None
  pidstate['boost'] = 0
  logger.info('Main process started')

  up, down, kill, boost = gpio_temp_control(lock, pidstate)

  logger.info('Buttons assigned')

  logger.info('Starting PID loop')
  p = Process(target=pid_loop,args=(lock, pidstate))
  p.daemon = True
  p.start()

  logger.info('Starting heat control')
  h = Process(target=he_control_loop,args=(lock, pidstate))
  h.daemon = True
  h.start()

  logger.info('Starting GUI')
  gui = Process(target=pygame_gui, args=(lock, pidstate))
  gui.daemon = True
  gui.start()

  logger.info('Starting status loop')
  fmt = PartialFormatter()
  dir(fmt)
  while p.is_alive and gui.is_alive and h.is_alive and not pidstate['exit']:
    try:
      print fmt.format('P: {pterm:7.2f}\tI: {iterm:7.2f}\tD: {dterm:7.2f}\tS: {sterm:7.2f}\tOut: {pidval:7.2f}\tTemp: {avgtemp:7.2f}', **pidstate)
      sleep(1)
    except KeyboardInterrupt:
      logger.error('Keyboard interrupt, exiting')
      break
    except Exception as e:
      logger.error('Error in status loop:')
      logger.error(str(e))
      break

  logger.info('Killing PID process')
  p.terminate()
  logger.info('Killing heat control process')
  h.terminate()
  logger.info('Killing GUI process')
  gui.terminate()
  p.join()
  h.join()
  gui.join()

  logging.info('All threads joined, exiting')
