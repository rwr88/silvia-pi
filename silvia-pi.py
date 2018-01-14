#!/usr/bin/python

def he_control_loop(lock,state):
  from heat import Heat

  try:
    heat_control = Heat(state)
    heat_control.run()
  except Exception as e:
    print e
  finally:
    print "----------------Closing heat control----------------"
    heat_control.cleanup()

def pid_loop(lock,state):
  from sensor import Sensor
  try:
    pid = Sensor(state)
    pid.run()
  except Exception as e:
    print e
  finally:
    print "--------------------Closing PID---------------------"
    pid.cleanup()


def pygame_gui(lock, state):
  from chart import Chart

  try:
    Chart.start_pygame()
    c = Chart(0.5, 30, state)
    c.run()
  except Exception as e:
    print e
  finally:
    print "--------------------Closing GUI---------------------"
    Chart.stop_pygame()

def gpio_temp_control(lock, state):
  from gpiozero import Button

  def increase():
    print "increase"
    state['settemp'] += 0.1

  def decrease():
    print "decrease"
    state['settemp'] -= 0.1

  def exit():
    import sys
    sys.exit()

  up = Button(17)
  up.when_pressed = increase
  down = Button(22)
  down.when_pressed = decrease
  kill = Button(27)
  kill.when_pressed = exit

  return up, down, kill


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

  up, down, kill = gpio_temp_control(lock, pidstate)

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
      print pidstate
      sleep(5)
    except:
      break

  p.terminate()
  h.terminate()
  gui.terminate()
