# This is a Shell for Err plugins, use this to get started quickly.

from errbot import BotPlugin, botcmd
from types import MethodType
from os import listdir
from os.path import isfile, join
import logging

# Logger for the shell_exec command
log = logging.getLogger("shell_exec")

def shell_exec(user, command, command_path):
	"""
	Run a shell script of the format command_action.
	"""
	log.debug( "Running command [" + command + "]" )
	pass

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
		self._load_shell_commands()

	def deactivate(self):
		super(ShellExec, self).deactivate()
		self._bot.remove_commands_from(self.dynamic_plugin)

	@botcmd
	def unloadcommands(self, msg, args):
		self.log.debug("Unloading ShellExec Scripts")
		self._bot.remove_commands_from(self.dynamic_plugin)
		return("Done unloading commands.")

	@botcmd
	def rehash(self, msg, args):
		"""
		Remove the previous set of methods and add new ones based on the
		current set of scripts.
		"""
		self.log.debug("Reloading ShellExec Scripts")
		self._load_shell_commands()
		return("Done loading commands.")


	def _load_shell_commands(self):
		load_path = self.config['SCRIPT_PATH']
		# Read the files
		files = [ f for f in listdir( load_path ) if isfile( join( load_path, f ) ) and f.endswith('.sh') ]
		commands = {}
		for file in files:
			file, _ = file.split(".")
			commands[file] = self._create_method(file)

		plugin_class = type("ShellCmd", (BotPlugin,), commands)
		plugin_class.__errdoc__ = 'The ShellCmd plugin is created and managed by the ShellExec plugin.'

		self.dynamic_plugin = plugin_class(self._bot)
		self.log.debug("Registering Dynamic Plugin: %s" % (self.dynamic_plugin))
		self._bot.inject_commands_from(self.dynamic_plugin)

	def _get_command_help(self, command_name):
		return "Temporary Documentation for command: %s" % (command_name)

	def _create_method(self, command_name):
		"""
		Create a botcmd decorated method for our dynamic shell object
		"""
		self.log.debug("Adding command '{}'".format( command_name ))

		def new_method(self, msg, args, command_name=command_name):
			self.log.debug("Running command '{}'.sh".format(command_name))
			shell_exec( command_name + ".sh" )

		new_method.__name__ = command_name
		new_method.__doc__ = self._get_command_help(command_name)

		# Decorate the method
		return botcmd(new_method)

	def get_configuration_template(self):
		"""Defines the configuration structure this plugin supports"""
		return { 	'SCRIPT_PATH': u'/tmp/scripts' }