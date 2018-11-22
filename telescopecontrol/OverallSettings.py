from Python_Diagnostic_Program_Modified import PythonDiagnosticProgramm
from katpoint import Timestamp, Catalogue, construct_azel_target, construct_radec_target, deg2rad, Target
from PLCCommunication import PLCCommunicationQueue, PLCCommunicationThread
from SensorClassModifications import _sensorClassModification
from Window import WindowThread
import time
import os
from wetton_settings import init_wetton_telescope
from movingAdapter import moveIncrementalAdapter
from check_target import check_target, filter_catalogue, dms2dd
import h5py
from datetime import datetime
import numpy as np
import threading


class OverallSettings(object):
    def __init__(self):
        """A container for the settings which are used in several processes.
        Also there are lists which contains objecs
        It also contains a lock which is used in :meth: 'moveIncrementalAdapter' and :meth: 'moveContinuousAdapter'


        attributes
        ----------
        antennaList: list with objects of :class: 'Antenna'
            a list with all antennas

        antennaDict: dict with objects of :class: 'Antenna'
            a dict with all antennas for use in KATCP

        sensorList: list with objects of :class: 'Sensor
            It is special reserved for sensors of antennas.

        sensorUpdaterList: list with objects of :class: 'Sensor
            It contains all sensors.

        PDPList: list with objects of :class: 'PythonDiagnosticProgramm'
            a list which contains the client for modbus communication with the PLC
        
        backGroundUpdater: objects of :Thread: 'BackgroundUpdater'
            The thread which gets the values of the PLC

        axisToMoveRegister: int
            Select the axis which should move The axis which will move have to be selected in register '21'. 
            As a consequence unselected axis will not move even if there is a value in register 'X20' or 'X21'. 
            The axis is selected with bits. This is explained in table 5.2 below. Combinations are possible, 
            so that '5' or binary '0b0101' has to be written in register '21' to move Elevation of both telescopes.
            
            Value in Binary Notation                           0b1       0b10       0b100       0b1000
            Value in Dec. Notation                              1         2          4           8
            Description                                      Elevation  Azimuth    Elevation   Azimuth
                                                                Telescope 1             Telescope 2 

        motionCommandRegister: int
            Command Move now The last command makes the selected axis moving. By writing in register '20' the value '13' 
            the selected axes will move incremental for the distance which is described in step 1. By writing '12' the 
            selected axes will move absolute to the position which is described in step 1. By writing '15' it will move 
            continuous on the selected axes.

        moveIncrementalValue: int
            The value which have to be written in 'motionCommandRegister' to move to an incremental distance.

        moveContinuousValue: int
            The value which have to be written in 'motionCommandRegister' to move to an absolute postition.

        cataloguesToTrack: list with the params for 'TrackCatalogue, without 'OVST'
            It contains the catalogues which will observed in the future.
            
        cataloguesTracked: list with objects of :class: 'TrackCatalogue'
            It contains the catalogues objects which are finished


        currentTrack: object of :class: 'TrackTarget'
            The current running 'TrackTarget' Thread.

        currentCatalogue: object of :class: 'TrackCatalogue'
            The current running 'TrackCatalogue' Thread.
        """
        self.sensorUpdaterList = []
        self.antennaList = []
        self.sensorList = []
        self.PDPList = []
        self.cataloguesToTrack = []
        self.cataloguesTracked = []
        self.currentTrack = None
        self.currentCatalogue = None
        self.error = False
        self.SUT = None                     # Sensor Updater Thread
        self.disconnectedManually = False
        self.halt = False                   # halt moveSavetyPosition or moveHomePosition
        self.haltMoveSavetyHome = False
        self.inSafetyPosition =False
        self.active_antennas = []
        # Create Catalogue
        self.Catalogue = Catalogue(add_specials=True, add_stars=True)



        @property
        def antennaDict(self):
            ''' A property which generates form the antenna list a antenna dict.
            It is necessary for katcp communication to work with a dict.
            '''
            global antennaList
            _antennaDict = {}
            for i in range(len(antennaList)):
                _antennaDict[antennaList[i].name] = antennaList[i]
            return _antennaDict

        # does not belong to the class to avoid confusion with self
        _sensorClassModification()

        # Make the telescope specific settings
        init_wetton_telescope(self)

        # set the rollover counter for each telescope
        self.rollover_startup()

        # Open Modbus Connection
        self.openModbusConnections()

        # Add Catalogues
        self.addCatalogues(self.Catalogue)

        # Set BackgroundUpdater, creates PLCCommunicationQueue
        self.setBackgroundUpdater()

        self.active_antennas = self.antennaList

        # Start update of targets in range
        self.update_time = None
        self.in_range = None
        threading.Thread(target=self.check_in_range, args=(True,)).start()


