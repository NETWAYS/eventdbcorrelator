# To change this template, choose Tools | Templates
# and open the template in the editor.
from receptors import *
from persisters import *
from processors import *
#from config import Chain
from datasource import *
import logging 

class InstanceFactory(object):
    def __init__(self,config):
        self.config = config
        
        instanceDefs = self.config.get_instance_definitions()
        self.instances = { "all": {} }
        for id in instanceDefs:
            if id == "global":
                continue
            cfgObject = instanceDefs[id]
            self.register(id,cfgObject)
            
        logging.debug("Registered %i instances" % len (self.instances["all"]))

    def register(self,id,cfgObject,factoryFn = None):
        logging.debug(cfgObject)
        # type myType and class myClass will be called MyTypeMyClass()
        
        r = None
        if factoryFn == None:
            # Default factory using the setup method
            instanceCls = cfgObject["class"].capitalize()
            configname = cfgObject["type"].capitalize()+instanceCls
            r = globals()[configname]()
            r.setup(id,cfgObject)
        else:
            # Pass instance creation to factory function
            r = factoryFn(id,cfgObject)

        if not cfgObject["class"] in self.instances:
            self.register_class(cfgObject["class"])

        self.instances[cfgObject["class"]][id] = r    
        self.instances["all"][id] = r        
        
    def register_class(self,classname):
        self.instances[classname] = {}
        # register class methods so they are available with get%CLASS%(id)
        getter = lambda id: self.instances[classname][(id,id[1:])[id[0] == '@']]
        getter.__name__ = "get"+classname.capitalize()
        setattr(self,getter.__name__,getter)
        
    def __getitem__(self,id):
        if id[0] == '@':
            id = id[1:]
        if id in self.instances:
            return self.instances[id]
        if id in self.instances["all"]:
            return self.instances["all"][id]
        return None
        
    
    