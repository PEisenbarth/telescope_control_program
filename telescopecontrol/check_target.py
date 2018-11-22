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
    if isinstance(target, Target):
        target = target
    elif isinstance(target, str) and ',' in target:       # Check if target has format: e.g. 'azel, 30, 60'
        target = Target(target)
    elif isinstance(target, str):
        try:
            target = catalogue[target]
        except ValueError:
            raise ValueError("Target not in Catalogue")

    if not tmstmp:
        tmstmp = Timestamp()

    for antenna in antennas:
        ae = target.azel(timestamp=tmstmp, antenna=antenna)
        azel.append([rad2deg(ae[0]), rad2deg(ae[1])])

    az = [item[0] for item in azel]
    el = [item[1] for item in azel]
    if check:
        if all((OVST.az_limit[1]-2 < i < OVST.az_limit[0]+2 for i in az)) or all(i < OVST.el_limit[0] for i in el):
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

def filter_catalogue(OVST):
    '''

    :return: list with all targets, which are in telescope range
    '''
    inRange = []
    for tar in OVST.Catalogue.iternames():
        target = [tar]
        try:
            azel = check_target(OVST, tar)
            target.append(round(azel[0][0], 4))
            target.append(round(azel[0][1], 4))
            inRange.append(target)
        except:
            pass
    return inRange


def dms2dd(degree):
    """   
    Converts a degree angle from degrees minutes seconds to degrees in decimal notation
    :param      degree: str: 'DEG:MIN:SEC"
    :return:    degree in decimal notation
    """
    deg_dec = 0
    degree_list = degree.split(':')
    for i, deg in enumerate(degree_list):
        if float(degree_list[0])<0 and i: # Change sign of all values if first value is negativ
            deg = float(deg)*-1
        else:
            deg = float(deg)
        deg_dec += deg/(60**i)
    return deg_dec
