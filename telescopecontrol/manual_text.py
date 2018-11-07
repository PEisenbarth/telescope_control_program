import numpy as np


def get_manual_text(address, registerValue=0, description=False):
    ''' 
    format of the addresses dictionary:
    {address value: [description, {dict for register values}] }    
    '''
    returnText = registerValue
    if address<100:
        addresses_list= range(6)+[10, 11, 13, 14, 15, 16, 20, 22]
        addresses = {
                    0:      "Reports the application software version",
                    1:      "Reports the controller firmware version",
                    2:      ["If a BASIC error is detected this VR reports the process number for which the error occurred: ",
                                str(registerValue) + '\t' +
                                            {
                                                0:      "No BASIC error",
                                                1:      "BASIC error in STARTUP",
                                                2:      "BASIC error in MONITOR",
                                                3:      "BASIC error in MAIN",
                                                4:      "BASIC error in VR-UPDATE",
                                                5:      "Other user process"
                                            }[5 if registerValue > 4 else registerValue],],
                    3:      "If a BASIC error is detected this VR reports the process line number for which the error occurred",
                    4:      "If a BASIC error is detected this VR reports the error code",
                    5:      "Sets axes to default settings after next power cycle",
                    10:     ["Reports current system status",
                                            {
                                                0:      "System initialising",
                                                1:      "Axes disabled",
                                                2:      "System ready",
                                                3:      "Homing all axes",
                                                4:      "Jogging an axis",
                                                5:      "Moving to Inc or Abs position",
                                                6:      "Running main routine",
                                                7:      "stopping",
                                                99:     "fault",
                                                100:    ""
                                            }[registerValue if registerValue < 8 or registerValue == 99 else 100]],
                    11:     ["In the event of a system fault this VR reports the fault code:  ",
                                        {
                                                0:      "No fault present",
                                                1:      "Emergency stop active",
                                                2:      "CAN I/O Fault",
                                                3:      "X forward limit switch hit",
                                                4:      "X reverse limit switch hit",
                                                5:      "Y forward limit switch hit",
                                                6:      "Y reverse limit switch hit",
                                                7:      "Z forward limit switch hit",
                                                8:      "Z reverse limit switch hit",
                                                9:      "R forward limit switch hit",
                                                10:     "R reverse limit switch hit",
                                                11:     "Axis 0 drive comms fault",
                                                12:     "Axis 1 drive comms fault",
                                                13:     "Axis 2 drive comms fault",
                                                14:     "Axis 3 drive comms fault",
                                                15:     "Axis 0 drive fault",
                                                16:     "Axis 1 drive fault",
                                                17:     "Axis 2 drive fault",
                                                18:     "Axis 3 drive fault",
                                                19:     "Axis 0 following error fault",
                                                20:     "Axis 1 following error fault",
                                                21:     "Axis 2 following error fault",
                                                22:     "Axis 3 following error fault",
                                                99:     "BASIC error",
                                                100:    ""
                                        }[registerValue if registerValue < 23 or registerValue == 99 else 100]],
                    13:     ["Reports of the system has been homed. This flag is reset if a fault is detected. ",
                                        {
                                                0:      "Axis not homed",
                                                1:      "home completed successfully",
                                                100:    ""
                                        }[registerValue if registerValue<2 else 100]],
                    14:     ["Reports any system warnings that do not result in program interruption",
                                        {
                                                1:      "%s \t %s" % (bin(registerValue), " X forward software limit, "),
                                                2:      "%s \t %s" % (returnText, "X reverse software limit, "),
                                                4:      "%s \t %s" % (returnText, "Y forward software limit, "),
                                                8:      "%s \t %s" % (returnText, "Y reverse software limit, "),
                                                16:     "%s \t %s" % (returnText, "Z forward software limit, "),
                                                32:     "%s \t %s" % (returnText, "Z reverse software limit, "),
                                                64:     "%s \t %s" % (returnText, "R forward software limit, "),
                                                128:    "%s \t %s" % (returnText, "R reverse software limit, "),
                                                256:    "%s \t %s" % (returnText, "X warning following error, "),
                                                512:    "%s \t %s" % (returnText, "Y warning following error, "),
                                                1024:   "%s \t %s" % (returnText, "Z warning following error, "),
                                                2048:   "%s \t %s" % (returnText, "R warning following error, "),
                                                10000:  ""
                                        }[registerValue if registerValue != 0 and ((registerValue & (registerValue - 1)) == 0) else 10000]],
                    15:     ["Reports digital I/O state of inputs 0 to 31",
                            "%s \t %s" % (bin(_IEEE754reverse(registerValue)), " State of input or I/O point x (0 to 31)")],
                    16:     ["Reports digital I/O state of inputs 32 to 63",
                            "%s \t %s" % (bin(_IEEE754reverse(registerValue)), " State of input or I/O point x (32 to 63)")],
                    20:     "Call motion command if conditions are met",
                    22:     ["Acknowledge fault to clear",
                                        {
                                                0:      "0 \t No fault/fault acknowledged",
                                                1:      "1 \t Acknowledge fault",
                                                100:    ""
                                        }[registerValue if registerValue<1 else 100]],
                    100:    ""


        }[address if address in addresses_list else 100]
        return '%i \t %i \t %s \n'%(address, registerValue, addresses[not description])
    else:
        addressend = address % 100
        if (address < 200):
            axisText = "X"
        elif (address < 300):
            axisText = "Y"
        elif (address < 400):
            axisText = "Z"
        elif (address < 500):
            axisText = "R"
        if (addressend == 1):
            description = "%s %s" % (axisText, "limit switch configuration")
            if (registerValue == 0): returnText = "No limit switches (or no axis)"
            if (registerValue == 1): returnText = "N/C limit switches"
            if (registerValue == 2): returnText = "N/O limit switches"
            returnText = "%s \t %s" % (registerValue, returnText)
        if (addressend == 2):
            description = "%s %s" % (axisText, "limit switch configuration")
            if (registerValue == 0): returnText = "No home switches (or no axis)"
            if (registerValue == 1): returnText = "N/C home switches, forward home"
            if (registerValue == 2): returnText = "N/O home switches, forward home"
            if (registerValue == 3): returnText = "N/C home switches, reverse home"
            if (registerValue == 4): returnText = "N/O home switches, reverse home"
            returnText = "%s \t %s" % (registerValue, returnText)
        if (addressend == 3):
            description = "%s %s %s" % ("Steps per rev of the", axisText, "axis")
            returnText = "%s \t %s" % (registerValue, " steps/rev")
        if (addressend == 4):
            description = "User unit setting"
            returnText = "%s \t %s" % (registerValue, " User units per motor revolution")
        if (addressend == 5):
            description = "Rollover position"
            returnText = "rollover position in user units"
        if (addressend == 6):
            description = "Rollover option"
            if (registerValue == 0): returnText = "+/- Rollover position"
            if (registerValue == 1): returnText = "0 to rollover position"
            returnText = "%s \t %s" % (registerValue, returnText)
        if (addressend == 7):
            description = "Reverse software limit position (applied after homing)"
            returnText = "%s \t %s" % (registerValue, " Absolute position in user units")
        if (addressend == 8):
            description = "Forward software limit position (applied after homing)"
            returnText = "%s \t %s" % (registerValue, " Absolute position in user units")
        if (addressend == 9):
            description = "Jog speed and homing speed"
            returnText = "%s \t %s" % (registerValue, " Speed in user units/sec")
        if (addressend == 10):
            description = "Creep speed during homing"
            returnText = "%s \t %s" % (registerValue, " Speed in user units/sec")
        if (addressend == 11):
            description = "Move Abs/Inc speed"
            returnText = "%s \t %s" % (registerValue, " Speed in user units/sec")
        if (addressend == 12):
            description = "Acceleration and deceleration"
            returnText = "%s \t %s" % (registerValue, " Accel/decel in user units/sec2")
        if (addressend == 13):
            description = "S-curve time"
            returnText = "%s \t %s" % (registerValue, " S-curve time")
        if (addressend == 20):
            description = "Incremental move distance"
            returnText = "%s \t %s" % (registerValue, " Distance in user units")
        if (addressend == 21):
            description = "Absolute move target position"
            returnText = "%s \t %s" % (registerValue, " Absolute position in user units")
        if (addressend == 22):
            description = "Distance axis will move to clear limit switch"
            returnText = "%s \t %s" % (registerValue, " Distance in user units")
        if (addressend == 30):
            description = "%s %s" % (axisText, " axis current position")
            returnText = "%s \t %s" % (registerValue, " Actual value in user units")


def _IEEE754reverse(valueIntoVR):
    valueAsInt = np.asarray(abs(valueIntoVR), dtype=np.float32).view(np.int32).item()
    if (valueIntoVR<0):
        valueAsInt = valueAsInt | 0x80000000
    return (valueAsInt)