##### Telescope specific settings #####

    def rollover_startup(self):
        """ 
        Checks if the program was closed normally
        """
        rollover_file = os.path.dirname(__file__)+'/Catalogues/.rollover'
        try:
            with open(rollover_file, 'r') as csv:
                if csv.read() == 'Shutdown: properly':  # Program got exited with quit() or exit() in the last session
                    for i in range(len(self.sensorList)):
                        self.sensorList[i].raiseStatus = 3 # 'error'
                        if self.sensorList[i].isAzimuth:
                            self.sensorList[i].rolloverCounter = 0
                    os.remove(rollover_file)
                    self.inSafetyPosition = True
                    self.inHomePosition = True
                else:
                    os.remove(rollover_file)
                    raise ValueError

        except:     # Either no file exists(program was forced to exit) or file contains the wrong Value
            print "\nTelescope telescopecontrol program wasn't shut down properly. Next time please use quit() or exit() " \
                  "to close the program"
            self.inHomePosition = False
            self.askRolloverCounter()

    def askRolloverCounter(self, rollover=None):
        """This method ask the user for the current rollover position.
        It will be called, if the previous session wasn't closed with quit() or exit()
        """
        n = 0
        for i in range(len(self.sensorList)):
            self.sensorList[i].raiseStatus = 3 # 'error'
            if self.sensorList[i].isAzimuth:
                isInt=False
                if rollover and len(rollover) == len(self.antennaList):
                    self.sensorList[i].rolloverCounter = rollover[n]
                else:
                    while not isInt:
                        try:    # Put that lines in a method
                            self.sensorList[i].rolloverCounter = int(raw_input("According to the limits, the zone of %s is between %i and %i.\nInsert the current rollover zone. \n > "
                                                                               %(self.sensorList[i].name, self.sensorList[i].rolloverCounterMinMax[0],self.sensorList[i].rolloverCounterMinMax[1])))
                            isInt = True
                        except ValueError:
                            print "Please insert an Integer!"
                            isInt = False
                n += 1

##### Open, Close Modbus Connections #####

    def openModbusConnections(self, amount=1):
        """The defined number of client objects can be defined, opend and append to the 'PDPList' with that method.
        This does not need to be added to the Queue because it does not write or read anything.
        Maximum length of the 'PDPList' is 10.

        params
        ------
        amount: int
            The amount of objects, which will be opened.
            The program uses always the first entry in the list. 
            The user could use a second entry           
            """
        self.disconnectedManually = False
        for i in range (amount):
            self.PDPList.insert(0,PythonDiagnosticProgramm())
            connected = self.PDPList[0].modbusConnectionOpen()
            if connected:
                self.ConnectionStatus.set(Timestamp(),1,True)
            else:
                self.ConnectionStatus.set(Timestamp(),5,False)
        if len(self.PDPList)>10:
            for i in range(len(self.PDPList)-10):
                self.PDPList.pop()

    def closeAllModbusConnections(self):
        '''Close all modbus connections listed in :attr: 'PDPList'.
        '''
        self.disconnectedManually = True
        for i in range(len(self.PDPList)):
            self.PDPList[i].modbusConnectionClose()
        self.PDPList = []
        self.ConnectionStatus.set(Timestamp(),5,False)
        try:
            print "Closed %r modbus connections at %s." %(i+1,Timestamp().to_string())
        except NameError:
            print "There was no modbus connection at %s."%Timestamp().to_string()

