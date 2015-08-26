err-shellexec
============

A plugin for [ErrBot](http://errbot.net/) that allows you to create a directory of shell
scripts that will each represent a single bot command.  The plugin will dynamically create
an additional pluging which it manages.  The dynaic plugin will have methods on it that
each represent one of the shell scripts in the directory specified in the config.

Config options
==============

* SCRIPT_PATH: The path on the file system where the scripts reside 
* SCRIP_LOGS: The path on the file system where logs of each script run should reside.


Example
=======
If you configure your bot with a SCRIPT_PATH of '/usr/local/scripts/' and a SCRIPT_LOGS of
'/var/logs/bog/', and the path '/usr/local/scripts' contains 4 files:

 - deploy_fun.sh
 - deploy_now.sh
 - restart__system.sh
 - cry.sh

Then the dynamic plugin ShellCmd will have 4 methods:

 - deploy_fun:        !deploy fun
 - deploy_now:        !deploy now
 - restart_systems    !restart systems
 - cry:               !cry

The bot will tell you when the command finishes executing.

TODO
=====

Create a way for the executed scripts to communicate specific info back to the bot for
relay to the chat channel in real time.
