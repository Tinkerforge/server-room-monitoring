#!/usr/bin/env python
# -*- coding: utf8 -*-
# based on Wiki project:
# http://www.tinkerunity.org/wiki/index.php/EN/Projects/IT_Infrastructure_Monitoring_-_Nagios_Plugin

OK = 0
WARNING = 1
CRITICAL = 2
UNKNOWN = 3

TYPE_PTC = "ptc"
TYPE_TEMPERATURE = "temp"

from tinkerforge.ip_connection import IPConnection
from tinkerforge.bricklet_temperature import Temperature
from tinkerforge.bricklet_ptc import PTC
from tinkerforge.bricklet_ptc_v2 import PTCV2
import argparse
import sys

class CheckTFTemperature(object):
    def __init__(self, host='localhost', port=4223):
        self.host = host
        self.port = port
        self.ipcon = IPConnection()

    def connect(self, type, uid):
        self.ipcon.connect(self.host, self.port)
        self.connected_type = type

        if self.connected_type == TYPE_PTC:
            ptc = PTC(uid, self.ipcon)

            if ptc.get_identity().device_identifier == PTCV2.DEVICE_IDENTIFIER:
                ptc = PTCV2(uid, self.ipcon)

            self.func = ptc.get_temperature
        elif self.connected_type == TYPE_TEMPERATURE:
            temperature = Temperature(uid, self.ipcon)
            self.func = temperature.get_temperature

    def disconnect(self):
        self.ipcon.disconnect()

    def read_temperature(self):
        return self.func()/100.0

    def read(self, warning, critical, mode='none', warning2=0, critical2=0):
        temp = self.read_temperature()

        if mode == 'none':
            print "temperature %s °C" % temp
        else:
            if mode == 'low':
                warning2 = warning
                critical2 = critical

            if temp >= critical and (mode == 'high' or mode == 'range'):
                print "CRITICAL : temperature too high %s °C" % temp
                return CRITICAL
            elif temp >= warning and (mode == 'high' or mode == 'range'):
                print "WARNING : temperature is high %s °C" % temp
                return WARNING
            elif temp <= critical2 and (mode == 'low' or mode == 'range'):
                print "CRITICAL : temperature too low %s °C" % temp
                return CRITICAL
            elif temp <= warning2 and (mode == 'low' or mode == 'range'):
                print "WARNING : temperature is low %s °C" % temp
                return WARNING
            elif (temp < warning and mode == 'high') or \
                 (temp > warning2 and mode == 'low') or \
                 (temp < warning and temp > warning2 and mode == 'range'):
                print "OK : %s°C " % temp
                return OK
            else:
                print "UNKNOWN : can't read temperature"
                return UNKNOWN

if __name__ == "__main__":
    parse = argparse.ArgumentParser()
    parse.add_argument("-u", "--uid", help="UID from Temperature Bricklet", required=True)
    parse.add_argument("-t", "--type", help="Type: temp = Temperature Bricklet, ptc = PTC Bricklet", type=str, choices=[TYPE_TEMPERATURE, TYPE_PTC], required=True)
    parse.add_argument("-H", "--host", help="Host Server (default=localhost)", default='localhost')
    parse.add_argument("-P", "--port", help="Port (default=4223)", type=int, default=4223)
    parse.add_argument("-m", "--modus", help="Modus: none (default, only print temperature), high, low or range", type=str, choices=['none', 'high','low','range'], default='none')
    parse.add_argument("-w", "--warning", help="Warning temperature level (temperatures above this level will trigger a warning message in high mode, temperature below this level will trigger a warning message in low mode)", required=False, type=float)
    parse.add_argument("-c", "--critical", help="Critical temperature level (temperatures above this level will trigger a critical message in high mode, temperature below this level will trigger a critical message in low mode)", required=False, type=float)
    parse.add_argument("-w2", "--warning2", help="Warning temperature level (temperatures below this level will trigger a warning message in range mode)", type=float)
    parse.add_argument("-c2", "--critical2", help="Critical temperature level (temperatures below this level will trigger a critical message in range mode)", type=float)

    args = parse.parse_args()

    tf = CheckTFTemperature(args.host, args.port)
    tf.connect(args.type, args.uid)
    exit_code = tf.read(args.warning, args.critical, args.modus, args.warning2, args.critical2)
    tf.disconnect()
    sys.exit(exit_code)
