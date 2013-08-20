#!/bin/sh
# connects to localhost:4223 by default, use --host and --port to change it

# change to your UID
UID=SCT31
HOST=ServerMonitoring
CRITICAL_MINIMUM=27
WARNING_MINIMUM=26

temp=$(/usr/local/bin/tinkerforge --host $HOST call temperature-bricklet $UID get-temperature --execute "echo '{temperature} / 100' | bc | xargs printf '%.0f\n'")
echo "Temperature is" $temp
if [ $temp -ge $CRITICAL_MINIMUM ]; then 
	echo "CRITICAL"
	exit 2
elif [ $temp -ge $WARNING_MINIMUM ]; then
	echo "WARNING"
	exit 1
else
	echo "OK"
	exit 0
fi


