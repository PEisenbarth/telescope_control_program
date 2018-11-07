from katpoint import Timestamp
import threading
import math


class SensorUpdateThread(threading.Thread):
    def __init__(self, arrayFromPLC, OVST):
        '''This thread assigns the values of the sensors with the values from the PLC.
        It also handles changing statuses.

        params
        ------
        arrayFromPLC: array
              The readout array, returned with 'modbusReadOutAll()'
              
        OVST: object of :class: 'OverallSettings'
            It uses
            sensorUpdaterList: List of objects of :class: 'Sensor'
                The sensor which will be updated.
            
            PCQ: object of :class: PLCCommunicationQueue
                Allows to set a new command to the PLC. It is used when a status change occur.  
        '''
        threading.Thread.__init__(self)
        self.name = "SensorUpdateThread"
        self.lock = threading.Lock()
        self.OVST = OVST
        self.arrayFromPLC = arrayFromPLC
        
        # start the thread
        self.start()

    def run(self):
        '''The logic behind assigning the values and statuses of the sensors.
        '''
        def printArray(self, name ,num):
            ''' This mehtod prints 'arrayFromPLC' when a status change its value.
            The sensors object which have a status change, are also displayed but the array only one time.

            params
            ------
            name: str
                Name of the sensor which causes the print

            num: int
                The problematic status of the sensor
            '''
            if not self.arrayAlreadyPrinted:
                print self.arrayFromPLC
                self.arrayAlreadyPrinted =True  
            print " @ Sensor '%s', status '%i', Timestamp %s"%(name, num, Timestamp().to_string())

        self.arrayAlreadyPrinted = False # To avoid printing the same array several times
        for i in range(len(self.OVST.sensorUpdaterList)):
            if not self.OVST.sensorUpdaterList[i].refRegister ==None:

                index1, index2 = divmod(self.OVST.sensorUpdaterList[i].refRegister,100)
                value = self.arrayFromPLC[index1][index2]
                if (self.OVST.sensorUpdaterList[i].isMoveIncremental==True):# Handles 'moveIncrementalDistance's
                    # Transform the 'moveIncrementalDistance' into a position 
                    index1, index2 = divmod(self.OVST.sensorUpdaterList[i].isValueRefRegister,100)
                    value += self.arrayFromPLC[index1][index2]
                elif (self.OVST.sensorUpdaterList[i].isElevation == True): # Handles Elevation
                    value = self.elevationLengthToDegree(value,self.OVST.sensorUpdaterList[i])
                elif (self.OVST.sensorUpdaterList[i].isAzimuth == True): # Handles Azimuth 
                    value = (value + 360 - self.OVST.sensorUpdaterList[i].offset) % 360
                    # It is important to update  the 'rolloverCounter' here, for further use in :meth: 'calculateStatus'
                    self.rolloverUpdate(value,self.OVST.sensorUpdaterList[i])
                status = self.OVST.sensorUpdaterList[i].calculateStatus(value)
                # {0: 'unknown', 1: 'nominal', 2: 'warn', 3: 'error', 4: 'failure', 5: 'unreachable', 6: 'inactive'}
                # It is important that only changes are processed. it allows to clear the fault.
                if not self.OVST.sensorUpdaterList[i].status() == status: 
                    if status == 2: 
                        self.OVST.PCQ.writeImportantTask(20, 0) #telescope Halt
                        printArray(self,self.OVST.sensorUpdaterList[i].name,2)
                    elif status == 3:
                        #telescope Disable
                        self.OVST.PCQ.writeImportantTask(20, 2) 
                        # is only set by the cange of 'False' to 'True', sothat it can be cleared by 'OVST.clearTelescopeFault()'
                        self.OVST.error = True 
                        try:
                            self.OVST.currentCatalogue.halt = True
                        except AttributeError:
                            pass #There is no Catalogue tracked
                        # Kill the current 'TrackTarget' Thread
                        if not self.OVST.currentTrack == None: 
                            self.OVST.currentTrack.halt=True
                        printArray(self,self.OVST.sensorUpdaterList[i].name,3)
                    elif status == 4: # Unused. 
                        self.OVST.PCQ.writeImportantTask(20, 2) #telescope Disable 
                        printArray(self,self.OVST.sensorUpdaterList[i].name,4)
                        
                    elif status == 5:  # It tries to reconnect at the point when the 'ConnectionException' Occures
                        printArray(self,self.OVST.sensorUpdaterList[i].name,5)
                    elif status == 6:  #Indicates that a value is older than 5 seconds
                        printArray(self,self.OVST.sensorUpdaterList[i].name,6)

                self.lock.acquire()
                self.OVST.sensorUpdaterList[i].set(Timestamp(),status,value)
                self.lock.release()
          

        readFailCounter = 0
        

    def elevationLengthToDegree(self, lengthparam, antennaSensor):
        '''Converts the elevation value from lenght in degrees 
        '885.205' is the length of the box of the zylinder box.
        The result has to be subtracted from '90' 
        because the fit has its '0' at elevation '90'

        params
        ------
        lengthparam: float
            Value of the elevation register in millimeter

        antennaSensor: object of :class: 'Antenna'
            Necessary to get the Offset of the antenna

        returns
        -------
        degree: float
            elevation in degree
        '''
        length = ((lengthparam - antennaSensor.offset) - 885.205) 
        try: 
            return 90 - ((math.pi - math.acos(0.000001160803620 * length * length - 1.650894908) + math.atan2(3,38) - math.asin(float(411)/565)) * 180 / math.pi)
            
        except ValueError:
            print '''It is not possible to convert the elevation.  
The input lenght from the register is %r
It calculates with the length %r''' %(lengthparam, length)
        except AttributeError:
            print '''It is not possible to convert the elevation.  
Sensor does not have a offset .  
'''

    def rolloverUpdate(self,newValue, antennaSensor):
        '''Updates the attribute 'rolloverCounter' at objects of 
        :class: 'Sensor' with the attribute 'isElevation == False'. 
        That means that they are azimuth sensors.
        Because the new value is not overgiven already the value in the antennaSensor is the old one.

        params
        ------
        newValue: float
            The value which has been read.

        antennaSensor: object of :class: 'Antenna'
            The antenna sensor which is checked for a rollover
        '''
        try:
            oldValue = antennaSensor.value()
            if not oldValue == 0: # Avoids troubles during start up
                delta = abs(newValue - oldValue)
                if (delta>antennaSensor.maxDeltaWithoutRolloverDetection):
                    if oldValue < newValue:
                         counter = -1
                    if oldValue > newValue:
                        counter = 1
                    self.lock.acquire()
                    antennaSensor.rolloverCounter += counter
                    self.lock.release()
        except AttributeError:
            print '''It is not possible to convert the azimuth.  
Sensor %s does not have a offset or 'maxDeltaWithoutRolloverDetection'.  
''' % antennaSensor.name