from katcp import Sensor
from katpoint import Antenna


                ### This file contains the telescope specific settings. ###
    ### To use this program on an other telescope you need to adapt this  file to your setup ###

# IP for the Modbus connection used in Python Diagnostic Program
modbus_ip = '192.168.0.250'
modbus_port = 502


def init_wetton_telescope(OVST):
    def _addToSensorList(OVST, sensor):
        '''A method which appends a sensor to the :list: 'sensorUpdaterList' and makes the settings
        sothat the sensors have an 'error' status if they are not in range.
        It is important that the :list: 'sensorUpdaterList' is ordered correct. It is used for updating the window.
        For easy handling order it following: first the sensors which value should be displayed as number and string.
        Then the sensors which value is just necessary as number.


        params
        ------
        sensor: object of :class: 'Sensor'
            Sensor which is appended.
        '''
        sensor.raiseStatus = 3  # 'error'
        OVST.sensorUpdaterList.append(sensor)

    # directory in which the position data gets stored
    OVST.daq_dirpath = '/home/telescopecontrol/philippe/DAQ/antenna_positions'

    OVST.az_limit = [173, 150]
    OVST.el_limit = [25, 95]

    # Values for writing
    OVST.axisToMoveRegister = 21
    OVST.motionCommandRegister = 20
    OVST.moveIncrementalValue = 13
    OVST.moveContinuousValue = 15

    # Status Sensors
    OVST.BasicError = (Sensor(Sensor.INTEGER, 'BasicError',
                              'If a BASIC error is detected this VR reports the process number for which the error occurred %s',
                              params=[0, 0], default=0))
    OVST.BasicError.refRegister = 2
    OVST.BasicError.stringDict = {0: "No BASIC error",
                                  1: "BASIC error in STARTUP",
                                  2: "BASIC error in MONITOR",
                                  3: "BASIC error in MAIN",
                                  4: "BASIC error in VR-UPDATE",
                                  5: "Other user process"  # other values are also possible but not handled
                                  }
    _addToSensorList(OVST, OVST.BasicError)

    OVST.CurrentSystemStatus = (
        Sensor(Sensor.INTEGER, 'Current System Status', 'Reports current system status', params=[0, 7],
               initial_status=0))
    OVST.CurrentSystemStatus.refRegister = 10
    OVST.CurrentSystemStatus.stringDict = {0: "System initialising",
                                           1: "Axes disabled",
                                           2: "System ready",
                                           3: "Homing all axes",
                                           4: "Jogging an axis",
                                           5: "Moving to Inc or Abs position",
                                           6: "Running main routine",
                                           7: "stopping",
                                           99: "fault"}
    _addToSensorList(OVST, OVST.CurrentSystemStatus)

    OVST.FaultCode = (
        Sensor(Sensor.INTEGER, 'Fault Code', 'In the event of a system fault this VR reports the fault code',
               params=[0, 0], initial_status=0))
    OVST.FaultCode.refRegister = 11
    OVST.FaultCode.stringDict = {0: "No fault present",
                                 1: "Emergency stop active",
                                 2: "CAN I/O Fault",
                                 3: "Telescope 1 Elevation forward limit switch hit",
                                 4: "Telescope 1 Elevation reverse limit switch hit",
                                 5: "Telescope 1 Azimuth forward limit switch hit",
                                 6: "Telescope 1 Azimuth reverse limit switch hit",
                                 7: "Telescope 2 Elevation (or Azimuth) forward limit switch hit",
                                 8: "Telescope 2 Elevation (or Azimuth) reverse limit switch hit",
                                 9: "Telescope 2 Azimuth (or Elevation) forward limit switch hit",
                                 10: "Telescope 2 Azimuth (or Elevation) reverse limit switch hit",
                                 11: "Telescope 1 Elevation drive comms fault",
                                 12: "Telescope 1 Azimuth drive comms fault",
                                 13: "Telescope 2 Elevation drive comms fault",
                                 14: "Telescope 2 Azimuth drive comms fault",
                                 15: "Telescope 1 Elevation drive fault",
                                 16: "Telescope 1 Azimuth drive fault",
                                 17: "Telescope 2 Elevation drive fault",
                                 18: "Telescope 2 Azimuth drive fault",
                                 19: "Telescope 1 Elevation following error fault",
                                 20: "Telescope 1 Azimuth following error fault",
                                 21: "Telescope 2 Elevation following error fault",
                                 22: "Telescope 2 Azimuth following error fault",
                                 99: "BASIC error"}
    _addToSensorList(OVST, OVST.FaultCode)

    OVST.AxisWarningsLimitSwitchHits = (Sensor(Sensor.INTEGER, 'Axis Warnings and software limitswitch hits',
                                               'Reports any system warnings that do not result in program interruption. Also combinations are possible. They are not handled',
                                               params=[0, 0], initial_status=0))
    OVST.AxisWarningsLimitSwitchHits.refRegister = 14
    OVST.AxisWarningsLimitSwitchHits.stringDict = {0: "No fault present",
                                                   1: "Telescope 1 Elevation forward software limit, ",
                                                   2: "Telescope 1 Elevation reverse software limit, ",
                                                   4: "Telescope 1 Azimuth forward software limit, ",
                                                   8: "Telescope 1 Azimuth reverse software limit, ",
                                                   16: "Telescope 2 Elevation forward software limit, ",
                                                   32: "Telescope 2 Elevation reverse software limit, ",
                                                   64: "Telescope 2 Azimuth forward software limit, ",
                                                   128: "Telescope 2 Azimuth reverse software limit, ",
                                                   256: "Telescope 1 Elevation warning following error, ",
                                                   512: "Telescope 1 Azimuth warning following error, ",
                                                   1024: "Telescope 2 Elevation warning following error, ",
                                                   2048: "Telescope 2 Azimuth warning following error, "}
    _addToSensorList(OVST, OVST.AxisWarningsLimitSwitchHits)

    OVST.CurrentMotionCommand = (Sensor(Sensor.INTEGER, 'Axis Warnings and software limitswitch hits',
                                        'Call motion command if conditions are met', params=[0, 15], initial_status=0))
    OVST.CurrentMotionCommand.refRegister = 20
    OVST.CurrentMotionCommand.stringDict = {0: "Stop motion",
                                            1: "Enable axes",
                                            2: "Disable axes",
                                            3: "Home all axes",
                                            4: "Telescope 1 Elevation forward jog",
                                            5: "Telescope 1 Elevation reverse jog",
                                            6: "Telescope 1 Azimuth forward jog",
                                            7: "Telescope 1 Azimuth reverse jog",
                                            8: "Telescope 2 Elevation forward jog",
                                            9: "Telescope 2 Elevation reverse jog",
                                            10: "Telescope 2 Azimuth forward jog",
                                            11: "Telescope 2 Azimuth reverse jog",
                                            12: "Move absolute on selected axis",
                                            13: "Move incremental on selected axis",
                                            14: "Start main sequence",
                                            15: "Move continuous on selected axis"}  # Start Main Sequence is not recognized as fault
    _addToSensorList(OVST, OVST.CurrentMotionCommand)

    OVST.ConnectionStatus = Sensor(Sensor.BOOLEAN, "Connection Status",
                                   "Describes the current status of the modbus connection", params=[True, True])
    OVST.ConnectionStatus.stringDict = {False: "Not connected", True: "Connected"}
    OVST.sensorUpdaterList.append(OVST.ConnectionStatus)

    # Create an antenna
    RTT = Antenna("Roof Top Telescope (Shed Side)", '51:45:34.5', '-1:15:34.8', 85)  # height is not exact
    # Define the registers
    # Absolute Position and Speed
    RTT.azimuthMoveAbsolutePositionRegister = 221
    RTT.azimuthMoveAbsoluteSpeedRegister = 225
    RTT.elevationMoveAbsolutePositionRegister = 121
    RTT.elevationMoveAbsoluteSpeedRegister = 125

    # Incremental
    RTT.azimuthMoveIncrementalDistanceRegister = 220
    RTT.elevationMoveIncrementalDistanceRegister = 120

    RTT.selectValue = 3  # Allow moving azimuth and elevation

    # Specify the antennas delaychannel
    # [channelNumber, hasPartialDelay, hardwareDelay, goemetricDelay]
    RTT.delayInfo = [0, False, 0, 0]

    OVST.antennaList.append(RTT)

    # Sensor Settings
    # Create a list with objects of :class: 'Sensors' , representing azimuth (index 0) and elevation (index 1)
    azElSensRTT = []

    # The Limits could be read out from the PLC. BUT not forget the offset
    azElSensRTT.append(
        Sensor(Sensor.FLOAT, 'AzimuthRTT', 'Describes the Azimuth of RoofTopTTelescope', 'degree', [-187, 150]))
    azElSensRTT.append(
        Sensor(Sensor.FLOAT, 'ElevationRTT', 'Describes the Elevation of RoofTopTTelescope', 'degree', [25, 95]))

    # Add the PLC registers where the encoder value is stored
    azElSensRTT[1].refRegister = 130  # Elevation
    azElSensRTT[0].refRegister = 230  # Azimuth
    # flag elvation registers; Not flaged Sensors work as azimuth
    azElSensRTT[1].isElevation = True
    azElSensRTT[0].isAzimuth = True
    # Hard coded offset, maybe it could be done by reading out the PLC
    azElSensRTT[1].offset = -41  # 21.04.2017
    azElSensRTT[0].offset = 266

    # If the value changes more than the 'maxDeltaWithoutRolloverDetection', it is interpret as Rollover
    azElSensRTT[0].maxDeltaWithoutRolloverDetection = 90

    # Include the property of psition without rollover reset

    # The values of antenna 1
    OVST.sensorList.append(azElSensRTT[0])  # add azimuth
    OVST.sensorList.append(azElSensRTT[1])  # add elevation


    # Concatenate the objecs of :class: 'Sensor' with a object of :class: 'antenna'
    RTT.azElPos = [OVST.sensorList[0], OVST.sensorList[1]]  # First the azimuth and then the elevation

    # Create an antenna
    RTT2 = Antenna("Roof Top Telescope 2 (Stairs Side)", '51:45:34.6', '-1:15:34.9', 85)  # height is not exact

    # Define the registers
    RTT2.azimuthMoveAbsolutePositionRegister = 421
    RTT2.elevationMoveAbsolutePositionRegister = 321
    RTT2.azimuthMoveAbsoluteSpeedRegister = 425
    RTT2.elevationMoveAbsoluteSpeedRegister = 325

    # Incremental
    RTT2.azimuthMoveIncrementalDistanceRegister = 420
    RTT2.elevationMoveIncrementalDistanceRegister = 320

    # select Value
    RTT2.selecaskRolloverCountertValue = 0b1100  # Allow moving azimuth and elevation

    # Specify the antennas delaychannel
    # [channelNumber, hasPartialDelay, hardwareDelay, goemetricDelay]
    RTT2.delayInfo = [1, True, 15 * 4 + 7, 0]

    OVST.antennaList.append(RTT2)

    # Sensor Settings
    # Create a list with objects of :class: 'Sensors' , representing azimuth (index 0) and elevation (index 1)
    azElSensRTT2 = []

    # The Limits could be read out from the PLC. BUT not forget the offset
    azElSensRTT2.append(
        Sensor(Sensor.FLOAT, 'AzimuthRTT2', 'Describes the Azimuth of RoofTopTelescope 2', 'degree', [-187, 150]))
    azElSensRTT2.append(
        Sensor(Sensor.FLOAT, 'ElevationRTT2', 'Describes the Elevation of RoofTopTTelescope 2', 'degree', [25, 95]))

    # Add the PLC registers where the encoder value is stored
    azElSensRTT2[1].refRegister = 330  # Elevation
    azElSensRTT2[0].refRegister = 430  # Azimuth
    # flag elevation registers; Not flagged Sensors work as azimuth
    azElSensRTT2[1].isElevation = True
    azElSensRTT2[0].isAzimuth = True
    # Hard coded offset, maybe it could be done by reading out the PLC
    azElSensRTT2[1].offset = -65
    azElSensRTT2[0].offset = 208.4

    # If the value changes more than the 'maxDeltaWithoutRolloverDetection', it is interpret as Rollover
    azElSensRTT2[0].maxDeltaWithoutRolloverDetection = 90

    # Include the property of possition without rollover reset
    # The values of antenna 2
    OVST.sensorList.append(azElSensRTT2[0])  # add azimuth
    OVST.sensorList.append(azElSensRTT2[1])  # add elevation

    # Concatenate the objecs of :class: 'Sensor' with a object of :class: 'antenna'
    RTT2.azElPos = [OVST.sensorList[2], OVST.sensorList[3]]  # First the azimuth and then the elevation

    RTT2.selectValue = 0b1100

    # Add the list to the sensor list which is used for updating
    OVST.sensorUpdaterList = OVST.sensorUpdaterList + OVST.sensorList  # + self.moveIncrSensLst + self.moveAbsSensLst

