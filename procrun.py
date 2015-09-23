# -*- coding: utf-8 -*-
"""
Object to treat a command execution as a generator
"""

from datetime import datetime
import os
import sys
import shlex
import subprocess
import time

ENCODING = 'UTF-8'


class ProcRun(object):
    """
    Wrapper around subprocess.Popen to treat execution as a generator or text.
    """

    def __init__(self, cmd, cwd, log_path):
        """ Initialize a """
        self.cmd = cmd
        self.cwd = cwd
        self.log_path = log_path
        self.process = None
        self.out = None
        self.err = None
        self.returncode = None
        self.exc = None
        self.time_format = '%Y-%m-%d-%H:%M:%S'
        self.stdout_lines = []
        self.stderr_lines = []

    def open_log(self, user):
        """Open the command log file """
        tstamp = datetime.fromtimestamp(time.time()).strftime(self.time_format)
        log_file_name = os.path.join(self.log_path, "{}-{}-{}.log".format(
            os.path.basename(self.cmd), tstamp, user))
        print(log_file_name)
        return open(log_file_name, "wb", 0)

    def expand_args(self, args):
        """Return [] if args is None, the array of args or an array of arguments split from a string. """
        if args is not None:
            if len(args):
                if isinstance(args, str):
                    return shlex.split(args)
                if isinstance(args, list):
                    return args
        return []

    def start_log(self, user, cmd_args):
        """Open the command log"""
        self._exec_log = self.open_log(user)
        self._exec_log.write("Starting Command [{}] as [{}]\n".format(" ".join(
            cmd_args), user).encode(ENCODING))

    def end_log(self):
        """Close the command log"""
        self._exec_log.flush()
        self._exec_log.close()

    def write_log(self, data):
        """Write a row of data to the command log"""
        self._exec_log.write(data.encode(ENCODING))
        return data

    def run_async(self, user, args=None, data=None, env={}, save=True):
        """ Run a the command asynchronously """
        # Get the environment, or set the environment
        environ = dict(os.environ).update(env or {})

        # Create the array of arguments for the subprocess call
        cmd_args = [os.path.join(self.cwd, self.cmd)] + self.expand_args(args)

        # Open the log file
        self.start_log(user, cmd_args)

        self.process = subprocess.Popen(self.cmd,
                                        universal_newlines=True,
                                        shell=False,
                                        env=environ,
                                        stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE,
                                        bufsize=0, )

        while True:
            output = self.process.stdout.readline()
            if output == '' and self.process.poll() is not None:
                # Process is done
                break
            if output:
                yield self.write_log(output)
        # Capture the return code
        self.rc = self.process.poll()
        # Done with the log
        self.end_log()

    def run(self, user, args=None, data=None, env={}, save=True):
        """ Run a command, giving arguments, and potentially STDIN """
        cmd_res = []
        for line in self.run_async(user, args=args, data=data, env=env):
            cmd_res.append(line)
        if save:
            self.stdout_lines = cmd_res
        return cmd_res
