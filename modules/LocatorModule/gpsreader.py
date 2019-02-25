import serial
import pynmea2
import threading
import json
from datetime import datetime
from collections import deque

import time



class GPSReader:
    class GPSDataPoint:
        def __init__(self, sentenceIimestamp):
            self.sentenceTimestamp = sentenceIimestamp
            self.data = {}
            self.data["sentenceTimestamp"] = sentenceIimestamp
        
        def isFixed(self):
            if "gps_quality" in self.data and self.data["gps_quality"] == 1:
                return True
            else:
                return False
        
        def saveSentenceResult(self, result):
            
            if result.sentence_type == 'GGA':
                self.data["latitude"] = result.lat             
                self.data["latitude_dir"] = result.lat_dir
                self.data["longitude"] = result.lon
                self.data["longitude_dir"] = result.lon_dir
                self.data["altitude"] = result.altitude
                self.data["altitude_units"] = result.altitude_units
                self.data["gps_quality"] = result.gps_qual
                self.data["num_sats"] = result.num_sats
                self.data["horizontal_dil"] = result.horizontal_dil
                self.data["geo_sep"] = result.geo_sep
                self.data["geo_sep_units"] = result.geo_sep_units
                self.data["age_gps_data"] = result.age_gps_data
                self.data["ref_station_id"] = result.ref_station_id

            if result.sentence_type == 'RMC':
                self.data["datestamp"] = result.datestamp
                self.data["speed"] = result.spd_over_grnd
                self.data["true_course"] = result.true_course
                self.data["mag_variation"] = result.mag_variation
                self.data["mag_var_dir"] = result.mag_var_dir

        def getJson(self):
            #try to get full timestamp (date + time), and save to "timestamp" json field
            if "datestamp" in self.data and self.data["datestamp"] is not None:
                fulldt = datetime.combine(self.data["datestamp"], self.sentenceTimestamp)
                self.data["timestamp"] = fulldt
                
            json.dumps(self.data)

    class GPSDataPointsManager:
        def __init__(self):
            self.storage = deque(maxlen=5)

        def getLatestFixedGPSPoint(self):
            for point in self.storage:
                if point.isFixed:
                    return point
            #return none if didnot find fixed one
            return None    

        def __getCorrectPointToUpdate(self, sentenceTimestamp):
            #step 1. try to search and update existing one
            for point in self.storage:
                if point.sentenceTimestamp == sentenceTimestamp:
                    return point
            #step 2. ELSE, we cannot find the existing point with that timestamp, create new one and put it into the storage
            newPoint = GPSReader.GPSDataPoint(sentenceTimestamp)
            self.storage.appendleft(newPoint)
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
                self.pointsManager.ingestNewSentence(result)
            except:
                print("drop invalid GGA: " + sentence)

        if sentence.find('RMC') > 0:
            try:
                result = pynmea2.parse(sentence)
                self.pointsManager.ingestNewSentence(result)
            except:
                print("drop invalid RMC: " + sentence)

    def __initSerialStream(self):
        print(">>> Initaling GPS serial stream from: " + self.__serialttyAC)
        self.isFixed = False

        if self.__serialStream is not None and not self.__serialStream.closed:
            self.__serialStream.close()

        self.serialStream = serial.Serial(self.__serialttyAC, 9600, timeout=0.5)

    # Gps Receiver thread funcion, check gps value for infinte times
    def __readSerialData(self):
        while True:
            #infinte loop for openining and reading content from device. If failed, restart
            try:
                self.__initSerialStream()
                try:
                    while True:
                        sentence = self.serialStream.readline()
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






