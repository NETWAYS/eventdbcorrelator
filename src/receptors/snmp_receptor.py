from receptors import PipeReceptor
import logging
import os 

class SnmpReceptor(PipeReceptor):
    
    def setup(self,id,config):
        self.id = id
        self.running = False
        self.callback = None
        self.config = {
            "mod": 0774,
            "owner": os.getuid(),
            "group": os.getgid(),
            "handler" : "/usr/local/edbc/bin/edbc_traphandler",
            "path" : "/usr/local/edbc/bin/edbc_traphandler.pipe",
            "handler_tpl" : "/usr/local/edbc/share/snmp_handler_template",
            "bufferSize" : 2048,
            "format" : None
        }
        if "handler" in config and not "path" in config:
            self.config["path"] = config["handler"]+".pipe"
            
        self.runFlags = os.O_RDONLY|os.O_NONBLOCK
        
        for key in config.keys():
            if key == 'owner':
                config[key] = pwd.getpwnam(config[key]).pw_uid
            else:
                if key == 'group':
                    config[key] = pwd.getpwnam(config[key]).pw_gid
                else:
                    self.config[key] = config[key]
        
        if "source_type" in self.config:
            self.source = self.config["source_type"]
        else:
            self.source = "snmp"
            
        if not os.path.exists(self.config["handler_tpl"]):
            logging.error("SNMP handler %s can't be created: %s doesn't exist." % (self.id,self.config["handler_tpl"]))
            return 

        self.pipe = None
        self.queues = []
        PipeReceptor.setup_pipe(self)
        self.__create_handler()
        
        
    def __create_handler(self):
        #logging.debug("Setting up PipeReceptor with %s" % self.config)
        if os.path.exists(self.config["handler"]):
            os.remove(self.config["handler"])
        handler_tpl = open(self.config["handler_tpl"],"r")
        trap_app = ""
        for line in handler_tpl:
            trap_app += line
        handler_tpl.close()

        trap_app = trap_app % ({"PIPE": self.config["path"] })
        file = open(self.config["handler"],"w+")
        file.write(trap_app)
        file.close()
        os.chown(self.config["handler"],self.config["owner"],self.config["group"])
        os.chmod(self.config["handler"],self.config["mod"])