##### Catalogue Functions #####


    @classmethod
    def addCatalogues(cls,catalogue):
        """
        Adds all files in the directory 'Catalogues' with file extionsion '.edb' or '.csv' to the catalogue 
        :param catalogue:   object of class Catalogue
        :return: 
        """

        print 'Initialising Catalogues...'
        dirpath = os.path.dirname(__file__) + '/Catalogues'
        files = os.listdir(dirpath)
        for cat in files:
            filepath = dirpath + '/' + cat
            try:
                if cat[-4:] == '.edb':
                    catalogue.add_edb(file(filepath))
                elif cat[-4:] == '.csv':
                    catalogue.add(file(filepath))
            except:
                print 'Unable to add Catalogue %s' % cat

        print 'Catalogues Initialised.'

    def check_in_range(self, loop=False):
        '''
        Checks which targets in self.catalogue are in telescope range
        :param loop: Checks every minute. Used for background update for the website
        :return: 
        '''
        self.in_range = filter_catalogue(self)
        self.update_time = datetime.now().time().isoformat()[:8]
        while loop:
            time.sleep(60)
            self.in_range = filter_catalogue(self)
            self.update_time = datetime.now().time().isoformat()[:8]

##### Set BackgroundUpdater #####

    def setBackgroundUpdater(self):
        '''Set BackgroundUpdater and a Queue.
        '''
        self.PCQ = PLCCommunicationQueue()
        self.PCT = (PLCCommunicationThread('BackgroundUpdater', self))

    def startControlWindow(self):
        self.WT = WindowThread(self)

##### Enable, Disable Telescoepe #####

    def choose_telescopes(self, telescopes=None):
        # choose the antennas you want to move
        self.active_antennas = []
        if not telescopes:
            self.active_antennas = self.antennaList
        if not isinstance(telescopes,list):
            telescopes = [telescopes]
        for ant in telescopes:
            if ant in self.antennaList:
                self.active_antennas.append(ant)
        if not isinstance(self.active_antennas, list):
            self.active_antennas = [self.active_antennas]

        for ant in self.active_antennas:
            print '%s is now active' % ant.name


    def haltTelescopes(self):
        """Halts the telescopes.
        """

        i = 0
        self.halt=True
        while not self.CurrentMotionCommand.value() == 0 and not self.error:
            self.PCQ.writeTask(20, 0)
            i += 1
            if i % 10 == 0:  # if it does send 10 times it gives the system some time
                time.sleep(5)
            else:
                time.sleep(2)
        print "Halt the telescopes at %s."%Timestamp().to_string()

    def enableTelescopes(self):
        '''Enables movement of the telescopes.
        It also allows automatically reconnection.
        '''
        self.clearTelescopeHalt()
        self.disconnectedManually = False
        i =0
        while not self.CurrentSystemStatus.value() == 2 and not self.error:
            self.PCQ.writeTask(20, 1)
            i += 1
            if i%10==0:     # if it does send 10 times it gives the system some time
                time.sleep(5)
            else:
                time.sleep(2)

        print "Telescopes Enabled at %s."%Timestamp().to_string()


    def disableTelescopes(self):
        '''Disables movement of the telescopes
        '''
        i=0
        while not self.CurrentSystemStatus.value() == 1 and not self.error:
            self.PCQ.writeTask(20, 2)
            i += 1
            if i % 10 == 0:  # if it does send 10 times it gives the system some time
                time.sleep(5)
            else:
                time.sleep(2)
        print "Telescopes Disabled at %s."%Timestamp().to_string()


    def clearTelescopeFault(self, rollover=None):
        '''Clear the telescope from faults, when a fault has occured
        It also clears the software fault

        param
        -----
        enable: bool
            Enable the Telescope
        '''
        self.PCQ.writeTask(22,1)
        self.askRolloverCounter(rollover)
        self.error = False

        self.clearTelescopeHalt()
        print "Telescope Faults cleared at %s."%Timestamp().to_string()

    def clearTelescopeHalt(self):
        '''Clear the telescope from faults, when a fault has occured
        It also clears the software fault

        param
        -----
        enable: bool
            Enable the Telescope
        '''
        self.halt =False
        try:
            # That also enables the Catalogue Manager
            self.currentCatalogue.halt = False
        except AttributeError:
            pass #There is no Catalogue tracked
        print "Telescope Halt cleared at %s."%Timestamp().to_string()


