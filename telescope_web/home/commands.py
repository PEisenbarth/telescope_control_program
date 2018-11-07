import threading
import os
import sys
import time
from functools import wraps
from Queue import Queue

class Q(Queue):
    def __init__(self):
        Queue.__init__(self)
        self.put(['Kochab', 40, None, '14:30:00', 20, 'Pong'])
        self.put(['Sun', 10, None, '16:10:00', 20, 'Raster'])
        self.put(['Capella', 20, None, '11:10:00', 20, 'Lissajous'])
        self.put(['Kochab', 40, None, '14:32:00', 20, 'Pong'])
        self.put(['Sun', 10, None, '16:12:00', 20, 'Raster'])
        self.put(['Capella', 20, None, '11:12:00', 20, 'Lissajous'])
        self.put(['Kochab', 40, None, '14:35:00', 20, 'Pong'])
        self.put(['Sun', 10, None, '16:15:00', 20, 'Raster'])
        self.put(['Capella', 20, None, '11:15:00', 20, 'Lissajous'])

q = Q()
print 'Queue initialised!!'
# Decorator function that threads the decorated function
def threaded(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        th = threading.Thread(target=func, args=args, kwargs=kwargs)
        th.start()
    return wrapper


### general commands ###

def choose_telescopes(telescopes = None):
    pass
def active_telescopes():
    pass
def show_telescopes():
    pass
def halt_telescopes():
    pass
def clear_fault():
    pass

### Moving Commands ###

@threaded
def move(az,el=None):
    pass
@threaded
def home():
    pass
@threaded
def safety():
    pass
### Tracking Commands ###


def track(target, duration=2, GoOff=None, startTime=None, mode=None):
    pass

def stop_track():
    pass

def continue_track():
    pass

def stop_all_tracks():
    q.queue.clear()

def mapping(mode, az_frame, el_frame, *args, **kwargs):
    pass

def current_track():
    return ['Capella', 120, '12:00:00', 'Raster']

def pending_tracks():
    return list(q.queue)


def delete_track(num=None):
    q.queue.remove(q.queue[num])
# def start_server():
#     sys.path.append('/home/telescopecontrol/PhilippE/telescope_control/telescope_web')
#     from telescope_web import run
#     run.run_server()

### DAQ ###

def position():
    pass
@threaded
def start_daq(name=None):
    pass

def stop_daq():
    pass

def window():
    pass


### Quit and Reset Functions ###

def hard_reset():
    pass
@threaded
def quit_tel():
    pass
def quit():
    quit_tel()

def exit():
    quit_tel()
