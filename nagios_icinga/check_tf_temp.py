#!/usr/bin/env python
# -*- coding: utf8 -*-
# based on Wiki project:
# http://www.tinkerunity.org/wiki/index.php/EN/Projects/IT_Infrastructure_Monitoring_-_Nagios_Plugin
 
OK = 0
WARNING = 1
CRITICAL = 2
UNKNOWN = 3
 
from tinkerforge.ip_connection import IPConnection
from tinkerforge.bricklet_temperature import Temperature
import argparse
import sys
 
class CheckTFTemperature(object):
    def __init__(self,host='localhost',port=4223):
	self.host = host
	self.port = port
	self.ipcon = IPConnection()
 
    def connect(self):
	self.ipcon.connect(self.host, self.port)
 
    def disconnect(self):
	self.ipcon.disconnect()
 
    def read_temperature(self,uid):
        self.temperature = Temperature(uid,self.ipcon)
	self.temp_uid = uid
 
	return self.temperature.get_temperature()/100.0
 
    def read(self, uid, warning, critical, mode='high', warning2=0,critical2=0):
	temp = self.read_temperature(uid)

        if mode == 'low':
            warning2 = warning
            critical2 = critical

	if temp >= critical and (mode == 'high' or mode == 'range'):
	    print "CRITICAL : Temperature too high %s ° " % temp
            return CRITICAL
        elif temp >= warning and (mode == 'high' or mode == 'range'):
	    print "WARNING : Temperature is high %s°" % temp
	    return WARNING
        elif temp <= critical2 and (mode == 'low' or mode == 'range'):
	    print "CRITICAL : Temperature too low %s ° " % temp
	    return CRITICAL
        elif temp <= warning2 and (mode == 'low' or mode == 'range'):
	    print "WARNING : temperature is low %s°" % temp
	    return WARNING
        elif (temp < warning and mode == 'high') or (temp > warning2 and mode == 'low') or (temp < warning and temp > warning2 and mode == 'range'):
	    print "OK : %s°"%temp
	    return OK
	else:
	    print "UNKOWN: Can't read temperature"
	    return UNKNOWN
 
if __name__ == "__main__":
 
    parse = argparse.ArgumentParser()
    parse.add_argument("-u","--uid",help="UID from Temperature Bricklet",required=True)
    parse.add_argument("-H","--host",help="Host Server (default=localhost)",default='localhost')
    parse.add_argument("-P","--port",help="Port (default=4223)",type=int,default=4223)
    parse.add_argument("-m","--modus",help="Modus: high (default), low or range",type=str,choices=['high','low','range'],default='high')
    parse.add_argument("-w","--warning",help="Warning temperature level (temperatures above this level will trigger a warning message in high mode,temperature below this level will trigger a warning message in low mode)",required=True,type=float)
    parse.add_argument("-c","--critical",help="Critical temperature level (temperatures above this level will trigger a critical message in high mode, temperature below this level will trigger a critical message in low mode)",required=True,type=float)
    parse.add_argument("-w2","--warning2",help="Warning temperature level (temperatures below this level will trigger a warning message in range mode)",type=float)
    parse.add_argument("-c2","--critical2",help="Critical temperature level (temperatures below this level will trigger a critical message in range mode)",type=float)
 
    args = parse.parse_args()
 
    tf = CheckTFTemperature(args.host, args.port)
    tf.connect()
    exit_code = tf.read(args.uid, args.warning, args.critical, args.modus, args.warning2, args.critical2)
    tf.disconnect()
    sys.exit(exit_code)
