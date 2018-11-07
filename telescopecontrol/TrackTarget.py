from ObservationMode import *
import threading
from GetMoveDistance import getMoveDistance
from movingAdapter import moveContinuousAdapter
from Queue import Queue
from check_target import *
import datetime

class TrackTarget:
    def __init__(self, OVST):
        """ This class observes a target

        params
        ------

        OVST: object of OverallSettings

        attributes:
        ----------            
        running: Boolean
            Shows if a tracking thread is already running
        """

        self.track_Queue = Queue()
        self.OVST = OVST
        self.antennas = OVST.active_antennas
        self.catalogue = OVST.Catalogue
        self.running = False
        self.halt = False
        self.stop_all = False

    def track(self, targetname, observationDuration=5, GoOffAzEl=None, startTime=None,
              moveIncrementalTime=60, mode = None):
            if startTime:
                try:
                    if len(startTime) == 8:  # Only a time was written into it
                        date = datetime.datetime.now().date().strftime('%Y_%m_%d ')
                        startTime = date + startTime
                    startTime = datetime.datetime.strptime(startTime, '%Y_%m_%d %H:%M:%S')
                    # Convert startTime to timestamp
                    startTime = time.mktime(startTime.timetuple())
                    if Timestamp(startTime) > Timestamp():
                        self.startTimeStamp = Timestamp(startTime)  # if it is None it uses the current time
                    else:
                        self.startTimeStamp = Timestamp()
                except ValueError:
                    print "The Start Time has the wrong format. It uses the current Time as StarttimeStamp.\n " \
                          "It was entered: '%r'" % startTime
                    self.startTimeStamp = Timestamp()
            else:
                self.startTimeStamp = Timestamp()

            if not checkAbsoluteSequenceHitsLimitSwitch(self.OVST, self.startTimeStamp, observationDuration*60,
                                                        targetname, mode)[0]:
                self.track_Queue.put((targetname, observationDuration, GoOffAzEl, self.startTimeStamp, moveIncrementalTime,
                                      mode))
                print 'target put into queue'
                if not self.running:
                    self.th = threading.Thread(target=self._tracking_thread)
                    self.th.start()
                    print 'Starting Track of %s at %s' % (targetname, self.startTimeStamp.to_string())
                    self.running = True
                else:
                    print 'Currently a target is tracked. New track was put into the Queue on position %i' \
                          % (self.track_Queue.qsize()-1)
            else:
                print "Can't track target without hitting a limit switch"

    def _tracking_thread(self):
        '''     this takes one item(target) of :Queue: track_Queue and tracks it. This gets repeated until the Queue is
                empty (until no target is left).'''
        self.waiting = False
        while not self.track_Queue.empty():
            # get all args of next item of track_Queue
            args = self.track_Queue.get()
            # start position data acquisition
            self._start_track(*args)
            if self.halt and not self.stop_all:
                # stop_track() got called
                print 'Current track(%s) was stopped, to go on with the next target type continue_track()' % args[0]
            if self.stop_all:
                # stop_all_tracks() got called (stop_all and halt got set to True)
                items = self.track_Queue.qsize()
                #  Clear whole Queue
                self.track_Queue.queue.clear()
                print 'All targets in Queue (%i) got deleted' % items
                self.stop_all = False
                self.halt = False
                self.OVST.halt = False
                self.OVST.clearTelescopeHalt()
            while self.halt:
                # Check every 0.5s if halt got cleared
                time.sleep(0.5)
            try:
                # Only if daq was started
                self.OVST.daq = False
                while not self.OVST.data_saved:
                    # Wait until position data is saved
                    time.sleep(0.5)
            except:
                pass
        self.running = False
        del self.current_track
        print 'No targets to track anymore moving to home position.'
        self.OVST.moveHomePosition()

    def _start_track(self, targetname, observationDuration, goOffAzEl, startTime, moveIncrementalTime,
                     mode):
        """
        Tracks a target 'targetname' for 'observationDuration' minutes   
        :param targetname:              str
        :param observationDuration:     float
        :param moveIncrementalTime:     float
        :param startTime:          float, string, ephem.Date
        :param mode:                     :object: 'GoOffPointing'
        """
        self.antennas = self.OVST.active_antennas
        if isinstance(targetname, Target):
            self.targetname = targetname
        self.moveIncrementalTime = moveIncrementalTime
        self.sleepingTimeSec = 0.01
        self.targetname = targetname

        self.observationDuration = observationDuration*60

        if isinstance(goOffAzEl, (int, float)):
            # if only one value is given, go this value in every direction
            goOffAzEl = (goOffAzEl, goOffAzEl)

        if isinstance(mode,ObservationMode):
            pass
        elif goOffAzEl:
            mode = ObservationMode(azGoOff=goOffAzEl[0], elGoOff=goOffAzEl[1], periodeGoOff=observationDuration)
        else:
            mode = ObservationMode()
        self.mode = mode
        self.mode.observationDuration = self.observationDuration


        if not self.halt:
            # Check if the target is only visible after the move incremental time.
            if (checkAbsoluteSequenceHitsLimitSwitch(self.OVST, self.startTimeStamp, self.observationDuration, self.targetname,
                                                     self.mode))[0]:
                # Set the starttimestamp after the moveIncrementalTime to avoid hitting a limitswitch
                self.startTimeStamp += self.moveIncrementalTime
            if (checkAbsoluteSequenceHitsLimitSwitch(self.OVST, self.startTimeStamp, self.observationDuration,
                                                                      self.targetname, self.mode)[0]):
                print "There is no moving possible without hitting a end switch at %s."% Timestamp().to_string()
                print "'startTime: %r ,real Time: %r"% (self.startTimeStamp,Timestamp()) #Debug issues
                print "Thread %s finished unsuccessful at %s."%(self.targetname, Timestamp().to_string())
            else:
                # The way it moves causes that it always wants to move as fast as possible.
                # The code avoids displaying warnings.
                if self.mode.mode == "RasterDiscrete":
                    disableMaxSpeedWarning = True
                else:
                    disableMaxSpeedWarning = False
                if Timestamp() < self.startTimeStamp:
                    sleepSec = (self.startTimeStamp - Timestamp())
                    print 'Waits for %.2f minutes to start the track' % (sleepSec/60.)
                    self.current_track = [targetname, observationDuration,
                                          (Timestamp()+sleepSec).to_string(), self.mode.mode]
                    sleepTimeWithChecks(self, sleepSec, True)
                if not self.halt:
                    print "Move Incremental to the start position of '%s' at %s. " % (
                    self.targetname, Timestamp().to_string())
                    # Drive incremental to the start position
                    azel = check_target(self.OVST, self.targetname)
                    self.mode.startTimeStamp = Timestamp()
                    azel_off = self.mode.currentOff
                    self.current_track = [targetname, observationDuration, 'Moving to start', self.mode.mode]
                    self.OVST.move_to_pos(self.targetname, for_track=True, azel_off=azel_off)
                    self.current_track = [targetname, observationDuration, Timestamp().to_string(), self.mode.mode]
                    if not self.halt:
                        print "In start position."
                        print "Start observing Target '%s' at %s for %r minutes. " \
                              % (self.targetname, Timestamp().to_string(), self.observationDuration/60)
                        # Start position daq
                        qth = threading.Thread(target=self.OVST.daq_pos, args=(self.targetname,))
                        qth.start()
                        print 'Data Acquisition got started'
                        # Calculate the :var: 'endTimeStamp' at this line to avoid loosing time with moving to the target
                        endTimeStamp = Timestamp() + self.observationDuration
                        #   set the correct starttimestamp to now
                        self.mode.startTimeStamp = Timestamp()
                        # First move command which sets 'move continous' mode
                        moveContinuousAdapter(self.OVST, self.targetname, Timestamp(),
                                              self.sleepingTimeSec, inTrack=False, mode=self.mode,
                                              disableMaxSpeedWarning=disableMaxSpeedWarning)
                        while (endTimeStamp>Timestamp())& (not self.halt):  # also interrupt the Track if there is a halt command
                            moveContinuousAdapter(self.OVST, self.targetname, Timestamp(),
                                                  self.sleepingTimeSec, inTrack=True, mode=self.mode,
                                                  disableMaxSpeedWarning=disableMaxSpeedWarning)
                            time.sleep(self.sleepingTimeSec)
                        if not self.halt:
                            print "Observing target %s finished successful at %s." % \
                                  (self.targetname, Timestamp().to_string())
                        else:
                            print "Observing target %s finished unsuccessful at %s." %\
                                  (self.targetname, Timestamp().to_string())
                            self.OVST.disableTelescopes()




