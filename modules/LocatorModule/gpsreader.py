import serial
import pynmea2
import threading
import json
from datetime import datetime
from collections import deque
import time
from decimal import *

class GPSReader:
    class GPSDataPoint:
        def __init__(self, sentenceIimestamp):
            self.sentenceTimestamp = sentenceIimestamp
            self.data = {}
            self.data["fixed_time"] = str(sentenceIimestamp) #make sure it is part of the json dump, have to convert from datetime to string for json dump
        
        def isFixed(self):
            if "gps_quality" in self.data and self.data["gps_quality"] == 1:
                return True
            else:
                return False

        def getCoordiateFromValueInSentence(self, value):
            if value is None or value == "":
                return None
            # The latitude is formatted as DDMM.ffff and longitude is DDDMM.ffff where D is the degrees and M is minutes plus the fractional minutes. 
            # So, 1300.8067,N is 13 degrees 00.8067 minutes North and the longitude of 07733.0003,E is read as 77 degrees 33.0003 minutes East.
            # Converting to degrees you would have to do this: 13 + 00.8067/60 for latitude and 77 + 33.0003/60 for the longitude.
            # ##NMEA outputs in a human readable DDDMM.mmmm format NOT DECIMAL DEGREES
            # 3746.03837
            # 37 46.03837
            # 37 + (46.03837 / 60)
            # result = 37 + 0.7673062
            
            #sample latitude: 5952.84746
            #sample longitude: 01029.68131

            #print("org: " + value)

            segments = value.split('.')
            if len(segments[0]) == 4:
                #latitue
                degree = segments[0][:2]
            else:
                #longtitude
                degree = segments[0][:3]

            #print("degree:" + degree)
            #print("minute part1: " + segments[0][-2:])
            #print("minute part2: " + segments[1])
            
            minute = round(Decimal(segments[0][-2:] + "." + segments[1])/60, 6)
            
            #print("computed minute:" + str(minute))
            
            result = Decimal(degree) + minute
            
            #print("result:" + str(result))

            return str(result)
        
        def saveSentenceResult(self, result):
            #document of protocol: https://www.gpsinformation.org/dale/nmea.htm
            #definition of pynmea2 sentence: https://github.com/Knio/pynmea2/blob/master/pynmea2/types/talker.py
            #sample test of pynmea2: https://github.com/Knio/pynmea2/blob/master/test/test_types.py 

            if result.sentence_type == 'GGA': # and result.gps_qual == 1: #only save valid (gps fixed) data
                self.data["latitude"] = self.getCoordiateFromValueInSentence(result.lat)            
                self.data["latitude_dir"] = result.lat_dir
                self.data["longitude"] = self.getCoordiateFromValueInSentence(result.lon)
                self.data["longitude_dir"] = result.lon_dir
                self.data["altitude"] = result.altitude
                self.data["altitude_units"] = result.altitude_units
                self.data["gps_quality"] = result.gps_qual
                self.data["num_sats"] = int(result.num_sats)
                self.data["horizontal_dil"] = result.horizontal_dil
                self.data["geo_sep"] = result.geo_sep
                self.data["geo_sep_units"] = result.geo_sep_units
                #self.data["age_gps_data"] = result.age_gps_data
                #self.data["ref_station_id"] = result.ref_station_id

            if result.sentence_type == 'RMC': # and result.spd_over_grnd is not None: #only save valid data
                self.data["fixed_date"] = str(result.datestamp) # have to convert from datetime to string for json dump

                #save full timestamp (date + time)
                if result.datestamp is not None:
                    fulldt = datetime.combine(result.datestamp, self.sentenceTimestamp)
                    self.data["fixed_full_timestamp"] = str(fulldt) # have to convert from datetime to string for json dump

                self.data["gps_speed"] = result.spd_over_grnd
                self.data["true_course"] = result.true_course
                self.data["mag_variation"] = result.mag_variation
                self.data["mag_var_dir"] = result.mag_var_dir
        
        def buildJsonPayload(self, deviceId):
            mydeviceId = deviceId + "_GPS"
            if "full_timestamp" in self.data:
                full_timestamp = self.data["full_timestamp"]
            else:   
                full_timestamp = str(datetime.now())
            payload = {'timestamp': full_timestamp, 'deviceId': mydeviceId, "series":[self.data]}

            return json.dumps(payload)
    
    
    class GPSDataPointsManager:
        def __init__(self):
            self.__storage = deque(maxlen=5)

        def getLatestFixedGPSPoint(self):
            for point in self.__storage:
                if point.isFixed():
                    return point
            #return none if didnot find fixed one
            return None    

        def __getCorrectPointToUpdate(self, sentenceTimestamp):
            #step 1. try to search and update existing one
            for point in self.__storage:
                if point.sentenceTimestamp == sentenceTimestamp:
                    return point
            #step 2. ELSE, we cannot find the existing point with that timestamp, create new one and put it into the storage
            newPoint = GPSReader.GPSDataPoint(sentenceTimestamp)
            self.__storage.appendleft(newPoint)
            return newPoint

        def ingestNewSentence(self, sentenceResult):
            toBeUpdatedPoint = self.__getCorrectPointToUpdate(sentenceResult.timestamp)
            toBeUpdatedPoint.saveSentenceResult(sentenceResult)

    def __init__(self, serialttyAC):
        self.__serialttyAC = serialttyAC
        self.__serialStream = None
        self.__pointsManager = GPSReader.GPSDataPointsManager()

        #start reading automatically
        serialReaderThread = threading.Thread(target=self.__readSerialData)
        serialReaderThread.start()
        print("serial reader thread started...")

    def __parseGPSData(self, sentence):
        sentence = sentence.decode()
        #GGA
        if sentence.find('GGA') > 0:
            try:
                result = pynmea2.parse(sentence)
                self.__pointsManager.ingestNewSentence(result)
            except Exception as e:
                print("drop invalid GGA: " + sentence + ". Error: " + str(e))

        if sentence.find('RMC') > 0:
            try:
                result = pynmea2.parse(sentence)
                self.__pointsManager.ingestNewSentence(result)
            except Exception as e:
                print("drop invalid RMC: " + sentence + ". Error: " + str(e))

    def __initSerialStream(self):
        print(">>> Initaling GPS serial stream from: " + self.__serialttyAC)

        if self.__serialStream is not None and not self.__serialStream.closed:
            print("close serial stream...")
            self.__serialStream.close()

        self.__serialStream = serial.Serial(self.__serialttyAC, 9600, timeout=0.5)

    # Gps Receiver thread funcion, check gps value for infinte times
    def __readSerialData(self):
        while True:
            #infinte loop for openining and reading content from device. If failed, restart
            try:
                self.__initSerialStream()
                try:
                    while True:
                        sentence = self.__serialStream.readline()
                        self.__parseGPSData(sentence)
                except Exception as e:
                    print("Error: " + str(e))        
            except serial.serialutil.SerialException as e:
                print("Error when reading from device:" + str(e))
                
            #exec this only if we had error at above
            print("Had error. Wait for 1 second and re-init the serial stream...")
            time.sleep(1)
    
    #public method
    def getLatestFixedGPSPoint(self):
        return self.__pointsManager.getLatestFixedGPSPoint()



