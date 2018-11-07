import threading
from katpoint import Timestamp
import time
from Queue import PriorityQueue 
from BackgroundUpdater import SensorUpdateThread
from pymodbus.exceptions import ConnectionException

class PLCCommunicationQueue (PriorityQueue):
    def readTask(self,*args):
        '''Handles reading tasks.

        params
        ------
        args: not used
        '''
        PriorityQueue.put(self, (5, Timestamp(), args))
        
    def writeTask(self, register, value,tmSp=None,):
        '''Handles writing tasks. It is sorted intern by timestamp so that it keeps the correct order.
        
        params
        ------
        register:
            The register which will be written.

        value:
            The value which is written in the register.

        tmSp: object of :class: 'Timestamp'
            It have to be a param because otherwise all commands of a method for instance :meth: 'moveIncrementalAdapter' get the same timestamp.
            As a result it is sorted by the register in which it writes and it is not a good idea to send first a move command and then set the distance.
            In less critical commands like :meth: 'enableTelescopes' the default can be used
        '''
        if not isinstance(tmSp,Timestamp):
            tmSp = Timestamp()
        PriorityQueue.put(self, (3, tmSp, (register,value)))
        time.sleep(0.002) # Makes sure that the next command get another 'Timestamp'

    def writeImportantTask(self,register, value):
        '''Handles writing tasks with higher priority. It is sorted intern by timestamp so that it keeps the correct order.
        It should be used for commands when exceptions occure.#

        params
        ------
        register:
            The register which will be written.

        value:
            The value which is written in the register.
        '''
        PriorityQueue.put(self, (2, Timestamp(), (register,value)))

class PLCCommunicationThread(threading.Thread):
    def __init__(self, name, OVST):
        '''
        The class updates objects of :class: 'Sensor'.
        Creating a object of :class: 'PLCCommunicationThread' also starts the thread. 
        The params are described in the class description
        
            params
        ------
        name: string
            A name for the object

        OVST: object of :class: 'OverallSettings'
            It uses
            PDPList[0]: object of :class: 'PythonDiagnosticProgramm'
                Necessary to use a modbus connection to read #UPDATE

            sensorUpdaterList: object of :class: 'Sensor'
                The sensor which value is updated. 
                Its argument 'refRegister' define the number 
                of the register which will be read.

            PCQ: object of :class: 'PLCCommunicationQueue'
            The thread works through the elements of this PCQ Queue.
        '''
        threading.Thread.__init__(self)
        self.OVST = OVST
        self.OVST.pointingLog = [[],[]]
        # start the thread
        self.start()
        
    def run(self):
        '''Infinite loop which updates a object of :class: 'Sensor' or sends commands to the PLC.
        It is called with 'BackgroundUpdaterObject.start()' in the command line.
        
        '''
        

        while True:
            # Add a readout command to the Queue if the Queue is not too long. Important for the first loop
            if self.OVST.PCQ.qsize() < 5:
                self.OVST.PCQ.readTask()
            # get the command
            priority,tmSp, args = self.OVST.PCQ.get()
            # if it is a reading task, the priority is 5
            if priority == 2:
                successful=False
                while not successful:
                    try:
                        self.OVST.PDPList[0].modbusWrite(args[0],args[1])
                        successful=True
                        #print "Send the priority 2 command '%r' to address '%r' at %s" %(args[1],args[0],Timestamp().to_string())
                    except OverflowError: 
                        print "OverflowError 'Writing Priority' at %r " % Timestamp()
                    except ConnectionException:
                        connectionExceptionHandling(self)
                    except AttributeError:
                        connectionExceptionHandling(self)
                    except IndexError:
                        # it is disconnected manually
                        setConnectionStatus(self)
                time.sleep(1) # avoid other commands for 1 seconds
            elif priority == 5:
                try:
                    # Process the command
                    returnValue = self.OVST.PDPList[0].modbusReadOutAll()
                    self.OVST.ConnectionStatus.set(Timestamp(), 1, True)
                except OverflowError: 
                        print "OverflowError Reading at %r " % Timestamp()
                except ConnectionException:
                    connectionExceptionHandling(self)
                except AttributeError:
                    connectionExceptionHandling(self)
                except IndexError:
                    # it is disconnected manually
                    setConnectionStatus(self)
                try:
                    #Check if the SUT is finished with working
                    if not self.OVST.SUT.is_alive():
                        self.OVST.SUT = SensorUpdateThread(returnValue,self.OVST)
                except AttributeError: # If the name is None 
                    try:
                        self.OVST.SUT = SensorUpdateThread(returnValue,self.OVST)
                    except UnboundLocalError:
                        pass #Just do not update: it happens when updating is not possible because of a lost modbus connection 
            if (priority == 3) & (not self.OVST.error): # it is a writing task
                # The asking for a error makest that it doesnot Move furhter. 
                # It is necessary because even if the telescope will be telescope disabled, the next 'moveAbsoluteCommand' cause it to move.
                try:
                    self.OVST.PDPList[0].modbusWrite(args[0],args[1])
                except OverflowError:
                    print "OverflowError Writing at %r " % Timestamp()
                    print "lenght of PCQ (not reliable)", (self.OVST.PCQ.qsize())
                except ConnectionException:
                    connectionExceptionHandling(self)
                except AttributeError:
                    connectionExceptionHandling(self)
                except IndexError:
                    # it is disconnected manually
                    setConnectionStatus(self)
                if args[0] == self.OVST.antennaList[0].azimuthMoveIncrementalDistanceRegister:
                    self.OVST.pointingLog[0].append(args[1])
                if args[0] == self.OVST.antennaList[0].elevationMoveIncrementalDistanceRegister:
                    self.OVST.pointingLog[1].append(args[1])

            # Indicates the Queue that the task is done.
            self.OVST.PCQ.task_done()

def connectionExceptionHandling(self):
            ''' Handles the event of a 'ConnectionException' with the modbus.
            It sets the 'ConnectionStatus' on 'False' and try to reconnect.
            '''
            print "Handle connection exception at %s."%Timestamp().to_string()
            setConnectionStatus(self)
            while not self.OVST.ConnectionStatus.value()==True and not self.OVST.disconnectedManually:
            #Reconnection if not disconnected manually
                self.OVST.openModbusConnections() #sets OVST.ConnectionStatus.value()=True
                try:
                    self.OVST.PDPList[0].modbusReadOut(1) # With default start address ist does not work
                except AttributeError:
                    setConnectionStatus(self)
                except ConnectionException:
                    setConnectionStatus(self)

def setConnectionStatus(self):
    self.OVST.ConnectionStatus.set(Timestamp(), 5, False)
