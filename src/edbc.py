#!/usr/bin/python
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
from resource import RLIMIT_NOFILE

from config import DaemonConfiguration,InstanceFactory;

import logging
import controller
import socket
import sys
import resource
import os

class Edbc(object):
    """ CLI entry point. Parses CLI params via the DaemonConfiguration class. Further object initialization and
        control is done by the controller.Controller

    """


    def __init__(self):

        if not socket.has_ipv6:
            print >> sys.stderr, 'WARNING: Your python version does not have IPv6 support enabled!'

        self.config = DaemonConfiguration()
        if self.config["foreground"] == False:
            self.__daemonize()
        self.__setup_logging()

        self.instances = InstanceFactory(self.config)
        controller.Controller(self.config, self.instances)

    def __daemonize(self):
        """ Makes this process a child process of init

        """

        pid = os.fork()
        if not pid > 0:
            cpid = os.fork()

            if cpid > 0:
                sys.exit(0)

            os.setsid();
            (nr_of_fds,ignore) = resource.getrlimit(RLIMIT_NOFILE)

            for i in range(0,nr_of_fds):
                try:
                    os.close(i)
                except OSError:
                    pass
        else:
            sys.exit(0)

    def __setup_logging(self):
        """ When 'log' is not set, logging is done to a logfile, otherwise to stdout
        """

        loglevel = logging.INFO
        if self.config["verbose"]:
            loglevel = logging.DEBUG

        if self.config["log"]:
            logging.basicConfig(level=loglevel, filename=self.config["log"])
        else:
            logging.basicConfig(level=loglevel)

            
if __name__ == "__main__":
    Edbc()
