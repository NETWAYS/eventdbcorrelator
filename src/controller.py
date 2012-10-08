# To change this template, choose Tools | Templates
# and open the template in the editor.
from event import *
from chain import ChainFactory
import logging

class Controller:
    
    def __init__(self,config,instances):
        self.config = config
        self.instances = instances
        self.threads = []
        self.__setup_receptors()
        try:
            self.__read_chain_definitions()        
            self.__lay_back_and_wait()
        finally:
            self.shutdown()
        
    
    def __setup_receptors(self):
        
        logging.debug("Receptors registered: %s" % self.instances["receptor"])
        for id in self.instances["receptor"]:
            receptor = self.instances["receptor"][id]
            if receptor.config["format"] != None:
                receptor.config["transformer"] = self.instances.getTransformer(receptor.config["format"])
            receptor.start()
            self.threads.append(receptor)
        
    def __read_chain_definitions(self):
        self.chainFactory = ChainFactory()
        chains = self.chainFactory.read_config_file(self.config["chain_dir"],self.instances)
        
        
        
    def __lay_back_and_wait(self):
        try:
            while True:
                for thread in self.threads:
                    thread.join(5)        
        except:
            pass
        logging.debug("Attempting shutdown...")

    def shutdown(self):
        logging.info("Stopping chains")
        chains = self.instances.getAllChainInstances()
        for chain in chains:
            chains[chain].stop()

        logging.info("Stopping receptors")
        for thread in self.threads:
            thread.stop()