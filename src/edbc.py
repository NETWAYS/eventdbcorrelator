#!/usr/bin/python

from config import *;

import logging
import controller
import socket
import sys
import os

class Edbc(object):
    def __daemonize(self):    
        pid = os.fork()
        if not pid > 0:
            cpid = os.fork()
            if cpid > 0:
                sys.exit(0)
        else:
            sys.exit(0)

    def __setupLogging(self):
        if self.config["log"]:
            logging.basicConfig(level=logging.INFO, filename=self.config["log"])
        else:
            logging.basicConfig(level=logging.INFO)
    def __init__(self):
        if not socket.has_ipv6:
            print >> sys.stderr, 'WARNING: Your python version does not have IPv6 support enabled!'
            
        self.config = DaemonConfiguration()
        self.__setupLogging()        
        if self.config["foreground"] == False:
            self.__daemonize()
        
        self.instances = InstanceFactory(self.config)
        controller.Controller(self.config, self.instances) 

   
    
            
if __name__ == "__main__":
    Edbc();
