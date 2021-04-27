#!/bin/bash
export LANG=C
ps -ef | grep -v "grep\|$$" | grep "$1" >/dev/null
if [ $? -ne 0 ]
then
	$1 &
	exit 0
else
	echo "Another process running. Quit."
	exit 1
fi
