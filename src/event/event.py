# To change this template, choose Tools | Templates
# and open the template in the editor.

__author__="moja"
__date__ ="$Sep 24, 2012 6:41:33 PM$"
import time
import logging
class Event(object):

    def __init__(self,date=time.ctime(), message = "", additional = dict()):
        self.message = message
        self.date = date
        
        self.data = dict();

        self.correlationGroup = None
        self.eventTag = None

        for val in additional: 
            self.data[val.lower()] = additional[val];
    
    def __getitem__(self,name):
        name = name.lower()
        if name == "message":
            return self.message
        if name == "date":
            return self.date
        if name == "source":
            return self.source
        if name == "correlationGroup":
            return self.correlationGroup
        if name == "eventTag":
            return self.eventTag
        if name in self.data:
            return self.data[name]
        return None
        
        