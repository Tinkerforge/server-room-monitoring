#!/usr/bin/env python
# -*- coding: utf8 -*-
# based on Wiki project:
# http://www.tinkerunity.org/wiki/index.php/EN/Projects/IT_Infrastructure_Monitoring_-_Nagios_Plugin

OK = 0
WARNING = 1
CRITICAL = 2
UNKNOWN = 3
MOTION_DETECTED = 1
NO_MOTION_DETECTED = 0

TYPE_PTC = "ptc"
TYPE_TEMPERATURE = "temp"
TYPE_HUMIDITY = "humidity"
TYPE_MOTION_DETECTOR = "motion_detector"
TYPE_SEGMENT_DISPLAY_4X7 = "segment_display_4x7"

from tinkerforge.ip_connection import IPConnection
from tinkerforge.bricklet_temperature import Temperature
from tinkerforge.bricklet_ptc import PTC
from tinkerforge.bricklet_humidity import Humidity
from tinkerforge.bricklet_motion_detector import MotionDetector
from tinkerforge.bricklet_motion_detector_v2 import MotionDetectorV2
from tinkerforge.bricklet_segment_display_4x7 import SegmentDisplay4x7
import argparse
import sys

class CheckTFTemperature(object):
    def __init__(self, host='localhost', port=4223):
        self.host = host
        self.port = port
        self.ipcon = IPConnection()
        self.name = 'unknown'
        self.unit = 'unknown'

    def connect(self, type, uid):
        self.ipcon.connect(self.host, self.port)
        self.connected_type = type

        if self.connected_type == TYPE_PTC:
            ptc = PTC(uid, self.ipcon)
            self.func = ptc.get_temperature
            self.name = 'temperature'
            self.unit = '°C'
        elif self.connected_type == TYPE_TEMPERATURE:
            temperature = Temperature(uid, self.ipcon)
            self.func = temperature.get_temperature
            self.name = 'temperature'
            self.unit = '°C'
        elif self.connected_type == TYPE_HUMIDITY:
            humidity = Humidity(uid, self.ipcon)
            self.func = humidity.get_humidity
            self.name = 'humidity'
            self.unit = '%RH'
        elif self.connected_type == TYPE_MOTION_DETECTOR:
            md = MotionDetector(uid, self.ipcon)

            if md.get_identity().device_identifier == MotionDetectorV2.DEVICE_IDENTIFIER:
                md = MotionDetectorV2(uid, self.ipcon)

            self.func = md.get_motion_detected
        elif self.connected_type == TYPE_SEGMENT_DISPLAY_4X7:
            display = SegmentDisplay4x7(uid, self.ipcon)
            self.func = display.set_segments

    def disconnect(self):
        self.ipcon.disconnect()

    def error(self, e):
        if e == "true":
            self.func((0, 80, 80, 121), 8, False)
        else:
            self.func((0, 0, 0, 0), 8, False)

    def read_sensor(self):
        if self.connected_type == TYPE_HUMIDITY:
            return self.func()/10.0
        elif self.connected_type == TYPE_MOTION_DETECTOR:
            return self.func()
        else: # Temperature, PTC
            return self.func()/100.0

    def read(self, warning, critical, mode='none', warning2=0, critical2=0):
        val = self.read_sensor()

        if self.connected_type == TYPE_MOTION_DETECTOR:
            if val == 1:
                print "motion detected"
                return MOTION_DETECTED
            else:
                print "no motion detected"
                return NO_MOTION_DETECTED
        else:
            if mode == 'none':
                print "%s %s %s" % (self.name, val, self.unit)
            else:
                if mode == 'low':
                    warning2 = warning
                    critical2 = critical

                if val >= critical and (mode == 'high' or mode == 'range'):
                    print "CRITICAL : %s too high %s %s" % (self.name, val, self.unit)
                    return CRITICAL
                elif val >= warning and (mode == 'high' or mode == 'range'):
                    print "WARNING : %s is high %s %s" % (self.name, val, self.unit)
                    return WARNING
                elif val <= critical2 and (mode == 'low' or mode == 'range'):
                    print "CRITICAL : %s too low %s %s" % (self.name, val, self.unit)
                    return CRITICAL
                elif val <= warning2 and (mode == 'low' or mode == 'range'):
                    print "WARNING : %s is low %s %s" % (self.name, val, self.unit)
                    return WARNING
                elif (val < warning and mode == 'high') or \
                     (val > warning2 and mode == 'low') or \
                     (val < warning and val > warning2 and mode == 'range'):
                    print "OK : %s %s" % (val, self.unit)
                    return OK
                else:
                    print "UNKNOWN : can't read %s" % self.name
                    return UNKNOWN

if __name__ == "__main__":
    parse = argparse.ArgumentParser()
    parse.add_argument("-u", "--uid", help="UID from Bricklet", required=True)
    parse.add_argument("-t", "--type", help="Choose fitting type for your Bricklet", type=str, choices=[TYPE_TEMPERATURE, TYPE_PTC, TYPE_HUMIDITY, TYPE_MOTION_DETECTOR, TYPE_SEGMENT_DISPLAY_4X7], required=True)
    parse.add_argument("-H", "--host", help="Host Server (default=localhost)", default='localhost')
    parse.add_argument("-P", "--port", help="Port (default=4223)", type=int, default=4223)
    parse.add_argument("-m", "--modus", help="Modus: none (default, only print value), high, low or range", type=str, choices=['none', 'high','low','range'], default='none')
    parse.add_argument("-w", "--warning", help="Warning value level (values above this level will trigger a warning message in high mode, values below this level will trigger a warning message in low mode)", required=False, type=float)
    parse.add_argument("-c", "--critical", help="Critical value level (values above this level will trigger a critical message in high mode, values below this level will trigger a critical message in low mode)", required=False, type=float)
    parse.add_argument("-w2", "--warning2", help="Warning value level (values below this level will trigger a warning message in range mode)", type=float)
    parse.add_argument("-c2", "--critical2", help="Critical value level (values below this level will trigger a critical message in range mode)", type=float)
    parse.add_argument("-e", "--error", help="Set Error Message on 4x7 Segment On/Off", choices=['true', 'false'], type=str, default='true')

    args = parse.parse_args()

    tf = CheckTFTemperature(args.host, args.port)
    tf.connect(args.type, args.uid)

    if args.type == TYPE_SEGMENT_DISPLAY_4X7:
        tf.error(args.error)
        exit_code = 0
    else:
        exit_code = tf.read(args.warning, args.critical, args.modus,
                            args.warning2, args.critical2)

    tf.disconnect()
    sys.exit(exit_code)
