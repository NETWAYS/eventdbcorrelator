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
from receptors import *
from processors import *
from event import *
from datasource import *
import logging 

class InstanceFactory(object):
    """
    Factory and Registry class that can register object instances and 
    matches instance references (@id in config files)

    @author Jannis Mosshammer <jannis.mosshammer@netways.de>
    """


    def __init__(self, config):
        """
        Initialize with the base edbc.cfg file as a starting point.
        The section global will be ignored here.
        """
        self.config = config
        self.deferred = {}
        instanceDefs = self.config.get_instance_definitions()
        self.instances = { "all": {} }
        for id in instanceDefs:
            if id == "global":
                continue
            cfg_object = instanceDefs[id]
            self.register(id, cfg_object)
            
        logging.debug("Registered %i instances", len (self.instances["all"]))


    def defer_registration(self, required, args):
        """ If an instance can' t be registered, because dependencies are missing
            registration will be deferred until the dependencies are met
        """
        if not required in self.deferred:
            self.deferred[required] = []

        self.deferred[required].append(args)
       
    def apply_template(self, cfg_object):    
        """ Reads the basic config of the parent instance and applies it to the given cfg_object
            
        """
        parent = self.__getitem__(cfg_object["template"])
        for i in parent.base_config:
            if not i in cfg_object:
                cfg_object[i] = parent.base_config[i]
   
    def register(self, instance_id, cfg_object, factory_fn = None):
        """
        Registers an object cfg_object with the identifier id. 
        the cfg_object is expected to have a class attribute, which will be registered and 
        used for instance creation.
        
        If factory_fn is given, this will be called (class is 
        only being registered here and not used for instance creation), otherwise 
        %class%.setup(id, cfg_object) is called.

        Instances look like
        {
            "class": "CLASSNAME",
            "type" : "typename",
            "arg1" : "argval1"
            ...
            "argN" : "argvalN"
            "ref1" : "@referencedId"
        }

        """ 
        # type myType and class myClass will be called MyTypeMyClass()
        required = self.resolve_references(cfg_object)
        if required != None:
            self.defer_registration(required,(instance_id, cfg_object, factory_fn))
            return False
        
        r = None
        
        if "template" in cfg_object:
            if not cfg_object["template"] in self.instances["all"]:
                self.defer_registration(required,(instance_id, cfg_object, factory_fn))
                return False
            else:
                self.apply_template(cfg_object)
            
        if not cfg_object["class"] in self.instances:
            self.register_class(cfg_object["class"])
        
        if factory_fn == None:
            # Default factory using the setup method
            instance_cls = cfg_object["class"].capitalize()
            configname = cfg_object["type"].capitalize()+instance_cls
            if not configname in globals():
                logging.error("Couldn't find %s, %s won't work.", configname, instance_id)
                return False
            
            r = globals()[configname]()
            
            logging.debug("Instance of %s : %s (instance_id=%i)", instance_id, r, id(r))
            r.setup(instance_id, cfg_object)
        else:
            # Pass instance creation to factory function
            r = factory_fn(instance_id, cfg_object)
        try: 
            r.base_config = cfg_object
        except:
            pass
        self.instances[cfg_object["class"]][instance_id] = r    
        self.instances["all"][instance_id] = r 
        self.handle_unresolved(instance_id)
        return True
        
    def handle_unresolved(self, id):
        """ Checks if deferred registrations can now be completed and completes them if so
        
        """          
        if "@"+id in self.deferred:

            unmatched = []
            while self.deferred["@"+id]:
                item = self.deferred["@"+id].pop()
                if not self.register(item[0], item[1], item[2]):
                    unmatched.append(item)
            if unmatched:
                self.deferred["@"+id] = unmatched
            else:
                del self.deferred["@"+id]
    
        
    def has_unmatched_dependencies(self):
        """ Returns true if there are instances waiting for dependencies to be fully registered

        """
        logging.debug(self.deferred)
        return len(self.deferred) > 0

    def resolve_references(self, cfgobject):
        """ resolves config variables beginning with @, i.e. refrences to other instances

        """
        for i in cfgobject:
            if cfgobject[i].startswith('@'):
                resolved = self.__getitem__(cfgobject[i])
                if not resolved:
                    return cfgobject[i]
                cfgobject[i] = resolved

    def register_class(self, classname):
        """ Registers the class with classname in the factories instances list and creates a
            get%Classname% method to allow convenient access

        """
        classname = classname.strip()
        self.instances[classname] = {}
        
        # register class methods so they are available with get%CLASS%(id)
        getter = lambda id: self.instances[classname][(id, id[1:])[id[0] == '@']]
        getter.__name__ = "get"+classname.capitalize()
        setattr(self, getter.__name__, getter)
        
        # register getAll%Class%Instances method
        getter = lambda : self.instances[classname]
        logging.debug("Registering %s ", "getAll"+classname.capitalize()+"Instances")
        getter.__name__ = "getAll"+classname.capitalize()+"Instances"
        setattr(self, getter.__name__, getter)
        
    def __getitem__(self, id):
        """
        Returns the object instance that can be found under the id "id"
    """
        if id[0] == '@':
            id = id[1:]
        if id in self.instances:
            return self.instances[id]
        if id in self.instances["all"]:
            return self.instances["all"][id]
        return None
        
    
    
