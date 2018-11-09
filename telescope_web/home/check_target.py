from katpoint import Catalogue, Antenna, Timestamp, rad2deg, Target
import os
import time
# Limits             Az             El
#               150     -187    95      25
#                       =173




def check_target(OVST, tar,tmstmp=None, check=True):
    azel = []
    if isinstance(tar, str):
        target = OVST.catalogue[tar]
    if isinstance(tar, Target):
        target = tar

    if not target:
        raise ValueError("Target not in Catalogue")
        return
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
        except:
            pass
    return inRange
