import ConfigParser
import logging
import os
from event import matcher

__all__=['ChainFactory']

class Chain(object):
    
    def setup(self,id, config):
        self.id = id
        
        if config["matcher"] == "all" :
            self.matcher = None
        else:
            self.matcher = matcher.Matcher(config["matcher"])
        
class ChainFactory(object):
    
    def read_config_file(self,chaindir,instances):
        self.instances = instances
        if not os.path.exists(chaindir):
            raise Exception("Chain configuration directory is non-existent or not readable")
        self.configReader = ConfigParser.ConfigParser()
        self.__read_dir(chaindir)
       
        self.__wire_chains()
        
    def __read_dir(self,curDir):
         for cfg in os.listdir(curDir):
            logging.debug("Reading chain %s " % cfg)
            filename = curDir+"/"+cfg
            if  os.path.isdir(filename) :
                self.__read_dir(filename)
            else:
                if filename[-5:] == 'chain':
                    self.configReader.readfp(open(filename))
        
    def __wire_chains(self):
        for section in self.configReader.sections():
            id = section
            chain = self.__read_chain(section)
    
    def __read_chain(self,id):
        chainDef = {'class': 'chain', 'type' : ''}
        for i in self.configReader.options(id):
            chainDef[i] = self.configReader.get(id,i)
        self.instances.register(id,chainDef,self.create_chain)
        
    def create_chain(self,id,config):
        chain = Chain()
        chain.setup(id,config)
        return None