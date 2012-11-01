import logging

class SqlPersister(object):
    def setup(self,id,config):
        self.id = id
        self.datasource = config["datasource"]
       
            
    
    