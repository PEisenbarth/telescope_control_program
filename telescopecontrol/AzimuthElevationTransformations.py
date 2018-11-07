import math


def elevationDegreeToLength(degree, offset):
        '''Converts the elevation value from lenght in degrees.
        Used mainly in :func: 'getMoveDistance()' and :func: 'moveContinuousAdapter'.

        explain the equation
        --------------------
        - Everything under the squareroot is the result of calculations
        - (-885) is the length of the box of the zylinder
        - a minus in front of the equation inverts the result, because the controller uses negative values
        
        params
        ------
        degree: float
            elevation in degree

        offset: float
            The offset of the encoder which had to be hard coded because it is too big.            
       
        returns
        -------
        length: float
            Value in millimeter

        '''
        degree = 90 - degree
        return (-(math.sqrt(1422200 - 861472.1584 * math.cos(math.asin(float(411)/565) + (1/float(180)) * degree * math.pi - math.atan2(3,38)))-885.205)) + offset 

def azimuthOffset(azimuth, offset):
    '''Calculates the azimuth considering the offset. 
    It is a value in range between 0 and 360.
    Used mainly in :func: 'getMoveDistance()' and :func: 'moveContinuousAdapter'.

    params
    ------
    azimuth: float 
        The azimuth value

    offset: float
        The offset value

    returns 
    -------
    a float in range of 0..360
    '''
    return (azimuth + 360 + offset) % 360 