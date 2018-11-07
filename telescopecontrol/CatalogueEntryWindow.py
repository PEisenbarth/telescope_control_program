from Tkinter import *
import threading
import time
from katpoint import Catalogue
from ObservationMode import ObservationMode


class CatalogueEntryWindow():
    def __init__(self, master, OVST):
        '''This is the class of the window in which an entry in list 'cataloguesToTrack' can be made.
        
        Attention i is not self.i!

        params
        ------
        master: object of :class: 'Tk'
            It is necessery sothat the 'Checkbutton' work. 

        OVST: object of :class: 'OverallSettings'
            It contains necessary attributes, like the catalogue from which the targets are selected and
            the list in which the created catalogue is inserted.

        
        '''
        self.master = master
        self.frame = Frame(master)
        self.OVST = OVST

        #self.callback = callback
        # Fenster
        self.master.title("Catalogue Entry Window")
        self.master.geometry('1400x300')

        
        
        # Measures
        # left side
        self.x11 = 20 #fist column
        self.x21 = 180 # second  column
        # right side
        self.x1 = 520 #fist column
        self.x2 = 690 # second  column
        self.x3 = 820 # third column
        self.x4 = 950# fourth column
        self.x5 = 1080 # fifth column
        self.x6 = 1210 # sixth column
        

        self.lblThreadName = Label(master=self.master, text='Thread Name: ')
        self.lblThreadName.place(x=self.x11, y=20)

        self.txtThreadName = Text(self.master, width=30, height=1)
        self.txtThreadName.place(x=self.x21, y = 20)
        self.txtThreadName.bind("<Tab>", self.focus_next_window)
        
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

        
        self.txtStartTimeStamp = Text(self.master, width=30, height=1)
        self.txtStartTimeStamp.place(x=self.x21, y =50+i*30)
        self.txtStartTimeStamp.bind("<Tab>", self.focus_next_window)

        i+=1        
        self.lblMoveIncrementalTime = Label(master=self.master, text='Move Incremental Time: ')
        self.lblMoveIncrementalTime.place(x=self.x11, y=50+i*30)

        
        self.txtMoveIncrementalTime = Text(self.master, width=30, height=1) 
        self.txtMoveIncrementalTime.place(x=self.x21,  y =50+i*30)
        self.txtMoveIncrementalTime.bind("<Tab>", self.focus_next_window)

        i+=1        
        self.lblSleepingTime = Label(master=self.master, text='Sleeping Time: ')
        self.lblSleepingTime.place(x=self.x11, y=50+i*30)

        
        self.txtSleepingTime = Text(self.master, width=30, height=1) 
        self.txtSleepingTime.place(x=self.x21,  y =50+i*30)
        self.txtSleepingTime.bind("<Tab>", self.focus_next_window)

        i+=1        
        self.lockOrder = BooleanVar()
        self.cbxLockOrder = (Checkbutton(self.master, text="Lock Target Order", variable=self.lockOrder))
        self.lockOrder.set(False)
        self.cbxLockOrder.place(x=self.x21,y=50+i*30)

	#right side        

        self.i=0
        self.btnAdd = Button(self.master, text="Add a Target",width=20, height=1,command=self.addRow)
        self.btnAdd.place(x=self.x1, y=20+self.i*30)

        self.btnSubmit = Button(self.master,text="Delete a Target",width=20, height=1,command=self.deleteRow)
        self.btnSubmit.place(x=self.x3, y =20+self.i*30)

        self.btnSubmit = Button(self.master,text="Submit",width=20, height=1,command=self.submit)
        self.btnSubmit.place(x=self.x5, y =20+self.i*30)

        self.i+=1
        # Column 1 header 1
        self.lblColumn2Header1 = Label(master=self.master, text='Targetname:')
        self.lblColumn2Header1.place(x=self.x1, y=30+self.i*30)

        # Column 2 header 1
        self.lblColumn2Header1 = Label(master=self.master, text='Obervation Duration \nin minutes:')
        self.lblColumn2Header1.place(x=self.x2-10, y=30+self.i*30)

        # Column 3 header 1
        self.lblColumn2Header1 = Label(master=self.master, text='Go Off Azimuth \nin degree:')
        self.lblColumn2Header1.place(x=self.x3, y=30+self.i*30)

        # Column 4 header 1
        self.lblColumn2Header1 = Label(master=self.master, text='Go Off Elevation \nin degree:')
        self.lblColumn2Header1.place(x=self.x4, y=30+self.i*30)

        # Column 5 header 1
        self.lblColumn2Header1 = Label(master=self.master, text='Go Off Periode \nin minutes:')
        self.lblColumn2Header1.place(x=self.x5, y=30+self.i*30)

        # Column 6 header 1
        self.lblColumn2Header1 = Label(master=self.master, text='Go Off Sequence:')
        self.lblColumn2Header1.place(x=self.x6, y=30+self.i*30)


        self.rowList = []







    def addRow(self):
        '''This method appends a new row to the window of :class: 'CatalogueEntryWindow'.
        '''
        self.i+=1 
        self.rowList.append([])
        self.row(self.i-2)
        

    def deleteRow(self):
        '''This method deletes the last row of the window of :class: 'CatalogueEntryWindow'.
        '''
        self.i-=1 #row lines index for adding a row
        toDelete = self.rowList.pop() 

        for i in range(len(toDelete)):
            toDelete[i].destroy()

    def submit(self):
        '''This method appends the new catalogue and its settings to the end of :.ist: 'cataloguesToTrack'.
        The list is managed by the thread :class: 'TrackManagement'.
        '''

        # Thread name is required
        if not len(self.txtThreadName.get("1.0",END)[:-1])==0:
            #left side

            #(["Castor,Mars,Merak, lock, start 5min", newCat, None, 4*60,Timestamp()+600, 6, 0.9 ,True ,[[4,4,6],[5,5,6],[3,6,6]]])
            self.cat = []                                                            #index
            self.cat.append(str(self.txtThreadName.get("1.0",END)[:-1]))              #0
            self.cat.append(Catalogue())                                              #1
            ants = []
            for i in range(len(self.antennaValueList)):
                if self.antennaValueList[i].get():
                    ants.append(self.OVST.antennaList[i])   
            self.cat.append(ants)                                                    #2
            self.cat.append(setDefaultValues(self.txtMoveIncrementalTime,120))         #3
            # handle timestamp as string, float representation is not handled
            startTmSp = (setDefaultValues(self.txtStartTimeStamp,None))           #4
            self.cat.append(startTmSp)
            self.cat.append([])# observationDuration                                   #5
            self.cat.append(setDefaultValues(self.txtSleepingTime,1))                  #6
            self.cat.append(self.lockOrder.get())                                             #7
            self.cat.append([])# goOffSequence                                           #8           

            #right side
            printSeq =False
            for i in range(len(self.rowList)):
                #Get Target
                targetname = str(self.rowList[i][0].get("1.0",END)[:-1])
                try:
                    self.cat[1].add(self.OVST.Catalogue.__getitem__(targetname))
                    successful = True
                except TypeError:
                    self.rowList[i][0].configure(background="red")
                    successful = False
                #ObservationDuration
                self.cat[5].append(setDefaultValues(self.rowList[i][1],20))

              
                azOff =(setDefaultValues(self.rowList[i][2],0))
                elOff =(setDefaultValues(self.rowList[i][3],0))
                #Go Off Period
                periodOff =(setDefaultValues(self.rowList[i][4], 5))
                #Directions
                goOffSequence = (self.rowList[i][5].get("1.0",END)[:-1]).split(" ")
                if not len(goOffSequence)==4:
                    printSeq = True
                    goOffSequence = ["+el", "-el", "+az", "-az"]
                self.cat[8].append(ObservationMode(startTmSp, azOff, elOff, periodOff, goOffSequence))
            if successful:
                if printSeq:
                    print 'The Format of the GoOffSequence was not of length 4. \nIt uses the default sequence "["+el","-el","+az","-az"]"'
                self.OVST.cataloguesToTrack.append(self.cat)
                self.master.destroy()
        else:
            self.txtThreadName.configure(background="red")
       
    def focus_next_window(self,event):
        '''Makes that the next widget is focused.

        params
        ------
        event:
            It has to be set a <TAB> before. Just copy and paste from another Widget.
        '''
        event.widget.tk_focusNext().focus()
        return("break")

    def row(self, i):
        self.rowList[i].append(Text(self.master,  wrap="none", width=20, height=1))
        self.rowList[i][-1].place(x=self.x1, y = 40+self.i*30)
        self.rowList[i][-1].bind("<Tab>", self.focus_next_window)

      

        self.rowList[i].append(Text(self.master, wrap="none",  width=15, height=1))
        self.rowList[i][-1].place(x=self.x2, y = 40+self.i*30)
        self.rowList[i][-1].bind("<Tab>", self.focus_next_window)
      

        self.rowList[i].append(Text(self.master, wrap="none",  width=15, height=1))
        self.rowList[i][-1].place(x=self.x3, y = 40+self.i*30)
        self.rowList[i][-1].bind("<Tab>", self.focus_next_window)
      

        self.rowList[i].append(Text(self.master, wrap="none",  width=15, height=1))
        self.rowList[i][-1].place(x=self.x4, y = 40+self.i*30)
        self.rowList[i][-1].bind("<Tab>", self.focus_next_window)
      

        self.rowList[i].append(Text(self.master, wrap="none",  width=15, height=1))
        self.rowList[i][-1].place(x=self.x5, y = 40+self.i*30)
        self.rowList[i][-1].bind("<Tab>", self.focus_next_window)
      

        self.rowList[i].append(Text(self.master, wrap="none", width=20, height=1))
        self.rowList[i][-1].place(x=self.x6, y = 40+self.i*30)
        self.rowList[i][-1].bind("<Tab>", self.focus_next_window)
      