def checkAbsoluteSequenceHitsLimitSwitch(OVST, startTimeStamp, observationDuration, targetname, gOP=None):
    """ Checks if the observation hits a limit switch. If motion is possible, it returns the rollover specification.
    

        Params
        ------
        startTimeStamp: object of :class: 'Timestamp'
            Timestamp, There is no default value or other format handled

        observationDuration: float
            Time in seconds in which the target is observed

        targetname: string,   object of :class: 'Target' 
            Name of the target on which will be pointed.
            If it is a object of :class: 'Target', catalogue value will be skipped.
            Used in :func: 'check_target'.

        catalogue: object of :class: 'Catalogue' 
            It should containing an element called 'targetname'.
            Used in :func: 'check_target'.

        antennas: list objects of :class: 'Antenna' 
            If there is no antenna specified the antenna(s) defined in 'catalogue' 
            or the antennas defined in the object of :class: 'Target' are used.    
            
        gOP: object of :class: 'GoOffPointing'
            It is used to calculate the 'OffPointing'.
            It is 'call-by-reference'. It also manipulates the 'GOP' object in the layer which calls the :meth: 'checkAbsoluteSequenceHitsLimitSwitch'.
            Therefore it is important to set at the end of this method the 'GOP.timeStampToCheck' to 'None'.
        

        :return hitsLimitSwitch:    bool
                                    Indicates if the limit switch will be hit during the observation.
                                    True if it hits a limit

        :return antStartAz:         float array
                                    list of lists with absolute azimuth start values without Rollovers
                                    The values contain already the GoOffPointing

    """
    catalogue = OVST.Catalogue
    antennas = OVST.active_antennas
    hitsLimitSwitch = False
    if gOP == None:
        gOP = ObservationMode()
    gOP.startTimeStamp = startTimeStamp
    # List with azEl for all antennas for each Timestamp
    azElTmSp = [] # [Timestamp][Antenna][Azimuth=0,Elevation=1]
    def getAndAddAzElAndOff(timeStampToCheck):
        """This method gets for the :Timestamp: 'timeStampToCheck' the azimuth and elevation and the 'OffPointing'.
        It also add the 'OffPointing to azimuth and elevation values.

        params
        ------
        timeStampToCheck: object of :class: 'Timestamp'
            The timestamp at which the values will be calculated

        returns
        -------
        azEl:    List with lists containing azimuth elevation values
        """
        azEl = check_target(OVST, targetname, timeStampToCheck)
        gOP.timeStampToCheck = timeStampToCheck
        azElOff = gOP.currentOff
        for i in range(len(antennas)):
            azEl[i][0] = azEl[i][0] + azElOff[0]
            azEl[i][1] = azEl[i][1] + azElOff[1]
        return azEl

    # for i in range(int(observationDuration//6)):#checks every 10 seconds with int as result
    # It would be possible to run into a limitswitch during the time between the checks. Therefore every second is checked.
    for i in range(int(observationDuration)):  # checks every seconds with int as result
        # Times at which the position is checked
        timeStampToCheck = startTimeStamp + i
        # Get azimuth and elevation of all antennas with the Offset
        # check_target returns  azimuth [0] and elevation [1]
        azElTmSp.append(getAndAddAzElAndOff(timeStampToCheck))

    # Check the elevation
    for ant in range(len(antennas)):
        for tmSp in range(len(azElTmSp)):
            # Drive in the negative limit switch
            if antennas[ant].azElPos[1].params[0] > azElTmSp[tmSp][ant][1]:
                hitsLimitSwitch = True
                break   # It does not repeat the 'print' command
            # Drive in the positive limit switch
            if antennas[ant].azElPos[1].params[1] < azElTmSp[tmSp][ant][1]:
                hitsLimitSwitch = True
                break # It does not repeat the 'print' command
        if hitsLimitSwitch:
            break # It does not repeat the 'print' command

    # Check the azimuth
    # A list of azimuth values for all antennas at start
    antStartAz = []   # [ant][AntennaStartValue]
    for ant in range (len(antennas)):
        # roCntMoveDistLst = []
        roCntPossible = []
        # check for all possible rollovers of the current antenna
        for roCnt in range(antennas[ant].azElPos[0].rolloverCounterMinMax[0], antennas[ant].azElPos[0].rolloverCounterMinMax[1]+1):
            moveDistLst = []    # A list of move distances
            moveDistLstAbs = []
            # Check all timestamps
            for tmSp in range(len(azElTmSp)-1):
                #              def getMoveDistance(coordinate,            antennaSensor,            initialPos=None,         disablePrints=False):
                moveDistLst.append(getMoveDistance(azElTmSp[tmSp+1][ant][0],antennas[ant].azElPos[0],((azElTmSp[tmSp][ant][0]) + 360 * roCnt),
                                                   True)) #True makes that it returns '999999' if it is not possible
                moveDistLstAbs.append(abs(moveDistLst[-1]))
            # the values in azLst are so close to each other (every seconds) that the move distance is lower than 30 degree
            if (max(moveDistLstAbs)<30) and ((azElTmSp[tmSp][ant][0]) + 360 * roCnt>antennas[ant].azElPos[0].params[0]) and ((azElTmSp[tmSp][ant][0]) + 360 * roCnt<antennas[ant].azElPos[0].params[1]):
                #it does not hit the limit switch (checked by :func: 'getMoveDistance' and does not move for about 360 to get in another rollover range
                #If it is so than append it to the list with possible rollover counts
                roCntPossible.append(roCnt)
        # Calculate the start values for azimuth. If limit switch is hit it retruns an empty list
        if (len(roCntPossible)==0):
            # The azimuth limit switch will be hit by tracking the target
            hitsLimitSwitch=True
            antStartAz.append([])
        else:
            # Get the start coordinate without rollover
            for i in range (len(roCntPossible)):
                # Uses the same name to avoid creating a new variable
                roCntPossible[i] = roCntPossible[i] * 360 + azElTmSp[0][ant][0]
            # Overgive the list
            antStartAz.append(roCntPossible)
    # Because it is 'call-by-reference' and later it needs the current time
    gOP.timeStampToCheck = None
    return hitsLimitSwitch, antStartAz


def sleepTimeWithChecks(self, sleepSec, fromTrack=False):
    '''This function makes it possible to break the thread even if it sleeps.
    It devides the sleeping time in 10 second sections. The method sleeps 10 seconds, checks if a 
    'kill' or 'halt condition is present and sleeps again 10 seconds if everythin is ok.

    param
    -----
    sleepSec:   float
        The whole sleeping time it should sleep in seconds. 

    fromTrack: bool
        If this function is called by :class: 'TrackTarget' it works around
        'self.kill' because it is no attribute of the class.
    '''
    tenSecSleep, remainSleep = divmod(sleepSec, 10)
    for i in range(int(tenSecSleep)):
        time.sleep(10)
        if fromTrack:
            if self.halt:  # stops waiting if halt or kill command is set
                break  # The text should be written later
        else:
            if self.kill or self.halt:  # stops waiting if halt or kill command is set
                break  # The text should be written later
    time.sleep(remainSleep)
