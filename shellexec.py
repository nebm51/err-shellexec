# This is a Shell for Err plugins, use this to get started quickly.

from errbot import BotPlugin, botcmd
from os import listdir
from os.path import isfile, join
from itertools import chain
import logging
import subprocess
import time
import datetime

# Logger for the shell_exec command
log = logging.getLogger("shell_exec")
CONFIG_TEMPLATE = { 'SCRIPT_PATH': './plugins/err-shellexec/handlers/',
		    		'SCRIPT_LOGS': './plugins/err-shellexec/handlers/logs',
		    		'NOTIFY_STRING': 'NOTIFY-', }

class ShellExec(BotPlugin):
	"""
	Class that dynamically creates bot actions based on a set of shell scripts
	in the form of command_action.sh
	ex. deploy_emp.yml
	"""
	min_err_version = '3.0.0' # Optional, but recommended

	def __init__(self):
		"""
		Constructor
		"""
		super(ShellExec, self).__init__()
		self.dynamic_plugin = None

	def activate(self):
		"""
		Activate this plugin,
		"""
		super(ShellExec, self).activate()
		if self.config is not None:
			self._load_shell_commands()

	def deactivate(self):
		"""
		Deactivate this plugin
		"""
		super(ShellExec, self).deactivate()
		self._bot.remove_commands_from(self.dynamic_plugin)

	def get_configuration_template(self):
		"""
		Defines the configuration structure this plugin supports
		"""
		return CONFIG_TEMPLATE

	def configure(self, configuration):
		"""
		Handle partial configuration changes.
		"""
		if configuration is not None and configuration != {}:
			config = dict(chain(CONFIG_TEMPLATE.items(), configuration.items()))
		else:
			config = CONFIG_TEMPLATE
		super(ShellExec, self).configure(config)

	def check_configuration(self, configuration):
		"""
		This should actually validate the configuration but does not yet.
		"""
		pass

	@property
	def script_path(self):
		return self.config['SCRIPT_PATH']

	@property
	def script_logs(self):
		return self.config['SCRIPT_LOGS']

	@property
	def notify_string(self):
		return self.config['NOTIFY_STRING']

	@botcmd
	def cmdunload(self, msg, args):
		"""
		Remove the dynamically added shell commands and the ShellCmd object.
		"""
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
		"""
		Load the list of shell scripts from the SCRIPT_PATH, then call create_method
		on each script to add a dynamically created method for that shell script.
		Once done, generate an object out of a dictionary of the dynamically created
		methods and add that to the bot.
		"""

		load_path = self.script_path
		# Read the files
		files = [ f for f in listdir( load_path ) if isfile( join( load_path, f ) ) and f.endswith('.sh') ]
		commands = {}

		# Create a method on the commands object for each script.
		for file in files:
			file, _ = file.split(".")
			commands[file] = self._create_method(file)

		plugin_class = type("ShellCmd", (BotPlugin,), commands)
		plugin_class.__errdoc__ = 'The ShellCmd plugin is created and managed by the ShellExec plugin.'
		plugin_class.command_path = self.script_path
		plugin_class.command_logs_path = self.script_logs

		self.dynamic_plugin = plugin_class(self._bot)
		self.log.debug("Registering Dynamic Plugin: %s" % (self.dynamic_plugin))
		self._bot.inject_commands_from(self.dynamic_plugin)

	def _get_command_help(self, command_name):
		"""
		Run the script with the --help option and capture the output to be used
		as its help text in chat.
		"""
		os_cmd = join( self.script_path, command_name + ".sh" )
		log.debug("Getting help info for '{}'".format(os_cmd))
		return subprocess.check_output([ os_cmd , "--help" ]).decode('utf-8')

	def _create_method(self, command_name):
		"""
		Create a botcmd decorated method for our dynamic shell object
		"""
		self.log.debug("Adding command '{}'".format( command_name ))

		def new_method(self, msg, args, command_name=command_name, notify_string = self.notify_string):
			# Get who ran the command
			user = msg.frm.node
			# Generate a timestamp string
			tstamp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d-%H:%M:%S')
			# The full command to run
			os_cmd = join( self.command_path, command_name + ".sh" )
			# The name of the log file for output of this command
			log_file_name = join(self.command_logs_path, "{}-{}-{}.log".format(command_name, tstamp, user) )
			cmd_args = [os_cmd]
			if len(args):
				cmd_args = cmd_args + args
			try:
				log.debug( "Running command [{}]".format( os_cmd ) )

				process = subprocess.Popen( cmd_args, stdout=subprocess.PIPE )
				log_file = open(log_file_name, "wb", 0)
				while True:
					output = process.stdout.readline()
					if output == '' and process.poll() is not None:
						break
					if output:
						# Write the raw output to the log file unbuffered
						log_file.write( output )
						# Convert bytes to string
						output = output.decode('utf-8')
						# Check to see if anything matches the NOTIFY_STRING
						if output.find(notify_string) >= 0:
							# Remove the NOTIFY_STRING part
							yield output.strip().replace(notify_string, '')
				rc = process.poll()
				log_file.flush()
				log_file.close()
				yield "{} finished with exit code {}".format( command_name, rc )
			except subprocess.CalledProcessError:
				yield "{} failed".format( command_name )


		self.log.debug("Updating metadata on command {} type {}".format(command_name, type(command_name)))
		new_method.__name__ = command_name
		new_method.__doc__ = self._get_command_help(command_name)

		# Decorate the method
		return botcmd(new_method)