##### Special Positions #####

    def moveSavetyPosition(self):
        '''This method moves the telescopes listed in :attr: 'antennaList' to elevation 90 degree.
        The telscopes will not move concurrently.
        '''
        if not self.inSafetyPosition:
            active = self.active_antennas
            for ant in self.antennaList:
                self.active_antennas = [ant]
                az = self.get_pos()[0][1]
                self.move_to_pos(az, 90, True)  # Move on the current azimuth to elevation 90

            pos = self.get_pos()
            if all(i[2]-0.5 <= 90.0 <= i[2]+0.5 for i in pos):
                print 'Telescopes in safety position'
                self.inSafetyPosition = True
            else:
                print 'Telescopes not in safety position'
            self.disableTelescopes()
            self.active_antennas = active

    def moveHomePosition(self):
        '''This method moves the telescopes listed in :attr: 'antennaList' to position azimuth 18 degree and elevation 90 degree.
        az is at 18 degree to have a certain value for rolloverCounter.
        '''
        active = self.active_antennas
        self.active_antennas = self.antennaList
        if not self.inHomePosition:
            print 'Moving to home position'
            self.move_to_pos(18, 90)        # Home position at az:18 and el:90

        pos = self.get_pos()
        if all(i[1] - 0.5 <= 18.0 <= i[1] + 0.5 for i in pos) and all(i[2] - 0.5 <= 90.0 <= i[2] + 0.5 for i in pos):
            print 'All telescopes in home position'
            self.inHomePosition = True
            self.inSafetyPosition = True
        else:
            print 'Telescopes not in home position'
        self.active_antennas = active

    def move_to_pos(self, az, el=None, for_track=False, azel_off=[0,0]):
        '''
        moves the telescopes to a specific azel or radec or to a target position
        :param az:  float/int, string
                    if float/int: az    if string: ra when in format ('HH:MM:SS') otherwise search for target
        :param el:  float/int, string
                    if float/int: el, if string: declination in degree
        '''
        if self.error:
            print "Error has occured. Can not move at %s."%Timestamp().to_string()
        elif self.halt:
            print "Halt has occured. Can not move at %s."%Timestamp().to_string()
        # Important if you choose another telescope while another is moving
        antennas = self.active_antennas
        # Checks whether azel, radec or a target is given
        if isinstance(az, (int, float)) and isinstance(el, (int, float)):
            az = az % 360
            target = construct_azel_target(deg2rad(az), deg2rad(el))
            target.name = 'Moving to az: %d, el: % d at %s' % (az, el, Timestamp().to_string())
        elif isinstance(az, str) and isinstance(el, str):
            target = construct_radec_target(az, el)
            target.name = 'Moving to ra: %s, dec: %s at %s' % (az, el, Timestamp().to_string())
        elif isinstance(az, str) and not el:
            if ',' in az:
                target = Target(az)
            else:
                target = self.Catalogue[az]
        elif isinstance(az, Target):
            target = az
        else:
            raise AttributeError('Wrong format')


        try:
            azel = check_target(self, target)
        except LookupError:
            return 'Target with position az: %s, el: %s is out of telescope range' % (az, el)
        self.enableTelescopes()
        self.inSafetyPosition = False
        moveIncrementalAdapter(self, target, antennas=antennas, azElOff=azel_off)
        #inRange = [[False]*2]*len(antennas)
        inRange = []
        for i in antennas:
            # list of Booleans which show if the antennas are at the right position
            inRange.append([False, False])
        all_inRange = False
        azel = np.add(azel,azel_off)
        while ((self.CurrentSystemStatus.value() == 5 or (not all_inRange)) and not
                self.error and not self.halt):
            for n, ant in enumerate(antennas):
                for i, az_el in enumerate(azel[n]):
                    # check if antenna is range
                    if az_el-0.5 <= ant.azElPos[i].value() <= az_el+0.5:
                        inRange[n][i] = True
            all_inRange = all(i == [True]*2 for i in inRange)

            time.sleep(1)
            if (not all_inRange and not self.CurrentMotionCommand.value() == self.moveIncrementalValue and
                    not self.error and not self.halt):
                moveIncrementalAdapter(self, target, antennas=antennas, azElOff=azel_off)

        # Get position of all Telescopes
        pos = self.get_pos()
        if not for_track:
            if inRange:
                print 'Telescopes are in position at %s:'% Timestamp().to_string()
                for i, azel in enumerate(pos):
                    print '%s     \t Azimuth: %s \t Elevation: %s' % (self.antennaList[i].name, azel[1], azel[2])
                self.disableTelescopes()

    def move_to_gal_pos(self, long, lat, name='galactic target'):
        """
        Moves telescopes to position of galactic coordinates
        :param long: galactic longitude
        :param lat: galactic latitude
        :param name: optional target name
        """
        target = Target(('%s, gal, %s, %s' % (name, long, lat)))
        message = self.move_to_pos(target)
        return message

    def get_pos(self):
        """
        :return:    list
                    position data of every telescope (format: [[tmsp, az1, el1], [tmsp, az2, el2], ...])
        """
        pos = [[], []]
        for i, ant in enumerate(self.antennaList):
            pos[i].append(ant.azElPos[0].read()[0])
            for sensor in ant.azElPos:
                pos[i].append(sensor.read()[2])
        return pos

    def daq_pos(self, name=None):
        '''
        Creates a hdf5 file for every day and stores the position of the current session in the group 'name'
        :param name:    string
                        name of the datagroup in the hdf file. If None it will use the format 
                        "positions_'start Timestamp of record'" 
        '''
        # One hdf file for one day: 'positions_YYYY_MM_DD.h5'
        data_dict = {}
        for i, ant in enumerate(self.antennaList):
            data_dict[ant] = []
        self.daq = True
        self.data_saved = False
        # Start data acquisition
        while self.daq:
            pos = self.get_pos()
            for i, ant in enumerate(self.antennaList):
                target = construct_azel_target(deg2rad(pos[i][1]), deg2rad(pos[i][2]))
                radec = target.astrometric_radec(timestamp=pos[i][0], antenna=ant)
                data_dict[ant].append((pos[i][0], pos[i][1], pos[i][2],
                                       radec[0], radec[1]))
            time.sleep(1)

        # If task is done, safe the data in an hdf5 file
        if not name:
            new_name = 'positions_%s' % Timestamp().local()[11:19] # positions_HH:MM:SS
        else:
            new_name = name
        used = True
        date = datetime.today().date().strftime('%Y_%m_%d')
        i = 1
        dtype = np.dtype([
            ('Timestamp', np.float),
            ('Azimuth', np.float),
            ('Elevation', np.float),
            ('RA (J2000)', h5py.special_dtype(vlen=str)),
            ('DEC (J2000)', h5py.special_dtype(vlen=str))
        ])

        with h5py.File(self.daq_dirpath + '/positions_%s.h5' % date, 'a') as hdf:
            while used:
                try:
                    G = hdf.create_group(new_name)
                    used = False
                except ValueError:
                    new_name = name + '_' + str(i)
                    i += 1
            for i, ant in enumerate(self.antennaList):
                data_array = np.array(data_dict[ant], dtype=dtype)
                G.create_dataset('%s' % ant.name, data=data_array)
            print 'Data saved!'
            self.data_saved = True

    def get_target_pos(self, target, tmsp=None, check=True):
        return check_target(self, target, tmsp, check=check)