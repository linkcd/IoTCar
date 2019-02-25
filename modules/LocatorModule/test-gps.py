
from gpsreader import GPSReader 
import time

reader = GPSReader("/dev/ttyACM0")
while True:
    latestFixedPoint = reader.getLatestFixedGPSPoint()

    if latestFixedPoint is not None:
        print(latestFixedPoint.getJson())
        print("++++++++++++++++++++")
    else:
        print("not fixed yet...")
    time.sleep(2)