#!/usr/bin/env python
# -*- coding: utf-8 -*-

import socket
import sys
import time
import math
import logging as log
import httplib
import json
import threading
log.basicConfig(level=log.INFO)

from tinkerforge.ip_connection import IPConnection
from tinkerforge.ip_connection import Error
from tinkerforge.brick_master import Master
from tinkerforge.bricklet_ambient_light import AmbientLight
from tinkerforge.bricklet_ambient_light_v2 import AmbientLightV2
from tinkerforge.bricklet_temperature import Temperature

class Xively:
    HOST = 'api.xively.com'
    AGENT = "Tinkerforge xively 1.0"
    FEED = '196340443.json'
    API_KEY = 'SGpMEW3ZZ6yJVd9jZlaPgex06v1W00lA2UZkv5rgskwlVkr6'

    def __init__(self):
        self.items = {}
        self.headers = {
            "Content-Type"  : "application/x-www-form-urlencoded",
            "X-ApiKey"      : Xively.API_KEY,
            "User-Agent"    : Xively.AGENT,
        }
        self.params = "/v2/feeds/" + str(Xively.FEED)
        self.upload_thread = threading.Thread(target=self.upload)
        self.upload_thread.daemon = True
        self.upload_thread.start()

    def put(self, identifier, value):
        try:
            _, min_value, max_value = self.items[identifier]
            if value < min_value:
                min_value = value
            if value > max_value:
                max_value = value
            self.items[identifier] = (value, min_value, max_value)
        except:
            self.items[identifier] = (value, value, value)

    def upload(self):
        while True:
            time.sleep(60) # Upload data every minute
            if len(self.items) == 0:
                continue

            stream_items = []
            for identifier, value in self.items.items():
                stream_items.append({'id': identifier,
                                     'current_value': value[0],
                                     'min_value': value[1],
                                     'max_value': value[2]})

            data = {'version': '1.0.0',
                    'datastreams': stream_items}
            self.items = {}
            body = json.dumps(data)

            try:
                http = httplib.HTTPSConnection(Xively.HOST)
                http.request('PUT', self.params, body, self.headers)
                response = http.getresponse()
                http.close()
                log.info('Start upload')

                if response.status != 200:
                    log.error('Could not upload to xively -> ' +
                              str(response.status) + ': ' + response.reason)
            except Exception as e:
                log.error('HTTP error: ' + str(e))

class ServerRoomMonitoring:
    HOST = "ServerMonitoring"
    PORT = 4223

    ipcon = None
    al = None
    al_v2 = None
    temp = None

    def __init__(self):
        self.xively = Xively()
        self.ipcon = IPConnection()
        while True:
            try:
                self.ipcon.connect(ServerRoomMonitoring.HOST, ServerRoomMonitoring.PORT)
                break
            except Error as e:
                log.error('Connection Error: ' + str(e.description))
                time.sleep(1)
            except socket.error as e:
                log.error('Socket error: ' + str(e))
                time.sleep(1)

        self.ipcon.register_callback(IPConnection.CALLBACK_ENUMERATE,
                                     self.cb_enumerate)
        self.ipcon.register_callback(IPConnection.CALLBACK_CONNECTED,
                                     self.cb_connected)

        while True:
            try:
                self.ipcon.enumerate()
                break
            except Error as e:
                log.error('Enumerate Error: ' + str(e.description))
                time.sleep(1)

    def cb_illuminance(self, illuminance):
        self.xively.put('AmbientLight', illuminance/10.0)
        log.info('Ambient Light ' + str(illuminance/10.0))

    def cb_illuminance_v2(self, illuminance):
        self.xively.put('AmbientLight', illuminance/100.0)
        log.info('Ambient Light ' + str(illuminance/100.0))

    def cb_temperature(self, temperature):
        self.xively.put('Temperature', temperature/100.0)
        log.info('Temperature ' + str(temperature/100.0))

    def cb_enumerate(self, uid, connected_uid, position, hardware_version,
                     firmware_version, device_identifier, enumeration_type):
        if enumeration_type == IPConnection.ENUMERATION_TYPE_CONNECTED or \
           enumeration_type == IPConnection.ENUMERATION_TYPE_AVAILABLE:
            if device_identifier == AmbientLight.DEVICE_IDENTIFIER:
                try:
                    self.al = AmbientLight(uid, self.ipcon)
                    self.al.set_illuminance_callback_period(1000)
                    self.al.register_callback(self.al.CALLBACK_ILLUMINANCE,
                                              self.cb_illuminance)
                    log.info('Ambient Light initialized')
                except Error as e:
                    log.error('Ambient Light init failed: ' + str(e.description))
                    self.al = None
            elif device_identifier == AmbientLightV2.DEVICE_IDENTIFIER:
                try:
                    self.al_v2 = AmbientLightV2(uid, self.ipcon)
                    self.al_v2.set_illuminance_callback_period(1000)
                    self.al_v2.register_callback(self.al_v2.CALLBACK_ILLUMINANCE,
                                                 self.cb_illuminance_v2)
                    log.info('Ambient Light 2.0 initialized')
                except Error as e:
                    log.error('Ambient Light 2.0 init failed: ' + str(e.description))
                    self.al_v2 = None
            elif device_identifier == Temperature.DEVICE_IDENTIFIER:
                try:
                    self.temp = Temperature(uid, self.ipcon)
                    self.temp.set_temperature_callback_period(1000)
                    self.temp.register_callback(self.temp.CALLBACK_TEMPERATURE,
                                               self.cb_temperature)
                    log.info('Temperature initialized')
                except Error as e:
                    log.error('Temperature init failed: ' + str(e.description))
                    self.temp = None

    def cb_connected(self, connected_reason):
        if connected_reason == IPConnection.CONNECT_REASON_AUTO_RECONNECT:
            log.info('Auto Reconnect')

            while True:
                try:
                    self.ipcon.enumerate()
                    break
                except Error as e:
                    log.error('Enumerate Error: ' + str(e.description))
                    time.sleep(1)

if __name__ == "__main__":
    log.info('Server Room Monitoring: Start')

    server_room_monitoring = ServerRoomMonitoring()

    if sys.version_info < (3, 0):
        input = raw_input # Compatibility for Python 2.x
    input('Press key to exit\n')

    if server_room_monitoring.ipcon != None:
        server_room_monitoring.ipcon.disconnect()

    log.info('Server Room Monitoring: End')
