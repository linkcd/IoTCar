
from gpsreader import GPSReader 
import time
import json


#start reading gps data...
myGPSReader = GPSReader("/dev/ttyACM0")
latestFixedTime = None

while True:
    latestFixedPoint = myGPSReader.getLatestFixedGPSPoint()
    if latestFixedPoint is not None and latestFixedPoint.sentenceIimestamp != latestFixedTime:
        #new GPS point than previous one, send to iot hub
        jsonPayload = latestFixedPoint.buildJsonPayload("test_device")
        print("Payload of new GPS data is: " + jsonPayload)
        print("++++++++++++++++++++")
    else:
        print("no fixed yet...")
    time.sleep(1)