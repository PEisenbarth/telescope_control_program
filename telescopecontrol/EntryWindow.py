from katpoint import *
from check_target import check_target
from Tkinter import *
import threading
import time
from katpoint import Catalogue
from CatalogueEntryWindow import setDefaultValues
from ObservationMode import ObservationMode

class EntryWindow():
    def __init__(self, master, OVST, mode):
        '''This is the class of the window in which entries of goOffPointing modes can be made.

        Attention i is not self.i!

        params
        ------
        master: object of :class: 'Tk'
            It is necessery sothat the 'Checkbutton' work. 

        OVST: object of :class: 'OverallSettings'
            It contains necessary attributes, like the catalogue from which the targets are selected and
            the list in which the created catalogue is inserted.

        mode: str
            The mode of :class: 'GoOffPointing'. It changes the Widgets which are shown.       
        '''
        self.master = master
        self.frame = Frame(master)
        self.OVST = OVST
        self.mode = mode
        #self.callback = callback
        # Fenster
        title = "%s Entry Window"%self.mode
        self.master.title(title)
        self.master.geometry('1050x400')

        
        
        # Measures
        # left side
        self.x11 = 20 #fist column
        self.x21 = 180 # second  column
        # right side
        self.x1 = 520 #fist column
        self.x2 = 800 # second  column

        

        self.lblThreadName = Label(master=self.master, text='Thread Name: ')
        self.lblThreadName.place(x=self.x11, y=20)

        self.tbxThreadName = Text(self.master, width=30, height=1)
        self.tbxThreadName.place(x=self.x21, y = 20)
        self.tbxThreadName.bind("<Tab>", self.focus_next_window)
        
        self.lblAntennaList = Label(master=self.master, text='Antennas: ')
        self.lblAntennaList.place(x=self.x11, y=50)

        # Attention i is not self.i!

        self.antennaValueList=[]
        self.cbxAntennaList=[]
        for i in range(len(self.OVST.antennaList)):      
            self.antennaValueList.append(BooleanVar())
            self.antennaValueList[-1].set(True) #Default True 
            self.cbxAntennaList.append(Checkbutton(self.master,text = self.OVST.antennaList[i].name, variable=self.antennaValueList[i]))
            self.cbxAntennaList[-1].place(x=self.x21,y=50+i*30)

        i+=1        
        self.lblStartTimeStamp = Label(master=self.master, text='Start Timestamp: ')
        self.lblStartTimeStamp.place(x=self.x11, y=50+i*30)

        
        self.tbxStartTimeStamp = Text(self.master, width=30, height=1)
        self.tbxStartTimeStamp.place(x=self.x21, y =50+i*30)
        self.tbxStartTimeStamp.bind("<Tab>", self.focus_next_window)

        i+=1        
        self.lblMoveIncrementalTime = Label(master=self.master, text='Move Incremental Time: ')
        self.lblMoveIncrementalTime.place(x=self.x11, y=50+i*30)

        
        self.tbxMoveIncrementalTime = Text(self.master, width=30, height=1) 
        self.tbxMoveIncrementalTime.place(x=self.x21,  y =50+i*30)
        self.tbxMoveIncrementalTime.bind("<Tab>", self.focus_next_window)

        i+=1        
        self.lblSleepingTime = Label(master=self.master, text='Sleeping Time: ')
        self.lblSleepingTime.place(x=self.x11, y=50+i*30)

        
        self.tbxSleepingTime = Text(self.master, width=30, height=1) 
        self.tbxSleepingTime.place(x=self.x21,  y =50+i*30)
        self.tbxSleepingTime.bind("<Tab>", self.focus_next_window)

        i+=1        
        self.lockOrder = BooleanVar()
        self.cbxLockOrder = (Checkbutton(self.master, text="Lock Target Order", variable=self.lockOrder))
        self.lockOrder.set(False)
        self.cbxLockOrder.place(x=self.x21,y=50+i*30)

        i+=1
        self.btnSubmit = Button(self.master, text="Submit", width=20, height=1, command=self.submit)
        self.btnSubmit.place(x=self.x21, y=50+i*30)

        #right side
        self.i=0        
        self.lblTargetName = Label(master=self.master, text='Target Name: ')
        self.lblTargetName.place(x=self.x1, y=20+self.i*30)

        self.tbxTargetName = Text(self.master, width=30, height=1) 
        self.tbxTargetName.place(x=self.x2,  y =20+self.i*30)
        self.tbxTargetName.bind("<Tab>", self.focus_next_window)

        self.i += 1
        self.lblObservationDuration = Label(master=self.master, text='Observation Duration in minutes: ')
        self.lblObservationDuration.place(x=self.x1, y=20 + self.i * 30)

        self.tbxObservationDuration = Text(self.master, width=30, height=1)
        self.tbxObservationDuration.place(x=self.x2, y=20 + self.i * 30)
        self.tbxObservationDuration.bind("<Tab>", self.focus_next_window)


        # Define frame
        self.i+=1        
        self.lblAngleConstAz = Label(master=self.master, text='Angle of the frame in Azimuth in degree: ')
        self.lblAngleConstAz.place(x=self.x1, y=20+self.i*30)

        self.tbxAngleConstAz = Text(self.master, width=30, height=1) 
        self.tbxAngleConstAz.place(x=self.x2,  y =20+self.i*30)
        self.tbxAngleConstAz.bind("<Tab>", self.focus_next_window)

        self.i+=1        
        self.lblAngleConstEl = Label(master=self.master, text='Angle of the frame in Elevation in degree: ')
        self.lblAngleConstEl.place(x=self.x1, y=20+self.i*30)

        self.tbxAngleConstEl = Text(self.master, width=30, height=1) 
        self.tbxAngleConstEl.place(x=self.x2,  y =20+self.i*30)
        self.tbxAngleConstEl.bind("<Tab>", self.focus_next_window)

        if self.mode=="RasterDiscrete":
            self.i+=1        
            self.lblPointsAz = Label(master=self.master, text='Number of Points in Azimuth: ')
            self.lblPointsAz.place(x=self.x1, y=20+self.i*30)

            self.pointsAz = StringVar()
            self.pointsAz.set("3")
            self.sbxPointsAz = Spinbox(self.master, width=25, from_=1, to=float("inf"), textvariable = self.pointsAz)
            self.sbxPointsAz.place(x=self.x2,  y =20+self.i*30)
            self.sbxPointsAz.bind("<Tab>", self.focus_next_window)

            self.i+=1        
            self.lblPointsEl = Label(master=self.master, text='Number of Points in Elevation: ')
            self.lblPointsEl.place(x=self.x1, y=20+self.i*30)

            self.pointsEl = StringVar()
            self.pointsEl.set("3")
            self.sbxPointsEl = Spinbox(self.master, width=25, from_=1, to=float("inf"), textvariable = self.pointsEl)
            self.sbxPointsEl.place(x=self.x2,  y =20+self.i*30)
            self.sbxPointsEl.bind("<Tab>", self.focus_next_window)

        if self.mode =="Raster":
            self.i+=1        
            self.lblRasterLines = Label(master=self.master, text='Number of Lines: ')
            self.lblRasterLines.place(x=self.x1, y=20+self.i*30)

            self.rasterLines = StringVar()
            self.rasterLines.set("3")
            self.sbxRasterLines = Spinbox(self.master, width=25, from_=1, to=float("inf"), textvariable = self.rasterLines)
            self.sbxRasterLines.place(x=self.x2,  y =20+self.i*30)
            self.sbxRasterLines.bind("<Tab>", self.focus_next_window)

        if self.mode =="Raster" or self.mode == "RasterDiscrete":
            self.firstAz = BooleanVar()
            self.firstAz.set(True)
            self.rbtFirstAz = (Radiobutton(self.master, text="First Azimuth", variable=self.firstAz, value=True))
            self.rbtFirstEl = (Radiobutton(self.master, text="First Elevation", variable=self.firstAz, value=False))
            self.i+=1 
            self.rbtFirstAz.place(x=self.x2,y=20+self.i*30)
            self.i+=1
            self.rbtFirstEl.place(x=self.x2,y=20+self.i*30)

        if self.mode=="Lissajous":
            self.i += 1
            self.lblOmegaAz = Label(master=self.master, text='Omega in Azimuth in degree per second:')
            self.lblOmegaAz.place(x=self.x1, y=20 + self.i * 30)

            self.tbxOmegaAz = Text(self.master, width=30, height=1)
            self.tbxOmegaAz.place(x=self.x2, y=20 + self.i * 30)
            self.tbxOmegaAz.bind("<Tab>", self.focus_next_window)

            self.i += 1
            self.lblOmegaEl = Label(master=self.master, text='Omega in Elevation in degree per second:')
            self.lblOmegaEl.place(x=self.x1, y=20 + self.i * 30)

            self.tbxOmegaEl = Text(self.master, width=30, height=1)
            self.tbxOmegaEl.place(x=self.x2, y=20 + self.i * 30)
            self.tbxOmegaEl.bind("<Tab>", self.focus_next_window)

            self.i += 1
            self.lblPhiAz = Label(master=self.master, text='Phi in Azimuth in degree:')
            self.lblPhiAz.place(x=self.x1, y=20 + self.i * 30)

            self.tbxPhiAz = Text(self.master, width=30, height=1)
            self.tbxPhiAz.place(x=self.x2, y=20 + self.i * 30)
            self.tbxPhiAz.bind("<Tab>", self.focus_next_window)

            self.i += 1
            self.lblPhiEl = Label(master=self.master, text='Phi in Elevation in degree:')
            self.lblPhiEl.place(x=self.x1, y=20 + self.i * 30)

            self.tbxPhiEl = Text(self.master, width=30, height=1)
            self.tbxPhiEl.place(x=self.x2, y=20 + self.i * 30)
            self.tbxPhiEl.bind("<Tab>", self.focus_next_window)

        if self.mode=='Pong':
            self.i += 1
            self.lblStartAz = Label(master=self.master, text='Start  Off in Azimuth in degree:')
            self.lblStartAz.place(x=self.x1, y=20 + self.i * 30)

            self.tbxStartAz = Text(self.master, width=30, height=1)
            self.tbxStartAz.place(x=self.x2, y=20 + self.i * 30)
            self.tbxStartAz.bind("<Tab>", self.focus_next_window)

            self.i += 1
            self.lblStartEl = Label(master=self.master, text='Start Off in Elevation in degree:')
            self.lblStartEl.place(x=self.x1, y=20 + self.i * 30)

            self.tbxStartEl = Text(self.master, width=30, height=1)
            self.tbxStartEl.place(x=self.x2, y=20 + self.i * 30)
            self.tbxStartEl.bind("<Tab>", self.focus_next_window)

            self.i += 1
            self.lblStartAngle = Label(master=self.master, text='Start Angle in degree:')
            self.lblStartAngle.place(x=self.x1, y=20 + self.i * 30)

            self.tbxStartAngle = Text(self.master, width=30, height=1)
            self.tbxStartAngle.place(x=self.x2, y=20 + self.i * 30)
            self.tbxStartAngle.bind("<Tab>", self.focus_next_window)

            self.i += 1
            self.lblVelocity = Label(master=self.master, text='Velocity in degree per second:')
            self.lblVelocity.place(x=self.x1, y=20 + self.i * 30)

            self.tbxVelocity = Text(self.master, width=30, height=1)
            self.tbxVelocity.place(x=self.x2, y=20 + self.i * 30)
            self.tbxVelocity.bind("<Tab>", self.focus_next_window)


        self.i += 1
        self.lblGoOffAz = Label(master=self.master, text='Go Off Azimuth in degree:')
        self.lblGoOffAz.place(x=self.x1, y=20 + self.i * 30)

        self.tbxGoOffAz = Text(self.master, width=30, height=1)
        self.tbxGoOffAz.place(x=self.x2, y=20 + self.i * 30)
        self.tbxGoOffAz.bind("<Tab>", self.focus_next_window)

        self.i += 1
        self.lblGoOffEl = Label(master=self.master, text='Go Off Elevation in degree:')
        self.lblGoOffEl.place(x=self.x1, y=20 + self.i * 30)

        self.tbxGoOffEl = Text(self.master, width=30, height=1)
        self.tbxGoOffEl.place(x=self.x2, y=20 + self.i * 30)
        self.tbxGoOffEl.bind("<Tab>", self.focus_next_window)

        self.i += 1
        self.lblGoOffPeriode = Label(master=self.master, text='Go Off Periode in minutes:')
        self.lblGoOffPeriode.place(x=self.x1, y=20 + self.i * 30)

        self.tbxGoOffPeriode = Text(self.master, width=30, height=1)
        self.tbxGoOffPeriode.place(x=self.x2, y=20 + self.i * 30)
        self.tbxGoOffPeriode.bind("<Tab>", self.focus_next_window)

        self.i += 1
        self.lblGoOffSequence= Label(master=self.master, text='Go Off Sequence:')
        self.lblGoOffSequence.place(x=self.x1, y=20 + self.i * 30)

        self.tbxGoOffSequence = Text(self.master, width=30, height=1)
        self.tbxGoOffSequence.place(x=self.x2, y=20 + self.i * 30)
        self.tbxGoOffSequence.bind("<Tab>", self.focus_next_window)



    def submit(self):
        '''This method appends the new catalogue and its settings to the end of :.ist: 'cataloguesToTrack'.
        The list is managed by the thread :class: 'TrackManagement'.
        '''
        # Thread name is required
        if not len(self.tbxThreadName.get("1.0",END)[:-1])==0:
            #left side
            self.cat = []                                                            #index
            self.cat.append(str(self.tbxThreadName.get("1.0",END)[:-1]))              #0
            self.cat.append(Catalogue())
            #createRaster(targetname, az_frame=1, el_frame=1, pointsAz = 3, pointsEl =3, firstAz =True)
            targetname = str(self.tbxTargetName.get("1.0",END)[:-1])
            try:
                self.cat[1].add(self.OVST.Catalogue.__getitem__(targetname))
                successful = True
            except TypeError:
                self.tbxTargetName.configure(background="red")
                successful = False
            ants = []
            for i in range(len(self.antennaValueList)):
                if self.antennaValueList[i].get():
                    ants.append(self.OVST.antennaList[i])   
            self.cat.append(ants)                                                    #2

            self.cat.append(setDefaultValues(self.tbxMoveIncrementalTime,60))         #3
            # handle timestamp as string, float representation is not handled
            startTmSp = setDefaultValues(self.tbxStartTimeStamp,None)              #4
            self.cat.append(startTmSp)
            self.cat.append([])# observationDuration                                   #5
            self.cat.append(setDefaultValues(self.tbxSleepingTime,1))                  #6
            self.cat.append(True) # Locked Orderder                                            #7
            self.cat.append([])# goOff                                             #8
            #right side

            #ObservationDuration
            observationDuration =(setDefaultValues(self.tbxObservationDuration,20))
            self.cat[5].append(observationDuration)

            angleConstAz = setDefaultValues(self.tbxAngleConstAz,1)
            angleConstEl = setDefaultValues(self.tbxAngleConstEl,1)
            kwargs = {}
            kwargs['mode'] = self.mode
            if self.mode == "RasterDiscrete" or self.mode == "Raster":
                kwargs['firstAz'] = self.firstAz.get()
                kwargs['observationDuration'] = observationDuration
            if self.mode == "RasterDiscrete":
                kwargs['pointsAz'] = int(self.pointsAz.get())
                kwargs['pointsEl'] = int(self.pointsEl.get())
            if self.mode == "Raster":
                kwargs['rasterLines'] = int(self.rasterLines.get())
            if self.mode == "Lissajous":
                kwargs['omegaAz'] = setDefaultValues(self.tbxOmegaAz,3)
                kwargs['omegaEl'] = setDefaultValues(self.tbxOmegaEl,3)
                kwargs['phiAz'] = setDefaultValues(self.tbxPhiAz,3)
                kwargs['phiEl'] = setDefaultValues(self.tbxPhiEl,3)
            if self.mode == "Pong":
                kwargs['startAz'] = setDefaultValues(self.tbxStartAz,3)
                kwargs['startEl'] = setDefaultValues(self.tbxStartEl,3)
                kwargs['startAngle'] = setDefaultValues(self.tbxStartAngle,3)
                kwargs['velocity'] = setDefaultValues(self.tbxVelocity,3)

            #Azimuth and Elevation go Off
            azOff =(setDefaultValues(self.tbxGoOffAz,0))
            elOff =(setDefaultValues(self.tbxGoOffEl,0))
            #Go Off Period
            periodOff = (setDefaultValues(self.tbxGoOffPeriode, 5))
            #Directions
            goOffSequence = (self.tbxGoOffSequence.get("1.0",END)[:-1]).split(" ")
            if not len(goOffSequence)==4:
                print 'The Format of the GoOffSequence was not of lenght 4. \nIt uses the default sequence "["+el","-el","+az","-az"]"'
                goOffSequence = ["+el", "-el", "+az", "-az"]
            self.cat[8].append(ObservationMode(startTmSp, azOff, elOff, periodOff, goOffSequence, angleConstAz, angleConstEl, **kwargs))
            if successful:
                self.OVST.cataloguesToTrack.append(self.cat)
                self.master.destroy()
        else: 
            self.tbxThreadName.configure(background="red")

       
    def focus_next_window(self,event):
        '''Makes that the next widget is focused.

        params
        ------
        event:
            It has to be set a <TAB> before. Just copy and paste from another Widget.
        '''
        event.widget.tk_focusNext().focus()
        return("break")

def setDefaultValues(tbxobj,default):
    '''Return a variable with the text of a textbox. If the textbox is empty it returns the default value.

            params
            ------
            tbxobj: object of :Text:
                The Textbox which contains the text which should sign a variable

            default: 
                The value which should be written if the 'tbxobj' is of length '0', so that it is empty.
            '''
    try:
        value = float(tbxobj.get("1.0",END)[:-1])
    except ValueError:
        value = str(tbxobj.get("1.0",END)[:-1])

    if len(tbxobj.get("1.0",END)[:-1])==0:
        return default
    else:
        return value

