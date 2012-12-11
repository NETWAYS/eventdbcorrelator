import ConfigParser
import logging
import os

from chain import Chain

__all__=['ChainFactory']

'''
Factory that handles chain registration and creation. Chains are created in a three 
step process: 
- Create and register all chains and call the setup() method directly after chain
  creation
- After all chains are created, call the setupEventPath() method for each chain.
  As chains may reference other chains, every instance must be existing for this
  step
- Now call the start method for each chain, causing the chain to accept events in
  a newly created thread (except "noThread" has been set in the config, but this
  should only be used for test cases)
  
'''
class ChainFactory(object):
    def __init(self):
        self.chains = []
        
    def read_config_file(self,chaindir,instances):
        self.instances = instances
        if not os.path.exists(chaindir):
            raise Exception("Chain configuration directory is non-existent or not readable")
        self.configReader = ConfigParser.ConfigParser()
        self.read_dir(chaindir)
        self.create_chain_instances()
        self.wire_chains()
        self.start_chains()
        
    def read_dir(self,curDir):
         for cfg in os.listdir(curDir):
            if cfg[0] == ".":
                continue
            logging.debug("Reading chain %s " % cfg)
            filename = curDir+"/"+cfg
            # recursive read 
            if  os.path.isdir(filename) :
                self.read_dir(filename)
            else:
                if filename[-5:] == 'chain':
                    self.configReader.readfp(open(filename))
        
    def create_chain_instances(self):
        for section in self.configReader.sections():
            self.read_chain(section)
        
    def read_chain(self,id):
        chainDef = {'class': 'chain', 'type' : ''}
        for i in self.configReader.options(id):
            chainDef[i] = self.configReader.get(id,i)
        logging.debug("Registering chain %s", id)
        self.instances.register(id,chainDef,self.create_chain)
 
        
    def create_chain(self,id,config):
        chain = Chain()
        config["instances"] = self.instances
        chain.setup(id,config)
        
        return chain

    def wire_chains(self):
        allChains = self.instances.getAllChainInstances()
        for chain in allChains:
            logging.debug("%s" % chain)
            allChains[chain].setup_event_path()
    
    def start_chains(self):
        allChains = self.instances.getAllChainInstances()
        for chain in allChains:
            allChains[chain].start()
            
            