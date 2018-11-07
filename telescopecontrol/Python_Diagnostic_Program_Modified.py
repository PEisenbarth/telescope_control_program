from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadBuilder, BinaryPayloadDecoder
from pymodbus.client.sync import ModbusTcpClient as ModbusClient
import numpy as np
import time
import math
import sqlite3
from wetton_settings import modbus_ip, modbus_port

class PythonDiagnosticProgramm():

#Modbus general
    def modbusConnectionOpen(self, iPAddress=modbus_ip, port=modbus_port):
        self.client = ModbusClient(iPAddress, port) # PLC Address and Port; '192.168.000.250' does not work!
        time.sleep(0.1)
        return self.client.connect() 
         
        
    def modbusConnectionClose(self):
        self.client.close()

#Modbus read
    def modbusReadOut(self, startAddress=0, numberOfAddresses=2):
        floatSolutionArray=[]
        # numberOfAddresses should be not too much
        time.sleep(0.1) # Can be modified: 0.1 becomes instable
        # numberOfAddresses*2 because we read 32bit registers
        result = self.client.read_input_registers(startAddress, numberOfAddresses*2) 
        decoder = BinaryPayloadDecoder.fromRegisters(result.registers, endian = Endian.Little)
        decodedAsInt= {i : decoder.decode_32bit_int() for i in range(0, numberOfAddresses)}
        #convert the received values in floats
        for m in range (numberOfAddresses):
            floatSolutionArray.append( (self._intToFloatPLC(decodedAsInt.get(m))))
        return floatSolutionArray 
   
    def modbusReadOutAxis(self, axis):
        # With 0 there are 31 values to 30
        return self.modbusReadOut(axis*100, 31)

    def modbusReadOutAll(self):
        # it reads of every Axis the first 31 Registers
        floatSolutionArray = np.zeros((5,31))
        for axis in range (0, len(floatSolutionArray)):
            floatSolutionArray[axis,:] = self.modbusReadOutAxis(axis)
        # To be sure that it is an Numpy Array
        return np.array(floatSolutionArray)

    def modbusReadOutVariableAxisData(self):
        # Relevant Addressends for the Variable Axis Data Database
        addressend=[9, 10, 11, 12, 20, 21, 30] 
        sQLArray = np.zeros([5,7])
        floatSolutionArray = self.modbusReadOutAll()
        for m in range (len(addressend)):
            sQLArray[:,m]=floatSolutionArray[:,(addressend[m])]
        return sQLArray

#Modbus write
    def modbusWrite(self, address, value):
        toChange = self._IEEE754reverse(value)
        toSend = self._changingTheOrder(toChange)
        builder = BinaryPayloadBuilder(endian=Endian.Little)
        # That is because of difficulies with the PLC
        builder.add_32bit_uint((toSend))
        payload = builder.build()
        #result  = client.write_registers(address, payload, skip_encode=True)
        result  = self.client.write_registers(address, payload, skip_encode=True)

#SQL
#SQL General
    def sQLConnectionOpen(self, filePath):
        self.connection = sqlite3.connect(filePath)
        self.cursor = self.connection.cursor()

    def sQLConnectionClose(self):
        self.connection.commit()
        self.connection.close()

#SQL Editing Methods
    def sQLCommand(self, sql_command):
        self.cursor.execute(sql_command)
        self.connection.commit()

    def sQLReadingTable(self, tableName="VariableAxisData"):
        self.cursor.execute("SELECT * FROM %s" %tableName)
        stringList = self.cursor.fetchall()
        for i in range(len(stringList)):
            print stringList[i]
        
    def sQLCreateTableVariableAxisData(self):
        sql_command = """
        CREATE TABLE VariableAxisData ( 
    Axis Int,
    X9 float,
    X10 float,
    X11 float,
    X12 float,
    X20 float,
    X21 float,
    X30 float);"""
        self.cursor.execute(sql_command)

    def sQLOverwriteVariableAxisData(self):
        floatSolutionArray = self.modbusReadOutVariableAxisData();
        for axis in range(len(floatSolutionArray[:,0])):
            sql_command = """
            DELETE FROM VariableAxisData WHERE Axis=%i;""" %(axis)
            self.cursor.execute(sql_command)
            # Insert the new Values
            sql_command = """
            INSERT INTO VariableAxisData VALUES (%i,%f,%f,%f,%f,%f,%f,%f);""" % (axis, floatSolutionArray[axis][0], floatSolutionArray[axis][1], floatSolutionArray[axis][2], floatSolutionArray[axis][3], floatSolutionArray[axis][4], floatSolutionArray[axis][5], floatSolutionArray[axis][6])
            self.cursor.execute(sql_command)
            # Confirm
        self.connection.commit()

# txt 
# Private Methodes
    def _intToFloatPLC(self, decodedAsInt):
    # Separate the Bytes; Initial order: byte4 | byte3 | byte2 | byte1
            byte1= (decodedAsInt) & (0xFF)
            byte2= (decodedAsInt)>>8 & (0xFF)
            byte3= (decodedAsInt)>>16 & (0xFF)
            byte4= (decodedAsInt)>>24 & (0xFF)
            # Combine the Bytes correct; Final order: byte3 | byte4 | byte1 | byte2
            result=(byte3<<(24))
            result=(byte4<<(16))| result
            result=(byte1<<(8)) | result
            result=(byte2) | result  
            # Transform the bitorder in a float
            # Refering to IEEE 754:
            # The 23 lowest significant bits 
            mantissa = result & 0x7FFFFF
            # The next 8 bits
            exponent = (result>>(23)) & 0xFF
            # The formula according to IEEE 754:
            _floatSolution=(1+((mantissa)/(math.pow(2,23))))*math.pow(2,(exponent-127))
            # The most significant bit defines the sign
            if ((byte3 & 0x80) == 0x80): #byte3 is the new most significant byte
                    _floatSolution=-_floatSolution
            # Underflow case: Exception of IEEE 754
            if (result == 0):
                    _floatSolution = 0
            # round the result
            _floatSolution=round(_floatSolution,4)
            # Print-Function for test issues
            # print "Address, Decoded: ", address, ", " ,floatSolution, bin(result)
            # print axis, m
            # Save the result, it will be overwritten in the next loop
            return _floatSolution

    def _changingTheOrder(self, decodedAsInt):
        # Separate the Bytes; Initial order: byte4 | byte3 | byte2 | byte1
        byte1= (decodedAsInt) & (0xFF)
        byte2= (decodedAsInt)>>8 & (0xFF)
        byte3= (decodedAsInt)>>16 & (0xFF)
        byte4= (decodedAsInt)>>24 & (0xFF)
        # Combine the Bytes correct; Final order: byte3 | byte4 | byte1 | byte2
        result=(byte3<<(24))
        result=(byte4<<(16))| result
        result=(byte1<<(8)) | result
        result=(byte2) | result 
        return (result)


    def _IEEE754reverse(self, valueIntoVR):
        valueAsInt = np.asarray(abs(valueIntoVR), dtype=np.float32).view(np.int32).item()
        if (valueIntoVR<0):
            valueAsInt = valueAsInt | 0x80000000
        return (valueAsInt)

