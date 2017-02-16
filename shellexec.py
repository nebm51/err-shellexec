# This is a Shell for Err plugins, use this to get started quickly.

from errbot import BotPlugin, botcmd
from os import listdir
from os.path import isfile, join
from itertools import chain
import logging
import subprocess
import time
import datetime
import shlex

import procrun

# Logger for the shell_exec command
log = logging.getLogger("shell_exec")
CONFIG_TEMPLATE = {
'SCRIPT_PATH': './plugins/err-shellexec/handlers/',
'SCRIPT_LOGS': './plugins/err-shellexec/handlers/logs',
'NOTIFY_STRING': 'NOTIFY',
}


def status_to_string(exit_code):
    if exit_code == 0:
        return "successfully"
    return "unsuccessfully"

class ShellExec(BotPlugin):
    """
    Class that dynamically creates bot actions based on a set of shell scripts
    in the form of command_action.sh
    ex. deploy_emp.yml
    """
    min_err_version = '4.0.0'  # Optional, but recommended

    def __init__(self, bot):
        """
        Constructor
        """
        super().__init__(bot)
        self.dynamic_plugin = None

    def activate(self):
        """
        Activate this plugin,
        """
        super().activate()
        if self.config is not None:
            self._load_shell_commands()

    def deactivate(self):
        """
        Deactivate this plugin
        """
        super().deactivate()
        self._bot.remove_commands_from(self.dynamic_plugin)

    def get_configuration_template(self):
        """
        Defines the configuration structure this plugin supports
        """
        return CONFIG_TEMPLATE
#        return {'SCRIPT_PATH': './plugins/err-shellexec/handlers/','SCRIPT_LOGS': './plugins/err-shellexec/handlers/logs','NOTIFY_STRING': 'NOTIFY'}

    @botcmd
    def cmdunload(self, msg, args):
        """
        Remove the dynamically added shell commands and the ShellCmd object.
        """
        self.log.debug("Unloading ShellExec Scripts")
        if self.dynamic_plugin is not None:
            self._bot.remove_commands_from(self.dynamic_plugin)
        return ("Done unloading commands.")

    @botcmd
    def printconfig(self, msg, args):
        return ("Config is: " + str(self.config) )

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
        script_path = self.config['SCRIPT_PATH']
        self.log.info("Loading scripts from {}".format(script_path))
        # Read the files
        files = [f for f in listdir(script_path) if isfile(join(script_path, f)) and f.endswith('.sh')]
        commands = {}

        # Create a method on the commands object for each script.
        for file in files:
            self.log.debug("Processing file [%s" % (file))
            file, _ = file.split(".")
            commands[file] = self._create_method(file)

        plugin_class = type("ShellCmd", (BotPlugin, ), commands)
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
        os_cmd = join(self.config['SCRIPT_PATH'], command_name + ".sh")
        log.debug("Getting help info for '{}'".format(os_cmd))
        return subprocess.check_output([os_cmd, "--help"]).decode('utf-8')

    def _create_method(self, command_name):
        """
        Create a botcmd decorated method for our dynamic shell object
        """
        self.log.debug("Adding shell command '{}'".format(command_name))

        def new_method(self, msg, args, command_name=command_name, notify_string=self.config['NOTIFY_STRING']):
            # Get who ran the command
            user = msg.frm
            # The full command to run
            os_cmd = join(self.command_path, command_name + ".sh")
            proc = procrun.ProcRun(os_cmd, self.command_path, self.command_logs_path)
            for line in proc.run_async(user, args=args):
                # Check to see if anything matches the NOTIFY_STRING
                if line.find(notify_string) >= 0:
                    # Remove the NOTIFY_STRING part
                    self.log.debug("Sending Notification")
                    yield line.strip().replace(notify_string, '')
                else:
                    self.log.debug(line.strip())
            yield "[{}] completed {}".format(command_name, status_to_string(proc.rc))

        self.log.debug("Updating metadata on command {} type {}".format(command_name, type(command_name)))
        new_method.__name__ = command_name
        new_method.__doc__ = self._get_command_help(command_name)

        # Decorate the method
        return botcmd(new_method)
