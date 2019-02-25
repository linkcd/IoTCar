
from gpsreader import GPSReader 
import time
import json
from datetime import datetime

#start reading gps data...
myGPSReader = GPSReader("/dev/ttyACM0")
latestFixedTime = None

while True:
    latestFixedPoint = myGPSReader.getLatestFixedGPSPoint()
    if latestFixedPoint is not None and latestFixedPoint.sentenceTimestamp != latestFixedTime:
        #new GPS point than previous one, send to iot hub
        jsonPayload = latestFixedPoint.buildJsonPayload("test_device")
        print("Payload of new GPS data is: " + jsonPayload)
        latestFixedTime = latestFixedPoint.sentenceTimestamp
        print("++++++++++++++++++++")
    else:
        print(str(datetime.now()) + ": Not fixed yet....")
    time.sleep(1)