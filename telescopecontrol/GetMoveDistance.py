import math
from AzimuthElevationTransformations import elevationDegreeToLength

def getMoveDistance(coordinate, antennaSensor,initialPos=None, trackTargetModifications=False):
        '''Checks if the limit switch will be hit if it moves to Azimth Elevation Coordinates
        Make shure that the initial position is in range. If it is not in range, it will not move.
        Is usesd in :func: 'checkAbsoluteSequenceHitsLimitSwitch()'
    
        Params
        ------
        coordinate:  float #its easier to implement it with a single float
            elevation or azimuth coordinate
    
        antennaSensor: object of :class: 'Sensor' #its easier to implement it with a single object
            To get the current value of the object of :class: 'Sensor' 
            with and without rollover reset.

        initialPos: float
            If it is default=None, the 'positionWithoutRollover' of the object :class: 'Sensor' is used.
            Was mainly add to adopt the method for usage in :function: 'checkAbsoluteSequenceHitsLimitSwitch()'

        
        trackTargetModifications: bool
            Diables print command of the method. So that it is no problem if it is iterated through target which are not reachable.
            If the target is not in range the return value is '999999' instead of '0' 


        Retruns
        -------
        moveDistance: float
            The distance which it has to move incremental.
            If motion is not possible it returns '0' and if 'trackTargetModifications=True', it returns '999999'
        '''
        if antennaSensor.isElevation:
            if (coordinate>antennaSensor.params[0]) & (coordinate<antennaSensor.params[1]):
                return (elevationDegreeToLength(coordinate, antennaSensor.offset) - elevationDegreeToLength(antennaSensor.value(), antennaSensor.offset))
            else: 
                if trackTargetModifications:
                    return 999999
                else:
                    print 'Can not move in elevation position without hitting an elevation end switch'
                    return 0



        elif(initialPos==None):
            initialPos = antennaSensor.positionWithoutRollover

        # Distance to move
        distance = coordinate - initialPos
        # the limitiswitch will be hit by moving in negative direction
        if coordinate<(antennaSensor.params[0]): # coordinate is lower than the min value
            # Move positive if it is in range
            moveDistance = math.fmod(360 + distance, 360) # modulo operator
            # Check if end postition is higher than the max value
            if ((moveDistance + initialPos) > (antennaSensor.params[1])):
                if trackTargetModifications:
                    return 999999
                else:
                    print 'Can not move in azimuth position without hitting an azimuth end switch'
                    return 0.0
            else:
                return moveDistance
        # the limitiswitch will be hit by moving in positive direction
        elif coordinate>(antennaSensor.params[1]): # coordinate is higher than the max value
            #move negative if it is in range
            moveDistance = math.fmod(distance - 360, 360)
            # Check if end postition is lower than the min value
            if ((initialPos + moveDistance) < (antennaSensor.params[0])):
                if trackTargetModifications:
                    return 999999
                else:
                    print 'Can not move in azimuth position without hitting an azimuth end switch'
                    return 0.0
            else:
                return moveDistance 
        else:
            # it returns a the distance because it will not hit any limit switch
            return math.fmod(distance, 360)