def setDefaultValues(txtobj,default):
    '''Return a variable with the text of a textbox. If the textbox is empty it returns the default value.

            params
            ------
            txtobj: object of :Text:
                The Textbox which contains the text which should sign a variable

            default: 
                The value which should be written if the 'txtobj' is of length '0', so that it is empty.
            '''
    try:
        value = float(txtobj.get("1.0",END)[:-1])
    except ValueError:
        value = str(txtobj.get("1.0",END)[:-1])

    if len(txtobj.get("1.0",END)[:-1])==0:
        return default
    else:
        return value






# The following code generates something like a excel table. It is just copied from internet, but can be helpful.

#class SimpleTableInput(Frame):
#    def __init__(self, parent, rows, columns):
#        Frame.__init__(self, parent)
        

#        self._entry = {}
#        self.rows = rows
#        self.columns = columns

#        # register a command to use for validation
#        self.vcmd = (self.register(self._validate), "%P")
        
#        # create the table of widgets
#        for row in range(self.rows):
#            for column in range(self.columns):
#                index = (row, column)
#                e = Entry(self, validate="key", validatecommand=self.vcmd)
#                e.grid(row=row, column=column, stick="nsew")
#                self._entry[index] = e
#        # adjust column weights so they all expand equally
#        for column in range(self.columns):
#            self.grid_columnconfigure(column, weight=1)
#        self._entry[0,0].insert(0,"Targetname:")
#        self._entry[0,1].insert(0,"Obervation Duration in minutes:")
#        self._entry[0,2].insert(0,"Go Off Azimuth in degree:")
#        self._entry[0,3].insert(0,"Go Off Elevation in degree:")
#        self._entry[0,4].insert(0,"Go Off Periode in minutes:")
#        self._entry[0,5].insert(0,"Go Off Sequence:")
#        # designate a final, empty row to fill up any extra space
#        self.grid_rowconfigure(rows, weight=1)

