from katpoint import *
import numpy as np

def obs_mode(mode, az_width=0, el_height=0, *args, **kwargs):
    if mode not in ['None', 'RasterDiscrete', 'Raster', 'Lissajous', 'Pong', 'Line']:
        raise ValueError("Mode '%s' not available" % mode)
    mapping_mode = ObservationMode(mode=mode, az_frame=az_width, el_frame=el_height, *args, **kwargs)
    return mapping_mode


class ObservationMode(object):
    def __init__(self, startTimeStamp=None, azGoOff=0, elGoOff=0, periodeGoOff=5,
                 goOffSequence=["+el", "-el", "+az", "-az"],
                 az_frame=0, el_frame=0, timeStampToCheck=None, **kwargs):
        ''' This method calculates the positions for different observation modes. 
        It works like vectors. The telescope points and this method makes the go Off on the target.
        Note that the crosses are independent from the observation duration. 
        When the observation duration is over the offset process of the crosses can be on any position.

        Through the 'goOffSequence' is worked in the time 'periodeGoOff' for the angles 'azGoOff' and 'elGoOff'.
        The observation duration has an impact on the second method like making a raster.
        Especially by making a discrete raster the 'observationDuration' divided by the points is the time in which a 
        raster point is used.

        params
        ------
        startTimeStamp: float, string, :class:`ephem.Date` object or None
            Timestamp, in various formats (if None, defaults to now)

        azGoOff: float
            The angle which the azimuth pointing goes of the targets (when doing a cross)

        elGoOff: float
            The angle which the elevation pointing goes of the targets (when doing a cross)

        periodeGoOff: float 
            The time in minutes in which the pointing goes off in in azimuth 
            and elevation each in positive and negative direction.

        goOffSequence: list of strings
            defines in which order which direction is driven during a period.
            It is only "+el","-el","+az","-az" allowed. (Not case sensitive).

        az_frame: float 
            The angle in azimuth direction which defines the frame in which all points are.

        el_frame: float
            The angle in elevation direction the frame in which all points are. 


        timeStampToCheck: object of :class: 'Timestamp'
            It calculates the current Offset for a special Timestamp. If this is zero it uses the current Timestamp().
            Because of this calculation every real targeted point has to be calculated. Otherwise it would be possible 
            to hit a limit switch.
            It is used for :meth: 'checkAbsoluteSequenceHitsLimitSwitch'.

        kwargs:
            mode: string
                One of the implemented modes. Crosses can be made simultaneously. They are:

            to 'RasterDiscrete'
                Drive to discrete points. The frame is defined by 'az_frame' and 'el_frame'.

                pointsAz: int
                    The amount of raster points in azimuth direction.
                    The angle between two points is angleConstXX devided by pointsXX-1.

                pointsEl: int
                    The amount of rasterpoints in azimuth direction.
                    The angle between two points is angleConstXX devided by pointsXX-1.

            to 'Raster'
                Drive through a raster in a given time. The frame is defined by 'az_frame' and 'el_frame'.

                rasterLines: int
                    The number of lines of the raster.

                observationDuration: float
                    The time in which the raster is tracked.   

            to 'Raster' or 'RasterDiscrete'
                firstAz: bool
                    Move first in azimuth or elevation.
                    A example for a 3x3 raster.
                    True:   1 2 3       False   1 6 7
                            6 5 4               2 5 8
                            7 8 9               3 4 9

            to 'Lissajous'
                Move Lissajous figures. Therefore the circuit frequencies should not be integral multiple, e.g. 2 and 4.
                It is implemented with sine function. The amplitude is defined by 'az_frame' and 'el_frame'.

                omegaAz: int or float
                    Circuit frequency of azimuth off pointing

                omegaEl: int or float
                    Circuit frequency of elevation off pointing

                phiAz: float
                    Phase shift in azimuth

                phiEl: float
                    Phase shift in azimuth

            to 'Pong'
                Move into a direction until a point is out of the frame. The path is mirrored on the fame like a light ray.
                If the initial values are chosen appropriately, all points in the frame are covered.                
                The frame is defined by 'az_frame' and 'el_frame'.

                startAz: float
                    The start position in azimuth

                startEl: float
                    The start position in azimuth

                startAngle: float
                    The start angle. It is zero in positive azimuth direction. The angle is counted positive counter clockwise.

                velocity: float
                    The velocity of the track. Azimuth and elevation velocity is the cosine and sine of this value.
                    
            to 'Lines'
                Move along a given path of positions
                :param linePoints: list with at least two points, e.g. [[30, 60], [30, 70], [35,70], [35,65], [30,65]]
                :param observationDuration: duration of the obvservation

        attributes
        ----------
        currentOff: list of 2 floats
            index 0 is the azimuth Off
            index 1 is the elevation Off
            it is used to go off the target 
        '''
        try:
            self.startTimeStamp = Timestamp(startTimeStamp)  # if it is None it uses the current time
        except ValueError:
            print "The Start Timestamp has the wrong format. It uses the current Time as StarttimeStamp.\n It was entered: '%r'" % startTimeStamp
            self.startTimeStamp = Timestamp()

        self.timeStampToCheck = timeStampToCheck

        # Transform minutes in seconds
        self.periodeGoOff = periodeGoOff * 60
        # The absolute value of off values in a list
        self.goOffMax = [azGoOff, elGoOff]
        # The sequence
        self.goOffSequence = goOffSequence

        self.az_frame = az_frame
        self.el_frame = el_frame

        for key, val in kwargs.items():
            # Deletes kwargs with None values (Necessary for the website)
            if val == None:
                kwargs.pop(key)

        self.mode = kwargs.get('mode', "None")  # The modus which should be applied
        self.pointsAz = kwargs.get('pointsAz', 3)  # Number of points by raster discrete mode in azimuth
        self.pointsEl = kwargs.get('pointsEl', 3)  # Number of points by raster discrete mode in elevation
        self.rasterLines = kwargs.get('rasterLines', 4)  # Number of lines by driving a raster
        self.firstAz = kwargs.get('firstAz', True)  # azimuth or elevation is first driven by making a raster
        self.observationDuration = kwargs.get('observationDuration', 20) * 60
        self.omegaAz = kwargs.get('omegaAz', 3)  # Circuit frequency by lissajous mode in azimuth
        self.omegaEl = kwargs.get('omegaEl', 2)  # Circuit frequency by lissajous mode in elevation
        self.phiAz = kwargs.get('phiAz', 0)  # Phase shift by lissajous mode in azimuth
        self.phiEl = kwargs.get('phiEl', 0)  # Phase shift by lissajous mode in elevation
        self.startAz = kwargs.get('startAz', 0)  # Start point by pong mode in azimuth
        self.startEl = kwargs.get('startEl', 0)  # Start point by pong mode in elevation
        self.startAngle = kwargs.get('startAngle', 30)  # Start angle in degree by pong mode; azimuth is zero degree,
        # counter clockwise is positive direction
        self.velocity = kwargs.get('velocity', 1)  # Velocity by pong mode

        self.linepoints = kwargs.get('linePoints', None)  # Points for a line track
        self.azElRasterList = []
        self.createRasterDiscreteList()  # fills 'azElRasterList'
        self.createRaster()  # Calculates several values
        if self.mode == 'Line':
            self.init_line_track()

    @property
    def currentOff(self):
        '''This property contatains and calculates the distance 
        to the true pointing point at the current time.
        '''

        if self.mode == "RasterDiscrete":  # pointsAz, pointsEl, observationDuration, firstAz,
            return np.add(self.makeCrosses(), self.makeRasterDiscrete())
        if self.mode == "Raster":  # rasterLines, observationDuration, firstAz
            return np.add(self.makeCrosses(), self.makeRaster())
        elif self.mode == "Lissajous":  # omegaAz,omegaEl,phiAz,phiEl
            return np.add(self.makeCrosses(), self.makeLissajous())
        elif self.mode == "Pong":  # startAz,startEl,startAngle,velocity
            return np.add(self.makeCrosses(), self.makePong())
        elif self.mode == 'Line':
            return np.add(self.makeCrosses(), self.trackLine())
        else:
            return self.makeCrosses()

    def makeCrosses(self):
        '''Make Crosses on the target

        attributes
        ----------        
        _time: float
            It is mainly a helper. Handle it carefully. because it is modified in 
            the :meth: 'currentDirection' for further use in :meth: 'distance'

        direction: string
            It is a string of the :list: 'goOffSequence', which indicates the current direction

        returns
        -------
        list of two floats
            the first represents the azimuth offset and the second the elevation offset
        '''
        # current offset, index 0 is azimuth, 1 is elevation
        # attention time is modified during the process
        if not isinstance(self.timeStampToCheck, Timestamp):
            self._time = (Timestamp() - self.startTimeStamp) % self.periodeGoOff
        else:
            self._time = (self.timeStampToCheck - self.startTimeStamp) % self.periodeGoOff
        self.currentDirection()  # modifies time
        if (self.direction.lower() == "+el"):
            return [0, self.distance(1)]
        elif (self.direction.lower() == "-el"):
            return [0, -self.distance(1)]
        elif (self.direction.lower() == "+az"):
            return [self.distance(0), 0]
        elif (self.direction.lower() == "-az"):
            return [-self.distance(0), 0]
        else:
            return [0, 0]

    def currentDirection(self):
        '''That method calculates in which phase of parameter 'goOffSequence' the system works. 
        Therefore the time is devided in 4 equal parts.
        This method modifies :attr: '_time' for further use in :meth: 'distance'.
        '''
        if self._time < (0.25 * self.periodeGoOff):
            self.direction = self.goOffSequence[0]
        elif self._time < (0.5 * self.periodeGoOff):
            self._time -= 0.25 * self.periodeGoOff
            self.direction = self.goOffSequence[1]
        elif self._time < (0.75 * self.periodeGoOff):
            self._time -= 0.5 * self.periodeGoOff
            self.direction = self.goOffSequence[2]
        else:
            self._time -= 0.75 * self.periodeGoOff
            self.direction = self.goOffSequence[3]

    def distance(self, index):
        '''This method caculates the current deflection. 
        It uses the modified :attr: '_time' from :meth: 'currentDirection'.

        params
        ------
        index: integer
            defines if it uses the maximal amplitude of azimuth or elevation stored in :attr:'goOfMax'.

        returns
        -------
        amplitude: float
            The current amplitude 
        '''
        # the reduced time through the time necessary to get to the max value
        amplitude = self.goOffMax[index] * self._time / (self.periodeGoOff / float(8))
        if (amplitude > self.goOffMax[index]):
            amplitude = 2 * self.goOffMax[index] - amplitude
        return amplitude

    def makeRasterDiscrete(self):
        ''''Gets the current off in azimuth and elevation according to 'starttimestamp' and 'observationDuration'.
        Mention that the time for moving between the points is not mentioned. The telescope will be not on the target at that time.  

        returns
        -------
        azEl: list with two floats
            This value are the goOff value caused by the discrete raster.
        '''
        if isinstance(self.timeStampToCheck, Timestamp):
            if self.timeStampToCheck < (self.startTimeStamp + self.observationDuration):
                i, remain = divmod(self.timeStampToCheck - self.startTimeStamp,
                                   self.observationDuration / (self.pointsAz * self.pointsEl))
                return self.azElRasterList[int(i)]
            else:
                return [0, 0]
        else:
            if Timestamp() < (self.startTimeStamp + self.observationDuration):
                i, remain = divmod(Timestamp() - self.startTimeStamp,
                                   self.observationDuration / (self.pointsAz * self.pointsEl))
                return self.azElRasterList[int(i)]
            else:
                return [0, 0]

    def createRasterDiscreteList(self):
        '''Creates a list with descrete points of a raster.
        The list which is created is 'azElRasterList'.
        '''
        startAz = -self.az_frame / float(2)
        startEl = self.el_frame / float(2)
        # Begin on the upper left corner
        if self.firstAz:
            for pEl in range(self.pointsEl):
                for pAz in range(self.pointsAz):
                    if pEl % 2 == 1:  # move from right to left
                        pAz = self.pointsAz - pAz - 1
                    self.azElRasterList.append([startAz + pAz * self.az_frame / float(self.pointsAz - 1),
                                                startEl - pEl * self.el_frame / float(self.pointsEl - 1)])
        else:
            for pAz in range(self.pointsAz):
                for pEl in range(self.pointsEl):
                    if pAz % 2 == 1:
                        pEl = self.pointsEl - pEl - 1
                    self.azElRasterList.append([startAz + pAz * self.az_frame / float(self.pointsAz - 1),
                                                startEl - pEl * self.el_frame / float(self.pointsEl - 1)])

    def makeRaster(self):
        '''Make a Raster which drives continuously through the points like in 'RasterDiscrete'.
        The long side is defined as azimuth if 'firstAz=True'. The velocity at the short side is the same as in the long side.
        The short side is inverted. The minus comes back in the definition if it is azimuht or elevation.

        returns
        -------
        azEl: list with two floats
            This value are the goOff value caused by the raster.
        '''
        if isinstance(self.timeStampToCheck, Timestamp):
            distance = self.velocityRaster * (self.timeStampToCheck - self.startTimeStamp)
        else:
            distance = self.velocityRaster * (Timestamp() - self.startTimeStamp)
        completedDistances, remainDistance = divmod(distance, (self.moveConstLong + self.moveConstShort))
        if remainDistance < self.moveConstLong:  # Handles if it still moving on the long side
            if completedDistances % 2:  # make the correkt direction, e.g. left to right or vice versa
                remainDistance = self.moveConstLong - remainDistance
            # define distance from startposition
            longSide = remainDistance
            shortSide = completedDistances * self.moveConstShort
        elif not (self.rasterLines - 1) == completedDistances:  # Handle moving on the short side
            # define the long side position, e.g. right or left side
            if completedDistances % 2 == 0:
                longSide = self.moveConstLong
            else:
                longSide = 0
            # calculate the short side
            shortSide = remainDistance - self.moveConstLong + completedDistances * self.moveConstShort
        else:  # If the raster is finished stay at the position
            # define long side, e.g. left or right side
            if completedDistances % 2 == 0:
                longSide = self.moveConstLong
            else:
                longSide = 0
            # define the short side
            shortSide = self.angleConstShort
        # Define which is the long side and which one is the short side
        if self.firstAz:
            return [longSide + self.startAzRaster, self.startElRaster - shortSide]
        else:
            return [shortSide + self.startAzRaster, self.startElRaster - longSide]

    def createRaster(self):
        '''This method defines values which are used in 'makeRaster'.
        The long side and short side is defined here.The long side is defined as azimuth if 'firstAz=True'.
        Also the start point in the upper left corner is calculated.
        The velocity is also calculated here
        '''
        self.startAzRaster = -self.az_frame / float(2)
        self.startElRaster = self.el_frame / float(2)
        if self.firstAz:
            self.moveConstLong = self.az_frame
            self.moveConstShort = self.el_frame / float(self.rasterLines - 1)
            self.angleConstShort = self.el_frame
        else:
            self.moveConstShort = self.az_frame / float(self.rasterLines - 1)
            self.moveConstLong = self.el_frame
            self.angleConstShort = self.az_frame
        self.velocityRaster = (self.rasterLines * (
        self.moveConstLong + self.moveConstShort) - self.moveConstShort) / float(self.observationDuration)

    def makeLissajous(self):
        '''This method makes lissajous figures. 

        returns
        -------
        azEl: list with two floats
            This value are the goOff value caused by the lissajous method.
        '''
        if isinstance(self.timeStampToCheck, Timestamp):
            return [self.az_frame / float(2) * np.sin(
                np.deg2rad(self.omegaAz * (self.timeStampToCheck - self.startTimeStamp) + self.phiAz)),
                    self.el_frame / float(2) * np.sin(
                        np.deg2rad(self.omegaEl * (self.timeStampToCheck - self.startTimeStamp) + self.phiEl))]
        else:
            return [self.az_frame / float(2) * np.sin(
                np.deg2rad(self.omegaAz * (Timestamp() - self.startTimeStamp) + self.phiAz)),
                    self.el_frame / float(2) * np.sin(
                        np.deg2rad(self.omegaEl * (Timestamp() - self.startTimeStamp) + self.phiEl))]

    def makePong(self):
        '''The 'Pong' method moves in a into an direction until it hits the frame, defined by 'az_frame' and 'angleContEl'.
        By hitting the frame it is mirrored. That means that the tangential direction keeps it velocity vector. 
        The perpendicular velocity part is inverted so that it moves into the other direction. As a result incoming angle is outcoming angle.

        returns
        -------
        azEl: list with two floats
            This value are the goOff value caused by Pong.
        '''
        # define the length form the upper left corner
        if isinstance(self.timeStampToCheck, Timestamp):
            az = self.startAz + self.velocity * np.cos(np.deg2rad(self.startAngle)) * (
            self.timeStampToCheck - self.startTimeStamp) - self.az_frame / float(
                2)  # set it to zero on the left border of the frame
            el = self.startEl + self.velocity * np.sin(np.deg2rad(self.startAngle)) * (
            self.timeStampToCheck - self.startTimeStamp) - self.el_frame / float(
                2)  # set it to zero on the bottom border of the frame
        else:
            az = self.startAz + self.velocity * np.cos(np.deg2rad(self.startAngle)) * (
            Timestamp() - self.startTimeStamp) - self.az_frame / float(
                2)  # set it to zero on the left border of the frame
            el = self.startEl + self.velocity * np.sin(np.deg2rad(self.startAngle)) * (
            Timestamp() - self.startTimeStamp) - self.el_frame / float(
                2)  # set it to zero on the bottom border of the frame
        # With the divmod it can be set back into the frame in which the value should be
        completedAz, remainAz = divmod(az, self.az_frame)
        completedEl, remainEl = divmod(el, self.el_frame)
        # Define azimuth from the middle of the box, dependent if it hits the left or the right border of the frame
        if (completedAz % 2) == 0:
            az = self.az_frame / float(2) - remainAz
        else:
            az = remainAz - self.az_frame / float(2)
        # Define elevation from the middle of the box, dependent if it hits the top or the bottom border of the frame
        if (completedEl % 2) == 0:
            el = self.el_frame / float(2) - remainEl
        else:
            el = remainEl - self.el_frame / float(2)
        return [az, el]

    def init_line_track(self):
        """
            Initialise line track
            Get total degree
            Get average velocity
        """
        start_az, start_el = self.linepoints[0]
        self.linepoints = np.subtract(self.linepoints, [start_az, start_el])
        self.total_deg = 0.0
        previous_az, previous_el = 0, 0
        # Get total degrees
        for az, el in self.linepoints[1:]:
            self.total_deg += abs(az -previous_az) + abs(el - previous_el)
            previous_az = az
            previous_el = el
        previous_az, previous_el = self.linepoints[0]
        self.relative_distances = []
        for az, el in self.linepoints[1:]:
            d_azel = abs(previous_az - az) + abs(previous_el - el)
            previous_az, previous_el = az, el
            self.relative_distances.append(d_azel / self.total_deg)
        self.velocity = self.total_deg / self.observationDuration

    def trackLine(self):
        if isinstance(self.timeStampToCheck, Timestamp):
            relative_position = (self.timeStampToCheck - self.startTimeStamp) / self.observationDuration
            # print 'relative position:', relative_position
        else:
            relative_position = (Timestamp() - self.startTimeStamp) / self.observationDuration
        rel = 0
        line_n = 0
        for line_n, line_rel in enumerate(self.relative_distances):
            rel += line_rel
            if relative_position < rel:
                break
        previous_lines = sum(self.relative_distances[:line_n])
        rel_pos_on_current_line = (relative_position - previous_lines)/self.relative_distances[line_n]
        # print rel_pos_on_current_line
        az = self.linepoints[line_n][0] + (self.linepoints[line_n+1][0] - self.linepoints[line_n][0])  * rel_pos_on_current_line
        el = self.linepoints[line_n][1] + (self.linepoints[line_n+1][1] - self.linepoints[line_n][1])  * rel_pos_on_current_line
        return [az, el]



if __name__ == '__main__':
    """For debugging issues"""
    from matplotlib import pyplot as plt
    t = np.linspace(0, 2*np.pi,400)
    x = 10*np.cos(t)
    y = 10*np.sin(t)
    val_list = []
    for i, val in enumerate(x):
        val_list.append((val, y[i]))
    print val_list
    mode = obs_mode('Line', linePoints=val_list, observationDuration=5)

    az_list = []
    el_list = []
    for i in np.linspace(0,300, 4000):
        mode.timeStampToCheck = Timestamp()+i
        az_list.append(mode.currentOff[0])
        el_list.append(mode.currentOff[1])
    plt.plot(az_list, el_list)
    plt.show()