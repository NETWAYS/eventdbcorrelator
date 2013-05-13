"""
EDBC - Message correlation and aggregation engine for passive monitoring events
Copyright (C) 2012  NETWAYS GmbH

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

"""
import threading
import time
import os
import logging
import re
import subprocess
from event import Matcher, TrueMatcher

class CommandProcessor(object):
    """ Processor that is able to submit icinga commands to a defined command pipe
        Thanks to David Mikulski for the send over ssh code
    """


    def __init__(self):
        self.lock = threading.Lock()

    def setup(self, id, config):
        """ Sets up the initial state

        """
        self.id = id

        if not "format" in config:
            logging.warn("No format given for CommandProcessor %s, ignoring.",id)
            self.format = None
        else:
            self.format = config["format"]

        if not "pipe" in config :
            logging.warn("No pipe given for CommandProcessor %s, ignoring", id)
            self.pipe = None
        else:
            self.pipe = config["pipe"].split(";")

        if "matcher" in config:
            self.matcher = Matcher(config["matcher"])
        else:
            self.matcher = TrueMatcher()

        if "uppercasetokens" in config:
            self.uppercase_tokens = True
        else:
            self.uppercase_tokens = False

        if "use_ssh" in config:
            self.use_ssh = True
            if not "ssh_bin" in config:
                self.ssh_binary = "ssh"
            else:
                self.ssh_binary = config["ssh_bin"]

            if not "remote_address" in config:
                logging.error("remote_address directive is missing in command processor %s, this should include the ip of the remote host", id)
            else:
                self.remote_address = config["remote_address"]
                if not "remote_user" in config:
                    self.remote_user = os.getlogin()
                    logging.warn("remote_user directive not set, using %s as default", self.remote_user)
                else:
                    self.remote_user = config["remote_user"]

            if not "remote_port" in config:
                self.remote_port = "22"
            else:
                self.remote_port = config["remote_port"]

        else:
            self.use_ssh = False


    def process(self, event):
        """ Matches the event with the defined matcher (if any), rewrites
            it if necessary and submits it in the icinga command format

        """
        if not self.format or not self.pipe:
            return "PASS"

        try:
            self.lock.acquire()
            if not self.matcher.matches(event):
                return "PASS"
            groups = self.matcher.get_match_groups()
            msg = self.create_notification_message(event, groups)
            msg = "[%i] %s" % (time.time(), msg)

            try:
                for pipe in self.pipe:
                    self.send_to_pipe(msg, pipe)
                return "OK"
            except:
                return "FAIL"

        finally:
            self.lock.release()

    def send_to_pipe(self, msg, pipe_name):
        """ opens the icinga pipe and writes the string msg to it

        """

        try:
            if self.use_ssh:
                process = subprocess.Popen([self.ssh_binary, '-p', self.remote_port, self.remote_user+'@'+self.remote_address, "echo", "-e", "\""+msg+"\"", ">>", pipe_name], shell=False)
                process.communicate(input="exit")
            else:
                pipe = os.open(pipe_name, os.O_WRONLY)
                os.write(pipe, msg)

                os.close(pipe)
        except Exception, e:
            logging.error("Could not send command %s to pipe : %s", msg,e)
            raise e


    def create_notification_message(self, event, matchgroups):
        """ Creates the message and substitues #FIELD with message fields
            and $VAR with named regular expression groups
        """
        msg = self.format
        tokens = re.findall("[#$]\w+", msg)
        for token in tokens:
            if token[0] == '#':
                token_tmp = str(event[token[1:]])
                if self.uppercase_tokens:
                    token_tmp = token_tmp.upper()
                msg = msg.replace(token, token_tmp)
                continue
            if token[0] == '$':
                token_tmp = str(matchgroups[token[1:]])
                if self.uppercase_tokens:
                    token_tmp = token_tmp.upper()
                msg = msg.replace(token, token_tmp)
                continue
        if not msg.endswith("\n"):
            msg += "\n"
        return msg
