'''
Pseudo persister that forfeits the event 
'''
import logging
from abstract_persister import AbstractPersister

class SqlPersister(AbstractPersister):
    def setup(self,id,config):
        self.id = id
        
        self.datasource = config["datasource"]
       
            
    def process(self,event):
        logging.debug("Inserting %s" % event)
        return self.datasource.insert(event)
    
