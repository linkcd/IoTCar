from datetime import datetime

import obd
import time

messageToSend = []

def getValue(r):
    if not r.is_null():
        return r.value.magnitude
    else:
        return 0

def getVehicleTelemtries():
    global connection
    if(not connection.is_connected()):
        print("Not connection, reconnecting...")
        connection = obd.OBD(fast=True) 
    try:
        
        timestamp = str(datetime.now())
        message = {'timestamp': timestamp}
        # allCommands = connection.supported_commands
        allCommands = [obd.commands.RUN_TIME, obd.commands.SPEED, obd.commands.RPM]
        for command in allCommands:
            try:
                response = connection.query(obd.commands[command.name])
                telemetryValue = getValue(response)
                message[command.name] = str(telemetryValue)
                #print(command.name + " : "  + str(telemetryValue))  
            
            except Exception as e:
                print ("Error querying OBDII entry: " + command.name + " , " + str(e))
                if(command.name == "RPM"):
                    print("cannot read RPM, reconnecting...")
                    connection = obd.OBD(fast=True) 
        
        if(message["RPM"] == "0"):
            print("Not RPM, reconnecting...")
            connection = obd.OBD(fast=True) 
            return None
        else:
            return message

    except Exception as e:
        print("Error with OBDII, error is " + str(e))


connection = obd.OBD(fast=True) # auto-connects to USB or RF port

while True:
    msg = getVehicleTelemtries()
    print(msg)
    time.sleep(1)