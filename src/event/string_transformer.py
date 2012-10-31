# Helper class to transform strings, arrays, etc to EVent objects
import re
import logging
import os
import time
from event import *

class StringTransformer(object):
    def setup(self,id,config):
        self.id = id
        self.format = re.compile(config["format"])
        if "defaultMessage" in config:
            self.defaultMessage = config["defaultMessage"]
        else:
            self.defaultMessage = "No message given"
        self.fixed = {}
        
        if "fixed" in config:
            fixed = config["fixed"].split(",")
            for keyval in fixed:
                keyval = keyval.split("=")
                self.fixed[keyval[0].lower()] = keyval[1]
        self.dateFormat = "%b %d %H:%M:%S"
    
    def set_current_year(self,st):
        now = time.localtime()
        return (now[0],st[1],st[2],st[3],st[4],st[5],st[6],st[7],st[8])
    
    def transform(self,string):
        try:
            matches =  self.format.match(string)
            if matches == None:
                return None

            matchdict = matches.groupdict()
            for i in self.fixed:
                matchdict[i] = self.fixed[i]
            if not "DATE" in matchdict:
                matchdict["DATE"] = time.ctime()
            else:
                matchdict["DATE"] = time.strptime(matchdict["DATE"],self.dateFormat)
                if matchdict["DATE"][0] < 2000:
                    matchdict["DATE"] = self.set_current_year(matchdict["DATE"])
                matchdict["DATE"] = time.mktime(matchdict["DATE"])

            if not "MESSAGE" in matchdict:
                matchdict["MESSAGE"] = self.defaultMessage
            
            event = Event(matchdict["MESSAGE"],matchdict["DATE"],matchdict)
            return event
        except Exception, e:
            logging.warn(e)
        
    
    