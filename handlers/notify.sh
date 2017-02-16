#!/bin/bash

if [ "$1" == '--help' ]; then
	echo "notify shit!"
	exit 0
fi

echo "This is a successful command"
echo "NOTIFY: this command will send stuff back to the bot"
echo "but not everything."
echo "only some commands will go back to the bot"
exit 0
