from receptors import *
from persisters import *
from processors import *
from datasource import *
import logging 

'''
Factory and Registry class that can register object instances and 
matches instance references (@id in config files)

@author Jannis Mosshammer <jannis.mosshammer@netways.de>
'''
class InstanceFactory(object):

    """
    Initialize with the base edbc.cfg file as a starting point.
    The section global will be ignored here.
    """
    def __init__(self,config):
        self.config = config
        self.deferred = {}
        instanceDefs = self.config.get_instance_definitions()
        self.instances = { "all": {} }
        for id in instanceDefs:
            if id == "global":
                continue
            cfgObject = instanceDefs[id]
            self.register(id,cfgObject)
            
        logging.debug("Registered %i instances" % len (self.instances["all"]))


    def defer_registration(self,required,args):
        if not required in self.deferred:
            self.deferred[required] = []
        self.deferred[required].append(args)
        
    """
    Registers an object cfgObject with the identifier id. 
    the cfgObject is expected to have a class attribute, which will be registered and 
    used for instance creation.
    
    If factoryFn is given, this will be called (class is 
    only being registered here and not used for instance creation), otherwise 
    %class%.setup(id,cfgObject) is called.
    
    """
    def register(self,id,cfgObject,factoryFn = None):
        # type myType and class myClass will be called MyTypeMyClass()
        required = self.resolve_references(cfgObject)
        if required != None:
            self.defer_registration(required,(id,cfgObject,factoryFn))
            return False
        
        r = None
        if not cfgObject["class"] in self.instances:
            self.register_class(cfgObject["class"])
        
        if factoryFn == None:
            # Default factory using the setup method
            instanceCls = cfgObject["class"].capitalize()
            configname = cfgObject["type"].capitalize()+instanceCls
            r = globals()[configname]()
            
            r.setup(id,cfgObject)
        else:
            # Pass instance creation to factory function
            r = factoryFn(id,cfgObject)

        self.instances[cfgObject["class"]][id] = r    
        self.instances["all"][id] = r 
        self.handle_unresolved(id)
        return True
        
    def handle_unresolved(self,id):
            
        if "@"+id in self.deferred:

            unmatched = []
            while self.deferred["@"+id]:
                item = self.deferred["@"+id].pop()
                if not self.register(item[0],item[1],item[2]):
                    unmatched.append(item)
            if unmatched:
                self.deferred["@"+id] = unmatched
            else:
                del self.deferred["@"+id]
            
    def has_unmatched_dependencies(self):
        logging.debug(self.deferred)
        return len(self.deferred) > 0

    def resolve_references(self,cfgobject):
        for i in cfgobject:
            if cfgobject[i].startswith('@'):
                resolved = self.__getitem__(cfgobject[i])
                if not resolved:
                    return cfgobject[i]
                cfgobject[i] = resolved

    def register_class(self,classname):
        classname = classname.strip()
        self.instances[classname] = {}
        
        # register class methods so they are available with get%CLASS%(id)
        getter = lambda id: self.instances[classname][(id,id[1:])[id[0] == '@']]
        getter.__name__ = "get"+classname.capitalize()
        setattr(self,getter.__name__,getter)
        
        # register getAll%Class%Instances method
        getter = lambda : self.instances[classname]
        logging.debug("Registering %s " % ("getAll"+classname.capitalize()+"Instances"))
        getter.__name__ = "getAll"+classname.capitalize()+"Instances"
        setattr(self,getter.__name__,getter)
        
    """
        Returns the object instance that can be found under the id "id"
    """
    def __getitem__(self,id):
        if id[0] == '@':
            id = id[1:]
        if id in self.instances:
            return self.instances[id]
        if id in self.instances["all"]:
            return self.instances["all"][id]
        return None
        
    
    
