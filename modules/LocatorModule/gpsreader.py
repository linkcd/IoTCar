import serial
import pynmea2
import threading
import os
from datetime import datetime
import time

class GSPReporter:
    def parseGPSData(self, sentence):
        sentence = sentence.decode()
        #GGA
        if sentence.find('GGA') > 0:
            try:
                result = pynmea2.parse(sentence)
                self.latitude = result.lat
                self.latitude_dir = result.lat_dir
                self.longitude = result.lon
                self.longitude_dir = result.lon_dir
                self.altitude = result.altitude
                self.altitude_units = result.altitude_units
                self.gps_quality = result.gps_qual

                if result.gps_qual == 1:
                    self.isFixed = True

                self.num_sats = result.num_sats
                self.horizontal_dil = result.horizontal_dil
                self.geo_sep = result.geo_sep
                self.geo_sep_units = result.geo_sep_units
                self.age_gps_data = result.age_gps_data
                self.ref_station_id = result.ref_station_id
            except:
                print("drop invalid GGA: " + sentence)

        if sentence.find('RMC') > 0:
            try:
                result = pynmea2.parse(sentence)
                self.speed = result.spd_over_grnd
                self.datestamp = result.datestamp
                self.timestamp = result.timestamp
                self.true_course = result.true_course
                self.mag_variation = result.mag_variation
                self.mag_var_dir = result.mag_var_dir
            except:
                print("drop invalid RMC: " + sentence)

    def initSerialStream(self):
        print(">>> Initaling GPS serial stream from: " + self.serialttyAC)
        self.isFixed = False

        if self.serialStream is not None and not self.serialStream.closed:
            self.serialStream.close()

        self.serialStream = serial.Serial(self.serialttyAC, 9600, timeout=0.5)

    # Gps Receiver thread funcion, check gps value for infinte times
    def readSerialData(self):
        while True:
            #infinte loop for openining and reading content from device. If failed, restart
            try:
                self.initSerialStream()
                try:
                    while True:
                        sentence = self.serialStream.readline()
                        self.parseGPSData(sentence)
                except Exception as e:
                    print("Error: " + str(e))        
            except serial.serialutil.SerialException as e:
                print("Error when reading from device:" + str(e))
                
            #exec this only if we had error at above
            print("Had error. Wait for 1 second and re-init the serial stream...")
            time.sleep(1)


    def __init__(self, serialttyAC):
        self.serialttyAC = serialttyAC
        self.serialStream = None
        self.isFixed = False

        serialReaderThread = threading.Thread(target=self.readSerialData)
        serialReaderThread.start()
        print("serial reader thread started...")


def getGPS(ttyAC):
    reporter = GSPReporter(ttyAC)
    while True:
        if reporter.isFixed:
            print(reporter.latitude + ' ' + reporter.latitude_dir)
            print(reporter.longitude + ' ' + reporter.longitude_dir)
            print(reporter.altitude)
            print(reporter.num_sats)
            print(reporter.speed)
            print(reporter.timestamp)
            print(reporter.datestamp)
            print("++++++++++++++++++++")
        else:
            print("not fixed yet...")
        time.sleep(2)

    #gpsdata = pynmea2.parse(sentence)
    #print(gpsdata)


getGPS("/dev/ttyACM0")





