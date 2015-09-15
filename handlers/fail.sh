#!/bin/sh

if [ "$1" == '--help' ]; then
	echo "Fail hard"
	exit 0
fi

echo "This is a failed command"
exit 1
