from Tkinter import *
import threading
import time
from EntryWindow import EntryWindow
from CatalogueEntryWindow import CatalogueEntryWindow
from katpoint import Timestamp

class ControlWindow(Tk):
    def __init__(self, master, OVST,  offset):
        ''' The window class

        params
        ------
        sensorList: A list of objects of :class: 'Sensor'
            The sensors which should be displayed. 
            The order of the list is important

        offset: int
            The index at which Azimuth and Elevation values starts at the 'sensorList'
        '''   
      
        self.master = master
        self.frame = Frame(master)    
        self.offset = offset
        self.OVST = OVST
        #self.callback = callback
        # Fenster
        self.master.title("Control Window")
        self.master.geometry('800x600')
        
        #MenuBar
        menubar = Menu(self.master)
        fileMenu = Menu(menubar)
        fileMenu.add_command(label="Add Catalogue", command=self.openCatalogueEntryWindow)
        fileMenu.add_command(label="Add Raster Discrete", command=self.openRasterDiscreteEntryWindow)
        fileMenu.add_command(label="Add Raster", command=self.openRasterEntryWindow)
        fileMenu.add_command(label="Add Lissajous", command=self.openLissajousEntryWindow)
        fileMenu.add_command(label="Add Pong", command=self.openPongEntryWindow)
        menubar.add_cascade(label="Add", menu=fileMenu)
        self.master.config(menu = menubar)
        
        
        # Measures
        self.x1 = 20 #fist column
        self.x2 = 180 # second  column
        self.x3 = 260 # third column
        self.x4 = 360 # fourth column

        # Column 2 header 1
        self.lblColumn2Header1 = Label(master=self.master, text='in degree:')
        self.lblColumn2Header1.place(x=self.x2, y=20)

        # Column 4 header 1
        self.lblColumn2Header1 = Label(master=self.master, text='in degree without rollover:')
        self.lblColumn2Header1.place(x=self.x4, y=20)

        # Azimuth 1
        self.lblAzimuth1 = Label(master=self.master, text='Azimuth 1:')
        self.lblAzimuth1.place(x=self.x1, y=50)

        self.tbxAzimuth1 = Text(self.master, state='disabled', width=20, height=1)
        self.tbxAzimuth1.place(x=self.x2, y = 50)

        self.tbxAzimuth1Rll = Text(self.master, state='disabled', width=20, height=1)
        self.tbxAzimuth1Rll.place(x=self.x4, y = 50)

        # Elevation 1
        self.lblElevation1 = Label(master=self.master, text='Elevation 1: ')
        self.lblElevation1.place(x=self.x1, y=80)

        self.tbxElevation1 = Text(self.master, state='disabled', width=20, height=1)
        self.tbxElevation1.place(x=self.x2, y = 80)

        self.tbxElevation1Rll = Text(self.master, state='disabled', width=20, height=1)
        self.tbxElevation1Rll.place(x=self.x4, y = 80)

        # Azimuth 2
        self.lblAzimuth2 = Label(master=self.master, text='Azimuth 2: ')
        self.lblAzimuth2.place(x=self.x1, y=110)

        self.tbxAzimuth2 = Text(self.master, state='disabled', width=20, height=1)
        self.tbxAzimuth2.place(x=self.x2, y = 110)

        self.tbxAzimuth2Rll = Text(self.master, state='disabled', width=20, height=1)
        self.tbxAzimuth2Rll.place(x=self.x4, y = 110)

        # Elevation 2
        self.lblElevation2 = Label(master=self.master, text='Elevation 2: ')
        self.lblElevation2.place(x=self.x1, y=140)

        self.tbxElevation2 = Text(self.master, state='disabled', width=20, height=1)
        self.tbxElevation2.place(x=self.x2, y = 140)

        self.tbxElevation2Rll = Text(self.master, state='disabled', width=20, height=1)
        self.tbxElevation2Rll.place(x=self.x4, y = 140)


        # Column 2 header 2
        self.lblColumn2Header1 = Label(master=self.master, text='PLC Code:')
        self.lblColumn2Header1.place(x=self.x2, y=270)
        
        # Column 2 header 2
        self.lblColumn2Header1 = Label(master=self.master, text='PLC Code as text:')
        self.lblColumn2Header1.place(x=self.x3, y=270)

        # Width settings 
        widthInt = 8
        widthStr = 65

        # CurrentMotionCommand
        self.lblCurrentMotionCommand = Label(master=self.master, text='Current Motion Command: ')
        self.lblCurrentMotionCommand.place(x=self.x1, y=300)

        self.tbxCurrentMotionCommandInt = Text(self.master, state='disabled', width=widthInt, height=1)
        self.tbxCurrentMotionCommandInt.place(x=self.x2, y = 300)

        self.tbxCurrentMotionCommandStr = Text(self.master, state='disabled', width=widthStr, height=1)
        self.tbxCurrentMotionCommandStr.place(x=self.x3, y = 300)

        # CurrentSystemStatus
        self.lblCurrentSystemStatus = Label(master=self.master, text='Current System Status: ')
        self.lblCurrentSystemStatus.place(x=self.x1, y=330)

        self.tbxCurrentSystemStatusInt = Text(self.master, state='disabled', width=widthInt, height=1)
        self.tbxCurrentSystemStatusInt.place(x=self.x2, y = 330)

        self.tbxCurrentSystemStatusStr = Text(self.master, state='disabled', width=widthStr, height=1)
        self.tbxCurrentSystemStatusStr.place(x=self.x3, y = 330)

        # FaultCode
        self.lblFaultCode = Label(master=self.master, text='Fault Code: ')
        self.lblFaultCode.place(x=self.x1, y=360)

        self.tbxFaultCodeInt = Text(self.master, state='disabled', width=widthInt, height=1)
        self.tbxFaultCodeInt.place(x=self.x2, y = 360)

        self.tbxFaultCodeStr = Text(self.master, state='disabled', width=widthStr, height=1)
        self.tbxFaultCodeStr.place(x=self.x3, y = 360)

        # AxisWarningsLimitSwitchHits
        self.lblAxisWarningsLimitSwitchHits = Label(master=self.master, text='Telescope Status: ')
        self.lblAxisWarningsLimitSwitchHits.place(x=self.x1, y=390)

        self.tbxAxisWarningsLimitSwitchHitsInt = Text(self.master, state='disabled', width=widthInt, height=1)
        self.tbxAxisWarningsLimitSwitchHitsInt.place(x=self.x2, y = 390)

        self.tbxAxisWarningsLimitSwitchHitsStr = Text(self.master, state='disabled', width=widthStr, height=1)
        self.tbxAxisWarningsLimitSwitchHitsStr.place(x=self.x3, y = 390)

        # BasicError
        self.lblBasicError = Label(master=self.master, text='Basic Errors: ')
        self.lblBasicError.place(x=self.x1, y=420)

        self.tbxBasicErrorInt = Text(self.master, state='disabled', width=widthInt, height=1)
        self.tbxBasicErrorInt.place(x=self.x2, y = 420)

        self.tbxBasicErrorStr = Text(self.master, state='disabled', width=widthStr, height=1)
        self.tbxBasicErrorStr.place(x=self.x3, y = 420)

        # BasicError
        self.lblConnectionStatus = Label(master=self.master, text='Connection Status: ')
        self.lblConnectionStatus.place(x=self.x1, y=420)

        self.tbxConnectionStatus = Text(self.master, state='disabled', width=widthInt, height=1)
        self.tbxConnectionStatus.place(x=self.x2, y = 420)

        self.tbxConnectionStatusStr = Text(self.master, state='disabled', width=widthStr, height=1)
        self.tbxConnectionStatusStr.place(x=self.x3, y = 420)

        
        # InterpreterWindow
        #
        # self.tbxInterpreterOut = Text(self.master,state='disabled', width=70, height=40)
        # self.tbxInterpreterOut.place(x=800, y = 20)
        #
        # self.tbxInterpreterIn = Text(self.master, width=67, height=2 )
        # self.tbxInterpreterIn.place(x=825, y = 680)
        #
        # self.lblInterpreterMark = Label(master=self.master, text='>')
        # self.lblInterpreterMark.place(x=800, y=680)
        
        # A list with the same order as the sensor list. 
        # It uses later the :meth: 'value'.
        self.tbxListValue = []
        self.tbxListValue.append(self.tbxBasicErrorInt)
        self.tbxListValue.append(self.tbxCurrentSystemStatusInt)
        self.tbxListValue.append(self.tbxFaultCodeInt)
        self.tbxListValue.append(self.tbxAxisWarningsLimitSwitchHitsInt)
        self.tbxListValue.append(self.tbxCurrentMotionCommandInt)
        self.tbxListValue.append(self.tbxConnectionStatus)
        self.tbxListValue.append(self.tbxElevation1)
        self.tbxListValue.append(self.tbxAzimuth1)
        self.tbxListValue.append(self.tbxElevation2)
        self.tbxListValue.append(self.tbxAzimuth2)
        

        # A list with the same order as the sensor list. 
        # It differs later between the 'value()' and the .
        self.tbxListValueToString = []
        self.tbxListValueToString.append(self.tbxBasicErrorStr)
        self.tbxListValueToString.append(self.tbxCurrentSystemStatusStr)
        self.tbxListValueToString.append(self.tbxFaultCodeStr)
        self.tbxListValueToString.append(self.tbxAxisWarningsLimitSwitchHitsStr)
        self.tbxListValueToString.append(self.tbxCurrentMotionCommandStr)
        self.tbxListValueToString.append(self.tbxConnectionStatusStr)

        # A list with the same order as the sensor list. 
        # It uses later the :attr: 'valueToString' at elevation and 'positionWithoutRollover' at azimuth.
        self.tbxListRll = []
        self.tbxListRll.append(self.tbxElevation1Rll)
        self.tbxListRll.append(self.tbxAzimuth1Rll)
        self.tbxListRll.append(self.tbxElevation2Rll)
        self.tbxListRll.append(self.tbxAzimuth2Rll)
      
    def update(self):
        '''The intern updating loop 
        It calls itself every 500 ms, sothat it periodic updates the window.
        '''
        self.updateSensors()
        self.master.after(500,self.update) # process run again in 500 ms     
    
    def updateSensors(self):
        '''This method updates the textboxes. 
        It iters through different loops, in which always the same method/parameter of a sensor is used
        '''
        for i in range(len(self.tbxListValue)):
            self._updateFunc(self.tbxListValue[i], self.OVST.sensorUpdaterList[i].value(),self.OVST.sensorUpdaterList[i])

        for i in range(len(self.tbxListValueToString)):
            self._updateFunc(self.tbxListValueToString[i],self.OVST.sensorUpdaterList[i].valueToString, self.OVST.sensorUpdaterList[i])

        for i in range(len(self.tbxListRll)):
            # differ into azimuth and elevation
            if self.OVST.sensorUpdaterList[i+self.offset].isAzimuth:
                self._updateFunc(self.tbxListRll[i], self.OVST.sensorUpdaterList[i+self.offset].positionWithoutRollover, self.OVST.sensorUpdaterList[i+self.offset])
            elif self.OVST.sensorUpdaterList[i+self.offset].isElevation: 
                self._updateFunc(self.tbxListRll[i], self.OVST.sensorUpdaterList[i+self.offset].value(), self.OVST.sensorUpdaterList[i+self.offset])
               
            
    def _updateFunc(self, tbxobj, value, sensor):
        '''Enables writing to the textboxes, deletes the old value, writes in the new value and disables it for the user again.

        params
        ------
        tbxobj: object of :class: 'Text'
            The textbox in which is written in.

        value: string, float, int
            The value which is written.
        
        status: int 
            Status of the sensor
        '''
        tmSp = Timestamp(float(sensor.read()[0]))
        if tmSp < Timestamp()-5:# Was not updated the last five seconds
            status=6 # Time is over
            sensor.set(tmSp,5,(sensor.read()[2]))
        else:
            status = sensor.read()[1]
        tbxobj.configure(state="normal")
        tbxobj.delete("1.0",END)
        tbxobj.insert(END, value)
        if status == 0: 
            color = "white" 
        elif status == 1: 
            color = "green"
        elif status == 2: 
            color = "yellow"
        elif status == 3: 
            color = "red"
        elif status == 4: 
            color = "magenta"
        elif status == 5: 
            color = "cyan"
        elif status == 6: 
            color = "blue"
        tbxobj.configure(background=color)
        tbxobj.configure(state="disabled")

    def openCatalogueEntryWindow(self):
        '''Open a window, in which several targets can be tracked.
        There is the option to make crosses on a target
        '''
        self.CEW = CatalogueEntryWindow(Toplevel(self.master), self.OVST)

    def openRasterEntryWindow(self):
        '''Open a window in which the settings for making a raster can be made.
         '''
        self.REW = EntryWindow(Toplevel(self.master), self.OVST, 'Raster')

    def openRasterDiscreteEntryWindow(self):
        '''Open a window in which the settings for making a raster with discrete points can be made.
         '''
        self.RDEW = EntryWindow(Toplevel(self.master), self.OVST, 'RasterDiscrete')

    def openLissajousEntryWindow(self):
        '''Open a window in which the settings for making lissajous figures can be made.
         '''
        self.LEW = EntryWindow(Toplevel(self.master), self.OVST, 'Lissajous')

    def openPongEntryWindow(self):
        '''Open a window in which the settings for making the 'Pong' function can be made.
         '''
        self.PEW = EntryWindow(Toplevel(self.master), self.OVST, 'Pong')

   

   

class WindowThread(threading.Thread):
    def __init__(self,OVST):
        '''The thread in which the window exists.

        params
        ------
        sensorList: A list of objects of :class: 'Sensor'
            The sensors which should be displayed. 
            The order of the list is important
        '''
        threading.Thread.__init__(self)
        self.name = "SensorUpdateThread"
        self.OVST = OVST
        # start the thread
        self.start()

    def run(self):   
        '''Creates the window
        '''
        self.root = Tk() # The master
        self.controlWindow =ControlWindow(self.root,self.OVST,6)
        self.controlWindow.update()
        self.root.mainloop()
       
    
