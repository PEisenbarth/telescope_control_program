# Intended for debugging issues (Contains all telescope control commands so that you don't need to start
# the whole control program)
import threading
import os
from functools import wraps
from Queue import Queue
from katpoint import Antenna, Catalogue, rad2deg
from datetime import datetime
import time
from .check_target import filter_catalogue
from optparse import OptionParser
import sys

class Vars(Queue):
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
        RTT = Antenna("Roof Top Telescope (Shed Side)", '51:45:34.5', '-1:15:34.8', 85)
        RTT2 = Antenna("Roof Top Telescope 2 (Stairs Side)", '51:45:34.6', '-1:15:34.9', 85)
        self.antennaList = [RTT, RTT2]
        self.active_antennas = [RTT, RTT2]
        self.halt = False
        self.catalogue = Catalogue(add_specials=True, add_stars=True)
        print 'Initialising Catalogues...'

        filedir = '/Users/eisenbarth/Desktop/telescope_control_repo/telescope_control_program/telescopecontrol'
        #
        # # Hipparcos Catalogue
        # filename = os.path.join(filedir, 'Catalogues/hipparcos.edb')
        # self.catalogue.add_edb(file(filename))
        #
        # CBASS Catalogue
        filename = os.path.join(filedir, 'Catalogues/CBASS_Catalogue.csv')
        self.catalogue.add(file(filename))
        #
        # # Messier Catalogue
        filename = os.path.join(filedir, 'Catalogues/MESSIER.edb')
        self.catalogue.add_edb(file(filename))
        self.update_time = None
        self.in_range = None

        # Checks which targets are in range of the telescopes. Depending on the size of the Catalogue, this can take
        # very long. That's why it is threaded. If the first loop was completed, the list will be shown on the website
        threading.Thread(target=self.check_in_range).start()

        print 'Initialization Done!'

    def check_in_range(self, loop=True):
        while loop:
            self.in_range = filter_catalogue(self)
            self.update_time = datetime.now().time().isoformat()[:8]
            if loop:
                time.sleep(60)



class RoachReadout():
    def __init__(self, mode):
        self.mode = mode
        self.katcp_port=7147
        self.boffiles = ['tut3.bof',                        #original design with an accu length 2^10
                         'cw_vers_2_2017_Apr_25_1221.bof',  #test()CW readout design with an accu length of 2^9
                         'tut3_hr_v4_2017_May_05_2026.bof'  #CW readout design with an accu length of 2^9
                         ]
        self.bitstream = self.boffiles[2]
        self.acc_len = 2 * (2 ** 28) / 1024
        self.gain = 0x0fffffff
        self.save = False
        self.p = OptionParser()
        self.p.set_usage('spectrometer.py <ROACH_HOSTNAME_or_IP> [options]')
        self.p.set_description(__doc__)
        self.p.add_option('-s', '--skip', dest='skip', action='store_true',
                     help='Skip reprogramming the FPGA and configuring EQ.')
        self.opts, self.args = self.p.parse_args(sys.argv[1:])

        self.roach = 'grasshopper'  # default value for wetton telescope
        self.fpga = None
        self.old_acc_n = None
        self.running = False # As long as readout is true, the data gets plotted
        self.plot_xlims = [13750, 13800]
        self.plot_ylims = [13750, 13800]
        self.filename = None


roach = RoachReadout('spectrum')
OVST = Vars()

# Decorator function that threads the decorated function
def threaded(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        th = threading.Thread(target=func, args=args, kwargs=kwargs)
        th.start()
    return wrapper


### general commands ###

def choose_telescopes(telescopes=None):
    OVST.active_antennas = []
    if not telescopes:
        OVST.active_antennas = OVST.antennaList
        return
    if not isinstance(telescopes, list):
        telescopes = [telescopes]
    for ant in telescopes:
        if ant in telescopes:
            OVST.active_antennas.append(ant)

    print ('active antennas: ', OVST.active_antennas)
def active_telescopes():
    return OVST.active_antennas

def show_telescopes():
    return OVST.antennaList

def halt_telescopes():
    OVST.halt = True

def clear_halt():
    OVST.halt = False

def clear_fault():
    print 'Fault cleared!'



### Moving Commands ###

@threaded
def move(az,el=None):
    pass

@threaded
def move_galactic(lat, long):
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
    OVST.queue.clear()

def mapping(mode, az_frame, el_frame, *args, **kwargs):
    pass

def current_track():
    return ['Capella', 120, '12:00:00', 'Raster']

def pending_tracks():
    return list(OVST.queue)

def delete_track(num=None):
    OVST.queue.remove(OVST.queue[num])
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
