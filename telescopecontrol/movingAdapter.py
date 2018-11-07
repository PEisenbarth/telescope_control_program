from ObservationMode import ObservationMode
from AzimuthElevationTransformations import elevationDegreeToLength, azimuthOffset
from katpoint import Timestamp
from GetMoveDistance import getMoveDistance
from check_target import check_target


##### Move Adapter #####


def moveContinuousAdapter(OVST, targetname, tmSp=None, deltaTmSp=None,
                          inTrack=False, mode=ObservationMode(), disableMaxSpeedWarning=False):
    '''This function allows moving to an continuous position by writing into the PLC.
    A modbus connection has to be defined in the :object: 'OVST' :attr: 'PDPList' to use the default of modbus.

    !!Attention!!
    -------------
    :func:  'moveContinuousAdapter' does not check if limit switch will be hit! 
            It belongs to the responsibility of the user.

    Params
    ------
    OVST:
    
    targetname:     string,   object of :class: 'Target'
                    Name of the target on which will be pointed.
                    If it is a object of :class: 'Target', catalogue value will be skipped.
                    Used in :func: 'check_target'

    tmSp:           object of :class: 'Timestamp'
                    The Timestamp at which the azimuth and elevation cooordinate calculated.

    deltaTmSp:      float
                    The time between the next Timestamp and the current Timestamp.
                    It is used to calculate the speed between two points.
                    Too big values are handled in this class.
                    Too small and also too big values are handled in the PLC to protect it from damage.

    inTrack:        bool
                    If it is true the antennas are not updated during the observation.
                    The value is already writtin in the incremental movement to the start position.
            
    mode:           object of :class: 'GoOffPointing'.
                    The GoOffPointing Class of the target. It returns the 'currentOff'.

    disableMaxSpeedWarning

    '''

    # if antenna is not defined, use the first one which is stored in OVST.antennaList
    antennas = (OVST.active_antennas)

    # Creates a list of a single antenna
    if not isinstance(antennas, list):
        antennas = [antennas]
    # Initialise
    axisToMove = 0
    current_azEl = check_target(OVST, targetname, tmSp, False)
    nextAzEl = check_target(OVST, targetname, tmSp + deltaTmSp, False)
    azElOff = mode.currentOff
    mode.timeStampToCheck = Timestamp() + deltaTmSp
    nextAzElOff = mode.currentOff
    mode.timeStampToCheck = None  # It is very important to clear the timestamp for the next check
    for i in range(len(antennas)):
        # Calculation of Speed
        azSpeed = abs((nextAzEl[i][0] + nextAzElOff[0] - current_azEl[i][0] - azElOff[0]) / deltaTmSp)
        elSpeed = abs((elevationDegreeToLength(nextAzEl[i][1] + nextAzElOff[1], antennas[i].azElPos[1].offset) -
                       elevationDegreeToLength(current_azEl[i][1] + azElOff[1], antennas[i].azElPos[1].offset)) / deltaTmSp)

        if disableMaxSpeedWarning:
            # Only for RasterDiscrete
            azSpeed = 5.0
            elSpeed = 5.0

        # Catches too big speed values
        if azSpeed > 5:
            azSpeed = 5.0
            if not disableMaxSpeedWarning:
                print "Azimuth Speed is higher than 5 at %s" % Timestamp().to_string()
        OVST.PCQ.writeTask(antennas[i].azimuthMoveAbsoluteSpeedRegister, float(azSpeed), Timestamp())

        if elSpeed > 5:
            elSpeed = 5.0
            if not disableMaxSpeedWarning:
                print "Elevation Speed is higher than 5 at %s" % Timestamp().to_string()
        OVST.PCQ.writeTask(antennas[i].elevationMoveAbsoluteSpeedRegister, float(elSpeed), Timestamp())

        # Positions after speed. Otherwise it uses the old speed from the last writing period.
        # Write the values in the registers
        OVST.PCQ.writeTask(antennas[i].azimuthMoveAbsolutePositionRegister,
                           float(azimuthOffset(nextAzEl[i][0] + nextAzElOff[0], antennas[i].azElPos[0].offset)),
                           Timestamp())
        OVST.PCQ.writeTask(antennas[i].elevationMoveAbsolutePositionRegister, float(
            elevationDegreeToLength(nextAzEl[i][1] + nextAzElOff[1], antennas[i].azElPos[1].offset)), Timestamp())

        if not inTrack:
            # Only called when Track gets started
            axisToMove += antennas[i].selectValue
            # Write which axis should move
            OVST.PCQ.writeTask(OVST.axisToMoveRegister, axisToMove, Timestamp())
            # Start move continuous status
            OVST.PCQ.writeTask(OVST.motionCommandRegister, OVST.moveContinuousValue, Timestamp())
    OVST.inSavetyPosition = False
    OVST.inHomePosition = False


