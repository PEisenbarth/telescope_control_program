from katpoint import Catalogue, Antenna, Timestamp, rad2deg, Target, construct_azel_target, deg2rad
import os
import time
from Queue import Queue
import threading
from datetime import datetime
# Limits             Az             El
#               150     -187    95      25
#                       =173


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

        print 'Initialization Done!'




OVST = Vars()


def check_target(OVST, tar, tmstmp=None, check=True):
    azel = []
    if isinstance(tar, str):
        target = OVST.catalogue[tar]
    if isinstance(tar, Target):
        target = tar

    if not target:
        raise ValueError("Target not in Catalogue")
        return

    if tmstmp and len(tmstmp) == 5:
        tmstmp += ':00'

    if tmstmp and len(tmstmp) == 8:
        print len(tmstmp)
        tmstmp = str(datetime.now().date()) + ' ' + tmstmp

    for antenna in OVST.antennaList:
        ae = target.azel(timestamp=tmstmp, antenna=antenna)
        azel.append((rad2deg(ae[0]), rad2deg(ae[1])))

    az = [item[0] for item in azel]
    el = [item[1] for item in azel]
    if check:
        if all((148 < i < 175 for i in az)) or all(i < 26 for i in el):
            #print 'target cannot get focused (target at azimuth %.2f and elevation %.2f)\n' \
                  #'Allowed limits: az no in range of 150-173 and elevation > 25'%(az, el)
            raise LookupError('target cannot get focused (target at azimuth %.2f and elevation %.2f).\n Allowed limits: az no in range of 150-173 and elevation > 25'%(azel[0][0], azel[0][1]))
    return azel     #format: [(az1, el1), (az2, el2), ...]

def check_available(OVST, targ):
    inRange = False
    i =0
    tmsp = time.time()
    while not inRange:
        try:
            if tmsp-time.time() > 60*60*24:     # stop if the target won't be in range the next 24h
                print "%s won't be in range the next 24h"%targ
                break
            tmsp = time.time()+i*60
            i += 1
            azel = check_target(targ, tmstmp=tmsp)
            inRange = True
        except ValueError:
            print "Target '%s' not in Catalogue!" % targ
            break
        except LookupError:     # target can't be focused at this tmsp, repeat the loop
            pass
    if inRange == True:
        print 'In range on %s \tat position az: %.2f, el: %.2f' %(time.ctime(tmsp)[0:16], azel[0][0], azel[0][1])
        return azel

def filter_catalogue(OVST):
    '''

    :return: list with all targets, which are in telescope range
    '''
    inRange = []
    for tar in OVST.catalogue.iternames():
        target = [tar]
        try:
            azel = check_target(OVST, tar)
            target.append(round(azel[0][0], 4))
            target.append(round(azel[0][1], 4))
            inRange.append(target)
            threading.Thread(target=self.check_in_range).start()

        except:
            pass
    return inRange

if __name__ == '__main__':
    target = construct_azel_target(deg2rad(30), deg2rad(50))
    print check_target(OVST, target)