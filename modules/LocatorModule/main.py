# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import random
import time
import sys
import iothub_client
# pylint: disable=E0611
from iothub_client import IoTHubModuleClient, IoTHubClientError, IoTHubTransportProvider
from iothub_client import IoTHubMessage, IoTHubMessageDispositionResult, IoTHubError
import json
from datetime import datetime
from gpsreader import GPSReader 

# messageTimeout - the maximum time in milliseconds until a message times out.
# The timeout period starts at IoTHubModuleClient.send_event_async.
# By default, messages do not expire.
MESSAGE_TIMEOUT = 10000

#TODO get real device id
DEVICE_ID = "FengsDevice"
GPSDeviceTtyAC = "/dev/ttyACM0"


# global counters
RECEIVE_CALLBACKS = 0
SEND_CALLBACKS = 0

# Choose HTTP, AMQP or MQTT as transport protocol.  Currently only MQTT is supported.
PROTOCOL = IoTHubTransportProvider.MQTT

# Callback received when the message that we're forwarding is processed.
def send_confirmation_callback(message, result, user_context):
    global SEND_CALLBACKS
    print ( "Confirmation[%d] received for message with result = %s" % (user_context, result) )
    map_properties = message.properties()
    key_value_pair = map_properties.get_internals()
    print ( "    Properties: %s" % key_value_pair )
    SEND_CALLBACKS += 1
    print ( "    Total calls confirmed: %d" % SEND_CALLBACKS )

class HubManager(object):

    def __init__(
            self,
            protocol=IoTHubTransportProvider.MQTT):
        self.client_protocol = protocol
        self.client = IoTHubModuleClient()
        self.client.create_from_environment(protocol)

        # has to setup auto_url_encode_decode in order to use content type and encoding
        self.client.set_option('auto_url_encode_decode', True)

        # set the time until a message times out
        self.client.set_option("messageTimeout", MESSAGE_TIMEOUT)
        
    # Forwards the message received onto the next stage in the process.
    def forward_event_to_output(self, outputQueueName, event, send_context):
        self.client.send_event_async(
            outputQueueName, event, send_confirmation_callback, send_context)

def main(protocol):
    try:
        print ( "\nPython %s\n" % sys.version )
        print ( "IoT Hub Client for Python" )

        hub_manager = HubManager(protocol)

        print ( "Starting the GPS locator module using protocol %s..." % hub_manager.client_protocol )
        print ( "This module is now waiting for messages and will indefinitely.  Press Ctrl-C to exit. ")

        #start reading gps data...
        myGPSReader = GPSReader(GPSDeviceTtyAC)
        latestFixedTime = None

        while True:
            latestFixedPoint = myGPSReader.getLatestFixedGPSPoint()
            if latestFixedPoint is not None and latestFixedPoint.sentenceTimestamp != latestFixedTime:
                #new GPS point than previous one, send to iot hub
                jsonPayload = latestFixedPoint.buildJsonPayload(DEVICE_ID)
                print("Payload of new GPS data is: " + jsonPayload)

                msg = IoTHubMessage(bytearray(jsonPayload, 'utf8'))

                #in order to use IoT Hub message routing on body, we have to setup the content type and encoding
                set_content_result = msg.set_content_encoding_system_property("utf-8")
                set_content_type_result = msg.set_content_type_system_property("application/json")

                if set_content_result != 0:
                    print("set_content_encoding_system_property FAILED")
                            
                if set_content_type_result != 0:
                    print("set_content_type_system_property FAILED")

                hub_manager.forward_event_to_output("gps", msg, 0)
                latestFixedTime = latestFixedPoint.sentenceTimestamp
            else:
                print(str(datetime.now()) + ": Not fixed yet....")
            time.sleep(1)

    except IoTHubError as iothub_error:
        print ( "Unexpected error %s from IoTHub" % iothub_error )
        return
    except KeyboardInterrupt:
        print ( "IoTHubModuleClient sample stopped" )

if __name__ == '__main__':
    main(PROTOCOL)