def moveIncrementalAdapter(OVST, targetname, catalogue=None, antennas=None, modbus=None, azTargetRolloverCounter=None,
                           azElOff=[0, 0]):
    '''This function allows moving for a incremental distance
    If 'azTargetRolloverCounter' is not None it will use that azimuth values.
    A modbus connection has to be defined in the :object: 'OVST' :attr: 'PDPList' to use the default of modbus.

    Params
    ------
    targetname: string,   object of :class: 'Target'
        Name of the target on which will be pointed.
        If it is a object of :class: 'Target', catalogue value will be skipped.
        Used in :func: 'check_target'.

    catalogue: object of :class: 'Catalogue'
        It should containing an element called 'targetname'.
        Used in :func: 'check_target'.

    antennas: list objects of :class: 'Antenna'
        If there is no antenna specified the antenna(s) defined in 'catalogue' or
        the antennas defined in the object of :class: 'Target' are used.

    modbus: object of :class: 'ModbusClient'
        Necessary for Modbus Communication.

    azTargetRolloverCounter: array of floats
        a array of possible azimuth start values for each axis in an absolute coordinate without rollovers
        It already mention the goOff in azimuth

    azElOff: list of two floats
        The first entry is the off in azimuth and the second is the off in elevation.
        It is necessary for moving to the correct start position,
        if the goOffPointing does not start at the target itself.
        Azimuth Off is already mentioned in 'azTargetRolloverCounter
    '''
    # if modbus is not defined, use the first one which is stored in OVST.PDPList
    if (modbus == None):
        modbus = (OVST.PDPList[0])
    # if catalogue is not defined, use the first one which is stored in OVST.Catalogue
    if (catalogue == None):
        catalogue = (OVST.Catalogue)
    # if antenna is not defined, use the first one which is stored in OVST.antennaList
    if (antennas == None):
        antennas = (OVST.antennaList)
    # Creates a list of a single antenna
    if not isinstance(antennas, list):
        antennas = [antennas]
    # Initialise that only the selected axis move
    axisToMove = 0
    # azEl has to be defined for elevation
    azEl = check_target(OVST, targetname)

    if not azTargetRolloverCounter == None:
        # make sure that it is a list
        if not isinstance(azTargetRolloverCounter, list):
            azTargetRolloverCounter = [azTargetRolloverCounter]
    for i in range(len(antennas)):
        if (azTargetRolloverCounter == None):
            # Gives the shortest move distance
            azMoveDistance = getMoveDistance(azEl[i][0] + azElOff[0], antennas[i].azElPos[0])
        else:
            # Make the add for each axis seperate because the lenght of the sublist must not be of the same length
            distLst = []
            absLst = []
            # Get the closest azimuth that is closest to the current possition
            for azi in range(len(azTargetRolloverCounter[i])):
                distLst.append(azTargetRolloverCounter[i][azi] - antennas[i].azElPos[0].positionWithoutRollover)
                absLst.append(abs(distLst[azi]))
            # take the shortest azimuth distance
            # a.index(min(a)) index of minimal value
            azMoveDistance = (distLst[absLst.index(min(absLst))])
        # Write the values in the registers
        OVST.PCQ.writeTask(antennas[i].azimuthMoveIncrementalDistanceRegister, (azMoveDistance), Timestamp())
        OVST.PCQ.writeTask(antennas[i].elevationMoveIncrementalDistanceRegister,
                           (getMoveDistance(azEl[i][1] + azElOff[1], antennas[i].azElPos[1])), Timestamp())
        # Add the axis to the list of axis which move when move command occures
        axisToMove += antennas[i].selectValue
    # Write which axis should move
    OVST.PCQ.writeTask(OVST.axisToMoveRegister, axisToMove, Timestamp())
    # Move to the absolute position
    OVST.PCQ.writeTask(OVST.motionCommandRegister, OVST.moveIncrementalValue, Timestamp())
    OVST.inSavetyPosition = False
    OVST.inHomePosition = False


