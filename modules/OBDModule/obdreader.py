from datetime import datetime
import obd

connection = obd.OBD(fast=True) # auto-connects to USB or RF port

def getValue(r):
    if not r.is_null():
        return r.value.magnitude
    else:
        return 0

def getVehicleTelemtries():
    global connection
    if(not connection.is_connected()):
        print("No connecting to the car, reconnecting...")
        connection = obd.OBD(fast=True) 
    
    try:
        
        timestamp = str(datetime.now())
        message = {'timestamp': timestamp}
        # allCommands = connection.supported_commands
        allCommands = [
                        obd.commands.RUN_TIME, 
                        obd.commands.RPM,
                        obd.commands.SPEED,                          
                        obd.commands.MAF, 
                        obd.commands.THROTTLE_POS, 
                        obd.commands.COOLANT_TEMP,
                        
                        
                        obd.commands.ENGINE_LOAD,
                        obd.commands.SHORT_FUEL_TRIM_1, 
                        obd.commands.LONG_FUEL_TRIM_1,
                        obd.commands.SHORT_FUEL_TRIM_2,
                        obd.commands.LONG_FUEL_TRIM_2,
                        obd.commands.FUEL_PRESSURE,
                        obd.commands.INTAKE_PRESSURE,
                        obd.commands.TIMING_ADVANCE,
                        obd.commands.INTAKE_TEMP,
                        obd.commands.RELATIVE_THROTTLE_POS,
                        obd.commands.AMBIANT_AIR_TEMP, 
                        obd.commands.FUEL_LEVEL,
                        obd.commands.ABSOLUTE_LOAD,
                        obd.commands.OIL_TEMP,
                        obd.commands.OIL_TEMP

                    ]
        for command in allCommands:
            try:
                response = connection.query(obd.commands[command.name])
                telemetryValue = getValue(response)
                message[command.name] = str(telemetryValue)
            
            except Exception as e:
                print ("Error querying OBDII entry: " + command.name + ", error: " + str(e))
        
        if(message["RPM"] == "0"):
            print("Cannot read RPM, reconnecting...")
            connection = obd.OBD(fast=True) 
            return None
        else:
            return message

    except Exception as e:
        print("Error with OBDII, error: " + str(e) + ". Reconnecting...")
        connection = obd.OBD(fast=True)
        return None

