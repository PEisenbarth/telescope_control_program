from katpoint import Target, rad2deg, Timestamp
import time
# Limits             Az             El
#               150     -187    95      25
#                       =173


def check_target(OVST, target, tmstmp=None, check=True):
    '''
    
    :param tar:         str or object of class Target
                        if string: searches for the target in catalogue
    :param antennas:    list
                        list of antenna objects of class Antenna
    :param catalogue:   Catalogue
    :param tmstmp:      Timestamp
    :return:            list with position tuples
                        [(az1, el1), (az2, el2), ...]
    '''
    antennas = OVST.active_antennas
    catalogue = OVST.Catalogue

    azel = []
    if isinstance(target, str):
        target = catalogue[target]
    if isinstance(target, Target):
        target = target

    if not tmstmp:
        tmstmp = Timestamp()

    if not target:
        raise ValueError("Target not in Catalogue")

    for antenna in antennas:
        ae = target.azel(timestamp=tmstmp, antenna=antenna)
        azel.append([rad2deg(ae[0]), rad2deg(ae[1])])

    az = [item[0] for item in azel]
    el = [item[1] for item in azel]
    if check:
        if all((OVST.az_limit[1] < i < OVST.az_limit[0] for i in az)) or all(i < OVST.el_limit[0] for i in el):
            # print 'target cannot get focused (target at azimuth %.2f and elevation %.2f)\n' \
            #  'Allowed limits: az no in range of 150-173 and elevation > 25'%(az, el)
            raise LookupError('target cannot get focused at % s (target at azimuth %.2f and elevation %.2f).\n '
                          'Allowed limits: az not in range of 150-173 and elevation > 25' %
                          (tmstmp.local()[11:19], azel[0][0], azel[0][1]))

    return azel     # format: [(az1, el1), (az2, el2), ...]


def check_available(OVST, targ):
    in_Range = False
    i =0
    tmsp = time.time()
    while not in_Range:
        try:
            if tmsp-time.time() > 60*60*24:     # stop if the target won't be in range the next 24h
                print "%s won't be in range the next 24h" % targ
                break
            tmsp = time.time()+i*60
            i += 1
            azel = check_target(OVST, targ, tmstmp=tmsp)
            in_Range = True
        except ValueError:
            print "Target '%s' not in Catalogue!" % targ
            break
        except LookupError:     # target can't be focused at this tmsp, repeat the loop
            pass
    if in_Range:
        print 'In range on %s \tat position az: %.2f, el: %.2f' %(time.ctime(tmsp)[0:16], azel[0][0], azel[0][1])
        return azel