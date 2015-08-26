# This is a Shell for Err plugins, use this to get started quickly.

from errbot import BotPlugin, botcmd
from os import listdir
from os.path import isfile, join
import logging
import subprocess
import time
import datetime
import unicodedata

# Logger for the shell_exec command
log = logging.getLogger("shell_exec")

class ShellExec(BotPlugin):
	"""
	Class that dynamically creates bot actions based on a set of shell scripts
	in the form of command_action.sh
	ex. deploy_emp.yml
	"""
	min_err_version = '2.0.0' # Optional, but recommended

	def __init__(self):
		super(ShellExec, self).__init__()
		self.dynamic_plugin = None

	def activate(self):
		super(ShellExec, self).activate()
		if self.config is not None:
			self._load_shell_commands()

	def deactivate(self):
		super(ShellExec, self).deactivate()
		self._bot.remove_commands_from(self.dynamic_plugin)

	@botcmd
	def unloadcommands(self, msg, args):
		self.log.debug("Unloading ShellExec Scripts")
		if self.dynamic_plugin is not None:
			self._bot.remove_commands_from(self.dynamic_plugin)
		return("Done unloading commands.")

	@botcmd
	def rehash(self, msg, args):
		"""
		Remove the previous set of methods and add new ones based on the
		current set of scripts.
		"""
		self.log.debug("Reloading ShellExec Scripts")
		if self.config is not None:
			yield "Checking for available commands."
			self._bot.remove_commands_from(self.dynamic_plugin)
			self.dynamic_plugin = None
			self._load_shell_commands()
			yield "Done loading commands."
		else:
			yield "Wouldn't you like to configure the ShellExec command instead."


	def _load_shell_commands(self):
		load_path = self.config['SCRIPT_PATH']
		# Read the files
		files = [ f for f in listdir( load_path ) if isfile( join( load_path, f ) ) and f.endswith('.sh') ]
		commands = {}
		for file in files:
			file, _ = file.split(".")
			file = unicodedata.normalize('NFKD', file).encode('ascii','ignore')
			commands[file] = self._create_method(file)

		plugin_class = type("ShellCmd", (BotPlugin,), commands)
		plugin_class.__errdoc__ = 'The ShellCmd plugin is created and managed by the ShellExec plugin.'
		plugin_class.command_path = self.config['SCRIPT_PATH']
		plugin_class.command_logs_path = self.config['SCRIPT_LOGS']

		self.dynamic_plugin = plugin_class(self._bot)
		self.log.debug("Registering Dynamic Plugin: %s" % (self.dynamic_plugin))
		self._bot.inject_commands_from(self.dynamic_plugin)

	def _get_command_help(self, command_name):
		"""
		Run the script with the --help option and capture the output to be used
		as its help text in chat.
		"""
		os_cmd = join( self.config['SCRIPT_PATH'], command_name + ".sh" )
		log.debug("Getting help info for '{}'".format(os_cmd))
		return subprocess.check_output([ os_cmd , "--help" ])

	def _create_method(self, command_name):
		"""
		Create a botcmd decorated method for our dynamic shell object
		"""
		self.log.debug("Adding command '{}'".format( command_name ))

		def new_method(self, msg, args, command_name=command_name):
			# Generate a timestamp string
			tstamp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d-%H:%M:%S')
			# The full command to run
			os_cmd = join( self.command_path, command_name + ".sh" )
			# The name of the log file for output of this command
			log_file_name = join(self.command_logs_path, "{}-{}.log".format(command_name, tstamp) )
			log.debug( "Running command [{}]".format( os_cmd) )
			cmd_args = [os_cmd]
			if len(args):
				cmd_args = cmd_args + args
			command_output = subprocess.check_output(cmd_args)
			yield "{} finished".format(command_name)

			# Log the output of the command
			log_file = open(log_file_name, "w")
			log_file.write(command_output)
			log_file.close()

		self.log.debug("Updating metadata on command {} type {}".format(command_name, type(command_name)))
		new_method.__name__ = command_name
		new_method.__doc__ = self._get_command_help(command_name)

		# Decorate the method
		return botcmd(new_method)

	def get_configuration_template(self):
		"""Defines the configuration structure this plugin supports"""
		return { 	'SCRIPT_PATH': u'/tmp/scripts',
		            'SCRIPT_LOGS': u'/tmp/script_logs', }