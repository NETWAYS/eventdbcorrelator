#!/usr/bin/python


__author__="moja"
__date__ ="$Sep 24, 2012 5:45:19 PM$"

from config import *;

import logging
import controller

class Edbc(object):
    def __daemonize(self):    
        pass;
    
    def __setupLogging(self):
        logging.basicConfig(level=logging.DEBUG)

    def __init__(self):
        self.config = DaemonConfiguration()
        if self.config["foreground"]:
            self.__daemonize()
            
        self.__setupLogging()        
        self.instances = InstanceFactory(self.config)
        controller.Controller(self.config, self.instances) 

   
    
            
if __name__ == "__main__":
    Edbc();
    