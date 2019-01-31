#!/bin/sh

# Connects to localhost:4223 by default, use --host and --port to change it

# The following parameters according to your setup.
UID=GSb
HOST=localhost
CRITICAL_MINIMUM=27
WARNING_MINIMUM=26
# Change temperature Bricklet name according to the version of the Bricklet used.
#TEMPERATURE_BRICKLET=temperature-bricklet # Bricklet version 1.0.
TEMPERATURE_BRICKLET=temperature-v2-bricklet # Bricklet Version 2.0.

temp=\
	$(/usr/local/bin/tinkerforge \
		--host $HOST \
		call $TEMPERATURE_BRICKLET $UID \
		get-temperature \
		--execute "echo '{temperature} / 100' | bc | xargs printf '%.0f\n'")

if [ -n "$temp" ];
then

	echo "Temperature is" $temp

	if [ $temp -ge $CRITICAL_MINIMUM ];
	then

		echo "CRITICAL"

		exit 2
	elif [ $temp -ge $WARNING_MINIMUM ];
	then

		echo "WARNING"

		exit 1
	else
		echo "OK"

		exit 0
	fi
else
	echo "Failed to get temperature."
fi