#    def get(self):
#        '''Return a list of lists, containing the data in the table'''
#        result = []
#        for row in range(self.rows):
#            current_row = []
#            for column in range(self.columns):
#                index = (row, column)
#                current_row.append(self._entry[index].get())
#            result.append(current_row)
#        return result

#    def _validate(self, P):
#        '''Perform input validation. 

#        Allow only an empty value, or a value that can be converted to a float
#        '''
#        if P.strip() == "":
#            return True

#        #try:
#        #    f = float(P)
#        #except ValueError:
#        #    self.bell()
#        #    return False
#        return True

#    def append(self):
#        row = self.rows
#        for column in range(self.columns):
#            index = (row, column)
#            e = Entry(self, validate="key", validatecommand=self.vcmd)
#            e.grid(row=row, column=column, stick="nsew")
#            self._entry[index] = e
#        self.rows += 1

#    def delete(self):
#        row = self.rows - 1
#        for column in range(self.columns):
#            index = (row, column)
#            self._entry[index].grid_remove()
#        self.rows -= 1


#class Example(Frame):
#    def __init__(self, parent):
#        Frame.__init__(self, parent)
        
        
#        self.table = SimpleTableInput(self, 5, 6)
#        self.submit = Button(self, text="Submit", command=self.on_submit)
#        self.table.pack(fill="both", expand=True)
#        self.submit.pack(side="bottom")
#        self.addrow = Button(self,text="Add row", command=self.addrow)
#        self.addrow.pack()
#        self.delrow = Button(self,text="Delete row", command=self.delrow)
#        self.delrow.pack()

#    def on_submit(self):
#        print(self.table.get())

#    def addrow(self):
#        self.table.append()

#    def delrow(self):
#        self.table.delete()
