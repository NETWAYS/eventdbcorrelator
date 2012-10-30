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
        self["host_address"] = IPAddress("127.0.0.1")
        self["host_name"] = "unknown"
        if record != None:
            self.from_record(record)
            return
        
        self.message = message
        self.alternative_message = message
        self.data["created"] = date
        self.active = True
        self.group_id = None
        self.group_leader = None
        for val in additional: 
            self.data[val.lower()] = additional[val];
    
    def __setitem__(self,name,value):#
        name = name.lower()
        if name == "message":
            self.message = value
            return
        if name == "alternative_message":
            self.alternative_message = value
            return
        if name == "date":
            self.date = value
            return
        if name == "group_id":
            self.group_id = value
            return
        if name == "group_leader":
            self.group_leader = value
            return
        if name == "active":
            self.active = value
            return 
        
        self.data[name] = value
        return None
    
    def __getitem__(self,name):
        name = name.lower()
        if name == "message":
            return self.message
        if name == "alternative_message":
            return self.alternative_message
            return
        if name == "date":
            return self.date
        if name == "group_id":
            return self.group_id
        if name == "group_leader":
            return self.group_leader
        if name == "active":
            return self.active
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

    
    def in_active_group(self):
        return self.group_leader != None
    
    def from_record(self,record):
        
        keys = record["keys"]
        data = record["data"]
        for i in range(0,len(keys)):
            self[keys[i]] = data[i]
            
            if keys[i] == 'host_address':
                self["host_address"] = IPAddress(self["host_address"],binary=True)
    
    def free(self):
        del self.data
        del self