def moveAbsoluteAdapter(OVST,targetname, catalogue=None, antennas=None, modbus=None, tmSp=None, inTrack=False,
                        azElGoOff=[0, 0]):
    '''This function allows moving to an absolute position by writing into the PLC.
    A modbus connection has to be defined in the :object: 'OVST' :attr: 'PDPList' to use the default of modbus.

    Attention
    ---------
    :func: 'moveAbsoluteAdapter' does not check if limit switch will be hit! It belongs to the responsibility of the user.

    Params
    ------
    targetname: string,   object of :class: 'Target'
        Name of the target on which will be pointed.
        If it is a object of :class: 'Target', catalogue value will be skipped.
        Used in :func: 'check_target'

    catalogue: object of :class: 'Catalogue'
        It should containing an element called 'targetname'
        Used in :func: 'check_target'

    antennas: list of object or object of :class: 'Antenna'
        If there is no antenna specified the antenna(s)
        defined in 'catalogue' or the antennas defined in
        the object of :class: 'Target' are used.

    modbus: object of :class: 'ModbusClient'
        Necessary for Modbus communication
        If there is no object defined, the first object of the 'PDPList' in overall
        settings object 'OVST' is used

    tmSp: object of :class: 'Timestamp'
        The Timestamp at which the azimuth and elevation cooordinate calculated.

    inTrack: bool
        If it is true the antennas are not updated during the observation.
        The value is already writtin in the incremental movement to the start position.

    azElGoOff: list of 2 floats
            index 0 is the azimuth Off
            index 1 is the elevation Off
            it is used to go off the target
    '''

    # if modbus is not defined, use the first one which is stored in OVST.PDPList
    if (modbus == None):
        modbus = (OVST.PDPList[0])
    # if catalogue is not defined, use the first one which is stored in OVST.Catalogue
    if (catalogue == None):
        catalogue = (OVST.Catalogue)
    # if antenna is not defined, use the first one which is stored in OVST.antennaList
    if (antennas == None):
        antennas = (OVST.antennaList)

    # Creates a list of a single antenna
    if not isinstance(antennas, list):
        antennas = [antennas]
    # Initialise
    axisToMove = 0
    azEl = check_target(OVST, targetname, tmSp)
    for i in range(len(antennas)):
        # Write the values in the registers
        OVST.PCQ.writeTask(antennas[i].azimuthMoveAbsolutePositionRegister,
                           float(azimuthOffset(azEl[i][0] + azElGoOff[0], antennas[i].azElPos[0].offset)), Timestamp())
        OVST.PCQ.writeTask(antennas[i].elevationMoveAbsolutePositionRegister,
                           float(elevationDegreeToLength(azEl[i][1] + azElGoOff[1], antennas[i].azElPos[1].offset)),
                           Timestamp())
        # Add the axis to the list of axis which move when move command occures
        axisToMove += antennas[i].selectValue
    if not inTrack:
        # Write which axis should move
        OVST.PCQ.writeTask(OVST.axisToMoveRegister, axisToMove, Timestamp())
    # Move to the absolute position
    OVST.PCQ.writeTask(OVST.motionCommandRegister, OVST.moveAbsoluteValue, Timestamp())
    OVST.inSavetyPosition = False
    OVST.inHomePosition = False
