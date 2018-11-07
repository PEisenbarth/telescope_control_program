from katpoint import *
from katcp import *

def _sensorClassModification():
        '''Creates a function which calculates the current position without rollover
        and implements that as a property of :class: 'Sensor'.
        It sets some 
        '''
        def _positionWithoutRollover(self, value): 
            '''calculates the current possition without rollover

            params
            ------
            value: float
                The value without rollover. It is implemented as parameter for use in :meth: 'calculateStatus'

            attributes
            ----------
            rolloverCounter: int
                Indicates the current rollover zone. It is implemented in the BackgroundUpdater
            '''
            if self.isAzimuth:
                return self.rolloverCounter * 360 + value

        def _rolloverCounterMinMax(self):
            '''Helps to get an overview on which position the telescope is
        
                 0 ...  360 degree: returns  0
               360 ...  720 degree: returns  1
               720 ... 1080 degree: returns  2
              -360 ...    0 degree: returns -1  etc.
            '''
            if self.isAzimuth:
                rolloverConterMinMaxLst = []    
                for i in range (len(self.params)):
                    rolloverConterMinMaxLst.append(divmod(self.params[i],360)[0])
                return rolloverConterMinMaxLst

        def _valueToString(self):
            try:
                return self.stringDict[self.value()]
            except KeyError:
                return "Not handled Value."

        def _calculateStatus(self, value):
            '''Default for calculating the status. If it is outer the 'params' it returns a status.
            If it 'isAzimuth' it calculates first the value without rollover. 
            The rolloverCounter is updated a step before the call of this mehtod in :meth: 'SensorUpdateThread.run'.

            params
            ------
            value: int or float
                The new value from the PLC, which is the new '_value' of the sensor object.

            attributes
            ----------
            params: List of two ints or floats
                The limits of the Sensor.
                
            raiseStatus: int
                {0: 'unknown', 1: 'nominal', 2: 'warn', 3: 'error', 4: 'failure', 5: 'unreachable', 6: 'inactive'}
                The status which is returned if the value is not in range of 'params'
                Default is unknown

            return
            ------
            status: int
                {0: 'unknown', 1: 'nominal', 2: 'warn', 3: 'error', 4: 'failure', 5: 'unreachable', 6: 'inactive'}
                If the value is in range it returns 'nominal'
            '''
            if self.isAzimuth:
                value = self._positionWithoutRolloverMethod(value)
            if self.params == None or not isinstance(self.params,list):
                return 0 # unknown because missing information
            elif value>=self.params[0] and value<=self.params[1]:
                return 1 # everything is ok
            else: # not in range
                return self.raiseStatus # the predefined status for a Sensor


        Sensor._positionWithoutRolloverMethod = _positionWithoutRollover
        Sensor.positionWithoutRollover = property(lambda self: self._positionWithoutRolloverMethod(self.value()))
        Sensor._rolloverCounterMinMaxMethod = _rolloverCounterMinMax
        Sensor.rolloverCounterMinMax = property(lambda self: self._rolloverCounterMinMaxMethod())
        Sensor._valueToStringMethod = _valueToString
        Sensor.valueToString = property(lambda self: self._valueToStringMethod())
        Sensor.raiseStatus = 0 # predefined as unknown
        Sensor.calculateStatus = _calculateStatus
        Sensor.isAzimuth=False
        Sensor.isElevation=False
        Sensor.isMoveIncremental=False
        Sensor.refRegister=None
