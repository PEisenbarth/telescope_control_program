from telescopecontrol import OVST
import threading
import os
import sys
from TrackTarget import TrackTarget
from ObservationMode import obs_mode
import time
from functools import wraps

# Decorator function that threads the decorated function
def threaded(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        th = threading.Thread(target=func, args=args, kwargs=kwargs)
        th.start()
    return wrapper


### general commands ###

def choose_telescopes(telescopes = None):
    # choose wich telescopes you want to use
    OVST.choose_telescopes(telescopes)

def active_telescopes():
    return OVST.active_antennas

def show_telescopes():
    return OVST.antennaList

def halt_telescopes():
    OVST.haltTelescopes()

def clear_fault(rollover=None):
    OVST.clearTelescopeFault(rollover)

def clear_halt():
    OVST.clearTelescopeHalt()


### Moving Commands ###

@threaded
def move(az,el=None):
    '''
    :param az:  azimuth if float, right ascension if string (format: 'HH:MM:SS') 
    :param el:  elevation if float, declination if string(in degrees)
    '''
    OVST.move_to_pos(az, el)

@threaded
def home():
    OVST.moveHomePosition()

@threaded
def safety():
    OVST.moveSavetyPosition()

### Tracking Commands ###

trackq = TrackTarget(OVST)

def track(target, duration=2, GoOff=None, startTime=None, mode=None):
    """
    :param target:      str 
                        name of the target (e.g. 'HIP72603')
    :param duration:    float 
                        duration of the observation in minutes    
    """
    trackq.track(targetname=target, observationDuration=duration, GoOffAzEl=GoOff, startTime=startTime, mode=mode)

def stop_track():
    trackq.halt = True
    if trackq.waiting:
        trackq.th.cancel()
        # Delete the current track in the Queue
        t = trackq.track_Queue.get()
        trackq.running = False
        print t
    OVST.haltTelescopes()

def continue_track():
    trackq.halt = False
    if not trackq.running and not trackq.track_Queue.empty():
        target = trackq.track_Queue.get()
        track(target[0],target[1], target[2], startTime=None)
        print str(target[0]),str(target[1]), str(target[2])

def stop_all_tracks():
    # stop and delete all tracks and move telescopes to home position
    trackq.halt = True
    trackq.stop_all = True
    # If thread is waiting to start, cancel it
    if trackq.waiting:
        trackq.th.cancel()
        tracks = trackq.track_Queue.qsize()
        trackq.track_Queue.queue.clear()
        print 'All tracks (%i) got cleared' % tracks
        trackq.running = False
        home()
        trackq.stop_all = False
        trackq.halt = False
    OVST.haltTelescopes()

def mapping(mode, az_frame, el_frame, *args, **kwargs):
    return obs_mode(mode, az_frame, el_frame, *args, **kwargs)

def current_track():
    try:
        return trackq.current_track
    except AttributeError:
        return None

def pending_tracks():
    if trackq.track_Queue.empty():
        return None
    pending = list(trackq.track_Queue.queue)
    for i, pen in enumerate(pending):
        if pen[5]:
            pending[i].append(pen[5].mode)    # Add the name of the mode
    return pending

def delete_track(num=None):
    if not isinstance(num, int):
        print 'Please type in the number of the track you want to delete'
        for i, t in enumerate(trackq.track_Queue.queue):
            print i, t
        return
    try:
        t = trackq.track_Queue.queue[num]
        trackq.track_Queue.queue.remove(t)
        print '%s got deleted!' % (t,)
    except (ValueError, IndexError):
        print 'Track index not in list'
        for i, t in enumerate(trackq.track_Queue.queue):
            print i, t

# def start_server():
#     sys.path.append('/home/telescopecontrol/PhilippE/telescope_control/telescope_web')
#     from telescope_web import run
#     run.run_server()

### DAQ ###

def position():
    """
    :return:    list
                position data of every telescope (format: [[az1, el1], [az2, el2], ...])
    """
    return OVST.get_pos()

@threaded
def start_daq(name=None):
    OVST.daq_pos(name)


def stop_daq():
    OVST.daq = False


def window():
    OVST.startControlWindow()# Decorator function that threads the decorated function



### Quit and Reset Functions ###

def hard_reset():
    if not OVST.inHomePosition:
        OVST.moveHomePosition()
    print('\nrestarting the telescope telescopecontrol program\n')
    os.execl(sys.executable, sys.executable, *sys.argv)

@threaded
def quit_tel():
    # exit the telescope control program safely
    if not OVST.inHomePosition:
        print('Telescopes are not in home position. Moving to home position...\n')
        home()
        while not OVST.inHomePosition:
            time.sleep(1)
    else:
        pass
    with open(os.path.dirname(__file__)+'/Catalogues/.rollover', 'w') as csv:
        csv.write('Shutdown: properly')
    OVST.closeAllModbusConnections()
    print('\n\nTelescope telescopecontrol program exited.')
    os._exit(0)

def quit():
    quit_tel()

def exit():
    quit_tel()
