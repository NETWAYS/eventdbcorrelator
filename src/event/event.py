# To change this template, choose Tools | Templates
# and open the template in the editor.

__author__="moja"
__date__ ="$Sep 24, 2012 6:41:33 PM$"
import time
import logging
from ip_address import IPAddress

class Event(object):

    def __init__(self, message = "", date=time.ctime(),additional = dict(),record=None):
        self.data = dict();
        self.correlationGroup = None
        self.eventTag = None
        if record != None:
            self.from_record(record)
            return
        
        self.message = message
        self.date = date
        
        for val in additional: 
            self.data[val.lower()] = additional[val];
    
    def __setitem__(self,name,value):#
        name = name.lower()
        if name == "message":
            self.message = value
            return
        if name == "date":
            self.date = value
            return
        if name == "correlationGroup":
            self.correlationGroup = value
            return
        if name == "eventTag":
            self.eventTag = value
            return
        
        self.data[name] = value
        return None
    
    def __getitem__(self,name):
        name = name.lower()
        if name == "message":
            return self.message
        if name == "date":
            return self.date
        if name == "correlationGroup":
            return self.correlationGroup
        if name == "eventTag":
            return self.eventTag
        if name in self.data:
            return self.data[name]
        return None
    
    def __eq__(self,event):
        
        if event.message != self.message:
            return False
        if event.date != self.date:
            return False
        for i in self.data:
            if self.data[i] != event[i]:
                return False
        return True
            
    
    def from_record(self,record):
        keys = record["keys"]
        data = record["data"]
        for i in range(0,len(keys)):
            self[keys[i]] = data[i]
            
            if keys[i] == 'host_address':
                self["host_address"] = IPAddress(self["host_address"],binary=True)
        
        