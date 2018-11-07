from katpoint import Catalogue, Antenna, Timestamp, rad2deg, Target
import os
import time
# Limits             Az             El
#               150     -187    95      25
#                       =173

RTT = Antenna("Roof Top Telescope (Shed Side)", '51:45:34.5', '-1:15:34.8', 85)
RTT2 = Antenna("Roof Top Telescope 2 (Stairs Side)", '51:45:34.6', '-1:15:34.9', 85)  # height is not exact

antennalist = [RTT, RTT2]

catalogue = Catalogue(add_specials=True, add_stars=True)
print 'Initialising Catalogues...'

# Hipparcos Catalogue
filedir = '/home/telescopecontrol/PhilippE/telescope_control/telescopecontrol'

filename = os.path.join(filedir, 'Catalogues/hipparcos.edb')
catalogue.add_edb(file(filename))

# CBASS Catalogue
filename = os.path.join(filedir, 'Catalogues/CBASS_Catalogue.csv')
catalogue.add(file(filename))

# Messier Catalogue
filename = os.path.join(filedir, 'Catalogues/MESSIER.edb')
catalogue.add_edb(file(filename))

print 'Initialization Done!'


def check_target(tar,tmstmp=None):
    azel = []
    if isinstance(tar, str):
        target = catalogue[tar]
    if isinstance(tar, Target):
        target = tar

    if not target:
        raise ValueError("Target not in Catalogue")
        return
    for antenna in antennalist:
        ae = target.azel(timestamp=tmstmp,antenna=antenna)
        azel.append((rad2deg(ae[0]), rad2deg(ae[1])))

    az = [item[0] for item in azel]
    el = [item[1] for item in azel]
    if all((150 < i < 173 for i in az)) or all(i < 25 for i in el):
        #print 'target cannot get focused (target at azimuth %.2f and elevation %.2f)\n' \
              #'Allowed limits: az no in range of 150-173 and elevation > 25'%(az, el)
        raise LookupError('target cannot get focused (target at azimuth %.2f and elevation %.2f).\n Allowed limits: az no in range of 150-173 and elevation > 25'%(azel[0][0], azel[0][1]))

    else:
        return azel     #format: [(az1, el1), (az2, el2), ...]

def check_available(targ):
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